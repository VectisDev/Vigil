"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `centinel_engine/rate_limiter.py`.
Este módulo forma parte de Centinel Engine y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - HARD_CEILING / PRESET_MODES
  - TokenBucketRateLimiter
  - _load_rate_limiter_config
  - get_rate_limiter
  - switch_mode
  - reset_rate_limiter

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `centinel_engine/rate_limiter.py`.
This module is part of Centinel Engine and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - HARD_CEILING / PRESET_MODES
  - TokenBucketRateLimiter
  - _load_rate_limiter_config
  - get_rate_limiter
  - switch_mode
  - reset_rate_limiter

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from collections import deque
from typing import Any, Deque, Optional

from centinel_engine.config_loader import load_config

logger = logging.getLogger(__name__)

HARD_CEILING_MAX_REQUESTS_PER_HOUR: int = 480
HARD_CEILING_MIN_INTERVAL: float = 2.0
HARD_CEILING_MAX_BURST: int = 8

PRESET_MODES: dict[str, dict[str, Any]] = {
    "normal": {
        "rate_interval": 10.0, "burst": 5, "min_interval": 6.0,
        "max_interval": 12.0, "max_requests_per_hour": 240,
        "conservative_min_delay_seconds": 600.0,
    },
    "electoral": {
        "rate_interval": 7.0, "burst": 6, "min_interval": 3.0,
        "max_interval": 8.0, "max_requests_per_hour": 360,
        "conservative_min_delay_seconds": 300.0,
    },
    "aggressive": {
        "rate_interval": 5.0, "burst": 8, "min_interval": 2.0,
        "max_interval": 6.0, "max_requests_per_hour": 480,
        "conservative_min_delay_seconds": 120.0,
    },
    "conservative": {
        "rate_interval": 15.0, "burst": 3, "min_interval": 10.0,
        "max_interval": 20.0, "max_requests_per_hour": 120,
        "conservative_min_delay_seconds": 900.0,
    },
}

DEFAULT_RATE_INTERVAL: float = 10.0
DEFAULT_BURST: int = 5
DEFAULT_MIN_INTERVAL: float = 6.0
DEFAULT_MAX_INTERVAL: float = 12.0
DEFAULT_MAX_REQUESTS_PER_HOUR: int = 240
DEFAULT_BACKOFF_JITTER_MIN: float = 0.55
DEFAULT_BACKOFF_JITTER_MAX: float = 1.85
DEFAULT_CONSERVATIVE_MIN_DELAY_SECONDS: float = 600.0
DEFAULT_429_WINDOW_SECONDS: float = 300.0
DEFAULT_429_THRESHOLD: int = 2


class TokenBucketRateLimiter:
    """Throttle requests using a thread-safe token bucket.

    Bilingual: Limita solicitudes usando un token-bucket thread-safe.

    Args:
        rate_interval: Seconds to refill one token.
        burst: Maximum token capacity.
        min_interval: Minimum spacing between requests in seconds.
        max_interval: Maximum enforced wait in seconds.
        max_requests_per_hour: Hard legal/ethical upper limit.
        conservative_min_delay_seconds: Minimum delay while in conservative mode.

    Returns:
        None: Class constructor.

    Raises:
        ValueError: If any provided threshold is invalid.
    """

    def __init__(
        self,
        rate_interval: float = DEFAULT_RATE_INTERVAL,
        burst: int = DEFAULT_BURST,
        min_interval: float = DEFAULT_MIN_INTERVAL,
        max_interval: float = DEFAULT_MAX_INTERVAL,
        max_requests_per_hour: int = DEFAULT_MAX_REQUESTS_PER_HOUR,
        conservative_min_delay_seconds: float = DEFAULT_CONSERVATIVE_MIN_DELAY_SECONDS,
        *,
        mode: str = "normal",
        enforce_ceiling: bool = True,
    ) -> None:
        if enforce_ceiling:
            max_requests_per_hour = min(int(max_requests_per_hour), HARD_CEILING_MAX_REQUESTS_PER_HOUR)
            min_interval = max(float(min_interval), HARD_CEILING_MIN_INTERVAL)
            burst = min(int(burst), HARD_CEILING_MAX_BURST)
        self._validate_limits(rate_interval, burst, min_interval, max_interval, max_requests_per_hour)
        self.rate_interval = float(rate_interval)
        self.burst = int(burst)
        self.min_interval = float(min_interval)
        self.max_interval = float(max_interval)
        self.max_requests_per_hour = int(max_requests_per_hour)
        self.conservative_min_delay_seconds = float(conservative_min_delay_seconds)
        self._mode = mode
        self._enforce_ceiling = enforce_ceiling

        self._tokens = float(self.burst)
        self._last_refill = time.monotonic()
        self._last_request = 0.0
        self._lock = threading.Lock()
        self._total_wait = 0.0
        self._total_waits = 0
        self._consecutive_failures = 0
        self._recent_429_timestamps: Deque[float] = deque()
        self._request_timestamps: Deque[float] = deque()
        self._conservative_mode_until = 0.0

    @staticmethod
    def _validate_limits(
        rate_interval: float,
        burst: int,
        min_interval: float,
        max_interval: float,
        max_requests_per_hour: int,
    ) -> None:
        """Validate limiter configuration values.

        Bilingual: Valida valores de configuración del limitador.

        Args:
            rate_interval: Seconds per token refill.
            burst: Maximum token count.
            min_interval: Minimum spacing between calls.
            max_interval: Maximum allowed sleep window.
            max_requests_per_hour: Hard cap per rolling hour.

        Returns:
            None: Validation helper.

        Raises:
            ValueError: If configuration is inconsistent.
        """
        if rate_interval <= 0:
            raise ValueError("rate_interval must be positive")
        if burst < 1:
            raise ValueError("burst must be >= 1")
        if min_interval < 0:
            raise ValueError("min_interval must be >= 0")
        if max_interval <= 0:
            raise ValueError("max_interval must be positive")
        if min_interval > max_interval:
            raise ValueError("min_interval must be <= max_interval")
        if max_requests_per_hour < 1:
            raise ValueError("max_requests_per_hour must be >= 1")

    def _refill_tokens(self, now: float) -> None:
        """Refill tokens according to elapsed monotonic time.

        Bilingual: Rellena tokens según tiempo monotónico transcurrido.

        Args:
            now: Current monotonic timestamp.

        Returns:
            None: Internal state update.

        Raises:
            None.
        """
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return
        added_tokens = elapsed / self.rate_interval
        self._tokens = min(float(self.burst), self._tokens + added_tokens)
        self._last_refill = now

    def _compute_wait(self, now: float) -> float:
        """Compute required blocking time for the next request.

        Bilingual: Calcula el tiempo de bloqueo requerido para la siguiente solicitud.

        Args:
            now: Current monotonic timestamp.

        Returns:
            float: Sleep duration in seconds.

        Raises:
            None.
        """
        token_wait = 0.0
        if self._tokens < 1.0:
            token_wait = (1.0 - self._tokens) * self.rate_interval

        min_gap_wait = max(0.0, self.min_interval - (now - self._last_request))
        desired_wait = max(token_wait, min_gap_wait)
        return min(desired_wait, self.max_interval)

    def _enforce_hourly_limit_wait(self, now_wall: float) -> float:
        """Return extra wait needed to honor the per-hour request cap.

        Bilingual: Retorna espera extra necesaria para respetar el límite por hora.

        Args:
            now_wall: Current wall-clock timestamp.

        Returns:
            float: Additional wait seconds to maintain cap.

        Raises:
            None.
        """
        window_start = now_wall - 3600.0
        while self._request_timestamps and self._request_timestamps[0] < window_start:
            self._request_timestamps.popleft()
        if len(self._request_timestamps) < self.max_requests_per_hour:
            return 0.0
        oldest_within_window = self._request_timestamps[0]
        return max(0.0, (oldest_within_window + 3600.0) - now_wall)

    def _compute_adaptive_backoff_delay(self) -> float:
        """Compute adaptive backoff with exponential jitter.

        Bilingual: Calcula backoff adaptativo con jitter exponencial.

        Args:
            None.

        Returns:
            float: Delay derived from failures and jitter.

        Raises:
            None.
        """
        if self._consecutive_failures <= 0:
            return 0.0
        base = max(3600.0 / float(self.max_requests_per_hour), self.min_interval)
        jitter = random.uniform(DEFAULT_BACKOFF_JITTER_MIN, DEFAULT_BACKOFF_JITTER_MAX)
        return base * (2 ** self._consecutive_failures) * jitter

    def _is_conservative_active(self, now_wall: float) -> bool:
        """Check whether conservative mode is active.

        Bilingual: Verifica si el modo conservador está activo.

        Args:
            now_wall: Current wall-clock timestamp.

        Returns:
            bool: True when conservative mode still applies.

        Raises:
            None.
        """
        return now_wall < self._conservative_mode_until

    def wait(self) -> float:
        """Block until next request is allowed and consume one token.

        Bilingual: Bloquea hasta permitir la siguiente solicitud y consume un token,
        aplicando jitter más amplio y sleep aleatorio para romper patrones avanzados de timing.

        Args:
            None.

        Returns:
            float: Seconds waited for the call, including adaptive and random delays.

        Raises:
            None.
        """
        total_waited = 0.0
        with self._lock:
            while True:
                now_mono = time.monotonic()
                now_wall = time.time()
                self._refill_tokens(now_mono)
                core_wait = self._compute_wait(now_mono)
                hourly_wait = self._enforce_hourly_limit_wait(now_wall)
                adaptive_wait = self._compute_adaptive_backoff_delay()
                conservative_wait = self.conservative_min_delay_seconds if self._is_conservative_active(now_wall) else 0.0

                wait_seconds = max(core_wait, hourly_wait, adaptive_wait, conservative_wait)
                # Wider jitter + random sleep to disrupt advanced timing fingerprinting / # Jitter más amplio + sleep random para romper fingerprinting por timing avanzado
                random_sleep: float = random.uniform(0.0, 3.2)
                time.sleep(random_sleep)
                total_waited += random_sleep
                if wait_seconds <= 0:
                    break
                # English: sleep in bounded chunks so long waits can adapt quickly. / Español: dormir en bloques para adaptar esperas largas.
                sleep_chunk = min(wait_seconds, 60.0)
                time.sleep(sleep_chunk)
                total_waited += sleep_chunk

            now_mono = time.monotonic()
            now_wall = time.time()
            self._refill_tokens(now_mono)
            self._tokens = max(0.0, self._tokens - 1.0)
            self._last_request = now_mono
            self._request_timestamps.append(now_wall)
            self._total_wait += total_waited
            self._total_waits += 1
            return total_waited

    def notify_response(self, status_code: Optional[int], *, success: bool) -> None:
        """Update adaptive state from upstream response outcomes.

        Bilingual: Actualiza estado adaptativo con el resultado de respuesta.

        Args:
            status_code: Optional HTTP response status code.
            success: Whether request is considered successful.

        Returns:
            None.

        Raises:
            None.
        """
        with self._lock:
            if success:
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1

            now_wall = time.time()
            if status_code == 429:
                self._recent_429_timestamps.append(now_wall)
            window_start = now_wall - DEFAULT_429_WINDOW_SECONDS
            while self._recent_429_timestamps and self._recent_429_timestamps[0] < window_start:
                self._recent_429_timestamps.popleft()

            if len(self._recent_429_timestamps) > DEFAULT_429_THRESHOLD:
                # English: force immediate conservative mode under repeated 429 bursts. / Español: forzar modo conservador inmediato ante ráfagas 429.
                self._conservative_mode_until = max(
                    self._conservative_mode_until,
                    now_wall + self.conservative_min_delay_seconds,
                )
                logger.warning(
                    "rate_limiter_forced_conservative | 429_burst=%s window_seconds=%s",
                    len(self._recent_429_timestamps),
                    int(DEFAULT_429_WINDOW_SECONDS),
                )

    def reconfigure(self, *, mode: str | None = None, **overrides: Any) -> None:
        """Hot-reconfigure the limiter for a new mode or custom values.

        Bilingual: Reconfigura el limitador en caliente para un nuevo modo o valores custom.
        """
        with self._lock:
            if mode and mode != "custom":
                preset = PRESET_MODES.get(mode)
                if not preset:
                    raise ValueError(f"Unknown mode: {mode}. Available: {', '.join(PRESET_MODES)}")
                self._mode = mode
                for key, value in preset.items():
                    setattr(self, key, type(getattr(self, key))(value))
            elif overrides:
                self._mode = mode or "custom"
                for key, value in overrides.items():
                    if hasattr(self, key):
                        setattr(self, key, type(getattr(self, key))(value))

            if self._enforce_ceiling and self._mode != "custom":
                self.max_requests_per_hour = min(self.max_requests_per_hour, HARD_CEILING_MAX_REQUESTS_PER_HOUR)
                self.min_interval = max(self.min_interval, HARD_CEILING_MIN_INTERVAL)
                self.burst = min(self.burst, HARD_CEILING_MAX_BURST)

            self._tokens = min(self._tokens, float(self.burst))
            logger.info(
                "rate_limiter_reconfigured | mode=%s rph=%d min_interval=%.1f burst=%d",
                self._mode, self.max_requests_per_hour, self.min_interval, self.burst,
            )

    @property
    def mode(self) -> str:
        with self._lock:
            return self._mode

    @property
    def stats(self) -> dict[str, Any]:
        """Expose lightweight runtime metrics.

        Bilingual: Expone métricas operativas simples en tiempo real.

        Args:
            None.

        Returns:
            dict[str, Any]: Current limiter configuration and counters.

        Raises:
            None.
        """
        with self._lock:
            return {
                "mode": self._mode,
                "rate_interval": self.rate_interval,
                "burst": self.burst,
                "min_interval": self.min_interval,
                "max_interval": self.max_interval,
                "max_requests_per_hour": self.max_requests_per_hour,
                "conservative_min_delay_seconds": self.conservative_min_delay_seconds,
                "tokens": self._tokens,
                "consecutive_failures": self._consecutive_failures,
                "recent_429_count": len(self._recent_429_timestamps),
                "total_wait_seconds": self._total_wait,
                "total_waits": self._total_waits,
                "hard_ceiling": {
                    "max_requests_per_hour": HARD_CEILING_MAX_REQUESTS_PER_HOUR,
                    "min_interval_seconds": HARD_CEILING_MIN_INTERVAL,
                    "max_burst": HARD_CEILING_MAX_BURST,
                },
            }

    @property
    def tokens_available(self) -> float:
        """Return current token availability snapshot.

        Bilingual: Retorna el snapshot actual de tokens disponibles.

        Args:
            None.

        Returns:
            float: Available tokens in bucket.

        Raises:
            None.
        """
        with self._lock:
            return self._tokens


_rate_limiter_singleton: Optional[TokenBucketRateLimiter] = None
_rate_limiter_lock = threading.Lock()


def _load_rate_limiter_config(env: str = "prod") -> dict[str, Any]:
    """Load rate limiter config with safe fallback.

    Bilingual: Carga configuración de rate limiter con fallback seguro.

    Args:
        env: Configuration environment folder.

    Returns:
        dict[str, Any]: Parsed limiter configuration.

    Raises:
        None.
    """
    try:
        return load_config("rate_limiter.yaml", env=env)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rate_limiter_config_fallback | usando defaults: %s", exc)
        return {}


def _load_core_limits(env: str = "prod") -> dict[str, Any]:
    """Load core legal/ethical limits from shared production config.

    Bilingual: Carga límites legales/éticos desde configuración productiva compartida.

    Args:
        env: Configuration environment folder.

    Returns:
        dict[str, Any]: Mapping with governance limits.

    Raises:
        None.
    """
    try:
        return load_config("rules_core.yaml", env=env)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rate_limiter_core_limits_fallback | usando defaults: %s", exc)
        return {}


def get_rate_limiter(env: str = "prod") -> TokenBucketRateLimiter:
    """Return singleton limiter instance.

    Bilingual: Retorna la instancia singleton del limitador.

    Args:
        env: Configuration environment folder.

    Returns:
        TokenBucketRateLimiter: Shared limiter instance.

    Raises:
        None.
    """
    global _rate_limiter_singleton
    with _rate_limiter_lock:
        if _rate_limiter_singleton is None:
            config = _load_rate_limiter_config(env)
            core_limits = _load_core_limits(env)

            active_mode = str(config.get("active_mode", "normal"))
            modes = config.get("modes", {})
            mode_cfg = modes.get(active_mode, {}) if isinstance(modes, dict) else {}

            def _resolve(key: str, alt_key: str, default: Any) -> Any:
                return mode_cfg.get(key, config.get(key, config.get(alt_key, default)))

            max_requests_per_hour = int(
                _resolve(
                    "max_requests_per_hour", "max_requests_per_hour",
                    core_limits.get("MAX_REQUESTS_PER_HOUR", DEFAULT_MAX_REQUESTS_PER_HOUR),
                )
            )

            ceiling = config.get("hard_ceiling", {})
            is_custom = active_mode == "custom"

            _rate_limiter_singleton = TokenBucketRateLimiter(
                rate_interval=float(_resolve("rate_interval", "rate_interval_seconds", DEFAULT_RATE_INTERVAL)),
                burst=int(_resolve("burst", "capacity", DEFAULT_BURST)),
                min_interval=float(_resolve("min_interval", "min_interval_seconds", DEFAULT_MIN_INTERVAL)),
                max_interval=float(_resolve("max_interval", "max_interval_seconds", DEFAULT_MAX_INTERVAL)),
                max_requests_per_hour=max_requests_per_hour,
                conservative_min_delay_seconds=float(
                    _resolve("conservative_min_delay_seconds", "conservative_min_delay_seconds", DEFAULT_CONSERVATIVE_MIN_DELAY_SECONDS)
                ),
                mode=active_mode,
                enforce_ceiling=not is_custom,
            )

            if ceiling and not is_custom:
                HARD_CEILING_MAX_REQUESTS_PER_HOUR_CFG = int(ceiling.get("max_requests_per_hour", HARD_CEILING_MAX_REQUESTS_PER_HOUR))
                HARD_CEILING_MIN_INTERVAL_CFG = float(ceiling.get("min_interval_seconds", HARD_CEILING_MIN_INTERVAL))
                HARD_CEILING_MAX_BURST_CFG = int(ceiling.get("max_burst", HARD_CEILING_MAX_BURST))
                _rate_limiter_singleton.max_requests_per_hour = min(
                    _rate_limiter_singleton.max_requests_per_hour, HARD_CEILING_MAX_REQUESTS_PER_HOUR_CFG
                )
                _rate_limiter_singleton.min_interval = max(
                    _rate_limiter_singleton.min_interval, HARD_CEILING_MIN_INTERVAL_CFG
                )
                _rate_limiter_singleton.burst = min(
                    _rate_limiter_singleton.burst, HARD_CEILING_MAX_BURST_CFG
                )

            logger.info(
                "rate_limiter_initialized | mode=%s rph=%d min_interval=%.1f burst=%d enforce_ceiling=%s",
                active_mode, _rate_limiter_singleton.max_requests_per_hour,
                _rate_limiter_singleton.min_interval, _rate_limiter_singleton.burst,
                not is_custom,
            )
        return _rate_limiter_singleton


def switch_mode(mode: str, **custom_overrides: Any) -> TokenBucketRateLimiter:
    """Switch the active rate limiter mode at runtime.

    Bilingual: Cambia el modo activo del rate limiter en tiempo de ejecución.
    """
    limiter = get_rate_limiter()
    if mode == "custom":
        limiter.reconfigure(mode="custom", **custom_overrides)
    else:
        limiter.reconfigure(mode=mode)
    return limiter


def reset_rate_limiter() -> None:
    """Reset singleton limiter instance for tests and controlled reload.

    Bilingual: Reinicia la instancia singleton para pruebas y recarga controlada.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    global _rate_limiter_singleton
    with _rate_limiter_lock:
        _rate_limiter_singleton = None
