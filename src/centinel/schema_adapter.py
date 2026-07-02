"""
SchemaAdapter: converts raw electoral payloads into Centinel Snapshot objects.

Each country's electoral authority publishes data in its own format. This
module provides adapters that parse those formats into the canonical
Snapshot model used by the storage and rules engine.

Registry por formato (parse_payload): el formato detectado por
format_detector selecciona el parser — JSON y CSV hoy; XML/HTML/PDF se
detectan pero aún no tienen parser (registrar con @register_parser).
Cero código por país: país nuevo = detección de formato + field_map
declarativo en config, con auto-mapeo heurístico de columnas comunes
del continente como fallback.

Format registry (parse_payload): the format detected by format_detector
selects the parser — JSON and CSV today; XML/HTML/PDF are detected but
have no parser yet (register with @register_parser). Zero per-country
code: new country = format detection + declarative field_map in config,
with heuristic auto-mapping of common continent column names as fallback.

Country-specific adapter implemented: Honduras (HN) national-level JSON.
  File pattern: HN.PRESIDENTE.{dept_code}-{dept_name}.{mun_code}-{mun_name} YYYY-MM-DD HH_MM_SS.json
  Schema: resultados[], estadisticas.{totalizacion_actas, distribucion_votos, estado_actas_divulgadas}
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("centinel.schema_adapter")

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
        """Convert to centinel.core.models.Snapshot for storage/rules engine."""
        from centinel.core.models import CandidateResult, Meta, Snapshot, Totals

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
            from centinel.countries import LATAM_COUNTRIES
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


# ══════════════════════════════════════════════════════════════════════════════
# Registry de parsers por formato / Per-format parser registry
# ══════════════════════════════════════════════════════════════════════════════

class UnsupportedFormatError(ValueError):
    """Formato detectado pero sin parser registrado (XML/HTML/PDF hoy).
    Format detected but no parser registered (XML/HTML/PDF today)."""


FORMAT_PARSERS: Dict[str, Callable[..., "AdaptedSnapshot"]] = {}


def register_parser(fmt: str):
    """Registra un parser para un formato. Registers a parser for a format.

    Para soportar XML/HTML mañana basta registrar aquí el parser — la
    detección ya los identifica. To support XML/HTML tomorrow just
    register the parser here — detection already identifies them.
    """
    def _decorator(fn: Callable[..., "AdaptedSnapshot"]):
        FORMAT_PARSERS[fmt] = fn
        return fn
    return _decorator


# ── Aliases de campos comunes del continente / Continent-wide field aliases ───
# Nombres reales usados por CNE-HN, TSE-GT/BR, INE-MX (PREP), CNE-EC,
# Registraduría-CO, DINE-AR, etc. Real names used across the continent.

_PARTY_ALIASES = (
    "partido", "party", "agrupacion", "organizacion", "sigla",
    "partido_politico", "nombre_agrupacion", "sg_partido", "nm_partido",
    "agrupacion_politica", "organizacion_politica",
)
_CANDIDATE_ALIASES = (
    "candidato", "candidate", "nombre", "nome", "nombre_candidato",
    "nm_candidato", "nm_votavel", "candidatura",
)
_VOTES_ALIASES = (
    "votos", "votes", "sufragios", "cantidad_votos", "qtde_votos",
    "qt_votos", "total_votos", "votos_cantidad", "vote_count", "cantidad",
)
_PCT_ALIASES = ("porcentaje", "percentage", "pct", "percentual", "porcentagem")

_VALID_ALIASES = ("votos_validos", "valid_votes", "validos")
_NULL_ALIASES = ("votos_nulos", "null_votes", "nulos", "votos_nulos_cantidad")
_BLANK_ALIASES = ("votos_blancos", "blank_votes", "blancos", "votos_en_blanco")


def _norm_name(name: str) -> str:
    """Normaliza nombres de columna/clave: minúsculas, sin acentos,
    espacios→_. Normalizes column/key names: lowercase, accent-stripped,
    spaces→_."""
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.strip().lower().replace(" ", "_").replace("-", "_")


def _pick_key(row: Dict, aliases: tuple) -> Optional[str]:
    """Encuentra la clave real de un dict que coincide con algún alias.
    Finds the actual dict key matching any alias."""
    normalized = {_norm_name(k): k for k in row.keys()}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def _dig(obj, dotpath: str):
    """Resuelve un dot-path (ej. 'estadisticas.distribucion_votos.validos').
    Resolves a dot-path (e.g. 'estadisticas.distribucion_votos.validos')."""
    current = obj
    for part in dotpath.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _first_path(obj, paths: List[str]):
    """Primer dot-path que resuelve a un valor no-None.
    First dot-path resolving to a non-None value."""
    for path in paths or []:
        value = _dig(obj, path)
        if value is not None:
            return value
    return None


# field_map por defecto: la forma del TREP de Honduras, que también es la
# convención dominante en los TREP JSON del continente.
# Default field_map: the Honduras TREP shape, also the dominant convention
# across the continent's JSON TREPs.
_DEFAULT_JSON_FIELD_MAP: Dict = {
    "totals": {
        "valid_votes": ["estadisticas.distribucion_votos.validos"],
        "null_votes": ["estadisticas.distribucion_votos.nulos"],
        "blank_votes": ["estadisticas.distribucion_votos.blancos"],
        "total_votes": ["estadisticas.distribucion_votos.total"],
    },
    "actas": {
        "total": ["estadisticas.totalizacion_actas.actas_totales"],
        "divulgadas": ["estadisticas.totalizacion_actas.actas_divulgadas"],
        "correctas": ["estadisticas.estado_actas_divulgadas.actas_correctas"],
        "inconsistentes": ["estadisticas.estado_actas_divulgadas.actas_inconsistentes"],
    },
    "candidate_roots": ["resultados"],
    "timestamp": ["timestamp", "fecha", "fecha_hora", "hora_actualizacion",
                  "meta.timestamp_utc"],
}


def _merged_field_map(field_map: Optional[Dict]) -> Dict:
    merged = {k: (dict(v) if isinstance(v, dict) else list(v))
              for k, v in _DEFAULT_JSON_FIELD_MAP.items()}
    for key, value in (field_map or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def _candidate_from_row(row: Dict) -> Optional[Dict]:
    """Extrae {name, party, votes, percentage} de una fila JSON/CSV usando
    aliases del continente. Extracts candidate dict from a JSON/CSV row
    using continent-wide aliases."""
    votes_key = _pick_key(row, _VOTES_ALIASES)
    party_key = _pick_key(row, _PARTY_ALIASES)
    cand_key = _pick_key(row, _CANDIDATE_ALIASES)
    pct_key = _pick_key(row, _PCT_ALIASES)
    if votes_key is None or (party_key is None and cand_key is None):
        return None
    return {
        "name": str(row.get(cand_key, "") or "").strip().title(),
        "party": str(row.get(party_key, "") or "").strip(),
        "votes": _parse_int(row.get(votes_key)),
        "percentage": _parse_float(row.get(pct_key)) if pct_key else 0.0,
    }


@register_parser("json")
def parse_json_payload(
    raw: bytes,
    *,
    field_map: Optional[Dict] = None,
    country_code: str = "XX",
    timestamp_utc: str = "",
    dept_cne_code: str = "00",
    dept_name: str = "TODOS",
    scope: str = "nacional",
    source_name: str = "",
) -> AdaptedSnapshot:
    """
    Parser JSON genérico dirigido por field_map (dot-paths con fallbacks).
    Sin field_map usa la convención TREP (forma HN) + aliases de candidato.
    Generic field_map-driven JSON parser (dot-paths with fallbacks).
    Without field_map it uses the TREP convention (HN shape) + candidate
    aliases.
    """
    payload = json.loads(raw.decode("utf-8-sig"))
    if isinstance(payload, list):
        # Algunos TREP publican una lista con un único objeto de resultados
        # Some TREPs publish a list with a single results object
        payload = payload[0] if payload and isinstance(payload[0], dict) else {}

    fmap = _merged_field_map(field_map)

    candidates: List[Dict] = []
    for root in fmap.get("candidate_roots", []):
        rows = _dig(payload, root)
        if isinstance(rows, dict):
            rows = list(rows.values())
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    cand = _candidate_from_row(row)
                    if cand:
                        candidates.append(cand)
            if candidates:
                break

    totals_map = fmap.get("totals", {})
    valid = _parse_int(_first_path(payload, totals_map.get("valid_votes", [])))
    null = _parse_int(_first_path(payload, totals_map.get("null_votes", [])))
    blank = _parse_int(_first_path(payload, totals_map.get("blank_votes", [])))
    total = _parse_int(_first_path(payload, totals_map.get("total_votes", [])))
    if not valid and candidates:
        valid = sum(c["votes"] for c in candidates)
    if not total:
        total = valid + null + blank

    actas_map = fmap.get("actas", {})
    if not timestamp_utc:
        timestamp_utc = str(_first_path(payload, fmap.get("timestamp", [])) or "")

    return AdaptedSnapshot(
        timestamp_utc=timestamp_utc,
        country_code=country_code,
        dept_cne_code=dept_cne_code,
        dept_name=dept_name,
        scope=scope,
        actas_total=_parse_int(_first_path(payload, actas_map.get("total", []))),
        actas_divulgadas=_parse_int(_first_path(payload, actas_map.get("divulgadas", []))),
        actas_correctas=_parse_int(_first_path(payload, actas_map.get("correctas", []))),
        actas_inconsistentes=_parse_int(_first_path(payload, actas_map.get("inconsistentes", []))),
        votos_validos=valid,
        votos_nulos=null,
        votos_blancos=blank,
        votos_total_emitidos=total,
        candidates=candidates,
        source_filename=source_name,
    )


def _decode_csv(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _resolve_csv_columns(fieldnames: List[str], csv_map: Dict) -> Dict[str, Optional[str]]:
    """Resuelve columnas: field_map explícito manda; si falta, auto-mapeo
    por aliases. Resolves columns: explicit field_map rules; missing ones
    auto-map via aliases."""
    by_norm = {_norm_name(f): f for f in fieldnames}

    def _explicit(key: str) -> Optional[str]:
        wanted = csv_map.get(key)
        return by_norm.get(_norm_name(wanted)) if wanted else None

    def _auto(aliases: tuple) -> Optional[str]:
        for alias in aliases:
            if alias in by_norm:
                return by_norm[alias]
        return None

    return {
        "party": _explicit("party_column") or _auto(_PARTY_ALIASES),
        "candidate": _explicit("candidate_column") or _auto(_CANDIDATE_ALIASES),
        "votes": _explicit("votes_column") or _auto(_VOTES_ALIASES),
        "valid": _explicit("valid_column") or _auto(_VALID_ALIASES),
        "null": _explicit("null_column") or _auto(_NULL_ALIASES),
        "blank": _explicit("blank_column") or _auto(_BLANK_ALIASES),
    }


def suggest_csv_field_map(raw: bytes) -> Dict[str, Optional[str]]:
    """
    Auto-mapeo de columnas para que el operador lo confirme en el wizard.
    Column auto-mapping for the operator to confirm in the wizard.
    """
    from centinel.format_detector import csv_dialect_for

    text = _decode_csv(raw)
    reader = csv.reader(io.StringIO(text), csv_dialect_for(raw))
    header = next(reader, [])
    cols = _resolve_csv_columns(header, {})
    return {
        "party_column": cols["party"],
        "candidate_column": cols["candidate"],
        "votes_column": cols["votes"],
        "valid_column": cols["valid"],
        "null_column": cols["null"],
        "blank_column": cols["blank"],
    }


@register_parser("csv")
def parse_csv_payload(
    raw: bytes,
    *,
    field_map: Optional[Dict] = None,
    country_code: str = "XX",
    timestamp_utc: str = "",
    dept_cne_code: str = "00",
    dept_name: str = "TODOS",
    scope: str = "nacional",
    source_name: str = "",
) -> AdaptedSnapshot:
    """
    Parser CSV real: delimitador por csv.Sniffer, columnas por field_map.csv
    o auto-mapeo, agregación de filas (los CSV electorales suelen venir por
    mesa/casilla) sumando votos por partido+candidato.
    Real CSV parser: csv.Sniffer delimiter, columns from field_map.csv or
    auto-mapping, row aggregation (electoral CSVs usually come per polling
    station) summing votes by party+candidate.

    Raises:
        ValueError: si no hay columnas reconocibles — nunca datos inventados.
                    if no recognizable columns — never invented data.
    """
    from centinel.format_detector import csv_dialect_for

    text = _decode_csv(raw)
    reader = csv.DictReader(io.StringIO(text), dialect=csv_dialect_for(raw))
    fieldnames = reader.fieldnames or []
    csv_map = (field_map or {}).get("csv", {}) if field_map else {}
    cols = _resolve_csv_columns(list(fieldnames), csv_map)

    if not cols["votes"] or not (cols["party"] or cols["candidate"]):
        raise ValueError(
            "csv_columns_unrecognized: no se identificó columna de votos y "
            "partido/candidato. Columnas encontradas: "
            f"{fieldnames}. Declara field_map.csv "
            "(party_column/candidate_column/votes_column) en la config. / "
            "votes and party/candidate columns not identified — declare "
            "field_map.csv in config."
        )

    aggregated: Dict[tuple, Dict] = {}
    valid_sum = null_sum = blank_sum = 0
    for row in reader:
        party = str(row.get(cols["party"], "") or "").strip() if cols["party"] else ""
        cand = str(row.get(cols["candidate"], "") or "").strip() if cols["candidate"] else ""
        votes = _parse_int(row.get(cols["votes"]))
        key = (party, cand)
        if key not in aggregated:
            aggregated[key] = {
                "name": cand.title(),
                "party": party,
                "votes": 0,
                "percentage": 0.0,
            }
        aggregated[key]["votes"] += votes
        if cols["valid"]:
            valid_sum += _parse_int(row.get(cols["valid"]))
        if cols["null"]:
            null_sum += _parse_int(row.get(cols["null"]))
        if cols["blank"]:
            blank_sum += _parse_int(row.get(cols["blank"]))

    candidates = sorted(aggregated.values(), key=lambda c: c["votes"], reverse=True)
    if not candidates:
        raise ValueError("csv_empty: el CSV no contiene filas de resultados / "
                         "the CSV contains no result rows")

    total_candidate_votes = sum(c["votes"] for c in candidates)
    valid = valid_sum or total_candidate_votes
    for cand in candidates:
        cand["percentage"] = round(cand["votes"] * 100.0 / valid, 2) if valid else 0.0

    return AdaptedSnapshot(
        timestamp_utc=timestamp_utc,
        country_code=country_code,
        dept_cne_code=dept_cne_code,
        dept_name=dept_name,
        scope=scope,
        actas_total=0,
        actas_divulgadas=0,
        actas_correctas=0,
        actas_inconsistentes=0,
        votos_validos=valid,
        votos_nulos=null_sum,
        votos_blancos=blank_sum,
        votos_total_emitidos=valid + null_sum + blank_sum,
        candidates=candidates,
        source_filename=source_name,
    )


def parse_payload(
    raw: bytes,
    fmt: Optional[str] = None,
    *,
    content_type: Optional[str] = None,
    url: Optional[str] = None,
    field_map: Optional[Dict] = None,
    country_code: str = "XX",
    timestamp_utc: str = "",
    dept_cne_code: str = "00",
    dept_name: str = "TODOS",
    scope: str = "nacional",
    source_name: str = "",
) -> AdaptedSnapshot:
    """
    Punto de entrada universal: detecta el formato (si no viene dado) y
    despacha al parser registrado. Universal entry point: detects the
    format (when not given) and dispatches to the registered parser.

    Args:
        raw:          Bytes crudos del payload / Raw payload bytes
        fmt:          Formato conocido o None para auto-detectar
                      Known format, or None to auto-detect
        content_type: Header Content-Type (pista) / (hint)
        url:          URL de origen (pista) / Source URL (hint)
        field_map:    Mapeo declarativo por país / Declarative per-country map
        country_code, timestamp_utc, dept_cne_code, dept_name, scope,
        source_name:  Metadatos del snapshot / Snapshot metadata

    Raises:
        UnsupportedFormatError: formato detectado sin parser registrado
                                detected format without a registered parser
    """
    from centinel.format_detector import detect_format

    detected = fmt or detect_format(raw, content_type, url)
    if fmt and fmt != "unknown":
        confirmed = detect_format(raw, content_type, url)
        if confirmed not in ("unknown", fmt):
            logger.warning(
                "format_hint_mismatch hint=%s detected=%s — usando lo detectado "
                "/ using detected", fmt, confirmed,
            )
            detected = confirmed

    parser = FORMAT_PARSERS.get(detected)
    if parser is None:
        raise UnsupportedFormatError(
            f"format '{detected}' detectado pero sin parser registrado — "
            f"soportados: {sorted(FORMAT_PARSERS)}. Para XML/HTML: registrar "
            "parser con @register_parser en schema_adapter.py; PDF requiere "
            f"OCR (fase futura). / format '{detected}' detected but no parser "
            "registered."
        )

    return parser(
        raw,
        field_map=field_map,
        country_code=country_code,
        timestamp_utc=timestamp_utc,
        dept_cne_code=dept_cne_code,
        dept_name=dept_name,
        scope=scope,
        source_name=source_name,
    )
