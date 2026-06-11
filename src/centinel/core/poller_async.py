"""
CENTINEL — Async Continuous Poller
====================================
Motor de polling asíncrono para N endpoints con intervalo garantizado.
Async polling engine for N endpoints with guaranteed interval.

Diseño / Design:
  - Corre como long-running job dentro de GitHub Actions (hasta 5.5h)
    Runs as long-running job inside GitHub Actions (up to 5.5h)
  - GitHub ve 1 job; asyncio gestiona 100 endpoints en paralelo
    GitHub sees 1 job; asyncio manages 100 endpoints in parallel
  - Hash chain actualizada 1 vez por ciclo (batch), no por endpoint
    Hash chain updated once per cycle (batch), not per endpoint
  - Graceful shutdown antes del límite de 6h de GitHub
    Graceful shutdown before GitHub's 6h job limit
  - Integra con hashchain.py y endpoint_monitor.py existentes
    Integrates with existing hashchain.py and endpoint_monitor.py

Author: CENTINEL Team
License: AGPL-3.0
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiohttp

# Optional: pre-capture evidentiary custody (graceful degradation if unavailable).
# Opcional: custodia de evidencia pre-captura (degradación graceful si no disponible).
try:
    from centinel.core.pre_capture_custody import (
        build_envelope as _build_custody_envelope,
        sign_envelope  as _sign_custody_envelope,
    )
    _CUSTODY_AVAILABLE = True
except ImportError:
    _CUSTODY_AVAILABLE = False


def _get_operator_key():
    """Load Ed25519 private key from env (raw hex). Returns None if not configured."""
    hex_key = os.environ.get("CENTINEL_OPERATOR_PRIVATE_KEY_HEX")
    if not hex_key or not _CUSTODY_AVAILABLE:
        return None
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(hex_key))
    except Exception:
        return None

# ── Logging estructurado / Structured logging ──────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("centinel.poller_async")


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
    custody_envelope: Optional[dict] = field(default=None)
    # ^ Pre-capture evidentiary envelope. None if module unavailable or key not set.
    #   See: src/centinel/core/pre_capture_custody.py


# ── Fetch asíncrono / Async fetch ──────────────────────────────────────────────

async def fetch_one(
    session: aiohttp.ClientSession,
    endpoint: EndpointConfig,
) -> FetchResult:
    """
    Fetch un endpoint y calcula su SHA-256.
    Fetch one endpoint and compute its SHA-256.

    Degradación graceful: nunca propaga excepciones.
    Graceful degradation: never propagates exceptions.

    Args:
        session:   ClientSession compartida / Shared ClientSession
        endpoint:  Configuración del endpoint / Endpoint config

    Returns:
        FetchResult con success=True o False según resultado
        FetchResult with success=True or False based on outcome
    """
    t_start = time.monotonic()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        async with session.get(
            endpoint.url,
            headers=endpoint.headers,
            timeout=aiohttp.ClientTimeout(total=endpoint.timeout_seconds),
            ssl=True,
        ) as response:
            content = await response.read()
            latency_ms = (time.monotonic() - t_start) * 1000
            content_hash = hashlib.sha256(content).hexdigest()

            # ── Pre-capture custody envelope ─────────────────────────
            # Built on raw bytes BEFORE any parsing. TLS extraction is
            # skipped in the async path (socket is sync); HTTP headers +
            # body hash provide sufficient provenance evidence.
            custody = None
            if _CUSTODY_AVAILABLE:
                try:
                    env = _build_custody_envelope(
                        url=str(endpoint.url),
                        operator_id=os.environ.get(
                            "CENTINEL_OPERATOR_ID", "centinel-operator"),
                        response_body=content,
                        response_status=response.status,
                        response_headers=dict(response.headers),
                        tls_metadata={},
                    )
                    op_key = _get_operator_key()
                    if op_key:
                        env = _sign_custody_envelope(env, op_key)
                    custody = env.to_dict()
                except Exception as _exc:  # noqa: BLE001
                    log.debug("custody_envelope_failed endpoint=%s err=%s",
                              endpoint.id, _exc)
            # ─────────────────────────────────────────────────────────

            return FetchResult(
                endpoint_id=endpoint.id,
                timestamp_utc=timestamp,
                success=response.status < 400,
                status_code=response.status,
                content_hash=content_hash,
                content_bytes=content,
                error=None if response.status < 400 else f"http_{response.status}",
                latency_ms=latency_ms,
                custody_envelope=custody,
            )

    except asyncio.TimeoutError:
        return FetchResult(
            endpoint_id=endpoint.id,
            timestamp_utc=timestamp,
            success=False,
            status_code=None,
            content_hash=None,
            content_bytes=None,
            error=f"timeout_after_{endpoint.timeout_seconds}s",
            latency_ms=(time.monotonic() - t_start) * 1000,
        )
    except Exception as exc:  # noqa: BLE001
        return FetchResult(
            endpoint_id=endpoint.id,
            timestamp_utc=timestamp,
            success=False,
            status_code=None,
            content_hash=None,
            content_bytes=None,
            error=str(exc)[:200],
            latency_ms=(time.monotonic() - t_start) * 1000,
        )


async def fetch_all(endpoints: list[EndpointConfig]) -> list[FetchResult]:
    """
    Fetch TODOS los endpoints en paralelo usando asyncio.
    Fetch ALL endpoints simultaneously using asyncio.

    Tiempo total = max(latencias_individuales), no la suma.
    Total time = max(individual_latencies), not their sum.

    Con 100 endpoints y timeout=30s:
    With 100 endpoints and timeout=30s:
      Peor caso / Worst case: ~32 segundos / seconds
      Caso típico / Typical:  ~3-8 segundos / seconds

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

def commit_cycle(
    cycle_number: int,
    cycle_hash: str,
    results: list[FetchResult],
) -> None:
    """
    Commit atómico de los datos del ciclo al repositorio.
    Atomic commit of cycle data to repository.

    1 commit por ciclo (no 100 commits por endpoint).
    1 commit per cycle (not 100 commits per endpoint).

    Args:
        cycle_number: Número del ciclo / Cycle number
        cycle_hash:   Hash del ciclo para el mensaje / Cycle hash for commit msg
        results:      Lista de FetchResult / FetchResult list
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

    # Git commit atómico / Atomic git commit
    try:
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
        subprocess.run(["git", "push"], check=True, capture_output=True)
        log.info("git commit cycle=%d hash=%s", cycle_number, cycle_hash[:16])
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
          1. fetch_all()     — 100 endpoints en paralelo / in parallel
          2. hash_chain.append() — 1 entrada en la cadena / 1 chain entry
          3. commit_cycle()  — 1 git commit / 1 git commit
          4. sleep           — hasta completar el intervalo / until interval completes
        """
        job_start = time.monotonic()
        log.info(
            "poller_start endpoints=%d interval=%ds max_runtime=%ds",
            len(self.endpoints),
            self.interval,
            self.max_runtime,
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

            # 3. Git commit
            try:
                commit_cycle(self._cycle, cycle_hash, results)
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

        log.info("poller_shutdown cycles=%d", self._cycle)


# ── Carga de endpoints / Endpoint loader ───────────────────────────────────────

def load_endpoints() -> list[EndpointConfig]:
    """
    Carga endpoints desde secret de GitHub Actions o archivo local.
    Load endpoints from GitHub Actions secret or local file.

    Nunca loguea URLs (pueden ser sensibles).
    Never logs URLs (may be sensitive).

    Returns:
        Lista de EndpointConfig / List of EndpointConfig

    Raises:
        SystemExit: si no hay endpoints configurados
                    if no endpoints configured
    """
    raw = os.environ.get("ENDPOINTS_JSON")
    if raw:
        data = json.loads(raw)
    else:
        config_file = Path("command_center/endpoints.json")
        if not config_file.exists():
            # Fallback: intentar profiles.py si existe
            # Fallback: try profiles.py if it exists
            log.error("no endpoints configured — set ENDPOINTS_JSON secret or create command_center/endpoints.json")
            sys.exit(1)
        data = json.loads(config_file.read_text())

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

    log.info("endpoints_loaded count=%d", len(endpoints))
    return endpoints


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CENTINEL Async Continuous Poller — 100 endpoints × N min × costo cero"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3,
        help="Intervalo de polling en minutos (default: 3) / Polling interval in minutes",
    )
    parser.add_argument(
        "--max-runtime",
        type=int,
        default=19_800,
        help="Tiempo máximo en segundos (default: 19800 = 5.5h) / Max runtime in seconds",
    )
    args = parser.parse_args()

    endpoints = load_endpoints()

    poller = ContinuousPoller(
        endpoints=endpoints,
        interval_seconds=args.interval * 60,
        max_runtime_seconds=args.max_runtime,
    )
    poller.run()
