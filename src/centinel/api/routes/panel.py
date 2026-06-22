"""
Panel Operador — Rutas API
Operador Panel — API Routes

Endpoint `/operator/panel` que retorna estado del sistema en formato JSON.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Query

from centinel.core.argos_protocol import ArgosLayer

router = APIRouter(prefix="/operator", tags=["operator"])


@router.get("/panel")
async def get_panel(
    verbose: bool = Query(False, description="Incluir detalles verbosos / Include verbose details")
) -> Dict[str, Any]:
    """
    Retorna estado del panel operador.
    (Return operador panel status.)

    **Threat Score:**
    - 🟢 GREEN: 0–30 (operación normal)
    - 🟡 YELLOW: 31–74 (anomalía detectada)
    - 🔴 RED: ≥75 (amenaza activa)

    **Protocolo ARGOS — Capas:**
    - 🐦 Corvid: Memoria distribuida
    - 🦑 Cephalopod: Cifrado tránsito
    - 🦌 Evasion: Jitter timing
    - 🦎 Regeneration: Auto-healing
    - ⚔️ Kill Switch: Congelación + recuperación

    """
    threat_score = 22  # Placeholder: cargar desde estado real

    # Determinar color/status
    if threat_score < 31:
        status = "🟢 GREEN"
    elif threat_score < 75:
        status = "🟡 YELLOW"
    else:
        status = "🔴 RED"

    # Construir respuesta
    response = {
        "threat_score": threat_score,
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "defenses": {
            "corvid": {
                "emoji": ArgosLayer.CORVID.emoji,
                "name_es": ArgosLayer.CORVID.name_es,
                "title_es": ArgosLayer.CORVID.title_es,
                "enabled": True,
                "last_check_ts": 1715851800.0,
                "last_attestation": "2m ago",
                "siblings_online": 2,
            },
            "cephalopod": {
                "emoji": ArgosLayer.CEPHALOPOD.emoji,
                "name_es": ArgosLayer.CEPHALOPOD.name_es,
                "title_es": ArgosLayer.CEPHALOPOD.title_es,
                "enabled": True,
                "last_check_ts": 1715851800.0,
                "cipher": "chacha20poly1305",
                "key_hash": "abc123def456...",
                "last_encrypted_messages": 2847,
            },
            "evasion": {
                "emoji": ArgosLayer.EVASION.emoji,
                "name_es": ArgosLayer.EVASION.name_es,
                "title_es": ArgosLayer.EVASION.title_es,
                "enabled": True,
                "last_check_ts": 1715851800.0,
                "jitter_percent": 30,
                "base_interval_seconds": 30,
                "last_snapshot_seconds_ago": 30,
            },
            "regeneration": {
                "emoji": ArgosLayer.REGENERATION.emoji,
                "name_es": ArgosLayer.REGENERATION.name_es,
                "title_es": ArgosLayer.REGENERATION.title_es,
                "enabled": True,
                "last_check_ts": 1715851800.0,
                "mirrors_online": 3,
                "mirrors_total": 3,
                "last_sync_hours_ago": 2,
            },
            "kill_switch": {
                "emoji": ArgosLayer.KILL_SWITCH.emoji,
                "name_es": ArgosLayer.KILL_SWITCH.name_es,
                "title_es": ArgosLayer.KILL_SWITCH.title_es,
                "status": "READY",
                "activated": False,
                "frozen_at": None,
                "recovery_attempts": 0,
            },
        },
        "metrics": {
            "merkle_root": "abc123def456abc123def456",
            "merkle_age_seconds": 120,
            "benford_anomalies": 0,
            "zscore_anomalies": 0,
            "connectivity": {
                "endpoints_total": 4,
                "endpoints_up": 4,
                "pct_up": 100,
            },
            "snapshots_total": 2847,
            "last_snapshot_seconds_ago": 30,
        },
        "next_actions": "Monitor normally. Green status maintained.",
    }

    if verbose:
        response["verbose"] = {
            "threat_score_breakdown": {
                "merkle_divergence_pts": 0,
                "benford_severity_pts": 0,
                "connectivity_loss_pts": 0,
                "consensus_broken_pts": 0,
            },
            "last_threat_events_24h": 0,
            "last_recovery_attempts": 0,
            "lock_file_present": False,
        }

    return response


@router.get("/panel/defenses")
async def get_defenses() -> Dict[str, Any]:
    """
    Retorna estado detallado de todas las capas del Protocolo ARGOS.
    (Return detailed status of all ARGOS Protocol layers.)
    """
    defenses = {}

    for key, defense in {
        "corvid": ArgosLayer.CORVID,
        "cephalopod": ArgosLayer.CEPHALOPOD,
        "evasion": ArgosLayer.EVASION,
        "regeneration": ArgosLayer.REGENERATION,
        "kill_switch": ArgosLayer.KILL_SWITCH,
    }.items():
        defenses[key] = {
            "emoji": defense.emoji,
            "name_es": defense.name_es,
            "name_en": key,
            "title_es": defense.title_es,
            "description_es": defense.description_es,
        }

    return {"defenses": defenses}


@router.get("/panel/threat-score")
async def get_threat_score() -> Dict[str, Any]:
    """
    Retorna threat score actual.
    (Return current threat score.)
    """
    threat_score = 22  # Placeholder

    # Coloreado
    if threat_score < 31:
        status = "🟢 GREEN"
    elif threat_score < 75:
        status = "🟡 YELLOW"
    else:
        status = "🔴 RED"

    return {
        "threat_score": threat_score,
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "threshold_activation": 75,
    }


@router.get("/panel/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Retorna métricas operacionales.
    (Return operational metrics.)
    """
    return {
        "merkle_root": "abc123def456abc123def456",
        "merkle_age_seconds": 120,
        "benford_anomalies": 0,
        "zscore_anomalies": 0,
        "connectivity": {
            "endpoints_total": 4,
            "endpoints_up": 4,
            "pct_up": 100,
        },
        "snapshots_total": 2847,
        "last_snapshot_seconds_ago": 30,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ── OTS Receipt endpoints ───────────────────────────────────────────────────

from pathlib import Path as _Path
from fastapi.responses import Response as _Response, JSONResponse as _JSONResponse

_OTS_DIR = _Path(__file__).resolve().parents[4] / "logs" / "anchors" / "ots"


@router.get("/ots/latest-meta")
async def ots_latest_meta() -> Dict[str, Any]:
    """Return metadata for the most recent OTS anchor (path, timestamp, hash prefix)."""
    if not _OTS_DIR.exists():
        return {"available": False, "reason": "no_anchors_yet"}
    ots_files = sorted(_OTS_DIR.glob("*.ots"))
    if not ots_files:
        return {"available": False, "reason": "no_ots_files"}
    latest = ots_files[-1]
    meta_path = latest.with_suffix(".json")
    meta: Dict[str, Any] = {}
    meta_error: str | None = None
    if meta_path.exists():
        import json as _json
        try:
            meta = _json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as exc:
            meta_error = str(exc)
    return {
        "available": True,
        "filename": latest.name,
        "size_bytes": latest.stat().st_size,
        "ts": latest.stem.split("_")[0] if "_" in latest.stem else "",
        "hash_prefix": latest.stem.split("_")[1] if "_" in latest.stem else "",
        "merkle_root": meta.get("merkle_root", ""),
        "chain_length": meta.get("chain_length", 0),
        "ots_status": meta.get("ots_status", ""),
        **({"meta_error": meta_error} if meta_error else {}),
    }


@router.get("/ots/latest.ots")
async def ots_latest_download():
    """Serve the most recent .ots receipt file for download."""
    if not _OTS_DIR.exists():
        return _JSONResponse({"error": "no_anchors_yet"}, status_code=404)
    ots_files = sorted(_OTS_DIR.glob("*.ots"))
    if not ots_files:
        return _JSONResponse({"error": "no_ots_files"}, status_code=404)
    latest = ots_files[-1]
    content = latest.read_bytes()
    return _Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{latest.name}"'},
    )
