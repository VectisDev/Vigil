"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `src/vigil/download.py`.
Este módulo forma parte de VIGIL y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - DownloadError
  - fetch_content
  - write_atomic
  - chained_hash
  - _build_chain_payload
  - _is_valid_hex_hash
  - build_client
  - download_and_hash

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `src/vigil/download.py`.
This module is part of VIGIL and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - DownloadError
  - fetch_content
  - write_atomic
  - chained_hash
  - _build_chain_payload
  - _is_valid_hex_hash
  - build_client
  - download_and_hash

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

# Download Module
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

import hashlib
import os
import ssl
import string
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


from .identity import request_headers

logger = structlog.get_logger(__name__)


class DownloadError(Exception):
    """Error controlado de descarga.

    English: Controlled download error.
    """


@retry(
    retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    reraise=True,
)
async def fetch_content(
    client: httpx.AsyncClient,
    url: str,
    if_none_match: Optional[str] = None,
    if_modified_since: Optional[str] = None,
) -> httpx.Response:
    """Descarga contenido con cabeceras condicionales.

    English: Fetch content with conditional headers.
    """
    headers = dict(request_headers())
    if if_none_match:
        headers["If-None-Match"] = if_none_match
    if if_modified_since:
        headers["If-Modified-Since"] = if_modified_since

    # Conexion directa. La salida no se reparte entre varias direcciones:
    # hacerlo sirve para no ser identificado, y VIGIL audita identificandose.
    # La unica salida alternativa que se conserva es un circuito Tor UNICO y
    # opcional, que protege a la persona sin disfrazar al observador — vive en
    # `vigil_engine/proxy_manager.py`. Ver `docs/NO-EVASION.md`.
    # English: direct connection. The exit is not spread across addresses --
    # that exists to avoid being identified. The one alternative kept is a
    # single optional Tor circuit, which protects the person without
    # disguising the observer.
    start = time.monotonic()
    logger.debug(
        "fetch_start",
        url=url,
        if_none_match=bool(if_none_match),
        if_modified_since=bool(if_modified_since),
    )
    try:
        response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        elapsed = time.monotonic() - start
        logger.warning(
            "request_error",
            elapsed_seconds=round(elapsed, 3),
            error=str(exc),
        )
        raise

    elapsed = time.monotonic() - start
    content_length = response.headers.get("Content-Length")
    logger.info(
        "direct_response",
        status_code=response.status_code,
        elapsed_seconds=round(elapsed, 3),
        content_length=content_length,
    )

    if response.status_code in {429, 503}:
        raise httpx.HTTPStatusError(
            f"Retryable status: {response.status_code}",
            request=response.request,
            response=response,
        )

    if response.status_code >= 400:
        raise DownloadError(f"Unexpected status {response.status_code} for {url}")

    return response


def write_atomic(path: Path, content: bytes) -> None:
    """Escritura atómica y DURABLE usando archivo temporal.

    English: Atomic AND durable write using a temporary file.

    Durability contract (critical for election-night evidence):
    the temp file is fsync'd before rename, and the parent directory
    is fsync'd after rename. Without the directory fsync a power loss
    or kernel crash immediately after rename can lose the snapshot
    even though rename() itself is atomic. An adversary with VM/host
    access could otherwise induce a crash at that exact window and
    erase evidence with no visible error.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=str(path.parent)) as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        temp_name = tmp_file.name
    shutil.move(temp_name, path)
    # fsync the parent directory so the rename itself is durable.
    dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def chained_hash(
    content: bytes,
    previous_hash: Optional[str],
    *,
    metadata: Optional[bytes] = None,
    timestamp: Optional[str] = None,
) -> str:
    """Calcula hash encadenado con separación de dominio.

    English: Compute chained hash with domain separation.
    """
    return hashlib.sha256(
        _build_chain_payload(
            content,
            previous_hash=previous_hash,
            metadata=metadata,
            timestamp=timestamp,
        )
    ).hexdigest()


def _build_chain_payload(
    content: bytes,
    *,
    previous_hash: Optional[str],
    metadata: Optional[bytes] = None,
    timestamp: Optional[str] = None,
) -> bytes:
    """Construye payload con separación de dominio y longitudes."""
    previous_hash_bytes = b""
    if previous_hash:
        normalized = previous_hash.strip().lower()
        previous_hash_bytes = normalized.encode("utf-8")
        if not _is_valid_hex_hash(normalized):
            logger.warning("hashchain_previous_hash_invalid value=%s", normalized)

    parts = [
        # Protocol constant: keeps the pre-rename name on purpose (see docs/architecture/LEGACY-NAMES.md).
        b"centinel-chain-v1",
        b"prev",
        str(len(previous_hash_bytes)).encode("utf-8"),
        previous_hash_bytes,
    ]
    if timestamp:
        timestamp_bytes = timestamp.encode("utf-8")
        parts.extend([b"ts", str(len(timestamp_bytes)).encode("utf-8"), timestamp_bytes])
    if metadata:
        parts.extend([b"meta", str(len(metadata)).encode("utf-8"), metadata])

    parts.extend([b"content", str(len(content)).encode("utf-8"), content])
    return b"|".join(parts)


def _is_valid_hex_hash(value: str) -> bool:
    if len(value) != 64:
        return False
    hex_chars = set(string.hexdigits.lower())
    return all(char in hex_chars for char in value)


def _build_tls_context() -> ssl.SSLContext:
    """El contexto TLS por defecto, sin barajar nada.

    Antes mezclaba el orden de los cifradores en cada cliente «para reducir
    una firma TLS determinista», es decir, para que la huella del cliente
    cambiara entre conexiones. Eso es ocultar quien se conecta, y VIGIL audita
    identificandose: el User-Agent dice quienes somos, asi que disimular la
    huella del TLS no protegia nada y solo hacia el comportamiento menos
    reproducible. Ver `docs/NO-EVASION.md`.

    English: this used to shuffle cipher order per client to blur the TLS
    fingerprint. VIGIL identifies itself in the User-Agent, so blurring the
    handshake protected nothing and only made behaviour less reproducible.
    """
    return ssl.create_default_context()


def build_client() -> httpx.AsyncClient:
    """Construye un cliente HTTP con timeout global.

    English: Build an HTTP client with a global timeout.
    """
    return httpx.AsyncClient(timeout=httpx.Timeout(30.0), verify=_build_tls_context())


async def download_and_hash(
    url: str,
    output_path: Path,
    previous_hash: Optional[str] = None,
    if_none_match: Optional[str] = None,
    if_modified_since: Optional[str] = None,
) -> str:
    """Descarga, guarda y devuelve el hash encadenado.

    English: Download, persist, and return the chained hash.
    """
    async with build_client() as client:
        try:
            response = await fetch_content(
                client,
                url,
                if_none_match=if_none_match,
                if_modified_since=if_modified_since,
            )
        except httpx.RequestError as exc:
            raise DownloadError(f"Request failed for {url}: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise DownloadError(f"HTTP error for {url}: {exc}") from exc
        except httpx.TransportError as exc:
            raise DownloadError(f"Transport/SSL error for {url}: {exc}") from exc

    content = response.content
    write_atomic(output_path, content)
    chained = chained_hash(content, previous_hash)
    logger.info(
        "download_hash_written",
        url=url,
        output_path=str(output_path),
        content_bytes=len(content),
        previous_hash=previous_hash,
        chained_hash=chained,
    )
    return chained
