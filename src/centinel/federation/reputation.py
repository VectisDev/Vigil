"""
Persistent Bayesian Trust Model (PBTM) for Centinel Swarm nodes.

Each node's trustworthiness is modelled as a Beta distribution:
    Trust = (α + 1) / (α + β + 2)

α grows with consistent fingerprints; β grows with divergences.
Silent outages receive a tiny reversible β so honest nodes that lose
power don't suffer the same penalty as nodes that deliberately lie.
"""
from __future__ import annotations

import logging
import math
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_RING1_SCORE = 0.85     # promote to Ring-1 when trust ≥ this
_RING2_DEMOTION = 0.40  # demote Ring-1 → Ring-2 when trust drops below this

_ALPHA_CONSISTENT = 1.0    # reward: fingerprint matches Ring-0 consensus
_ALPHA_RESTORE = 1.0       # reward: returned after outage with consistent data
_BETA_OUTAGE = 0.1         # tiny tentative penalty for silent timeout
_BETA_BETRAYAL = 5.0       # heavy penalty for divergent fingerprints

_HALFLIFE_ALPHA_DAYS = 14.0  # positive evidence half-life
_HALFLIFE_BETA_DAYS  = 30.0  # negative evidence half-life (betrayal remembered longer)

_DB_FILENAME = "federation_reputation.db"
_DECAY_INTERVAL_SECONDS = 86400.0  # run decay once per 24 hours

logger = logging.getLogger("centinel.federation.reputation")


@dataclass
class NodeReputation:
    node_id: str
    alpha: float = 1.0         # Beta prior — start neutral (1,1) → trust = 0.5
    beta: float = 1.0
    ring: int = 2              # 0=seed/Ring-0, 1=trusted, 2=observer
    arrival_order: int = -1    # monotone counter when node was first seen
    country_code: str = "HN"
    last_seen_utc: Optional[str] = None
    last_updated_utc: Optional[str] = None
    outage_count: int = 0
    betrayal_count: int = 0
    _pending_outage_beta: float = 0.0  # reversible β added during current outage
    _cached_trust_score: Optional[float] = None  # Cached trust score, invalidated on α/β change

    @property
    def trust_score(self) -> float:
        if self._cached_trust_score is None:
            self._cached_trust_score = (self.alpha + 1.0) / (self.alpha + self.beta + 2.0)
        return self._cached_trust_score

    def _invalidate_trust_cache(self) -> None:
        """Invalidate cached trust score when α or β changes."""
        self._cached_trust_score = None

    def _refresh_ring(self, ring0_ids: set[str]) -> None:
        if self.node_id in ring0_ids:
            self.ring = 0
            return
        if self.ring == 0:
            return  # Ring-0 is manually designated, never auto-demoted
        score = self.trust_score
        if score >= _RING1_SCORE:
            self.ring = 1
        elif score < _RING2_DEMOTION and self.ring == 1:
            self.ring = 2


class ReputationEngine:
    """Thread-safe Bayesian reputation store for Centinel swarm nodes (max 12)."""

    def __init__(
        self,
        ring0_node_ids: Optional[list[str]] = None,
        db_path: Optional[Path] = None,
    ) -> None:
        self._ring0: set[str] = set(ring0_node_ids or [])
        self._nodes: dict[str, NodeReputation] = {}
        self._counter = 0
        self._lock = threading.Lock()
        self._db_path = db_path
        self._decay_timer: Optional[threading.Timer] = None
        if db_path:
            self._init_db(db_path)
            self._load_db(db_path)
            self._schedule_decay()

    # ── decay scheduler ──────────────────────────────────────────────────────

    def _schedule_decay(self) -> None:
        self._decay_timer = threading.Timer(_DECAY_INTERVAL_SECONDS, self._run_decay)
        self._decay_timer.daemon = True
        self._decay_timer.start()

    def _run_decay(self) -> None:
        try:
            self.decay()
            logger.info("reputation_decay_completed nodes=%d", len(self._nodes))
        except Exception as exc:
            logger.warning("reputation_decay_error error=%s", exc)
        finally:
            self._schedule_decay()

    def stop(self) -> None:
        """Cancel the background decay scheduler. Call on process shutdown."""
        if self._decay_timer:
            self._decay_timer.cancel()
            self._decay_timer = None

    # ── persistence ──────────────────────────────────────────────────────────

    def _init_db(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS node_reputation (
                    node_id TEXT PRIMARY KEY,
                    alpha REAL NOT NULL DEFAULT 1.0,
                    beta REAL NOT NULL DEFAULT 1.0,
                    ring INTEGER NOT NULL DEFAULT 2,
                    arrival_order INTEGER NOT NULL DEFAULT -1,
                    country_code TEXT NOT NULL DEFAULT 'HN',
                    last_seen_utc TEXT,
                    last_updated_utc TEXT,
                    outage_count INTEGER NOT NULL DEFAULT 0,
                    betrayal_count INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reputation_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    alpha REAL NOT NULL,
                    beta REAL NOT NULL,
                    trust_score REAL NOT NULL,
                    ring INTEGER NOT NULL,
                    ts TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rep_events_node ON reputation_events(node_id)")
            conn.commit()

    def _load_db(self, path: Path) -> None:
        try:
            with sqlite3.connect(str(path)) as conn:
                rows = conn.execute(
                    "SELECT node_id, alpha, beta, ring, arrival_order, country_code,"
                    " last_seen_utc, last_updated_utc, outage_count, betrayal_count"
                    " FROM node_reputation"
                ).fetchall()
            for row in rows:
                rep = NodeReputation(
                    node_id=row[0], alpha=row[1], beta=row[2], ring=row[3],
                    arrival_order=row[4], country_code=row[5],
                    last_seen_utc=row[6], last_updated_utc=row[7],
                    outage_count=row[8], betrayal_count=row[9],
                )
                self._nodes[rep.node_id] = rep
                if rep.arrival_order >= self._counter:
                    self._counter = rep.arrival_order + 1
        except Exception as exc:
            logger.warning("reputation_load_rows_error error=%s", exc)

    def _record_event(self, rep: NodeReputation, event_type: str, ts: str) -> None:
        """Append a reputation event row for forensic audit trail (30-day TTL)."""
        if not self._db_path:
            return
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                conn.execute(
                    "INSERT INTO reputation_events"
                    " (node_id, event_type, alpha, beta, trust_score, ring, ts)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (rep.node_id, event_type, round(rep.alpha, 4),
                     round(rep.beta, 4), round(rep.trust_score, 4), rep.ring, ts),
                )
                # Cleanup old events (>30 days) to prevent DB bloat
                conn.execute(
                    "DELETE FROM reputation_events WHERE ts < datetime('now', '-30 days')"
                )
                conn.commit()
        except Exception as exc:
            logger.warning("reputation_record_event_error node_id=%s error=%s", rep.node_id, exc)

    def _save(self, rep: NodeReputation) -> None:
        if not self._db_path:
            return
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                conn.execute("""
                    INSERT INTO node_reputation
                        (node_id, alpha, beta, ring, arrival_order, country_code,
                         last_seen_utc, last_updated_utc, outage_count, betrayal_count)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(node_id) DO UPDATE SET
                        alpha=excluded.alpha, beta=excluded.beta, ring=excluded.ring,
                        last_seen_utc=excluded.last_seen_utc,
                        last_updated_utc=excluded.last_updated_utc,
                        outage_count=excluded.outage_count,
                        betrayal_count=excluded.betrayal_count
                """, (
                    rep.node_id, rep.alpha, rep.beta, rep.ring, rep.arrival_order,
                    rep.country_code, rep.last_seen_utc, rep.last_updated_utc,
                    rep.outage_count, rep.betrayal_count,
                ))
                conn.commit()
        except Exception as exc:
            logger.warning("reputation_save_error node_id=%s error=%s", rep.node_id, exc)

    # ── public API ────────────────────────────────────────────────────────────

    def ensure(self, node_id: str, country_code: str = "HN") -> NodeReputation:
        """Return existing reputation or create a neutral one with the next arrival order."""
        with self._lock:
            if node_id not in self._nodes:
                rep = NodeReputation(
                    node_id=node_id,
                    arrival_order=self._counter,
                    country_code=country_code,
                )
                self._counter += 1
                rep._refresh_ring(self._ring0)
                self._nodes[node_id] = rep
                self._save(rep)
            return self._nodes[node_id]

    def on_consistent(self, node_id: str) -> NodeReputation:
        """Node sent fingerprints consistent with Ring-0 consensus."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            rep = self._nodes.get(node_id)
            if rep is None:
                return self.ensure(node_id)
            prev_ring = rep.ring
            rep.alpha += _ALPHA_CONSISTENT
            rep._invalidate_trust_cache()
            rep.last_seen_utc = now
            rep.last_updated_utc = now
            rep._refresh_ring(self._ring0)
            self._save(rep)
            if rep.ring != prev_ring:
                self._record_event(rep, f"RING_PROMOTED_{prev_ring}_TO_{rep.ring}", now)
            return rep

    def on_inconsistent(self, node_id: str) -> NodeReputation:
        """Node fingerprints diverged from Ring-0 consensus → heavy β penalty."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            rep = self._nodes.get(node_id)
            if rep is None:
                return self.ensure(node_id)
            prev_ring = rep.ring
            rep.beta += _BETA_BETRAYAL
            rep._invalidate_trust_cache()
            rep.betrayal_count += 1
            rep.last_updated_utc = now
            rep._refresh_ring(self._ring0)
            self._save(rep)
            self._record_event(rep, "BETRAYAL", now)
            if rep.ring != prev_ring:
                self._record_event(rep, f"RING_DEMOTED_{prev_ring}_TO_{rep.ring}", now)
            return rep

    def on_timeout(self, node_id: str) -> NodeReputation:
        """Node went silent — tentative outage (tiny reversible β)."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            rep = self._nodes.get(node_id)
            if rep is None:
                return self.ensure(node_id)
            rep.beta += _BETA_OUTAGE
            rep._invalidate_trust_cache()
            rep._pending_outage_beta += _BETA_OUTAGE
            rep.outage_count += 1
            rep.last_updated_utc = now
            rep._refresh_ring(self._ring0)
            self._save(rep)
            return rep

    def on_restore_consistent(self, node_id: str) -> NodeReputation:
        """Node returned after silence with data matching the rest of the swarm.

        The outage β is reversed — the node was honest, just offline.
        A small α bonus rewards the eventual contribution.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            rep = self._nodes.get(node_id)
            if rep is None:
                return self.ensure(node_id)
            rep.beta = max(1.0, rep.beta - rep._pending_outage_beta)
            rep._pending_outage_beta = 0.0
            rep.alpha += _ALPHA_RESTORE
            rep._invalidate_trust_cache()
            rep.last_seen_utc = now
            rep.last_updated_utc = now
            rep._refresh_ring(self._ring0)
            self._save(rep)
            return rep

    def on_restore_inconsistent(self, node_id: str) -> NodeReputation:
        """Node returned after silence with divergent data → reclassified as betrayal."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            rep = self._nodes.get(node_id)
            if rep is None:
                return self.ensure(node_id)
            prev_ring = rep.ring
            rep._pending_outage_beta = 0.0  # outage β is not reversed; betrayal overrides
            rep.beta += _BETA_BETRAYAL
            rep.betrayal_count += 1
            rep.last_updated_utc = now
            rep._refresh_ring(self._ring0)
            self._save(rep)
            self._record_event(rep, "RESTORE_BETRAYAL", now)
            if rep.ring != prev_ring:
                self._record_event(rep, f"RING_DEMOTED_{prev_ring}_TO_{rep.ring}", now)
            return rep

    def decay(self) -> None:
        """Exponential half-life decay. Call once daily."""
        now = datetime.now(timezone.utc)
        with self._lock:
            for rep in self._nodes.values():
                if not rep.last_updated_utc:
                    continue
                try:
                    last = datetime.fromisoformat(rep.last_updated_utc)
                except ValueError:
                    continue
                days = (now - last).total_seconds() / 86400.0
                if days < 0.1:
                    continue
                rep.alpha = max(1.0, rep.alpha * math.pow(0.5, days / _HALFLIFE_ALPHA_DAYS))
                rep.beta  = max(1.0, rep.beta  * math.pow(0.5, days / _HALFLIFE_BETA_DAYS))
                rep._invalidate_trust_cache()
                rep._refresh_ring(self._ring0)

    # ── queries ───────────────────────────────────────────────────────────────

    def get_trust(self, node_id: str) -> float:
        with self._lock:
            rep = self._nodes.get(node_id)
            return rep.trust_score if rep else 0.5

    def get_ring(self, node_id: str) -> int:
        with self._lock:
            rep = self._nodes.get(node_id)
            return rep.ring if rep else 2

    def arrival_order(self, node_id: str) -> int:
        with self._lock:
            rep = self._nodes.get(node_id)
            return rep.arrival_order if rep else -1

    def get_all(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "node_id": rep.node_id,
                    "trust_score": round(rep.trust_score, 4),
                    "ring": rep.ring,
                    "alpha": round(rep.alpha, 3),
                    "beta": round(rep.beta, 3),
                    "arrival_order": rep.arrival_order,
                    "outage_count": rep.outage_count,
                    "betrayal_count": rep.betrayal_count,
                    "last_seen_utc": rep.last_seen_utc,
                    "country_code": rep.country_code,
                }
                for rep in sorted(self._nodes.values(), key=lambda r: r.arrival_order)
            ]

    def ring_counts(self) -> dict[str, int]:
        with self._lock:
            counts = {0: 0, 1: 0, 2: 0}
            for rep in self._nodes.values():
                counts[rep.ring] = counts.get(rep.ring, 0) + 1
            return {"ring0": counts[0], "ring1": counts[1], "ring2": counts[2]}

    def get_history(self, node_id: str, limit: int = 100) -> list[dict]:
        """Return recent reputation events for a node (forensic audit trail)."""
        if not self._db_path:
            return []
        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                rows = conn.execute(
                    "SELECT event_type, alpha, beta, trust_score, ring, ts"
                    " FROM reputation_events WHERE node_id=?"
                    " ORDER BY id DESC LIMIT ?",
                    (node_id, limit),
                ).fetchall()
            return [
                {"event_type": r[0], "alpha": r[1], "beta": r[2],
                 "trust_score": r[3], "ring": r[4], "ts": r[5]}
                for r in rows
            ]
        except Exception as exc:
            logger.warning("reputation_get_history_error node_id=%s error=%s", node_id, exc)
            return []
