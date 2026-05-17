#!/usr/bin/env python3
"""
Export a static snapshot.json consumed by the public panel.

Reads pipeline-generated files and writes web/data/snapshot.json.
No network calls. Designed to run after each pipeline cycle in CI.

Usage:
  python scripts/export_static_snapshot.py [--root .]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _blackout_hash(endpoint: str, blackout_since: str, error_type: str | None) -> str:
    raw = f"{endpoint}|{blackout_since}|{error_type or 'unknown'}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _build_cne_status(state: dict, endpoint: str) -> dict:
    consecutive = int(state.get("cne_consecutive_failures", 0))
    reachable = consecutive == 0

    last_ok = state.get("cne_last_successful_scrape_at")
    last_attempt = state.get("cne_last_attempt_at")
    first_unreachable = state.get("cne_first_unreachable_at")

    blackout_minutes = 0
    blackout_hash_val = None

    if not reachable and first_unreachable:
        try:
            since_dt = datetime.fromisoformat(first_unreachable.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            blackout_minutes = max(0, int((now_dt - since_dt).total_seconds() / 60))
        except Exception:
            pass
        blackout_hash_val = _blackout_hash(endpoint, first_unreachable, state.get("cne_last_error_type"))

    return {
        "reachable": reachable,
        "last_successful_fetch": last_ok,
        "last_attempt": last_attempt,
        "consecutive_failures": consecutive,
        "blackout_minutes": blackout_minutes,
        "blackout_since": first_unreachable if not reachable else None,
        "error_type": state.get("cne_last_error_type") if not reachable else None,
        "blackout_hash": blackout_hash_val,
    }


def _build_chain(state: dict, hash_dir: Path) -> dict:
    latest_hash = ""
    merkle_root = ""
    chain_length = 0

    all_hashes = sorted(hash_dir.glob("*.json")) if hash_dir.is_dir() else []
    if all_hashes:
        latest = _read_json(all_hashes[-1])
        latest_hash = latest.get("chained_hash") or latest.get("hash") or ""
        merkle_root = latest.get("merkle_root", "")
        chain_length = len(all_hashes)

    # Also check state for richer info
    recent = state.get("hashes", [])
    if recent and not latest_hash:
        latest_hash = recent[0].get("chained_hash") or recent[0].get("hash") or ""

    return {
        "latest_hash": latest_hash,
        "merkle_root": merkle_root,
        "chain_length": chain_length,
        "ots_status": state.get("ots_status", "pending"),
    }


def _build_national(snapshot: dict) -> dict:
    if not snapshot:
        return {}
    return {
        "actas_escrutadas": snapshot.get("actas_escrutadas", 0),
        "actas_total": snapshot.get("actas_total", 0),
        "total_votos": snapshot.get("total_votos", 0),
        "candidatos": snapshot.get("candidatos", {}),
        "source": snapshot.get("source", ""),
        "timestamp": snapshot.get("timestamp", ""),
    }


def _build_departments(snapshot: dict) -> dict:
    depts = snapshot.get("departamentos", [])
    if not isinstance(depts, list):
        return {}
    out = {}
    for d in depts:
        code = d.get("codigo") or d.get("nombre", "").upper().replace(" ", "_")
        out[code] = {
            "nombre": d.get("nombre", code),
            "actas_escrutadas": d.get("actas_escrutadas", 0),
            "actas_total": d.get("actas_total", 0),
            "total_votos": d.get("total_votos", 0),
            "candidatos": d.get("candidatos", {}),
        }
    return out


def _build_coverage(snapshot: dict) -> dict:
    total = snapshot.get("actas_total", 0)
    scrutinized = snapshot.get("actas_escrutadas", 0)
    pct = round(scrutinized / total * 100, 2) if total else 0.0
    return {
        "actas_escrutadas": scrutinized,
        "actas_total": total,
        "pct_coverage": pct,
    }


def _latest_snapshot(data_dir: Path) -> dict:
    candidates = sorted(
        [p for p in data_dir.glob("*.json") if p.stem not in ("pipeline_state", "heartbeat", "custody_verification")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # Skip temp/mock subdirectories; only files directly in data_dir
    direct = [p for p in candidates if p.parent == data_dir]
    if direct:
        return _read_json(direct[0])
    return {}


def export_snapshot(root: Path = Path(".")) -> Path:
    data_dir = root / "data"
    hash_dir = root / "hashes"
    analysis_dir = root / "analysis"
    out_dir = root / "web" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    state = _read_json(data_dir / "pipeline_state.json")
    alerts_raw = _read_json(analysis_dir / "alerts.json")
    alerts = alerts_raw if isinstance(alerts_raw, list) else alerts_raw.get("alerts", [])
    snapshot = _latest_snapshot(data_dir)

    endpoint = "https://resultados2029.cne.hn/"
    try:
        ep_cfg = _read_json(root / "config" / "prod" / "endpoints.yaml")
        endpoint = ep_cfg.get("cne", {}).get("main_url", endpoint)
    except Exception:
        pass

    forensics_path = analysis_dir / "forensics_latest.json"
    forensics = _read_json(forensics_path) if forensics_path.exists() else {}

    result = {
        "schema_version": 1,
        "generated_at": _utcnow(),
        "cne_status": _build_cne_status(state, endpoint),
        "chain": _build_chain(state, hash_dir),
        "national": _build_national(snapshot),
        "departments": _build_departments(snapshot),
        "forensics": forensics,
        "alerts": alerts[:50],
        "coverage": _build_coverage(snapshot),
        "report_pdf_url": state.get("last_report_pdf_url"),
    }

    out_path = out_dir / "snapshot.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export static snapshot.json for the public panel.")
    parser.add_argument("--root", default=".", help="Repository root (default: cwd)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = export_snapshot(root)
    print(f"Exported: {out}")


if __name__ == "__main__":
    sys.exit(main())
