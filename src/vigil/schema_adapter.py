"""
SchemaAdapter: converts raw CNE JSON into Centinel Snapshot objects.

Each country's CNE publishes data in its own format. This module provides
adapters that parse those formats into the canonical Snapshot model used
by the storage and rules engine.

Currently implemented: Honduras (HN) national-level JSON.
  File pattern: HN.PRESIDENTE.{dept_code}-{dept_name}.{mun_code}-{mun_name} YYYY-MM-DD HH_MM_SS.json
  Schema: resultados[], estadisticas.{totalizacion_actas, distribucion_votos, estado_actas_divulgadas}
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("vigil.schema_adapter")

# ── HN filename pattern ───────────────────────────────────────────────────────
# e.g. "HN.PRESIDENTE.00-TODOS.000-TODOS 2025-12-09 15_01_45.json"
_HN_FILENAME_RE = re.compile(
    r"^HN\.PRESIDENTE\."
    r"(?P<dept_code>\d+)-(?P<dept_name>[^.]+)\."
    r"(?P<mun_code>\d+)-(?P<mun_name>[^\s]+)"
    r"\s+(?P<ts>\d{4}-\d{2}-\d{2} \d{2}_\d{2}_\d{2})\.json$"
)


def _parse_int(value: str | int | None) -> int:
    """'1,027,090' → 1027090. Handles None and bare ints."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(str(value).replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0


def _parse_float(value: str | float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, float):
        return value
    try:
        return float(str(value).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return 0.0


def _filename_timestamp(filename: str) -> Optional[str]:
    """Extract ISO 8601 UTC timestamp from a CNE filename."""
    m = _HN_FILENAME_RE.match(filename)
    if not m:
        # Generic fallback: find any YYYY-MM-DD HH_MM_SS pattern
        m2 = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}_\d{2}_\d{2})", filename)
        if m2:
            ts = m2.group(1).replace("_", ":").replace(" ", "T") + "Z"
            return ts
        return None
    ts = m.group("ts").replace("_", ":").replace(" ", "T") + "Z"
    return ts


def _dept_code_from_filename(filename: str) -> str:
    """Return the CNE department code from filename, e.g. '00' or '08'."""
    m = _HN_FILENAME_RE.match(filename)
    return m.group("dept_code") if m else "00"


# ── Adapted snapshot type (thin wrapper, no SQLite dependency here) ───────────

@dataclass
class AdaptedSnapshot:
    """Parsed CNE data ready to be stored as a Centinel Snapshot."""

    timestamp_utc: str          # ISO 8601, from CNE filename (NOT wall clock)
    country_code: str           # "HN"
    dept_cne_code: str          # "00" = national, "01"–"18" = departments
    dept_name: str              # "TODOS", "Atlántida", …
    scope: str                  # "nacional" or "departamental"

    actas_total: int
    actas_divulgadas: int
    actas_correctas: int
    actas_inconsistentes: int

    votos_validos: int
    votos_nulos: int
    votos_blancos: int
    votos_total_emitidos: int   # validos + nulos + blancos

    candidates: List[Dict]      # [{name, party, votes, percentage}, ...]
    source_filename: str

    def to_snapshot_dict(self) -> dict:
        """Return dict compatible with the normalized/ pipeline format."""
        return {
            "timestamp_utc": self.timestamp_utc,
            "country_code": self.country_code,
            "dept_cne_code": self.dept_cne_code,
            "dept_name": self.dept_name,
            "scope": self.scope,
            "nivel": "presidencial",
            "departamento": self.dept_name,
            "resultados": {c["party"]: c["votes"] for c in self.candidates},
            "actas": {
                "totales": self.actas_total,
                "divulgadas": self.actas_divulgadas,
                "correctas": self.actas_correctas,
                "inconsistentes": self.actas_inconsistentes,
            },
            "votos_totales": {
                "validos": self.votos_validos,
                "nulos": self.votos_nulos,
                "blancos": self.votos_blancos,
                "total_emitidos": self.votos_total_emitidos,
            },
            "candidatos": self.candidates,
            "source_filename": self.source_filename,
        }

    def to_core_snapshot(self):
        """Convert to vigil.core.models.Snapshot for storage/rules engine."""
        from vigil.core.models import CandidateResult, Meta, Snapshot, Totals

        meta = Meta(
            election="presidencial",
            year=int(self.timestamp_utc[:4]),
            source=self.source_filename,
            scope=self.scope,
            department_code=self.dept_cne_code,
            timestamp_utc=self.timestamp_utc,
        )
        totals = Totals(
            registered_voters=0,   # Not in HN national JSON — set at dept level
            total_votes=self.votos_total_emitidos,
            valid_votes=self.votos_validos,
            null_votes=self.votos_nulos,
            blank_votes=self.votos_blancos,
        )
        candidates = [
            CandidateResult(
                slot=i + 1,
                votes=c["votes"],
                candidate_id=None,
                name=c["name"],
                party=c["party"],
            )
            for i, c in enumerate(self.candidates)
        ]
        return Snapshot(meta=meta, totals=totals, candidates=candidates)


# ── Honduras adapter ──────────────────────────────────────────────────────────

def adapt_hn_json(path: Path) -> AdaptedSnapshot:
    """Parse a Honduras CNE JSON file into an AdaptedSnapshot.

    Handles both national (00-TODOS) and departmental files.
    Timestamp is ALWAYS taken from the filename — never from wall clock.
    """
    filename = path.name
    raw = json.loads(path.read_text(encoding="utf-8"))

    timestamp_utc = _filename_timestamp(filename) or ""
    dept_code = _dept_code_from_filename(filename)

    # Infer dept name from countries.py if possible
    if dept_code == "00":
        dept_name = "TODOS"
        scope = "nacional"
    else:
        try:
            from vigil.countries import LATAM_COUNTRIES
            preset = LATAM_COUNTRIES["HN"]
            cne_map = preset.build_cne_map()
            dept_name = cne_map.get(dept_code, f"Departamento {dept_code}")
        except Exception:
            dept_name = f"Departamento {dept_code}"
        scope = "departamental"

    resultados = raw.get("resultados", [])
    stats = raw.get("estadisticas", {})

    candidates = []
    for r in resultados:
        votes = _parse_int(r.get("votos"))
        pct = _parse_float(r.get("porcentaje"))
        candidates.append({
            "name": (r.get("candidato") or "").strip().title(),
            "party": (r.get("partido") or "").strip(),
            "votes": votes,
            "percentage": pct,
        })

    actas = stats.get("totalizacion_actas", {})
    dist = stats.get("distribucion_votos", {})
    estado = stats.get("estado_actas_divulgadas", {})

    votos_validos = _parse_int(dist.get("validos"))
    votos_nulos = _parse_int(dist.get("nulos"))
    votos_blancos = _parse_int(dist.get("blancos"))

    return AdaptedSnapshot(
        timestamp_utc=timestamp_utc,
        country_code="HN",
        dept_cne_code=dept_code,
        dept_name=dept_name,
        scope=scope,
        actas_total=_parse_int(actas.get("actas_totales")),
        actas_divulgadas=_parse_int(actas.get("actas_divulgadas")),
        actas_correctas=_parse_int(estado.get("actas_correctas")),
        actas_inconsistentes=_parse_int(estado.get("actas_inconsistentes")),
        votos_validos=votos_validos,
        votos_nulos=votos_nulos,
        votos_blancos=votos_blancos,
        votos_total_emitidos=votos_validos + votos_nulos + votos_blancos,
        candidates=candidates,
        source_filename=filename,
    )


def adapt_hn_directory(directory: Path) -> List[AdaptedSnapshot]:
    """Parse all HN CNE JSON files in a directory, sorted by filename timestamp."""
    pattern = re.compile(r"^HN\.PRESIDENTE\..+\.json$")
    files = sorted(
        [p for p in directory.iterdir() if pattern.match(p.name)],
        key=lambda p: p.name,
    )
    snapshots = []
    for p in files:
        try:
            snapshots.append(adapt_hn_json(p))
        except Exception as exc:
            logger.warning("adapt_hn_json_failed file=%s error=%s", p.name, exc)
    return snapshots
