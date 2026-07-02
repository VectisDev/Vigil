"""
CENTINEL — Async Continuous Poller
====================================
Motor de polling asíncrono para N endpoints con intervalo garantizado.
Async polling engine for N endpoints with guaranteed interval.

Diseño / Design:
  - Corre como long-running job dentro de GitHub Actions (hasta 5.5h)
    Runs as long-running job inside GitHub Actions (up to 5.5h)
  - GitHub ve 1 job; asyncio gestiona hasta MAX_ENDPOINTS (100) en paralelo
    GitHub sees 1 job; asyncio manages up to MAX_ENDPOINTS (100) in parallel
  - Hash chain actualizada 1 vez por ciclo (batch), no por endpoint
    Hash chain updated once per cycle (batch), not per endpoint
  - Graceful shutdown antes del límite de 6h de GitHub
    Graceful shutdown before GitHub's 6h job limit
  - Integra con hashchain.py y endpoint_monitor.py existentes
    Integrates with existing hashchain.py and endpoint_monitor.py

Capacidad honesta / Honest capacity:
  El fetch de 100 endpoints en paralelo toma segundos, pero el presupuesto
  ético por host manda: con el techo de rate limit (480 req/h/host por
  defecto), un solo host admite como máximo 24 endpoints a ciclo de 3 min.
  Con más endpoints en un mismo host, el intervalo efectivo se estira
  automáticamente (resolve_safe_interval). 100 endpoints multi-host sí
  sostienen el ciclo de 3 minutos.

  Fetching 100 endpoints in parallel takes seconds, but the per-host
  ethical budget rules: with the rate-limit ceiling (default 480 req/h
  per host), a single host supports at most 24 endpoints at a 3-min
  cycle. With more endpoints on one host, the effective interval is
  stretched automatically (resolve_safe_interval). 100 multi-host
  endpoints do sustain the 3-minute cycle.

Author: CENTINEL Team
License: AGPL-3.0
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import math
import os
import random
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import aiohttp

# ── Logging estructurado / Structured logging ──────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("centinel.poller_async")


# ── Límites de capacidad / Capacity limits ─────────────────────────────────────

# Capacidad tope del poller: suficiente para cualquier país del continente
# (2× los 50 estados de EE.UU.). Configs mayores se truncan con warning.
# Poller capacity cap: enough for any country in the continent
# (2× the 50 US states). Larger configs are truncated with a warning.
MAX_ENDPOINTS = 100

# Piso ético del intervalo: 1 consulta cada 3 minutos por endpoint.
# Solo CENTINEL_CEILING_UNLOCKED=1 (ritual de desbloqueo del panel /ops)
# permite bajar de aquí — espejo del preset "Apagón / Crítico".
# Ethical interval floor: 1 request every 3 minutes per endpoint.
# Only CENTINEL_CEILING_UNLOCKED=1 (unlock ritual from the /ops panel)
# allows going below — mirrors the "Apagón / Crítico" preset.
ETHICAL_FLOOR_SECONDS = 180

# Techo de requests/hora por host si rate_limiter.yaml no está disponible.
# Per-host requests/hour ceiling if rate_limiter.yaml is unavailable.
DEFAULT_HOST_RPH_CEILING = 480

_RATE_LIMITER_CONFIG = Path("config/prod/rate_limiter.yaml")


def load_host_rph_ceiling(config_path: Path = _RATE_LIMITER_CONFIG) -> int:
    """
    Lee el techo duro de requests/hora por host desde rate_limiter.yaml.
    Reads the hard per-host requests/hour ceiling from rate_limiter.yaml.

    Fallback: DEFAULT_HOST_RPH_CEILING (480).
    """
    try:
        import yaml
        cfg = yaml.safe_load(config_path.read_text()) or {}
        ceiling = int(cfg.get("hard_ceiling", {}).get("max_requests_per_hour", 0))
        if ceiling > 0:
            return ceiling
    except Exception as exc:  # noqa: BLE001
        log.warning("rate_limiter_config_read_failed err=%s — using default %d",
                    exc, DEFAULT_HOST_RPH_CEILING)
    return DEFAULT_HOST_RPH_CEILING


def endpoints_per_host(endpoints: list["EndpointConfig"]) -> dict[str, int]:
    """
    Agrupa endpoints por hostname. Nunca loguea URLs completas.
    Groups endpoints by hostname. Never logs full URLs.
    """
    counts: dict[str, int] = {}
    for ep in endpoints:
        host = urlparse(ep.url).hostname or "unknown"
        counts[host] = counts.get(host, 0) + 1
    return counts


def resolve_safe_interval(
    endpoints: list["EndpointConfig"],
    requested_seconds: int,
    rph_ceiling: Optional[int] = None,
) -> int:
    """
    Calcula el intervalo efectivo que respeta el piso ético y el
    presupuesto de requests/hora por host.
    Computes the effective interval honoring the ethical floor and the
    per-host requests/hour budget.

    KaTeX:
      interval_efectivo = max(solicitado, piso_ético,
                              ceil(max_endpoints_por_host × 3600 / rph))

    Ejemplos con rph=480 / Examples with rph=480:
      ≤24 endpoints en 1 host → 180s (3 min) se mantiene / holds
      100 endpoints en 1 host → 750s (12.5 min)
      100 endpoints en 5 hosts (20 c/u) → 180s (3 min)
    """
    effective = requested_seconds

    if effective < ETHICAL_FLOOR_SECONDS:
        if os.environ.get("CENTINEL_CEILING_UNLOCKED") == "1":
            log.warning(
                "ethical_floor_bypassed interval=%ds — CENTINEL_CEILING_UNLOCKED=1 "
                "(preset Apagón/Crítico). Reactivar límites al cesar la emergencia.",
                effective,
            )
        else:
            log.warning(
                "interval_below_ethical_floor requested=%ds raised_to=%ds — "
                "límite ético: 1 consulta / 3 min (desbloqueo: CENTINEL_CEILING_UNLOCKED=1)",
                effective, ETHICAL_FLOOR_SECONDS,
            )
            effective = ETHICAL_FLOOR_SECONDS

    ceiling = rph_ceiling if rph_ceiling else load_host_rph_ceiling()
    per_host = endpoints_per_host(endpoints)
    if per_host:
        busiest_host, busiest_count = max(per_host.items(), key=lambda kv: kv[1])
        min_interval_for_budget = math.ceil(busiest_count * 3600 / ceiling)
        if min_interval_for_budget > effective:
            log.warning(
                "interval_stretched_for_host_budget host=%s endpoints=%d "
                "rph_ceiling=%d interval %ds → %ds — "
                "presupuesto por host: máx %d endpoints a %ds / "
                "per-host budget: max %d endpoints at %ds",
                busiest_host, busiest_count, ceiling,
                effective, min_interval_for_budget,
                ceiling * effective // 3600, effective,
                ceiling * effective // 3600, effective,
            )
            effective = min_interval_for_budget

    return effective


# ── Modelos de datos / Data models ─────────────────────────────────────────────

@dataclass
class EndpointConfig:
    """
    Configuración de un endpoint a monitorear.
    Configuration for one monitored endpoint.

    Args / Parámetros:
        id:               Identificador único, e.g. "HN-nacional"
                          Unique identifier, e.g. "HN-nacional"
        url:              URL del JSON público del CNE/TSE/etc.
                          Public JSON URL of CNE/TSE/etc.
        country:          Código de país ISO-3166 / ISO-3166 country code
        timeout_seconds:  Timeout por request / Timeout per request
        headers:          Headers HTTP opcionales / Optional HTTP headers
    """
    id: str
    url: str
    country: str = "XX"
    timeout_seconds: int = 30
    headers: dict = field(default_factory=dict)


@dataclass
class FetchResult:
    """
    Resultado de fetch de un endpoint.
    Result of fetching one endpoint.

    Nunca propaga excepciones — success=False en cualquier error.
    Never propagates exceptions — success=False on any error.
    """
    endpoint_id: str
    timestamp_utc: str
    success: bool
    status_code: Optional[int]
    content_hash: Optional[str]      # SHA-256 del contenido crudo / of raw content
    content_bytes: Optional[bytes]
    error: Optional[str]
    latency_ms: float


# ── Fetch asíncrono / Async fetch ──────────────────────────────────────────────

# Reintentos por endpoint dentro de un ciclo / Per-endpoint retries within a cycle
FETCH_MAX_ATTEMPTS = 3
FETCH_BACKOFF_BASE_SECONDS = 2.0
RETRY_AFTER_CAP_SECONDS = 60.0
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


def _retry_delay(attempt: int, retry_after_header: Optional[str]) -> float:
    """
    Delay antes del siguiente intento: honra Retry-After (cap 60s dentro
    del ciclo), si no backoff exponencial 2s/4s con jitter.
    Delay before next attempt: honors Retry-After (60s cap within the
    cycle), else exponential 2s/4s backoff with jitter.
    """
    if retry_after_header:
        try:
            return min(float(retry_after_header), RETRY_AFTER_CAP_SECONDS)
        except ValueError:
            pass  # Retry-After con fecha HTTP → usa backoff / HTTP-date form → backoff
    return FETCH_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)) + random.uniform(0, 0.5)


async def fetch_one(
    session: aiohttp.ClientSession,
    endpoint: EndpointConfig,
) -> FetchResult:
    """
    Fetch un endpoint y calcula su SHA-256, con reintentos y backoff.
    Fetch one endpoint and compute its SHA-256, with retries and backoff.

    Hasta FETCH_MAX_ATTEMPTS intentos por ciclo; en 429/5xx honra
    Retry-After. Degradación graceful: nunca propaga excepciones.
    Up to FETCH_MAX_ATTEMPTS attempts per cycle; honors Retry-After on
    429/5xx. Graceful degradation: never propagates exceptions.

    Args:
        session:   ClientSession compartida / Shared ClientSession
        endpoint:  Configuración del endpoint / Endpoint config

    Returns:
        FetchResult con success=True o False según resultado
        FetchResult with success=True or False based on outcome
    """
    t_start = time.monotonic()
    timestamp = datetime.now(timezone.utc).isoformat()
    last_error: Optional[str] = None
    last_status: Optional[int] = None

    for attempt in range(1, FETCH_MAX_ATTEMPTS + 1):
        retry_after: Optional[str] = None
        try:
            async with session.get(
                endpoint.url,
                headers=endpoint.headers,
                timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds),
                ssl=True,
            ) as response:
                content = await response.read()

                if response.status < 400:
                    return FetchResult(
                        endpoint_id=endpoint.id,
                        timestamp_utc=timestamp,
                        success=True,
                        status_code=response.status,
                        content_hash=hashlib.sha256(content).hexdigest(),
                        content_bytes=content,
                        error=None,
                        latency_ms=(time.monotonic() - t_start) * 1000,
                    )

                last_status = response.status
                last_error = f"http_{response.status}"
                if response.status not in _RETRYABLE_STATUS:
                    break  # 4xx no transitorio: no reintentar / non-transient 4xx
                retry_after = response.headers.get("Retry-After")

        except asyncio.TimeoutError:
            last_status = None
            last_error = f"timeout_after_{endpoint.timeout_seconds}s"
        except Exception as exc:  # noqa: BLE001
            last_status = None
            last_error = str(exc)[:200]

        if attempt < FETCH_MAX_ATTEMPTS:
            delay = _retry_delay(attempt, retry_after)
            log.info(
                "fetch_retry endpoint=%s attempt=%d/%d delay=%.1fs err=%s",
                endpoint.id, attempt, FETCH_MAX_ATTEMPTS, delay, last_error,
            )
            await asyncio.sleep(delay)

    return FetchResult(
        endpoint_id=endpoint.id,
        timestamp_utc=timestamp,
        success=False,
        status_code=last_status,
        content_hash=None,
        content_bytes=None,
        error=last_error,
        latency_ms=(time.monotonic() - t_start) * 1000,
    )


async def fetch_all(endpoints: list[EndpointConfig]) -> list[FetchResult]:
    """
    Fetch TODOS los endpoints en paralelo usando asyncio.
    Fetch ALL endpoints simultaneously using asyncio.

    Tiempo total = max(latencias_individuales), no la suma.
    Total time = max(individual_latencies), not their sum.

    Con 100 endpoints (MAX_ENDPOINTS) y timeout=30s:
    With 100 endpoints (MAX_ENDPOINTS) and timeout=30s:
      Caso típico / Typical:  ~3-8 segundos / seconds
      Peor caso / Worst case: ~32s sin reintentos; con los 3 intentos
      y backoff de fetch_one, hasta ~100s / ~32s without retries; with
      fetch_one's 3 attempts plus backoff, up to ~100s

    Args:
        endpoints: Lista de endpoints a consultar / List of endpoints to query

    Returns:
        Lista de FetchResult en el mismo orden / List of FetchResult in same order
    """
    connector = aiohttp.TCPConnector(
        limit=150,             # máx conexiones totales / max total connections
        limit_per_host=5,      # respeta rate limits del servidor / respects server rate limits
        ttl_dns_cache=300,     # cachea DNS 5 minutos / DNS cache 5 minutes
        enable_cleanup_closed=True,
    )

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_one(session, ep) for ep in endpoints]
        results = await asyncio.gather(*tasks)

    return list(results)


# ── Hash chain por batch / Batch hash chain ────────────────────────────────────

class BatchHashChain:
    """
    Cadena de hashes a nivel de ciclo completo.
    Hash chain at full-cycle level (not per endpoint).

    Cada ciclo produce 1 entrada en la cadena:
    Each cycle produces 1 entry in the chain:

    KaTeX:
      cycle_hash = SHA256(prev_hash || timestamp || merkle_root)
      merkle_root = raíz del árbol de Merkle de los content_hashes exitosos
                    Merkle root of successful content_hashes

    Append-only: nunca sobreescribe entradas anteriores.
    Append-only: never overwrites previous entries.

    Integra con el hashchain.py existente como capa de persistencia.
    Integrates with existing hashchain.py as persistence layer.
    """

    CHAIN_FILE = Path("data/poller_chain.jsonl")

    def __init__(self) -> None:
        self.CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._prev_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        """
        Carga el último hash de la cadena o usa bloque génesis.
        Load last chain hash or use genesis block.
        """
        if self.CHAIN_FILE.exists():
            lines = self.CHAIN_FILE.read_text().strip().splitlines()
            if lines:
                try:
                    return json.loads(lines[-1])["cycle_hash"]
                except (json.JSONDecodeError, KeyError):
                    pass
        return hashlib.sha256(b"CENTINEL-ASYNC-POLLER-GENESIS-2026").hexdigest()

    def _merkle_root(self, hashes: list[str]) -> str:
        """
        Merkle root de los hashes de contenido del ciclo.
        Merkle root of cycle's content hashes.

        Ordenado para determinismo: mismo conjunto → mismo root.
        Sorted for determinism: same set → same root.

        KaTeX:
          Si n=1: root = h_0
          Si n>1: root = SHA256(SHA256(h_i || h_{i+1})) iterado
          If n=1: root = h_0
          If n>1: root = SHA256(SHA256(h_i || h_{i+1})) iterated

        Args:
            hashes: Lista de hex-strings SHA-256 / List of SHA-256 hex strings

        Returns:
            Hex string del Merkle root / Merkle root hex string
        """
        if not hashes:
            return hashlib.sha256(b"empty-cycle").hexdigest()

        layer = [h.encode() for h in sorted(hashes)]  # sorted = determinístico

        while len(layer) > 1:
            next_layer = []
            for i in range(0, len(layer), 2):
                left = layer[i]
                right = layer[i + 1] if i + 1 < len(layer) else layer[i]
                next_layer.append(hashlib.sha256(left + right).digest())
            layer = next_layer

        return layer[0].hex()

    def append(
        self,
        cycle_number: int,
        timestamp: str,
        results: list[FetchResult],
    ) -> str:
        """
        Añade un ciclo a la cadena. Retorna el hash del ciclo.
        Append one cycle to the chain. Returns cycle hash.

        KaTeX:
          cycle_hash = SHA256(prev_hash || "|" || timestamp || "|" || merkle_root)

        Args:
            cycle_number: Número secuencial del ciclo / Sequential cycle number
            timestamp:    ISO-8601 UTC timestamp
            results:      Lista de FetchResult del ciclo / Cycle FetchResult list

        Returns:
            Hex string del cycle_hash / cycle_hash hex string
        """
        content_hashes = [
            r.content_hash for r in results
            if r.success and r.content_hash
        ]
        merkle = self._merkle_root(content_hashes)

        # Encadenamiento: SHA256(prev || timestamp || merkle)
        # Chaining: SHA256(prev || timestamp || merkle)
        raw = f"{self._prev_hash}|{timestamp}|{merkle}".encode()
        cycle_hash = hashlib.sha256(raw).hexdigest()

        successful = sum(1 for r in results if r.success)
        avg_latency = (
            sum(r.latency_ms for r in results) / len(results)
            if results else 0.0
        )

        entry = {
            "cycle":          cycle_number,
            "timestamp":      timestamp,
            "prev_hash":      self._prev_hash,
            "merkle_root":    merkle,
            "cycle_hash":     cycle_hash,
            "endpoints": {
                "total":   len(results),
                "success": successful,
                "failed":  len(results) - successful,
            },
            "avg_latency_ms": round(avg_latency, 1),
        }

        # Append-only — nunca sobreescribe / never overwrites
        with self.CHAIN_FILE.open("a") as f:
            f.write(json.dumps(entry) + "\n")

        self._prev_hash = cycle_hash
        return cycle_hash


# ── Git commit del ciclo / Cycle git commit ────────────────────────────────────

PUSH_MAX_ATTEMPTS = 3


def _push_branch_with_retry(
    data_branch: str,
    cwd: Optional[str] = None,
    attempts: int = PUSH_MAX_ATTEMPTS,
) -> bool:
    """
    Push con reintentos: en rechazo (ej. slots A/B solapados empujando a la
    misma branch) hace pull --rebase y reintenta con backoff.
    Push with retries: on rejection (e.g. overlapping A/B slots pushing to
    the same branch) it pull --rebases and retries with backoff.

    Returns:
        True si el push llegó / True if the push landed.
    """
    for attempt in range(1, attempts + 1):
        try:
            subprocess.run(
                ["git", "push", "origin", data_branch] if data_branch
                else ["git", "push"],
                check=True, capture_output=True, cwd=cwd,
            )
            return True
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode() if exc.stderr else ""
            log.warning(
                "push_failed branch=%s attempt=%d/%d err=%s",
                data_branch or "current", attempt, attempts, stderr[:200],
            )
            if attempt == attempts:
                return False
            subprocess.run(
                ["git", "pull", "--rebase", "origin", data_branch]
                if data_branch else ["git", "pull", "--rebase"],
                capture_output=True, cwd=cwd,
            )
            time.sleep(2 ** attempt)
    return False


def flush_pending_push(data_branch: str) -> bool:
    """
    Empuja commits locales pendientes de la data branch (batching de push).
    Usado al cierre del poller y cada CENTINEL_PUSH_EVERY_N ciclos.
    Pushes pending local commits of the data branch (push batching).
    Used at poller shutdown and every CENTINEL_PUSH_EVERY_N cycles.
    """
    if data_branch:
        import tempfile
        worktree_dir = Path(tempfile.mkdtemp(prefix="centinel-push-"))
        try:
            subprocess.run(
                ["git", "worktree", "add", "--checkout", str(worktree_dir), data_branch],
                check=True, capture_output=True,
            )
            return _push_branch_with_retry(data_branch, cwd=str(worktree_dir))
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode() if exc.stderr else ""
            log.error("flush_push_worktree_failed err=%s", stderr[:200])
            return False
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_dir)],
                capture_output=True,
            )
    return _push_branch_with_retry("")


def _push_to_data_branch(
    cycle_number: int,
    cycle_hash: str,
    results: list[FetchResult],
    data_branch: str,
    do_push: bool = True,
) -> None:
    """
    Push snapshot data to a dedicated data branch using git worktree.
    ES: Publica snapshots a una branch dedicada usando git worktree.

    The data branch is a separate history from main — it holds only
    snapshot JSON files and the hash chain. The main branch code is
    never modified. Any third party can verify by cloning data branch.

    Any third party can verify:
      git clone --branch data https://github.com/user/centinel
      python verify_chain.py data/poller_chain.jsonl

    Args:
        cycle_number: Sequential cycle number.
        cycle_hash:   SHA-256 cycle hash for commit message.
        results:      FetchResult list from this cycle.
        data_branch:  Name of the data branch (e.g. "data").
        do_push:      Push after committing. False = commit local solamente
                      (el push por lotes lo publica después) / commit locally
                      only (batched push publishes it later).
    """
    import tempfile

    worktree_dir = Path(tempfile.mkdtemp(prefix="centinel-data-"))

    try:
        # Add worktree pointing to data branch
        subprocess.run(
            ["git", "worktree", "add", "--checkout", str(worktree_dir), data_branch],
            check=True, capture_output=True,
        )

        # Write snapshots into the worktree
        snap_dir = worktree_dir / "snapshots"
        snap_dir.mkdir(exist_ok=True)

        for result in results:
            if result.success and result.content_bytes:
                ep_file = snap_dir / f"{result.endpoint_id}.json"
                try:
                    parsed = json.loads(result.content_bytes)
                    ep_file.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    ep_file.write_bytes(result.content_bytes)

        # Copy hash chain
        chain_src = Path("data/poller_chain.jsonl")
        if chain_src.exists():
            (worktree_dir / "poller_chain.jsonl").write_text(chain_src.read_text())

        # Copy cycle summary
        summary_src = Path("data/latest_cycle.json")
        if summary_src.exists():
            (worktree_dir / "latest_cycle.json").write_text(summary_src.read_text())

        # Commit from the worktree; push only when the batch is due
        ok_count = sum(1 for r in results if r.success)
        subprocess.run(["git", "add", "-A"], check=True, capture_output=True,
                       cwd=str(worktree_dir))
        subprocess.run(
            ["git", "commit", "-m",
             f"data cycle:{cycle_number} hash:{cycle_hash[:12]} "
             f"ok:{ok_count}/{len(results)}"],
            check=True, capture_output=True, cwd=str(worktree_dir),
        )
        if do_push:
            _push_branch_with_retry(data_branch, cwd=str(worktree_dir))

    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_dir)],
            capture_output=True,
        )


def commit_cycle(
    cycle_number: int,
    cycle_hash: str,
    results: list[FetchResult],
    do_push: bool = True,
    effective_interval_seconds: Optional[int] = None,
) -> None:
    """
    Commit atómico de los datos del ciclo al repositorio.
    Atomic commit of cycle data to repository.

    1 commit por ciclo (no 100 commits por endpoint); push por lotes
    cada CENTINEL_PUSH_EVERY_N ciclos para no saturar la data branch.
    1 commit per cycle (not 100 commits per endpoint); batched push
    every CENTINEL_PUSH_EVERY_N cycles to avoid flooding the data branch.

    Args:
        cycle_number: Número del ciclo / Cycle number
        cycle_hash:   Hash del ciclo para el mensaje / Cycle hash for commit msg
        results:      Lista de FetchResult / FetchResult list
        do_push:      Push en este ciclo / Push on this cycle
        effective_interval_seconds: Intervalo efectivo (transparencia en
                      latest_cycle.json) / Effective interval (transparency)
    """
    data_dir = Path("data/snapshots")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Guardar snapshot de cada endpoint exitoso
    # Save snapshot of each successful endpoint
    for result in results:
        if result.success and result.content_bytes:
            ep_file = data_dir / f"{result.endpoint_id}.json"
            try:
                parsed = json.loads(result.content_bytes)
                ep_file.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Guardar raw si no es JSON válido / Save raw if not valid JSON
                ep_file.write_bytes(result.content_bytes)

    # Resumen del ciclo / Cycle summary
    summary = {
        "cycle":      cycle_number,
        "cycle_hash": cycle_hash,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "effective_interval_seconds": effective_interval_seconds,
        "results": [
            {
                "endpoint":   r.endpoint_id,
                "success":    r.success,
                "status":     r.status_code,
                "hash":       r.content_hash,
                "latency_ms": round(r.latency_ms, 1),
                "error":      r.error,
            }
            for r in results
        ],
    }
    Path("data/latest_cycle.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)
    )

    # Git commit atómico — push a DATA_BRANCH si está configurado
    # Atomic git commit — push to DATA_BRANCH if configured
    data_branch = os.environ.get("DATA_BRANCH", "")
    try:
        if data_branch:
            # Push snapshots to dedicated data branch using worktree
            # so the main branch codebase is never polluted with data files.
            # ES: Los snapshots van a la branch de datos, no a main.
            _push_to_data_branch(cycle_number, cycle_hash, results, data_branch,
                                 do_push=do_push)
        else:
            # Legacy: commit directly to current branch
            subprocess.run(["git", "add", "data/"], check=True, capture_output=True)
            ok_count = sum(1 for r in results if r.success)
            subprocess.run(
                [
                    "git", "commit", "-m",
                    f"poller cycle:{cycle_number} "
                    f"hash:{cycle_hash[:12]} "
                    f"ok:{ok_count}/{len(results)}",
                ],
                check=True,
                capture_output=True,
            )
            if do_push:
                _push_branch_with_retry("")
        log.info("git commit cycle=%d hash=%s branch=%s push=%s",
                 cycle_number, cycle_hash[:16], data_branch or "current",
                 "yes" if do_push else "batched")
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode() if exc.stderr else ""
        log.error("git commit failed cycle=%d err=%s", cycle_number, stderr[:200])


# ── Motor principal / Main engine ──────────────────────────────────────────────

class ContinuousPoller:
    """
    Motor principal del poller continuo.
    Main engine of the continuous poller.

    Gestiona el loop, graceful shutdown y estadísticas.
    Manages the loop, graceful shutdown, and statistics.

    Garantías / Guarantees:
      - Nunca propaga excepción desde el loop principal
        Never propagates exception from main loop
      - SIGTERM → graceful exit antes del límite de 6h de GitHub
        SIGTERM → graceful exit before GitHub's 6h limit
      - 1 commit por ciclo (no por endpoint)
        1 commit per cycle (not per endpoint)
    """

    def __init__(
        self,
        endpoints: list[EndpointConfig],
        interval_seconds: int,
        max_runtime_seconds: int,
    ) -> None:
        self.endpoints = endpoints
        self.interval = interval_seconds
        self.max_runtime = max_runtime_seconds
        self.hash_chain = BatchHashChain()
        self._shutdown = False
        self._cycle = 0
        # Push por lotes: 1 push cada N ciclos (commits locales cada ciclo)
        # Batched push: 1 push every N cycles (local commits every cycle)
        try:
            self.push_every = max(1, int(os.environ.get("CENTINEL_PUSH_EVERY_N", "5")))
        except ValueError:
            self.push_every = 5
        self._pending_push = False

        # Graceful shutdown en SIGTERM
        # GitHub Actions envía SIGTERM al acercarse al límite
        # GitHub Actions sends SIGTERM approaching limit
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

    def _handle_sigterm(self, signum: int, frame) -> None:  # noqa: ANN001
        log.warning("signal=%d received — graceful shutdown initiated", signum)
        self._shutdown = True

    def run(self) -> None:
        """
        Loop principal del poller.
        Main poller loop.

        Flujo por ciclo / Per-cycle flow:
          1. fetch_all()     — hasta MAX_ENDPOINTS en paralelo / up to MAX_ENDPOINTS in parallel
          2. hash_chain.append() — 1 entrada en la cadena / 1 chain entry
          3. commit_cycle()  — 1 git commit; push cada push_every ciclos
                               1 git commit; push every push_every cycles
          4. sleep           — hasta completar el intervalo / until interval completes
        """
        job_start = time.monotonic()
        log.info(
            "poller_start endpoints=%d interval=%ds max_runtime=%ds push_every=%d",
            len(self.endpoints),
            self.interval,
            self.max_runtime,
            self.push_every,
        )

        while not self._shutdown:
            elapsed = time.monotonic() - job_start

            # Salir con tiempo suficiente para cleanup antes del límite de 6h
            # Exit with enough time for cleanup before 6h limit
            if elapsed >= self.max_runtime:
                log.info(
                    "max_runtime_reached elapsed=%.0fs — graceful exit for restart",
                    elapsed,
                )
                break

            self._cycle += 1
            cycle_start = time.monotonic()
            timestamp = datetime.now(timezone.utc).isoformat()

            log.info("cycle_start n=%d", self._cycle)

            # 1. Fetch todos los endpoints en paralelo
            #    Fetch all endpoints in parallel
            try:
                results = asyncio.run(fetch_all(self.endpoints))
            except Exception as exc:  # noqa: BLE001
                log.error("fetch_all_failed cycle=%d err=%s", self._cycle, exc)
                time.sleep(30)
                continue

            fetch_elapsed = time.monotonic() - cycle_start
            ok = sum(1 for r in results if r.success)
            log.info(
                "fetch_done cycle=%d ok=%d/%d elapsed=%.1fs",
                self._cycle, ok, len(results), fetch_elapsed,
            )

            # 2. Hash chain — 1 entrada por ciclo
            #    Hash chain — 1 entry per cycle
            try:
                cycle_hash = self.hash_chain.append(self._cycle, timestamp, results)
                log.info("hash_chain cycle=%d hash=%s", self._cycle, cycle_hash[:16])
            except Exception as exc:  # noqa: BLE001
                log.error("hash_chain_failed cycle=%d err=%s", self._cycle, exc)
                cycle_hash = hashlib.sha256(
                    f"fallback-{self._cycle}-{timestamp}".encode()
                ).hexdigest()

            # 3. Git commit — push solo cuando toca el lote
            #    Git commit — push only when the batch is due
            do_push = (self._cycle % self.push_every == 0)
            try:
                commit_cycle(
                    self._cycle, cycle_hash, results,
                    do_push=do_push,
                    effective_interval_seconds=self.interval,
                )
                self._pending_push = not do_push
            except Exception as exc:  # noqa: BLE001
                log.error("commit_failed cycle=%d err=%s", self._cycle, exc)

            # 4. Sleep hasta completar el intervalo
            #    Sleep until interval completes
            cycle_elapsed = time.monotonic() - cycle_start
            sleep_time = max(0.0, self.interval - cycle_elapsed)

            log.info(
                "cycle_done n=%d total=%.1fs sleep=%.1fs",
                self._cycle, cycle_elapsed, sleep_time,
            )

            if sleep_time > 0 and not self._shutdown:
                time.sleep(sleep_time)

        # Flush final: publica commits del lote pendiente antes de salir
        # Final flush: publish pending batched commits before exiting
        if self._pending_push:
            pushed = flush_pending_push(os.environ.get("DATA_BRANCH", ""))
            log.info("final_push_flush ok=%s", pushed)

        log.info("poller_shutdown cycles=%d", self._cycle)


# ── Carga de endpoints / Endpoint loader ───────────────────────────────────────

def _cap_endpoints(endpoints: list[EndpointConfig]) -> list[EndpointConfig]:
    """
    Aplica el tope MAX_ENDPOINTS (100): configs mayores se truncan.
    Applies the MAX_ENDPOINTS cap (100): larger configs are truncated.
    """
    if len(endpoints) > MAX_ENDPOINTS:
        log.warning(
            "endpoints_capped configured=%d max=%d — truncando: la capacidad "
            "del poller es %d endpoints / truncating: poller capacity is %d",
            len(endpoints), MAX_ENDPOINTS, MAX_ENDPOINTS, MAX_ENDPOINTS,
        )
        return endpoints[:MAX_ENDPOINTS]
    return endpoints


def load_endpoints(allow_empty: bool = False) -> list[EndpointConfig]:
    """
    Carga endpoints desde las fuentes disponibles, en orden de prioridad:
    Load endpoints from available sources, in priority order:

    1. command_center/config.yaml     <- generado por el Setup Wizard (cero fricción)
                                         generated by Setup Wizard (zero user friction)
    2. command_center/endpoints.json  <- fallback manual / manual fallback
    3. ENDPOINTS_JSON env var         <- fallback CI secret

    Máximo MAX_ENDPOINTS (100) endpoints; el exceso se trunca con warning.
    Maximum MAX_ENDPOINTS (100) endpoints; overflow truncated with warning.

    Nunca loguea URLs. Never logs URLs.

    Returns:
        Lista de EndpointConfig / List of EndpointConfig

    Raises:
        SystemExit: si no hay endpoints configurados / if no endpoints configured
    """
    # ── Fuente 1: command_center/config.yaml (Setup Wizard) ───────────────
    # El wizard_config.py lo genera automáticamente con el país elegido.
    # wizard_config.py generates this automatically with the selected country.
    config_yaml = Path("command_center/config.yaml")
    if config_yaml.exists():
        try:
            import yaml
            cfg = yaml.safe_load(config_yaml.read_text()) or {}
            country      = cfg.get("centinel", {}).get("country", "XX")
            raw_endpoints = cfg.get("endpoints", {})

            if raw_endpoints:
                endpoints = []
                for code, url in raw_endpoints.items():
                    if not url:
                        continue
                    label = "nacional" if code in ("00", "nacional") else f"dept_{code}"
                    endpoints.append(EndpointConfig(
                        id=f"{country}-{code}-{label}",
                        url=url,
                        country=country,
                        timeout_seconds=30,
                        headers={},
                    ))
                if endpoints:
                    log.info(
                        "endpoints_loaded source=config.yaml count=%d country=%s",
                        len(endpoints), country,
                    )
                    return _cap_endpoints(endpoints)
        except Exception as exc:  # noqa: BLE001
            log.warning("config_yaml_read_failed err=%s — trying fallback", exc)

    # ── Fuente 2: command_center/endpoints.json ────────────────────────────
    json_file = Path("command_center/endpoints.json")
    if json_file.exists():
        try:
            data = json.loads(json_file.read_text())
            endpoints = [
                EndpointConfig(
                    id=item["id"],
                    url=item["url"],
                    country=item.get("country", "XX"),
                    timeout_seconds=item.get("timeout", 30),
                    headers=item.get("headers", {}),
                )
                for item in data
            ]
            if endpoints:
                log.info("endpoints_loaded source=endpoints.json count=%d", len(endpoints))
                return _cap_endpoints(endpoints)
        except Exception as exc:  # noqa: BLE001
            log.warning("endpoints_json_read_failed err=%s — trying env", exc)

    # ── Fuente 3: ENDPOINTS_JSON env var (CI secret / override) ───────────
    raw = os.environ.get("ENDPOINTS_JSON")
    if raw:
        try:
            data = json.loads(raw)
            endpoints = [
                EndpointConfig(
                    id=item["id"],
                    url=item["url"],
                    country=item.get("country", "XX"),
                    timeout_seconds=item.get("timeout", 30),
                    headers=item.get("headers", {}),
                )
                for item in data
            ]
            if endpoints:
                log.info("endpoints_loaded source=env count=%d", len(endpoints))
                return _cap_endpoints(endpoints)
        except Exception as exc:  # noqa: BLE001
            log.error("endpoints_env_parse_failed err=%s", exc)

    if allow_empty:
        log.warning(
            "no_endpoints_configured — idle mode (scheduled run with nothing to poll). "
            "Configure ENDPOINTS_JSON secret or command_center/config.yaml to activate."
        )
        return []

    log.error(
        "no_endpoints_found — "
        "run Setup Wizard first or create command_center/config.yaml"
    )
    sys.exit(1)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "CENTINEL Async Continuous Poller — hasta 100 endpoints × costo cero. "
            "Piso ético: 3 min. Un solo host admite máx ~24 endpoints a 3 min "
            "(techo 480 req/h/host); con más, el intervalo se estira solo. "
            "/ Up to 100 endpoints × zero cost. Ethical floor: 3 min. A single "
            "host takes ~24 endpoints max at 3 min (480 req/h/host ceiling); "
            "beyond that the interval auto-stretches."
        )
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3,
        help="Intervalo de polling en minutos (default: 3, piso ético) / "
             "Polling interval in minutes (default: 3, ethical floor)",
    )
    parser.add_argument(
        "--data-branch",
        type=str,
        default="",
        help="Push data commits to this branch (empty = current branch)",
    )
    parser.add_argument(
        "--max-runtime",
        type=int,
        default=19_800,
        help="Tiempo máximo en segundos (default: 19800 = 5.5h) / Max runtime in seconds",
    )
    parser.add_argument(
        "--allow-no-endpoints",
        action="store_true",
        help="Exit cleanly (0) instead of failing when no endpoints are configured. "
             "Used by scheduled CI pollers so idle runs (between elections) stay green.",
    )
    args = parser.parse_args()

    endpoints = load_endpoints(allow_empty=args.allow_no_endpoints)

    if not endpoints:
        # Idle mode: nothing to poll. Stay armed for the next scheduled run.
        log.info("poller_idle_exit no endpoints configured — exiting cleanly")
        sys.exit(0)

    if args.data_branch:
        os.environ["DATA_BRANCH"] = args.data_branch

    # Piso ético + presupuesto por host / Ethical floor + per-host budget
    interval_seconds = resolve_safe_interval(endpoints, args.interval * 60)

    poller = ContinuousPoller(
        endpoints=endpoints,
        interval_seconds=interval_seconds,
        max_runtime_seconds=args.max_runtime,
    )
    poller.run()
