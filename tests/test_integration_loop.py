"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `tests/test_integration_loop.py`.
Este módulo forma parte de VIGIL y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - _scheduler_loop_backup_hook
  - test_rate_limiter_blocks_burst
  - test_backup_called_after_scrape
  - test_vital_signs_triggers_conservative

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `tests/test_integration_loop.py`.
This module is part of VIGIL and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - _scheduler_loop_backup_hook
  - test_rate_limiter_blocks_burst
  - test_backup_called_after_scrape
  - test_vital_signs_triggers_conservative

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from vigil_engine.rate_limiter import TokenBucketRateLimiter
from vigil_engine.vital_signs import check_vital_signs


def _scheduler_loop_backup_hook(scrape_ok: bool, backup_hook: Callable[[], dict[str, Any]]) -> None:
    """Run backup hook on success path and always again in finalizer.

    Bilingual: Ejecuta el hook de backup en ruta de éxito y siempre otra vez
    en el finalizador.

    Args:
        scrape_ok: Simulated scrape success state.
        backup_hook: Backup function to execute.
    """
    try:
        if scrape_ok:
            backup_hook()
    finally:
        # Fail-safe backup regardless of scrape result /
        # Respaldo fail-safe independientemente del resultado
        backup_hook()


def test_rate_limiter_blocks_burst() -> None:
    """Rate limiter must block burst traffic after token depletion.

    Bilingual: El rate limiter debe bloquear tráfico en ráfaga tras agotar tokens.
    """
    limiter = TokenBucketRateLimiter(
        rate_interval=0.12, burst=1, min_interval=0.0, max_interval=1.0, enforce_ceiling=False
    )

    start = time.monotonic()
    for _ in range(5):
        limiter.wait()
    elapsed = time.monotonic() - start

    assert elapsed >= 0.35


def test_backup_called_after_scrape() -> None:
    """Backup hook should run after successful scrape and again in finalizer.

    Bilingual: El hook de backup debe correr tras scrape exitoso y otra vez en finalizador.
    """
    calls: list[int] = []

    def _backup_stub() -> dict[str, Any]:
        """Track backup hook invocations in deterministic way.

        Bilingual: Registra invocaciones del hook de backup de forma determinística.

        Returns:
            Simulated backup metadata.
        """
        calls.append(1)
        return {"local": True}

    _scheduler_loop_backup_hook(scrape_ok=True, backup_hook=_backup_stub)

    assert len(calls) == 2


def test_vital_signs_triggers_conservative() -> None:
    """Four consecutive failures should trigger conservative mode delay.

    Bilingual: Cuatro fallos consecutivos deben activar delay en modo conservador.
    """
    config = {
        "scrape_interval_seconds": 300,
        "consecutive_failures_conservative": 3,
        "consecutive_failures_critical": 5,
    }
    status = {
        "consecutive_failures": 4,
        "success_history": [False, False, False, False],
        "latency_history": [1.0, 1.1, 1.2, 1.3],
        "hash_chain_valid": True,
    }

    vital_state = check_vital_signs(config, status)

    assert vital_state["mode"] == "conservative"
    assert int(vital_state["recommended_delay_seconds"]) >= 600
