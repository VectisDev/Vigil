"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `tests/test_failure_resilience.py`.
Este módulo forma parte de VIGIL y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - _DummyResponse
  - test_process_sources_handles_connection_error
  - test_healthcheck_returns_false_on_failures
  - test_process_sources_saves_snapshot

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `tests/test_failure_resilience.py`.
This module is part of VIGIL and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - _DummyResponse
  - test_process_sources_handles_connection_error
  - test_healthcheck_returns_false_on_failures
  - test_process_sources_saves_snapshot

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx
import requests

from scripts import download_and_hash
from scripts.healthcheck import check_cne_endpoints


class _DummyResponse:
    """Español: Clase _DummyResponse del módulo tests/test_failure_resilience.py.

    English: _DummyResponse class defined in tests/test_failure_resilience.py.
    """

    def __init__(self, url: str, payload: dict) -> None:
        """Español: Función __init__ del módulo tests/test_failure_resilience.py.

        English: Function __init__ defined in tests/test_failure_resilience.py.
        """
        self.url = url
        self._payload = payload

    def raise_for_status(self) -> None:
        """Español: Función raise_for_status del módulo tests/test_failure_resilience.py.

        English: Function raise_for_status defined in tests/test_failure_resilience.py.
        """
        return None

    def json(self):  # type: ignore[override]
        """Español: Función json del módulo tests/test_failure_resilience.py.

        English: Function json defined in tests/test_failure_resilience.py.
        """
        return self._payload


def test_process_sources_handles_connection_error(monkeypatch, tmp_path) -> None:
    """Español: Función test_process_sources_handles_connection_error del módulo tests/test_failure_resilience.py.

    English: Function test_process_sources_handles_connection_error defined in tests/test_failure_resilience.py.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        download_and_hash,
        "CHECKPOINT_PATH",
        Path(tmp_path / "download_checkpoint.json"),
    )

    def _raise_error(*_args, **_kwargs):
        """Español: Función _raise_error del módulo tests/test_failure_resilience.py.

        English: Function _raise_error defined in tests/test_failure_resilience.py.
        """
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(download_and_hash, "request_json_with_retry", _raise_error)

    sources = [{"source_id": "NACIONAL", "endpoint": "https://cne.hn/nacional"}]
    config = {"max_sources_per_cycle": 1}
    download_and_hash.process_sources(sources, {}, config)

    assert not (tmp_path / "download_checkpoint.json").exists()


_HEALTHCHECK_CONFIG = {
    "endpoints": {"nacional": "https://cne.hn/nacional"},
    "sources": [{"scope": "NATIONAL"}],
    "max_sources_per_cycle": 1,
}


def test_healthcheck_returns_false_on_failures(monkeypatch) -> None:
    """Un endpoint inalcanzable deja el healthcheck en False.

    `check_cne_endpoints` usa httpx. La version anterior de esta prueba
    parcheaba `requests.Session.get`, que el modulo dejo de usar, asi que la
    llamada salia a la red real en lugar de ejercitar la rama de fallo: la
    prueba no comprobaba nada de lo que decia comprobar.

    English: `check_cne_endpoints` uses httpx. The previous version patched
    `requests.Session.get`, which the module no longer uses, so the call went
    out to the real network instead of exercising the failure branch.
    """

    def _fail(*_args, **_kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.Client, "get", _fail)

    assert check_cne_endpoints(dict(_HEALTHCHECK_CONFIG)) is False


def test_healthcheck_returns_false_on_unexpected_error(monkeypatch) -> None:
    """Un error ajeno a httpx tambien reporta no-sano, en vez de abortar.

    Si el chequeo propaga, el job muere, y un job muerto es indistinguible de
    un job que nunca corrio. Esa ambiguedad es la que el sistema existe para
    eliminar, asi que un fallo de resolucion, de sockets o de TLS fuera de la
    jerarquia de httpx tiene que terminar en False y quedar registrado.

    English: if the check propagates, the job dies, and a dead job is
    indistinguishable from one that never ran -- the very ambiguity this
    system exists to remove.
    """

    def _boom(*_args, **_kwargs):
        raise OSError("resolver failed in a way httpx does not wrap")

    monkeypatch.setattr(httpx.Client, "get", _boom)

    assert check_cne_endpoints(dict(_HEALTHCHECK_CONFIG)) is False


def test_process_sources_saves_snapshot(monkeypatch, tmp_path) -> None:
    """Español: Función test_process_sources_saves_snapshot del módulo tests/test_failure_resilience.py.

    English: Function test_process_sources_saves_snapshot defined in tests/test_failure_resilience.py.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        download_and_hash,
        "CHECKPOINT_PATH",
        Path(tmp_path / "download_checkpoint.json"),
    )

    response = _DummyResponse(
        "https://cne.hn/nacional",
        {"timestamp": datetime.now(timezone.utc).isoformat(), "source": "CNE"},
    )

    monkeypatch.setattr(
        download_and_hash,
        "request_json_with_retry",
        lambda *_args, **_kwargs: (response, response.json()),
    )

    sources = [{"source_id": "NACIONAL", "endpoint": "https://cne.hn/nacional"}]
    # La validacion de endpoint resuelve el host y exige IP publica. Sin
    # desactivar ese paso la prueba depende de que cne.hn resuelva en la
    # maquina que la ejecuta: medía la red, no el guardado del snapshot. La
    # allowlist de hostname sigue aplicandose de verdad, y tiene cobertura
    # propia en test_is_cne_endpoint_*.
    # English: endpoint validation resolves the host and requires a public IP.
    # Without turning that step off the test depends on cne.hn resolving on
    # the machine running it, measuring the network instead of the snapshot
    # write. The hostname allowlist still applies for real.
    config = {"max_sources_per_cycle": 1, "enforce_public_ip_resolution": False}
    download_and_hash.process_sources(sources, {}, config)

    snapshots = list((tmp_path / "data" / "snapshots" / "NACIONAL").glob("snapshot_*.json"))
    hashes = list((tmp_path / "hashes" / "NACIONAL").glob("snapshot_*.sha256"))
    assert snapshots
    assert hashes


# ---------------------------------------------------------------------------
# Allowlist de endpoint: el control anti-spoofing no tenia ninguna prueba.
# Endpoint allowlist: the anti-spoofing control had no test at all.
# ---------------------------------------------------------------------------

# `enforce_public_ip_resolution` desactivado para no depender de DNS: lo que
# se ejercita aqui es el parseo de URL y el cotejo de hostname, no la red.
_ALLOWLIST_CONFIG = {"enforce_public_ip_resolution": False}


def test_is_cne_endpoint_accepts_the_real_domain_and_subdomains() -> None:
    assert download_and_hash._is_cne_endpoint("https://cne.hn/nacional", _ALLOWLIST_CONFIG)
    assert download_and_hash._is_cne_endpoint("https://resultados.cne.hn/x", _ALLOWLIST_CONFIG)
    # El hostname no distingue mayusculas. / Hostnames are case-insensitive.
    assert download_and_hash._is_cne_endpoint("https://CNE.HN/nacional", _ALLOWLIST_CONFIG)


def test_is_cne_endpoint_rejects_forgeries() -> None:
    """Fija los rechazos que motivaron el control.

    El docstring de `_is_cne_endpoint` nombra la falsificacion que la
    implementacion anterior aceptaba, `https://cne.hn.attacker.example.com/`,
    porque comparaba por substring. Ese rechazo no tenia ninguna prueba, de
    modo que nada impedia que una futura simplificacion lo reintrodujera. Un
    endpoint falso aceptado aqui significa que el sistema firma, encadena y
    ancla a Bitcoin datos que no vienen del CNE, con la misma apariencia de
    prueba criptografica que los autenticos.

    English: the docstring names the forgery the previous substring-matching
    implementation accepted. That rejection had no test, so nothing stopped a
    later simplification from reintroducing it. A forged endpoint accepted
    here means the system hashes, chains and anchors non-CNE data to Bitcoin
    with the same appearance of cryptographic proof as the genuine records.
    """
    forgeries = {
        "sufijo falsificado": "https://cne.hn.attacker.example.com/",
        "substring sin frontera de punto": "https://evilcne.hn/x",
        "dominio ajeno": "https://attacker.example.com/",
        "credenciales embebidas": "https://user:pass@cne.hn/x",
        "sin https": "http://cne.hn/x",
    }
    for label, endpoint in forgeries.items():
        assert not download_and_hash._is_cne_endpoint(endpoint, _ALLOWLIST_CONFIG), label
