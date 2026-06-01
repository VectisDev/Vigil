"""
POST /api/pipeline/start  — apply config and launch the scraping pipeline
GET  /api/pipeline/status — current pipeline state (running / stopped)
POST /api/pipeline/stop   — graceful shutdown
POST /api/config/apply    — write config YAMLs to disk silently (no modal/PAT)
"""

from __future__ import annotations

import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("centinel.api.pipeline")

router = APIRouter(tags=["pipeline"])

_BASE = Path(__file__).resolve().parents[4]
_SCRIPTS = _BASE / "scripts"
_CONFIG_DIR = _BASE / "config" / "prod"
_PID_FILE = _BASE / "run" / "pipeline.pid"


# ── helpers ──────────────────────────────────────────────────────────────────

def _read_pid() -> int | None:
    try:
        return int(_PID_FILE.read_text().strip())
    except Exception:
        return None


def _process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _pipeline_running() -> bool:
    pid = _read_pid()
    return pid is not None and _process_alive(pid)


# ── models ───────────────────────────────────────────────────────────────────

class ApplyConfigRequest(BaseModel):
    endpoints_yaml: dict | None = None
    country_code: str | None = None
    main_url: str | None = None


# ── endpoints ────────────────────────────────────────────────────────────────

@router.post("/api/config/apply")
def apply_config(req: ApplyConfigRequest) -> dict:
    """Write config to disk directly — no GitHub PAT required.
    Used by the Iniciar flow to persist settings before launching the pipeline.
    """
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ep_path = _CONFIG_DIR / "endpoints.yaml"

    if req.endpoints_yaml:
        ep_path.write_text(yaml.dump(req.endpoints_yaml, allow_unicode=True), encoding="utf-8")
    elif req.main_url:
        # Minimal update: just set main_url, keep the rest intact
        cfg = yaml.safe_load(ep_path.read_text(encoding="utf-8")) if ep_path.exists() else {}
        cfg.setdefault("cne", {})
        cfg["cne"]["main_url"] = req.main_url
        ep_path.write_text(yaml.dump(cfg, allow_unicode=True), encoding="utf-8")

    # Update country context if provided
    if req.country_code:
        try:
            from centinel.countries import LATAM_COUNTRIES
            cc = req.country_code.upper()
            if cc in LATAM_COUNTRIES:
                os.environ["CENTINEL_COUNTRY"] = cc
        except Exception:
            pass

    safe_country = (req.country_code or "").replace("\n", " ").replace("\r", " ") if req.country_code else None
    safe_url = (req.main_url or "").replace("\n", " ").replace("\r", " ") if req.main_url else None
    logger.info("config_applied country=%s main_url=%s", safe_country, safe_url)
    return {"success": True}


@router.post("/api/pipeline/start")
def pipeline_start(req: ApplyConfigRequest | None = None) -> dict:
    """Apply config (if provided) and launch the scraping pipeline."""
    if _pipeline_running():
        return {"status": "already_running", "pid": _read_pid()}

    # Apply any config updates first
    if req and (req.endpoints_yaml or req.main_url):
        apply_config(req)

    script = _SCRIPTS / "run_pipeline.py"
    if not script.exists():
        raise HTTPException(status_code=500, detail="run_pipeline.py not found.")

    _PID_FILE.parent.mkdir(parents=True, exist_ok=True)

    env = {**os.environ}
    try:
        import subprocess
        proc = subprocess.Popen(
            [sys.executable, str(script), "--run-now"],
            cwd=str(_BASE),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _PID_FILE.write_text(str(proc.pid))
        logger.info("pipeline_started pid=%d", proc.pid)
        return {"status": "started", "pid": proc.pid}
    except Exception as exc:
        safe_error = str(exc).replace("\n", " ").replace("\r", " ")
        logger.error("pipeline_start_failed error=%s", safe_error)
        raise HTTPException(status_code=500, detail=f"No se pudo iniciar el pipeline: {exc}")


@router.get("/api/pipeline/status")
def pipeline_status() -> dict:
    """Return current pipeline state."""
    pid = _read_pid()
    running = pid is not None and _process_alive(pid)
    if not running and pid is not None:
        _PID_FILE.unlink(missing_ok=True)
    return {"running": running, "pid": pid if running else None}


@router.post("/api/pipeline/stop")
def pipeline_stop() -> dict:
    """Send SIGTERM to the pipeline process for a graceful shutdown."""
    pid = _read_pid()
    if pid is None or not _process_alive(pid):
        _PID_FILE.unlink(missing_ok=True)
        return {"status": "not_running"}
    try:
        os.kill(pid, signal.SIGTERM)
        _PID_FILE.unlink(missing_ok=True)
        logger.info("pipeline_stopped pid=%d", pid)
        return {"status": "stopped", "pid": pid}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo detener el pipeline: {exc}")
