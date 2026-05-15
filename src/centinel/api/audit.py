"""Public audit endpoints for independent third-party verification.

This router exposes read-only endpoints that any external observer (OAS, EU,
Carter Center, NDI, citizen auditors, academics) can call without authentication
to verify the cryptographic chain of custody of captured electoral data.

Design principles:
- No authentication: data is public by mandate (CNE transparency law).
- No state mutation: every endpoint is a pure read.
- Deterministic: same inputs produce same outputs across deployments.
- Self-describing: responses include enough metadata for offline reproduction.

Endpoints:
    GET /audit/health             — audit subsystem readiness probe
    GET /audit/chain/verify       — full hash-chain integrity verification
    GET /audit/timeline           — chronological snapshot index
    GET /audit/snapshots/{date}   — snapshots captured on a given UTC date
    GET /audit/proof/{hash}       — inclusion proof for a specific snapshot hash

Bilingual / Bilingüe:
    Endpoints publicos de auditoria para verificacion independiente por
    terceros. Cualquier observador externo (OEA, UE, Carter Center, NDI,
    auditores ciudadanos, academicos) puede llamarlos sin autenticacion para
    verificar la cadena criptografica de custodia de los datos electorales.
"""

from __future__ import annotations

import json
from datetime import date as date_cls
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..hasher import (
    _SHA256_HEX_RE,
    collect_snapshot_entries,
    verify_hashchain_from_snapshots,
)

router = APIRouter(prefix="/audit", tags=["audit"])


_DEFAULT_SNAPSHOT_ROOT = Path("data") / "snapshots"


def _resolve_snapshot_root() -> Path:
    """Return the canonical snapshot directory for audit operations."""
    return _DEFAULT_SNAPSHOT_ROOT


def _serialize_entry(entry: Any) -> Dict[str, Any]:
    """Convert a SnapshotEntry into a JSON-serializable summary."""
    return {
        "path": str(entry.snapshot_dir),
        "expected_hash": entry.expected_hash,
        "previous_hash": entry.previous_hash,
        "timestamp_utc": entry.timestamp.astimezone(timezone.utc).isoformat(
            timespec="microseconds"
        ),
        "source_url": entry.metadata.get("source_url"),
        "software_version": entry.metadata.get("software_version"),
    }


@router.get("/health")
def audit_health() -> Dict[str, Any]:
    """Audit-subsystem readiness probe.

    Returns 200 with structural metadata about the audit surface. Used by
    external observers to confirm the deployment is reachable and exposes
    verifiable data before launching a full chain verification.
    """
    snapshot_root = _resolve_snapshot_root()
    return {
        "status": "ok",
        "subsystem": "audit",
        "server_time_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "snapshot_root": str(snapshot_root),
        "snapshot_root_exists": snapshot_root.exists(),
        "endpoints": [
            "/audit/health",
            "/audit/chain/verify",
            "/audit/timeline",
            "/audit/snapshots/{date}",
            "/audit/proof/{hash}",
        ],
        "no_auth_required": True,
        "data_license": "Public — CNE transparency law (Decreto 170-2006 Honduras)",
    }


@router.get("/chain/verify")
def audit_chain_verify() -> Dict[str, Any]:
    """Full hash-chain integrity verification.

    Reads every snapshot under the configured snapshot root, recomputes each
    chained hash, and reports either complete validity or the exact break
    point (broken_at index + filesystem path + diagnostic error).

    External auditors can run this against any deployment and compare the
    'last_valid_hash' across independent mirrors to detect divergence.
    """
    snapshot_root = _resolve_snapshot_root()
    if not snapshot_root.exists():
        return {
            "valid": True,
            "count": 0,
            "verified_count": 0,
            "last_valid_hash": None,
            "broken_at": None,
            "broken_at_path": None,
            "errors": [],
            "note": "snapshot_root_missing — no data captured yet",
        }
    result = verify_hashchain_from_snapshots(snapshot_root)
    result["snapshot_root"] = str(snapshot_root)
    result["verified_at_utc"] = datetime.now(timezone.utc).isoformat(
        timespec="microseconds"
    )
    return result


@router.get("/timeline")
def audit_timeline(
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> Dict[str, Any]:
    """Chronological snapshot index ordered by capture timestamp.

    Returns paginated metadata (no payload bodies) so auditors can scan the
    full timeline and request specific snapshots by hash via /audit/proof.
    """
    snapshot_root = _resolve_snapshot_root()
    if not snapshot_root.exists():
        return {
            "total": 0,
            "offset": offset,
            "limit": limit,
            "entries": [],
        }
    entries = collect_snapshot_entries(snapshot_root)
    total = len(entries)
    window = entries[offset : offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "entries": [_serialize_entry(entry) for entry in window],
    }


@router.get("/snapshots/{day}")
def audit_snapshots_by_day(day: str) -> Dict[str, Any]:
    """Snapshots captured on a given UTC date (YYYY-MM-DD).

    Used by auditors to inspect a specific election-day window or to
    reconstruct events around a reported anomaly.
    """
    try:
        target = date_cls.fromisoformat(day)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="invalid_date_format — expected YYYY-MM-DD (UTC)",
        )

    snapshot_root = _resolve_snapshot_root()
    if not snapshot_root.exists():
        return {"date_utc": day, "count": 0, "entries": []}

    entries = collect_snapshot_entries(snapshot_root)
    matching = [
        entry
        for entry in entries
        if entry.timestamp.astimezone(timezone.utc).date() == target
    ]
    return {
        "date_utc": day,
        "count": len(matching),
        "entries": [_serialize_entry(entry) for entry in matching],
    }


@router.get("/proof/{snapshot_hash}")
def audit_proof_for_hash(snapshot_hash: str) -> Dict[str, Any]:
    """Inclusion proof for a specific snapshot hash.

    Locates the snapshot identified by its canonical SHA-256 hex digest and
    returns its full metadata, previous-hash linkage, and the position of
    its predecessor in the chain (so the verifier can independently confirm
    the chained_hash by re-running compute_snapshot_hash locally).
    """
    if not _SHA256_HEX_RE.match(snapshot_hash):
        raise HTTPException(
            status_code=400,
            detail="invalid_hash_format — expected 64-char lowercase hex SHA-256",
        )

    snapshot_root = _resolve_snapshot_root()
    if not snapshot_root.exists():
        raise HTTPException(status_code=404, detail="snapshot_root_missing")

    entries = collect_snapshot_entries(snapshot_root)
    target_idx: Optional[int] = None
    for idx, entry in enumerate(entries):
        if entry.expected_hash == snapshot_hash:
            target_idx = idx
            break
    if target_idx is None:
        raise HTTPException(status_code=404, detail="hash_not_found_in_chain")

    target = entries[target_idx]
    predecessor = entries[target_idx - 1] if target_idx > 0 else None
    return {
        "snapshot_hash": snapshot_hash,
        "position": target_idx,
        "chain_length": len(entries),
        "snapshot": _serialize_entry(target),
        "predecessor": _serialize_entry(predecessor) if predecessor else None,
        "metadata": target.metadata,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(
            timespec="microseconds"
        ),
        "verification_instructions": (
            "Reproduce locally: compute_snapshot_hash(content, metadata, "
            "predecessor.expected_hash) must equal snapshot_hash."
        ),
    }
