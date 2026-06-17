"""Internal library — not a CLI entry point. Imported by pipeline modules.

Connectivity checks for CNE endpoints.
Comprobaciones de conectividad con endpoints del CNE.

Components / Componentes:
  - _build_client: Build HTTP client with retries.
  - _collect_endpoints: Collect configured endpoints for healthchecks.
  - check_cne_connectivity: Quick HEAD probe to CNE.
  - check_cne_endpoints: Full endpoint sweep.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from scripts.logging_utils import configure_logging, log_event

# ponytail: previously used requests.Session + HTTPAdapter(Retry); httpx HTTPTransport
# does not support backoff_factor or status_forcelist — add tenacity retry in Phase 2a
# when retry_backoff() is extracted.

logger = configure_logging("centinel.healthcheck", log_file="logs/centinel.log")


def _build_client(retries: int, backoff_factor: float, timeout: float) -> httpx.Client:
    """Build an HTTP client with retry transport.

    Construye un cliente HTTP con transporte de reintentos.
    """
    transport = httpx.HTTPTransport(retries=retries)
    return httpx.Client(transport=transport, timeout=timeout)


def _collect_endpoints(config: dict[str, Any]) -> list[str]:
    """Collect configured endpoints for healthchecks.

    Recoge endpoints configurados para el chequeo de salud.
    """
    endpoints = config.get("endpoints", {}) or {}
    sources = config.get("sources", []) or []
    max_sources = int(config.get("max_sources_per_cycle", 19))
    targets: list[str] = []
    for source in sources[:max_sources]:
        scope = source.get("scope")
        if scope == "NATIONAL":
            endpoint = endpoints.get("nacional") or endpoints.get("fallback_nacional")
        elif scope == "DEPARTMENT":
            department_code = source.get("department_code")
            endpoint = endpoints.get(department_code) if department_code else None
        else:
            endpoint = source.get("endpoint")
        if endpoint:
            targets.append(endpoint)
    return sorted(set(targets))


def check_cne_connectivity(config: dict[str, Any]) -> bool:
    """Check connectivity to CNE using a quick HEAD request.

    Verifica conectividad con CNE usando un HEAD rápido.
    """
    endpoints = config.get("endpoints", {}) or {}
    dummy_endpoint = (
        config.get("healthcheck_url")
        or config.get("base_url")
        or endpoints.get("nacional")
        or endpoints.get("fallback_nacional")
    )
    if not dummy_endpoint:
        log_event(logger, logging.WARNING, "healthcheck_missing_dummy_endpoint")
        return False

    try:
        response = httpx.head(str(dummy_endpoint), timeout=10, follow_redirects=True)
        if response.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status={response.status_code}",
                request=response.request,
                response=response,
            )
        log_event(logger, logging.INFO, "healthcheck_dummy_ok", endpoint=dummy_endpoint)
        return True
    except httpx.HTTPError as exc:
        log_event(
            logger,
            logging.WARNING,
            "healthcheck_dummy_failed",
            endpoint=dummy_endpoint,
            error=str(exc),
        )
        return False


def check_cne_endpoints(config: dict[str, Any]) -> bool:
    """Check connectivity to detailed CNE endpoints.

    Verifica conectividad con endpoints CNE detallados.
    """
    endpoints = _collect_endpoints(config)
    if not endpoints:
        log_event(logger, logging.WARNING, "healthcheck_no_endpoints")
        return False

    retries = int(config.get("retries", 5))
    backoff_factor = float(config.get("backoff_base_seconds", 0.5))
    timeout = float(config.get("timeout", 10))

    client = _build_client(retries=retries, backoff_factor=backoff_factor, timeout=timeout)
    ok_count = 0
    try:
        for endpoint in endpoints:
            try:
                response = client.get(endpoint)
                response.raise_for_status()
                ok_count += 1
            except httpx.HTTPError as exc:
                log_event(
                    logger,
                    logging.WARNING,
                    "healthcheck_failed",
                    endpoint=endpoint,
                    error=str(exc),
                )
    finally:
        client.close()

    log_event(
        logger,
        logging.INFO,
        "healthcheck_summary",
        ok_count=ok_count,
        total=len(endpoints),
    )
    return ok_count > 0
