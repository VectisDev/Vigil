"""
FormatDetector: identifica el formato de resultados electorales por contenido.
FormatDetector: identifies electoral results format from content.

Cada organismo electoral del continente publica en su propio formato:
Honduras/Guatemala/Brasil (TREP) = JSON; México INE-PREP, Argentina y los
portales de datos abiertos = CSV; portales históricos = HTML. Este módulo
detecta el formato real del payload para que el adaptador correcto se
seleccione solo — cero código nuevo por país.

Each electoral authority in the continent publishes in its own format:
Honduras/Guatemala/Brazil (TREP) = JSON; Mexico INE-PREP, Argentina and
open-data portals = CSV; legacy portals = HTML. This module detects the
actual payload format so the right adapter self-selects — zero new code
per country.

Orden de detección / Detection order:
  1. Magic bytes (%PDF, <?xml, <!DOCTYPE/<html, {/[)
  2. Parse tentativo JSON / Tentative JSON parse
  3. csv.Sniffer sobre las primeras líneas / over the first lines
  4. Content-Type header como desempate / as tiebreaker
  5. Extensión de la URL como última pista / URL extension as last hint

Solo stdlib. Stdlib only.
"""

from __future__ import annotations

import csv
import json
import logging
from typing import Optional

logger = logging.getLogger("centinel.format_detector")

# Formatos con parser registrado en schema_adapter hoy.
# Formats with a parser registered in schema_adapter today.
PARSEABLE_FORMATS = frozenset({"json", "csv"})

# Formatos que se detectan pero aún no tienen parser (puerta abierta).
# Formats detected but without a parser yet (door left open).
DETECTED_ONLY_FORMATS = frozenset({"xml", "html", "pdf"})

_SAMPLE_BYTES = 65536          # bytes inspeccionados / bytes inspected
_CSV_SNIFF_LINES = 10
_CSV_DELIMITERS = ",;\t|"

_CONTENT_TYPE_MAP = {
    "application/json": "json",
    "text/json": "json",
    "application/ld+json": "json",
    "text/csv": "csv",
    "application/csv": "csv",
    "text/xml": "xml",
    "application/xml": "xml",
    "text/html": "html",
    "application/xhtml+xml": "html",
    "application/pdf": "pdf",
}

_URL_EXTENSION_MAP = {
    ".json": "json",
    ".csv": "csv",
    ".tsv": "csv",
    ".xml": "xml",
    ".html": "html",
    ".htm": "html",
    ".pdf": "pdf",
}


def _decode_sample(content: bytes) -> str:
    """UTF-8 (con BOM) primero, latin-1 como red de seguridad — los CSV
    electorales viejos del continente suelen venir en latin-1.
    UTF-8 (BOM-aware) first, latin-1 as safety net — older electoral CSVs
    in the continent tend to be latin-1."""
    sample = content[:_SAMPLE_BYTES]
    try:
        return sample.decode("utf-8-sig")
    except UnicodeDecodeError:
        return sample.decode("latin-1", errors="replace")


def _detect_by_content(content: bytes) -> Optional[str]:
    """Detección por magic bytes y estructura. Content/magic-based detection."""
    if content.lstrip().startswith(b"%PDF"):
        return "pdf"

    text = _decode_sample(content).lstrip("﻿ \t\r\n")
    if not text:
        return None

    lowered = text[:2048].lower()
    if lowered.startswith("<?xml"):
        # XHTML servido como XML sigue siendo HTML para nuestros fines
        # XHTML served as XML is still HTML for our purposes
        return "html" if "<html" in lowered else "xml"
    if lowered.startswith("<!doctype html") or lowered.startswith("<html"):
        return "html"
    if text.startswith("<"):
        return "html" if "<html" in lowered else "xml"

    if text[0] in "{[":
        try:
            json.loads(_decode_sample(content) if len(content) <= _SAMPLE_BYTES else content.decode("utf-8", errors="replace"))
            return "json"
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Empieza como JSON pero no parsea completo (¿truncado?) —
            # sigue siendo la mejor hipótesis de contenido.
            # Starts as JSON but doesn't fully parse (truncated?) —
            # still the best content hypothesis.
            return "json"

    return _detect_csv(text)


def _detect_csv(text: str) -> Optional[str]:
    """csv.Sniffer sobre las primeras líneas, con verificación de columnas
    consistentes. csv.Sniffer over the first lines, verifying consistent
    column counts."""
    lines = [ln for ln in text.splitlines() if ln.strip()][:_CSV_SNIFF_LINES]
    if len(lines) < 2:
        return None
    sample = "\n".join(lines)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=_CSV_DELIMITERS)
    except csv.Error:
        return None
    rows = list(csv.reader(lines, dialect))
    widths = {len(r) for r in rows if r}
    # CSV real: ≥2 columnas y ancho consistente en las primeras filas
    # Real CSV: ≥2 columns and consistent width across the first rows
    if len(widths) == 1 and widths.pop() >= 2:
        return "csv"
    return None


def detect_format(
    content: bytes,
    content_type: Optional[str] = None,
    url: Optional[str] = None,
) -> str:
    """
    Detecta el formato del payload: 'json' | 'csv' | 'xml' | 'html' |
    'pdf' | 'unknown'. El contenido manda; el header Content-Type y la
    extensión de la URL solo desempatan.

    Detects the payload format: 'json' | 'csv' | 'xml' | 'html' |
    'pdf' | 'unknown'. Content rules; the Content-Type header and URL
    extension only break ties.

    Args:
        content:      Bytes crudos del payload / Raw payload bytes
        content_type: Header Content-Type (opcional) / (optional)
        url:          URL de origen (opcional, solo la extensión se usa)
                      Source URL (optional, only the extension is used)
    """
    if content:
        detected = _detect_by_content(content)
        if detected:
            return detected

    if content_type:
        mime = content_type.split(";")[0].strip().lower()
        mapped = _CONTENT_TYPE_MAP.get(mime)
        if mapped:
            return mapped

    if url:
        path = url.split("?")[0].split("#")[0].lower()
        for ext, fmt in _URL_EXTENSION_MAP.items():
            if path.endswith(ext):
                return fmt

    return "unknown"


def csv_dialect_for(content: bytes) -> csv.Dialect:
    """
    Devuelve el dialecto CSV detectado (delimitador , ; tab |).
    Returns the detected CSV dialect (delimiter , ; tab |).

    Raises:
        csv.Error: si no se puede inferir / if it cannot be inferred
    """
    text = _decode_sample(content)
    lines = [ln for ln in text.splitlines() if ln.strip()][:_CSV_SNIFF_LINES]
    return csv.Sniffer().sniff("\n".join(lines), delimiters=_CSV_DELIMITERS)
