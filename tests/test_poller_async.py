"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `tests/test_poller_async.py`.
Tests de los límites de capacidad honesta del poller asíncrono
(centinel.core.poller_async): cap de 100 endpoints, piso ético de 3 min,
estiramiento del intervalo por presupuesto req/h por host, reintentos con
backoff y Retry-After (429), y batching de push.

Componentes detectados:
  - TestResolveSafeInterval
  - TestEndpointCap
  - TestRetryDelay
  - TestFetchOneRetries
  - TestPushBatching

======================== ENGLISH ========================
File: `tests/test_poller_async.py`.
Tests for the async poller's honest capacity limits
(centinel.core.poller_async): 100-endpoint cap, 3-min ethical floor,
per-host req/h budget interval stretching, retries with backoff and
Retry-After (429), and push batching.

Detected components:
  - TestResolveSafeInterval
  - TestEndpointCap
  - TestRetryDelay
  - TestFetchOneRetries
  - TestPushBatching
"""

import asyncio

from centinel.core.poller_async import (
    ETHICAL_FLOOR_SECONDS,
    FETCH_MAX_ATTEMPTS,
    MAX_ENDPOINTS,
    ContinuousPoller,
    EndpointConfig,
    _cap_endpoints,
    _retry_delay,
    endpoints_per_host,
    fetch_one,
    resolve_safe_interval,
)


def _eps(count, host="cne.hn"):
    return [EndpointConfig(id=f"e{i}", url=f"https://{host}/api/{i}")
            for i in range(count)]


class TestResolveSafeInterval:
    def test_19_endpoints_one_host_keeps_3min(self):
        # Caso real Honduras: 19 endpoints × 20 ciclos/h = 380 req/h ≤ 480
        assert resolve_safe_interval(_eps(19), 180, rph_ceiling=480) == 180

    def test_24_endpoints_one_host_is_the_limit(self):
        assert resolve_safe_interval(_eps(24), 180, rph_ceiling=480) == 180

    def test_25_endpoints_one_host_stretches(self):
        assert resolve_safe_interval(_eps(25), 180, rph_ceiling=480) > 180

    def test_100_endpoints_one_host_stretches_to_750(self):
        # 100 × 3600 / 480 = 750s (12.5 min)
        assert resolve_safe_interval(_eps(100), 180, rph_ceiling=480) == 750

    def test_100_endpoints_multi_host_keeps_3min(self):
        eps = [EndpointConfig(id=f"e{i}", url=f"https://h{i % 5}.example/api/{i}")
               for i in range(100)]
        assert resolve_safe_interval(eps, 180, rph_ceiling=480) == 180

    def test_ethical_floor_enforced(self, monkeypatch):
        monkeypatch.delenv("CENTINEL_CEILING_UNLOCKED", raising=False)
        assert resolve_safe_interval(_eps(1), 60, rph_ceiling=480) == ETHICAL_FLOOR_SECONDS

    def test_ceiling_unlock_allows_below_floor(self, monkeypatch):
        monkeypatch.setenv("CENTINEL_CEILING_UNLOCKED", "1")
        # 1 endpoint: presupuesto por host no estira → 60s pasa
        assert resolve_safe_interval(_eps(1), 60, rph_ceiling=480) == 60

    def test_host_budget_applies_even_unlocked(self, monkeypatch):
        # El desbloqueo salta el piso, no el presupuesto del servidor ajeno
        monkeypatch.setenv("CENTINEL_CEILING_UNLOCKED", "1")
        assert resolve_safe_interval(_eps(19), 60, rph_ceiling=480) == 143

    def test_requested_above_all_limits_respected(self):
        assert resolve_safe_interval(_eps(19), 600, rph_ceiling=480) == 600

    def test_endpoints_per_host_grouping(self):
        eps = _eps(3, "a.example") + _eps(2, "b.example")
        # ids duplicados no importan para el conteo por host
        counts = endpoints_per_host(eps)
        assert counts == {"a.example": 3, "b.example": 2}


class TestEndpointCap:
    def test_max_endpoints_is_100(self):
        assert MAX_ENDPOINTS == 100

    def test_under_cap_untouched(self):
        eps = _eps(19)
        assert _cap_endpoints(eps) is eps

    def test_over_cap_truncated(self):
        capped = _cap_endpoints(_eps(150))
        assert len(capped) == MAX_ENDPOINTS


class TestRetryDelay:
    def test_exponential_backoff(self):
        assert 2.0 <= _retry_delay(1, None) <= 2.5
        assert 4.0 <= _retry_delay(2, None) <= 4.5

    def test_retry_after_honored(self):
        assert _retry_delay(1, "30") == 30.0

    def test_retry_after_capped_at_60(self):
        assert _retry_delay(1, "3600") == 60.0

    def test_retry_after_http_date_falls_back(self):
        delay = _retry_delay(1, "Wed, 21 Oct 2026 07:28:00 GMT")
        assert 2.0 <= delay <= 2.5


class _FakeResponse:
    """Respuesta HTTP simulada con la interfaz mínima que usa fetch_one.
    Simulated HTTP response with the minimal interface fetch_one uses."""

    def __init__(self, status, body=b"{}", headers=None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    async def read(self):
        return self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeSession:
    """Sesión que sirve una secuencia de respuestas y cuenta llamadas.
    Session serving a scripted response sequence, counting calls.
    El conftest bloquea sockets reales, por eso no hay servidor local.
    conftest blocks real sockets, hence no local server."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return self._responses[min(self.calls - 1, len(self._responses) - 1)]


class TestFetchOneRetries:
    @staticmethod
    def _fetch(session):
        ep = EndpointConfig(id="t", url="https://cne.example/api", timeout_seconds=5)
        return asyncio.run(fetch_one(session, ep))

    def test_success_first_attempt(self):
        session = _FakeSession([_FakeResponse(200, b'{"resultados": []}')])
        result = self._fetch(session)
        assert result.success is True
        assert session.calls == 1
        assert result.content_hash

    def test_429_retries_then_succeeds(self):
        session = _FakeSession([
            _FakeResponse(429, headers={"Retry-After": "0"}),
            _FakeResponse(429, headers={"Retry-After": "0"}),
            _FakeResponse(200, b'{"ok": true}'),
        ])
        result = self._fetch(session)
        assert result.success is True
        assert session.calls == 3

    def test_404_does_not_retry(self):
        session = _FakeSession([_FakeResponse(404)])
        result = self._fetch(session)
        assert result.success is False
        assert result.error == "http_404"
        assert session.calls == 1  # 4xx no transitorio: sin reintentos

    def test_persistent_500_exhausts_attempts(self, monkeypatch):
        import centinel.core.poller_async as pa

        monkeypatch.setattr(pa, "FETCH_BACKOFF_BASE_SECONDS", 0.01)
        session = _FakeSession([_FakeResponse(500)])
        result = self._fetch(session)
        assert result.success is False
        assert result.status_code == 500
        assert session.calls == FETCH_MAX_ATTEMPTS


class TestPushBatching:
    def test_default_push_every_5(self, monkeypatch):
        monkeypatch.delenv("CENTINEL_PUSH_EVERY_N", raising=False)
        poller = ContinuousPoller(endpoints=_eps(1), interval_seconds=180,
                                  max_runtime_seconds=1)
        assert poller.push_every == 5

    def test_push_every_env_override(self, monkeypatch):
        monkeypatch.setenv("CENTINEL_PUSH_EVERY_N", "2")
        poller = ContinuousPoller(endpoints=_eps(1), interval_seconds=180,
                                  max_runtime_seconds=1)
        assert poller.push_every == 2

    def test_push_every_invalid_falls_back(self, monkeypatch):
        monkeypatch.setenv("CENTINEL_PUSH_EVERY_N", "cero")
        poller = ContinuousPoller(endpoints=_eps(1), interval_seconds=180,
                                  max_runtime_seconds=1)
        assert poller.push_every == 5

    def test_push_every_minimum_1(self, monkeypatch):
        monkeypatch.setenv("CENTINEL_PUSH_EVERY_N", "0")
        poller = ContinuousPoller(endpoints=_eps(1), interval_seconds=180,
                                  max_runtime_seconds=1)
        assert poller.push_every == 1
