"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `src/centinel/logging.py`.
Este módulo forma parte de Centinel Engine y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - setup_logging
  - bind_context

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `src/centinel/logging.py`.
This module is part of Centinel Engine and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - setup_logging
  - bind_context

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

# Logging Module
# AUTO-DOC-INDEX
#
# ES: Índice rápido
#   1) Propósito del módulo
#   2) Componentes principales
#   3) Puntos de extensión
#
# EN: Quick index
#   1) Module purpose
#   2) Main components
#   3) Extension points
#
# Secciones / Sections:
#   - Configuración / Configuration
#   - Lógica principal / Core logic
#   - Integraciones / Integrations


from __future__ import annotations

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Optional

import structlog

# Log schema version — increment when the field set changes.
_LOG_SCHEMA = "centinel-log-v1"


def _add_schema_version(logger: Any, method: str, event_dict: dict) -> dict:
    """Inject schema identifier into every log record."""
    event_dict.setdefault("schema", _LOG_SCHEMA)
    return event_dict


def _add_election_context(logger: Any, method: str, event_dict: dict) -> dict:
    """Inject election_id and centinel_version from environment variables."""
    event_dict.setdefault("election_id", os.environ.get("CENTINEL_ELECTION_ID", "unknown"))
    event_dict.setdefault("centinel_version", os.environ.get("CENTINEL_VERSION", "unknown"))
    return event_dict


def setup_logging(log_level: str, storage_path: Path) -> structlog.BoundLogger:
    """Configura structlog y handlers de consola/archivo.

    English: Configure structlog and console/file handlers.
    Every emitted log line conforms to centinel-log-v1 schema.
    """
    log_dir = storage_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        log_dir / "vigil.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    console_handler = logging.StreamHandler()

    logging.basicConfig(
        level=log_level.upper(),
        handlers=[file_handler, console_handler],
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_schema_version,
            _add_election_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level.upper()),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


def bind_context(
    logger: structlog.BoundLogger,
    snapshot_id: Optional[str] = None,
    source_url: Optional[str] = None,
    hash_value: Optional[str] = None,
    snapshot_hash: Optional[str] = None,
) -> structlog.BoundLogger:
    """Adjunta contexto estándar al logger (snapshot_id, source_url, hash).

    English: Bind standard chain-of-custody context to the logger.
    snapshot_hash is the canonical field for centinel-log-v1 forensic traceability.
    """
    context: dict[str, Any] = {}
    if snapshot_id:
        context["snapshot_id"] = snapshot_id
    if source_url:
        context["source_url"] = source_url
    if hash_value:
        context["hash"] = hash_value
    if snapshot_hash:
        context["snapshot_hash"] = snapshot_hash
    return logger.bind(**context)
