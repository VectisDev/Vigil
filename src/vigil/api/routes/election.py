"""
Election lifecycle endpoints for Centinel.

POST /api/election/finalize  — trigger the end-of-election sequence
GET  /api/election/status    — current election state
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("vigil.api.election")

router = APIRouter(tags=["election"])

_BASE = Path(__file__).resolve().parents[4]
_ENV_PATH = _BASE / "centinel_engine" / ".env"
_CLOSED_MARKER = _BASE / "ELECTION_CLOSED"
_SCRIPTS_DIR = _BASE / "scripts"

_finalize_lock = asyncio.Lock()
_finalize_running = False


def _update_env(key: str, value: str) -> None:
    """Update or append KEY=VALUE in centinel_engine/.env."""
    if not _ENV_PATH.exists():
        _ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        _ENV_PATH.write_text(f"{key}={value}\n", encoding="utf-8")
        return
    text = _ENV_PATH.read_text(encoding="utf-8")
    pattern = re.compile(rf"^{re.escape(key)}\s*=.*$", re.MULTILINE)
    if pattern.search(text):
        text = pattern.sub(f"{key}={value}", text)
    else:
        text = text.rstrip("\n") + f"\n{key}={value}\n"
    _ENV_PATH.write_text(text, encoding="utf-8")


def _read_env(key: str, default: str = "") -> str:
    if not _ENV_PATH.exists():
        return default
    text = _ENV_PATH.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(key)}\s*=(.*)$", text, re.MULTILINE)
    return m.group(1).strip() if m else default


def _current_merkle_root() -> tuple[str, int]:
    try:
        import sqlite3
        db = _BASE / "data" / "snapshots.db"
        if not db.exists():
            return "0" * 64, 0
        with sqlite3.connect(str(db)) as conn:
            row = conn.execute(
                "SELECT hash, id FROM snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not row:
                return "0" * 64, 0
            count = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
            return row[0], count
    except Exception:
        return "0" * 64, 0


@router.post("/api/election/finalize")
async def finalize_election(request: Request) -> dict:
    """Trigger the end-of-election finalization sequence.

    1. Runs a forced full scrape cycle (all 19 sources, no throttle, no cooperative skip).
    2. Writes ELECTION_CLOSED marker — schedulers check this and exit immediately.
    3. Sets CENTINEL_MODE=maintenance in centinel_engine/.env.
    4. Returns the final Merkle root and chain length.

    Idempotent: safe to call more than once (returns current state if already closed).
    """
    global _finalize_running

    if _CLOSED_MARKER.exists():
        merkle_root, chain_length = _current_merkle_root()
        closed_at = _CLOSED_MARKER.read_text(encoding="utf-8").strip()
        return {
            "status": "already_closed",
            "closed_at": closed_at,
            "merkle_root": merkle_root,
            "chain_length": chain_length,
        }

    async with _finalize_lock:
        if _finalize_running:
            raise HTTPException(status_code=409, detail="Finalization already in progress.")
        _finalize_running = True

    now_iso = datetime.now(timezone.utc).isoformat()
    logger.info("election_finalize_requested at=%s", now_iso)

    try:
        script = _SCRIPTS_DIR / "download_and_hash.py"
        if not script.exists():
            raise HTTPException(status_code=500, detail="download_and_hash.py not found.")

        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(script), "--force-full-cycle",
            cwd=str(_BASE),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=600)
        output = stdout.decode(errors="replace") if stdout else ""

        if proc.returncode != 0:
            logger.error("election_finalize_scrape_failed rc=%d output=%s", proc.returncode, output[-500:])
            raise HTTPException(
                status_code=500,
                detail=f"Forced scrape failed (rc={proc.returncode}). Check logs.",
            )

        # Write closed marker and switch mode
        _CLOSED_MARKER.write_text(now_iso, encoding="utf-8")
        _update_env("CENTINEL_MODE", "maintenance")
        logger.info("election_finalize_complete mode=maintenance marker_written=%s", now_iso)

        merkle_root, chain_length = _current_merkle_root()
        return {
            "status": "finalized",
            "closed_at": now_iso,
            "merkle_root": merkle_root,
            "chain_length": chain_length,
            "mode": "maintenance",
        }

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Forced scrape timed out after 10 minutes.")
    finally:
        async with _finalize_lock:
            _finalize_running = False


@router.get("/api/election/status")
async def election_status() -> dict:
    """Return current election lifecycle state."""
    closed = _CLOSED_MARKER.exists()
    closed_at: Optional[str] = None
    if closed:
        try:
            closed_at = _CLOSED_MARKER.read_text(encoding="utf-8").strip()
        except Exception:
            closed_at = None

    merkle_root, chain_length = _current_merkle_root()
    mode = _read_env("CENTINEL_MODE", "maintenance")

    return {
        "election_closed": closed,
        "closed_at": closed_at,
        "centinel_mode": mode,
        "merkle_root": merkle_root,
        "chain_length": chain_length,
    }
