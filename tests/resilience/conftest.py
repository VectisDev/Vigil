"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `tests/resilience/conftest.py`.
Este módulo forma parte de Centinel Engine y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - _install_stub_modules
  - mock_responses
  - retry_config_path
  - retry_config
  - watchdog_config_path
  - proxies_config_path
  - sample_headers

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `tests/resilience/conftest.py`.
This module is part of Centinel Engine and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - _install_stub_modules
  - mock_responses
  - retry_config_path
  - retry_config
  - watchdog_config_path
  - proxies_config_path
  - sample_headers

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

from __future__ import annotations

import sys
import types

# Install stub modules at collection time so optional packages
# (centinel_engine, structlog) do not cause ImportError.
# ES: Instala stubs en tiempo de colección para evitar ImportError.
def _install_stub_modules() -> None:
    """Install stub modules for optional dependencies that fail to import.

    Instala stubs solo para dependencias opcionales que fallen al
    importarse; los modulos reales (cuando existen e importan
    correctamente) tienen siempre prioridad para no contaminar
    sys.modules y romper otros archivos de test que importen los
    modulos reales.
    """
    # scripts.download_and_hash stub -- avoids 8-level import chain
    try:
        import scripts.download_and_hash  # noqa: F401
    except ImportError:
        import importlib.machinery as _imm
        _dah = types.ModuleType("scripts.download_and_hash")
        _dah.__spec__ = _imm.ModuleSpec("scripts.download_and_hash", None)  # type: ignore[attr-defined]
        def _build_request_headers(config: dict, low_profile: dict, rng: object) -> dict:
            """Stub: build_request_headers for resilience tests."""
            if not low_profile.get("enabled", False):
                return {"Accept": "application/json", **config.get("headers", {})}
            import random as _r
            hdrs: dict = {"Accept": "application/json"}
            ua = low_profile.get("user_agents", [])
            al = low_profile.get("accept_languages", [])
            ref = low_profile.get("referers", [])
            _rng = rng if hasattr(rng, "choice") else _r.Random()
            if ua: hdrs["User-Agent"] = _rng.choice(ua)
            if al: hdrs["Accept-Language"] = _rng.choice(al)
            if ref: hdrs["Referer"] = _rng.choice(ref)
            return hdrs
        _dah.build_request_headers = _build_request_headers  # type: ignore[attr-defined]
        sys.modules["scripts.download_and_hash"] = _dah

    try:
        from centinel_engine.config_loader import load_config  # noqa: F401
    except ImportError:
        ce = types.ModuleType("centinel_engine")
        ce_cfg = types.ModuleType("centinel_engine.config_loader")
        def _load_config(file_name: str = "", env: str = "prod") -> dict:
            return {}
        ce_cfg.load_config = _load_config  # type: ignore[attr-defined]
        sys.modules["centinel_engine"] = ce
        sys.modules["centinel_engine.config_loader"] = ce_cfg

    try:
        import structlog  # noqa: F401
    except ImportError:
        import logging as _logging
        import importlib.machinery as _imm
        sl = types.ModuleType("structlog")
        sl.__spec__ = _imm.ModuleSpec("structlog", None)
        sl.get_logger = lambda *a, **kw: _logging.getLogger("centinel")  # type: ignore[attr-defined]
        sys.modules["structlog"] = sl

    # centinel.download stub (write_atomic)
    try:
        import centinel.download  # noqa: F401
    except ImportError:
        import importlib.machinery as _imm
        import centinel as _c
        cd = types.ModuleType("centinel.download")
        cd.__spec__ = _imm.ModuleSpec("centinel.download", None)  # type: ignore[attr-defined]
        def _write_atomic(path: object, data: object, **kw: object) -> None:
            import pathlib, json as _json
            p = pathlib.Path(str(path))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(_json.dumps(data) if not isinstance(data, str) else data)
        cd.write_atomic = _write_atomic  # type: ignore[attr-defined]
        sys.modules["centinel.download"] = cd
        setattr(_c, "download", cd)

    # centinel.defense / centinel.core stubs -- only for modules that
    # fail to import for real (e.g. partial forks missing these files).
    import importlib.machinery as _imm
    for _mod_name in (
        "centinel.defense",
        "centinel.defense.logger",
        "centinel.defense.security",
        "centinel.defense.attack_logger",
        "centinel.defense.fetcher",
        "centinel.defense.hasher",
        "centinel.defense.security_utils",
        "centinel.core.custody",
        "centinel.core.connectivity",
        "centinel.core.normalize",
    ):
        if _mod_name in sys.modules:
            continue
        try:
            __import__(_mod_name)
            continue
        except ImportError:
            pass
        import logging as _ll
        _m = types.ModuleType(_mod_name)
        _m.__spec__ = _imm.ModuleSpec(_mod_name, None)  # type: ignore[attr-defined]
        _m.logger = _ll.getLogger("centinel")  # type: ignore[attr-defined]
        # Common stubs for various functions these modules expose
        for _attr in (
            "build_rotating_request_profile",
            "trigger_post_hash_backup",
            "sign_hash_record",
            "is_safe_outbound_url",
            "diagnose_and_record",
            "validate_cne_response",
        ):
            setattr(_m, _attr, lambda *a, **kw: None)  # type: ignore[misc]
        sys.modules[_mod_name] = _m

    # centinel.paths: provided by real src/centinel/paths.py on PYTHONPATH

_install_stub_modules()

import logging
from pathlib import Path

import pytest
import responses
import yaml

from centinel.downloader import load_retry_config


@pytest.fixture()
def mock_responses():
    """Español: Provee un mock de HTTP con la librería responses, sin red real.

    English: Provide an HTTP mock using the responses library with no real network.
    """
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock


@pytest.fixture()
def retry_config_path(tmp_path: Path) -> Path:
    """Español: Crea un YAML temporal de reintentos para pruebas resilientes.

    English: Create a temporary retry YAML configuration for resilience tests.
    """
    payload = {
        "default": {
            "max_attempts": 3,
            "backoff_base": 1.0,
            "backoff_multiplier": 2.0,
            "max_delay": 5.0,
            "jitter": {"min": 0.1, "max": 0.2},
        },
        "per_status": {
            "429": {
                "max_attempts": 3,
                "backoff_base": 1.0,
                "backoff_multiplier": 2.0,
                "max_delay": 5.0,
                "jitter": {"min": 0.1, "max": 0.2},
            },
            "503": {
                "max_attempts": 3,
                "backoff_base": 1.0,
                "backoff_multiplier": 2.0,
                "max_delay": 5.0,
                "jitter": {"min": 0.1, "max": 0.2},
            },
        },
        "per_exception": {
            "ReadTimeout": {
                "max_attempts": 2,
                "backoff_base": 1.0,
                "backoff_multiplier": 2.0,
                "max_delay": 5.0,
                "jitter": 0.1,
            },
            "JSONDecodeError": {
                "max_attempts": 3,
                "backoff_base": 1.0,
                "backoff_multiplier": 2.0,
                "max_delay": 5.0,
                "jitter": 0.1,
            },
        },
        "timeout_seconds": 1.0,
        "log_payload_bytes": 200,
        "failed_requests_path": str(tmp_path / "failed_requests.jsonl"),
    }
    config_path = tmp_path / "retry_config.yaml"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return config_path


@pytest.fixture()
def retry_config(retry_config_path: Path):
    """Español: Carga la configuración de reintentos desde YAML temporal.

    English: Load retry configuration from the temporary YAML file.
    """
    return load_retry_config(retry_config_path)


@pytest.fixture()
def watchdog_config_path(tmp_path: Path) -> Path:
    """Español: Genera un watchdog.yaml temporal para escenarios controlados.

    English: Generate a temporary watchdog.yaml for controlled scenarios.
    """
    payload = {
        "check_interval_minutes": 3,
        "max_inactivity_minutes": 30,
        "heartbeat_timeout": 1,
        "failure_grace_minutes": 2,
        "action_cooldown_minutes": 5,
        "data_dir": str(tmp_path / "data"),
        "heartbeat_path": str(tmp_path / "data" / "heartbeat.json"),
        "state_path": str(tmp_path / "data" / "watchdog_state.json"),
        "log_path": str(tmp_path / "logs" / "centinel.log"),
        "lock_files": [str(tmp_path / "data" / "temp" / "pipeline.lock")],
    }
    config_path = tmp_path / "watchdog.yaml"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return config_path


@pytest.fixture()
def proxies_config_path(tmp_path: Path) -> Path:
    """Español: Construye un proxies.yaml temporal para pruebas de rotación.

    English: Build a temporary proxies.yaml for rotation tests.
    """
    payload = {
        "mode": "rotate",
        "rotation_strategy": "round_robin",
        "rotation_every_n": 1,
        "proxy_timeout_seconds": 5.0,
        "test_url": "https://cne.hn/health",
        "proxies": [
            "http://proxy-1.local:8080",
            "http://proxy-2.local:8080",
        ],
    }
    config_path = tmp_path / "proxies.yaml"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return config_path


class _KwargsLogger(logging.Logger):
    """Logger subclass that tolerates structlog-style keyword arguments.

    The production code calls ``self.logger.warning("msg", key=val)`` which
    the stdlib Logger rejects.  This subclass captures kwargs into the
    ``extra`` dict so the calls succeed without requiring structlog.
    """

    def _log(
        self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1, **kwargs
    ):
        if kwargs:
            extra = {**(extra or {}), **kwargs}
        super()._log(
            level,
            msg,
            args,
            exc_info=exc_info,
            extra=extra,
            stack_info=stack_info,
            stacklevel=stacklevel,
        )


@pytest.fixture()
def kwargs_logger() -> logging.Logger:
    """Provide a logger that accepts extra keyword arguments.

    Created via the logging manager so it propagates to root and
    is captured by pytest's ``caplog`` fixture.
    """
    prev_class = logging.getLoggerClass()
    logging.setLoggerClass(_KwargsLogger)
    logger = logging.getLogger("centinel.test.proxy")
    logging.setLoggerClass(prev_class)
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture()
def sample_headers() -> dict[str, str]:
    """Español: Entrega headers persistentes para pruebas de reintento.

    English: Provide persistent headers for retry tests.
    """
    return {
        "User-Agent": "Centinel-Test/1.0",
        "Accept-Language": "es-HN,es;q=0.9,en;q=0.8",
        "Referer": "https://cne.hn/",
        "Accept": "application/json",
    }
