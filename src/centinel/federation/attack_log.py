"""
FederationAttackLog — SQLite-backed persistent store for swarm-targeted attacks.

Only persists attacks to Centinel-specific paths or sustained DoS — filters
generic internet scan noise that is not relevant to other monitoring nodes.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from centinel.federation.gossip import FindingPayload

logger = logging.getLogger("centinel.federation.attack_log")

_SWARM_PATHS: frozenset[str] = frozenset(
    {
        "/api/swarm/",
        "/api/swarm/attest",
        "/api/swarm/finding",
        "/api/swarm/anomalies",
        "/api/swarm/attacks",
        "/api/swarm/status",
        "/api/swarm/connect",
        "/hashchain/verify",
        "/api/health",
        "/api/summaries",
        "/api/national-snapshot",
        "/api/departments/status",
        "/live",
    }
)

_DOS_FREQUENCY_THRESHOLD = 50
_DB_FILENAME = "federation_attacks.db"


class FederationAttackLog:
    """SQLite-backed persistent store for swarm-directed attacks.

    An attack is "directed" if it targets Centinel-specific paths or exceeds the
    sustained DoS threshold. Generic internet scan noise is discarded via
    is_swarm_targeted().
    """

    ACCEPTED_TYPE = "swarm_attack"

    def __init__(
        self,
        max_findings: int = 300,
        log_path: Optional[Path] = None,
        dos_frequency_threshold: int = _DOS_FREQUENCY_THRESHOLD,
    ) -> None:
        self._max = max_findings
        self._log_path = log_path
        self._dos_threshold = dos_frequency_threshold
        self._lock = threading.Lock()

        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._db_path: Optional[str] = str(log_path.parent / _DB_FILENAME)
            self._mem_conn: Optional[sqlite3.Connection] = None
        else:
            self._db_path = None
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)

        self._init_db()

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn  # reuse single in-memory connection
        conn = sqlite3.connect(self._db_path, check_same_thread=False)  # type: ignore[arg-type]
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            owned = self._mem_conn is None
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.row_factory = sqlite3.Row
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS findings (
                        finding_id   TEXT PRIMARY KEY,
                        node_id      TEXT,
                        country_code TEXT,
                        finding_type TEXT,
                        severity     TEXT,
                        rule_key     TEXT,
                        summary      TEXT,
                        timestamp_utc TEXT,
                        source       TEXT,
                        received_utc TEXT,
                        payload_json TEXT
                    )
                """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON findings(timestamp_utc DESC)")
                conn.commit()
            finally:
                if owned:
                    conn.close()

    def _close(self, conn: sqlite3.Connection) -> None:
        """Close connection only if it is not the shared in-memory connection."""
        if conn is not self._mem_conn:
            conn.close()

    def _evict(self, conn: sqlite3.Connection) -> None:
        count = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
        if count > self._max:
            excess = count - self._max
            conn.execute(
                """
                DELETE FROM findings WHERE finding_id IN (
                    SELECT finding_id FROM findings
                    ORDER BY timestamp_utc ASC
                    LIMIT ?
                )
            """,
                (excess,),
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def is_swarm_targeted(self, event: dict) -> bool:
        """True if the attack targets Centinel paths or is sustained DoS.

        Filters generic internet scan noise (wp-login, /admin, etc.) that is
        not relevant to other monitoring nodes in the surveillance network.
        """
        route = event.get("route", "")
        frequency = int(event.get("frequency_count", 0))
        if any(route == p or route.startswith(p) for p in _SWARM_PATHS):
            return True
        if frequency >= self._dos_threshold:
            return True
        return False

    def add(self, finding: "FindingPayload", source: str = "remote") -> bool:
        """Add attack to the store. Returns True if new (not a duplicate)."""
        if finding.finding_type != self.ACCEPTED_TYPE:
            return False

        received_utc = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(finding.to_dict(), ensure_ascii=False)

        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    "SELECT 1 FROM findings WHERE finding_id = ?",
                    (finding.finding_id,),
                )
                if cur.fetchone():
                    return False

                conn.execute(
                    """
                    INSERT INTO findings (
                        finding_id, node_id, country_code, finding_type,
                        severity, rule_key, summary,
                        timestamp_utc, source, received_utc, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        finding.finding_id,
                        finding.node_id,
                        finding.country_code,
                        finding.finding_type,
                        finding.severity,
                        finding.rule_key,
                        finding.summary,
                        finding.timestamp_utc,
                        source,
                        received_utc,
                        payload_json,
                    ),
                )
                self._evict(conn)
                conn.commit()

                if self._log_path:
                    self._append_jsonl(
                        {
                            **finding.to_dict(),
                            "_source": source,
                            "_received_utc": received_utc,
                        }
                    )
            finally:
                self._close(conn)

        logger.info(
            "federation_attack_added finding_id=%s rule=%s severity=%s source=%s",
            finding.finding_id,
            finding.rule_key,
            finding.severity,
            source,
        )
        return True

    def query(
        self,
        since_utc: Optional[str] = None,
        node_id: Optional[str] = None,
        rule_key: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Query attacks with optional filters, most recent first."""
        sql = "SELECT payload_json, source, received_utc FROM findings WHERE 1=1"
        params: list = []
        if since_utc:
            sql += " AND timestamp_utc >= ?"
            params.append(since_utc)
        if node_id:
            sql += " AND node_id = ?"
            params.append(node_id)
        if rule_key:
            sql += " AND rule_key = ?"
            params.append(rule_key)
        sql += " ORDER BY timestamp_utc DESC LIMIT ?"
        params.append(limit)

        conn = self._connect()
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            self._close(conn)

        result = []
        for row in rows:
            try:
                entry = json.loads(row[0])
                entry["_source"] = row[1]
                entry["_received_utc"] = row[2]
                result.append(entry)
            except Exception:
                pass
        return result

    def stats(self) -> dict:
        """Summary of stored attacks."""
        conn = self._connect()
        try:
            total = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
            by_node = {
                r[0]: r[1] for r in conn.execute("SELECT node_id, COUNT(*) FROM findings GROUP BY node_id").fetchall()
            }
            by_rule = {
                r[0]: r[1] for r in conn.execute("SELECT rule_key, COUNT(*) FROM findings GROUP BY rule_key").fetchall()
            }
        finally:
            self._close(conn)
        return {
            "total": total,
            "by_node": by_node,
            "by_rule": by_rule,
        }

    def _append_jsonl(self, entry: dict) -> None:
        try:
            with self._log_path.open("a", encoding="utf-8") as fh:  # type: ignore[union-attr]
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("federation_attack_log_write_error error=%s", exc)
