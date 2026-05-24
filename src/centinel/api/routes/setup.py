"""
Endpoints de configuración inicial y regeneración de seeds.
Initial setup and seed regeneration endpoints.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from centinel.countries import LATAM_COUNTRIES, list_countries
from centinel.seed_pdf import generate_seeds, hash_seeds, generate_pdf

logger = logging.getLogger("centinel.api.setup")

router = APIRouter(prefix="/api/setup", tags=["setup"])

_BASE = Path(__file__).resolve().parents[4]
_ACCESS_JSON = _BASE / "web" / "access.json"
_SETUP_MARKER = _BASE / ".centinel-setup.json"


def _read_setup() -> dict:
    if not _SETUP_MARKER.exists():
        return {}
    try:
        return json.loads(_SETUP_MARKER.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_access(hashes: dict[str, str]) -> None:
    payload = {
        "version": 1,
        "algo": "PBKDF2-SHA256",
        "salt": "centinel-admin-salt-v1",
        "iterations": 600_000,
        "seeds": hashes,
    }
    _ACCESS_JSON.parent.mkdir(parents=True, exist_ok=True)
    _ACCESS_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _pdf_response(seeds: dict, country_name: str, country_flag: str, code: str) -> Response:
    pdf_bytes = generate_pdf(seeds, country_name, country_flag)
    filename = f"centinel-seeds-{code.lower()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Request models ────────────────────────────────────────────────────────────


class InitRequest(BaseModel):
    country_code: str


class RegenerateRequest(BaseModel):
    country_code: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/status")
def setup_status() -> dict:
    """Retorna si el sistema ya fue configurado."""
    setup = _read_setup()
    return {
        "configured": bool(setup),
        "country_code": setup.get("country_code"),
        "country_name": setup.get("country_name"),
        "configured_at": setup.get("configured_at"),
    }


@router.get("/countries")
def get_countries() -> list[dict]:
    """Retorna la lista de países LATAM con sus presets."""
    return [
        {
            "code": c.code,
            "name": c.name,
            "flag": c.flag,
            "authority": c.authority,
            "divisions_label": c.divisions_label,
            "divisions_count": c.divisions_count,
        }
        for c in list_countries()
    ]


@router.post("/init")
def setup_init(req: InitRequest) -> Response:
    """
    Configura el sistema por primera vez.
    Genera 12 seeds, guarda hashes en access.json y retorna el PDF.
    Solo funciona si el sistema no ha sido configurado.
    """
    if _SETUP_MARKER.exists():
        raise HTTPException(
            status_code=409,
            detail="Sistema ya configurado. Usa /api/setup/regenerate para nuevos seeds.",
        )

    code = req.country_code.upper().strip()
    if code not in LATAM_COUNTRIES:
        raise HTTPException(status_code=400, detail=f"País '{code}' no soportado.")

    country = LATAM_COUNTRIES[code]
    seeds = generate_seeds()
    hashes = hash_seeds(seeds)

    _write_access(hashes)

    _SETUP_MARKER.write_text(
        json.dumps(
            {
                "country_code": code,
                "country_name": country.name,
                "configured_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    logger.info("setup_complete country=%s", code)
    return _pdf_response(seeds, country.name, country.flag, code)


@router.post("/regenerate")
def regenerate_seeds(req: RegenerateRequest) -> Response:
    """
    Regenera seeds nuevos (invalida todos los anteriores).
    Requiere que el sistema ya esté configurado.
    La autenticación se valida a nivel de middleware/sesión del panel OPS.
    """
    setup = _read_setup()
    if not setup:
        raise HTTPException(status_code=400, detail="Sistema no configurado aún.")

    code = (req.country_code or setup.get("country_code", "HN")).upper().strip()
    if code not in LATAM_COUNTRIES:
        raise HTTPException(status_code=400, detail=f"País '{code}' no soportado.")

    country = LATAM_COUNTRIES[code]
    seeds = generate_seeds()
    hashes = hash_seeds(seeds)

    _write_access(hashes)

    setup["last_regenerated_at"] = datetime.now(timezone.utc).isoformat()
    _SETUP_MARKER.write_text(json.dumps(setup, indent=2) + "\n", encoding="utf-8")

    logger.warning("seeds_regenerated country=%s — previous seeds invalidated", code)
    return _pdf_response(seeds, country.name, country.flag, code)
