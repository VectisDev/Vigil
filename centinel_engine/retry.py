"""Unified retry infrastructure for Centinel Engine.

Infraestructura unificada de reintentos para Centinel Engine.

Provides a single ``retry_backoff`` decorator built on tenacity that
replaces four manual while-loop patterns in the pipeline. All retry
parameters are configurable; defaults are conservative and safe for
production electoral monitoring.

Proporciona un único decorador ``retry_backoff`` sobre tenacity que
reemplaza cuatro patrones manuales de while-loop. Los parámetros son
configurables; los defaults son conservadores y seguros para monitoreo.

Components / Componentes:
  - retry_backoff: Main retry decorator using tenacity.
  - RetryConfig: Dataclass for retry parameters.
  - is_transient_network_error: Predicate for retryable exceptions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, Type

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Default retryable exception types for pipeline network calls.
# Includes both stdlib and requests connection errors so the decorator
# works before and after the httpx migration is complete.
_DEFAULT_RETRYABLE: tuple[type[BaseException], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


@dataclass
class RetryConfig:
    """Parameters for retry_backoff decorator.

    Parámetros para el decorador retry_backoff.
    """

    max_attempts: int = 3
    base_seconds: float = 5.0
    max_seconds: float = 60.0
    retryable_exceptions: Sequence[Type[BaseException]] = field(
        default_factory=lambda: list(_DEFAULT_RETRYABLE)
    )
    log_event: str = "retry_attempt"


def _make_before_sleep(cfg: RetryConfig) -> Callable[[RetryCallState], None]:
    """Build a tenacity before-sleep hook that logs the retry.

    Construye hook before-sleep de tenacity que loguea el reintento.
    """

    def _hook(state: RetryCallState) -> None:
        exc = state.outcome.exception() if state.outcome else None
        logger.warning(
            "%s attempt=%d error=%s delay_s=%.1f",
            cfg.log_event,
            state.attempt_number,
            exc,
            state.next_action.sleep if state.next_action else 0.0,
        )

    return _hook


def retry_backoff(
    *,
    max_attempts: int = 3,
    base_seconds: float = 5.0,
    max_seconds: float = 60.0,
    retryable_exceptions: Sequence[Type[BaseException]] | None = None,
    log_event: str = "retry_attempt",
) -> Callable[[Any], Any]:
    """Retry decorator with exponential back-off, built on tenacity.

    Decorador de reintento con back-off exponencial, basado en tenacity.

    Usage / Uso::

        @retry_backoff(max_attempts=3, base_seconds=5, max_seconds=60)
        def my_function():
            ...

    Args:
        max_attempts: Total number of attempts (including the first call).
        base_seconds: Base wait in seconds; doubles each attempt.
        max_seconds: Cap on the wait time between retries.
        retryable_exceptions: Tuple of exception types to retry on.
            Defaults to (ConnectionError, TimeoutError, OSError).
        log_event: Structured log event name emitted before each retry.

    Returns:
        Decorated callable with retry behaviour.
    """
    exc_types = tuple(retryable_exceptions) if retryable_exceptions else _DEFAULT_RETRYABLE
    cfg = RetryConfig(
        max_attempts=max_attempts,
        base_seconds=base_seconds,
        max_seconds=max_seconds,
        retryable_exceptions=exc_types,
        log_event=log_event,
    )
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_seconds, max=max_seconds),
        retry=retry_if_exception_type(exc_types),
        before_sleep=_make_before_sleep(cfg),
        reraise=True,
    )
