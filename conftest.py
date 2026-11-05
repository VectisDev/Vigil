"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `conftest.py`.
Este módulo forma parte de VIGIL y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - block_network

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `conftest.py`.
This module is part of VIGIL and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - block_network

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

# Conftest Module
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

from pathlib import Path
import socket
import sys
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent
PARENT_ROOT = REPO_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PARENT_ROOT) in sys.path:
    sys.path.remove(str(PARENT_ROOT))


@pytest.fixture(autouse=True)
def no_real_backoff_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ningún test debe dormir el backoff real de los reintentos.

    English:
        No test should sleep real retry backoff. The production retry policy
        (tenacity, exponential) is exercised by tests that simulate failing
        endpoints; without this, each of those tests blocks the whole run for
        the full backoff budget. tests/integration/test_full_cycle.py was
        hanging the suite this way, which is why CI had been narrowed to a
        two-file smoke subset instead.

        Only tenacity's sleep is replaced, so the retry LOGIC (attempt counts,
        exception classification, before_sleep hooks) is still exercised — only
        the wall-clock wait is removed.
    """
    # No parchear time.sleep: tenacity.nap.time ES el modulo time de la stdlib,
    # y desactivarlo globalmente rompe tests que dependen de ventanas reales.
    # Tampoco basta parchear tenacity.nap.sleep: Retrying fija su estrategia de
    # sleep como argumento por defecto al importar tenacity. El punto de
    # sustitucion es la indireccion que el propio codigo pasa a Retrying().
    # Do not patch time.sleep: tenacity.nap.time IS the stdlib time module, and
    # disabling it globally breaks tests that rely on real time windows. Nor is
    # patching tenacity.nap.sleep enough: Retrying binds its sleep strategy as
    # a default argument at tenacity import time. The seam is the indirection
    # the code itself passes to Retrying().
    try:
        from vigil import downloader
    except ImportError:  # pragma: no cover - entorno sin el paquete
        return

    monkeypatch.setattr(downloader, "_retry_sleep", lambda _seconds: None)


@pytest.fixture(autouse=True)
def block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Impide conexiones de red reales en tests.

    English:
        Prevents real network connections in tests.
    """

    def guarded_connect(*args: Any, **kwargs: Any) -> None:
        """Español: Función guarded_connect del módulo conftest.py.

        English: Function guarded_connect defined in conftest.py.
        """
        raise RuntimeError("Network access is disabled during tests.")

    def guarded_create_connection(*args: Any, **kwargs: Any) -> None:
        """Español: Función guarded_create_connection del módulo conftest.py.

        English: Function guarded_create_connection defined in conftest.py.
        """
        raise RuntimeError("Network access is disabled during tests.")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect, raising=True)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection, raising=True)


@pytest.fixture(autouse=True)
def _reset_global_singletons():
    """Reset module-level singletons between tests.

    The proxy rotator and healthcheck state are process-global
    singletons; without resetting them a test that initializes one
    leaks state into later tests (e.g. test_full_cycle initializing
    the rotator made test_process_sources_handles_connection_error
    fail). Reset both before and after each test.

    English: Prevents cross-test pollution from global singletons.
    """

    def _reset() -> None:
        try:
            import vigil.proxy_handler as _ph

            _ph._ROTATOR = None
        except Exception:
            # Module not importable in this test session: nothing to reset.
            pass
        try:
            from monitoring.health import reset_health_state

            reset_health_state()
        except Exception:
            # Module not importable in this test session: nothing to reset.
            pass

    _reset()
    yield
    _reset()
