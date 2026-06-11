"""
CENTINEL — Pre-Capture Evidentiary Custody
============================================

Module: src/centinel/core/pre_capture_custody.py

Audit finding addressed: Point 1 — Pre-capture custody gap.
Hallazgo de auditoría: Punto 1 — Brecha de custodia pre-captura.

Purpose / Propósito
-------------------

The cryptographic hash chain that CENTINEL constructs over captured CNE
JSON files begins **inside** the system. By itself, it does not preserve
any information about where the JSON came from. A hostile actor (e.g.,
a state prosecutor) can argue: "How do you prove that JSON came from the
CNE server and was not fabricated by your capture software?"

This module answers that question by attaching to every capture a
**pre-capture custody envelope** containing:

1. The exact URL requested.
2. The IP address resolved at capture time.
3. The TLS certificate chain fingerprint (SHA-256 of DER bytes).
4. The HTTP response headers as received — including the server's
   ``Date:`` header, ``ETag``, ``Last-Modified``, ``Content-Type``, etc.
5. The SHA-256 hash of the raw response body BEFORE any parsing.
6. The HTTP status code.
7. An Ed25519 signature over the entire envelope by the operator.

This envelope is computed FIRST, BEFORE the JSON is parsed or any
statistical rule is run. It is included in the hash chain link for the
capture, so any subsequent modification (or substitution) of the
envelope is detectable.

----

El hash chain criptográfico que construye CENTINEL sobre los JSON
capturados comienza **dentro** del sistema. Por sí solo, no preserva
ninguna información sobre dónde vino el JSON. Un actor hostil (p.ej., un
fiscal del Estado) puede argumentar: "¿Cómo prueba usted que ese JSON vino
del servidor del CNE y no fue fabricado por su software de captura?"

Este módulo responde a esa pregunta adjuntando a cada captura un **sobre
de custodia pre-captura** que contiene:

1. La URL exacta solicitada.
2. La dirección IP resuelta al momento de la captura.
3. La huella del certificado TLS (SHA-256 de los bytes DER).
4. Los headers HTTP de respuesta tal como se recibieron — incluyendo
   el ``Date:`` del servidor, ``ETag``, ``Last-Modified``, etc.
5. El hash SHA-256 del body crudo de la respuesta ANTES de cualquier parseo.
6. El código de estado HTTP.
7. Una firma Ed25519 sobre todo el sobre por parte del operador.

Este sobre se computa PRIMERO, ANTES de que el JSON sea parseado o se
ejecute cualquier regla estadística. Se incluye en el eslabón del hash
chain de la captura, por lo que cualquier modificación o sustitución
posterior del sobre es detectable.

Threat model
------------

This module addresses the following attacker capabilities:

1. **"Fabrication" allegation** — A state prosecutor alleges that the
   CENTINEL operator fabricated the JSON files locally. The envelope's
   TLS fingerprint + server timestamps + IP are independently verifiable
   against passive DNS and Certificate Transparency logs at the time of
   capture.

2. **"Tampered after capture" allegation** — The operator captured the
   JSON honestly but altered it before hash-chaining it. The envelope
   hash of the RAW body is computed before any parsing or transformation,
   and is included in the signature.

3. **"Software backdoored" allegation** — The operator's capture software
   itself was compromised. Mitigated by independent reproducibility: any
   third party with network access to the CNE during the same window can
   capture the same URL and observe a matching server certificate and
   IP, even if not the byte-exact JSON (because the published data
   may have updated by then). Federation of capture nodes (a separate
   audit item) eliminates this gap entirely.

License: AGPL-3.0 (matching the parent CENTINEL project)
"""

from __future__ import annotations

import hashlib
import json
import socket
import ssl
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

# Optional dependency: cryptography (for Ed25519 signing).
# It is already a CENTINEL dependency.
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.exceptions import InvalidSignature
    _CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CRYPTO_AVAILABLE = False


__all__ = [
    "CustodyEnvelope",
    "CustodyError",
    "build_envelope",
    "sign_envelope",
    "verify_envelope",
    "extract_tls_metadata",
    "envelope_canonical_bytes",
    "envelope_sha256",
]


class CustodyError(Exception):
    """Raised for custody-related failures. / Errores de custodia."""


# ---------------------------------------------------------------------------
# Data structure / Estructura de datos
# ---------------------------------------------------------------------------


@dataclass
class CustodyEnvelope:
    """
    A pre-capture custody envelope.

    All string fields use UTF-8. Binary fields (cert fingerprints, hashes,
    signatures) are stored as lowercase hex.

    Un sobre de custodia pre-captura.

    Todos los campos string son UTF-8. Los campos binarios (fingerprints
    de certificado, hashes, firmas) se almacenan como hex minúscula.

    Schema version
    --------------
    The serialized form of this envelope is versioned. Verifiers must
    refuse envelopes of unknown versions. Backward-compatible additions
    increment the minor version; breaking changes increment the major.

    El formato serializado está versionado. Los verificadores deben
    rechazar sobres de versión desconocida. Las adiciones compatibles
    incrementan la versión menor; los cambios incompatibles, la mayor.
    """

    # Identification / Identificación
    envelope_version: str = "1.0"
    envelope_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Capture-time metadata / Metadata del momento de la captura
    captured_at_utc: str = ""  # ISO-8601 UTC of when the capture began.
    operator_id: str = ""      # Stable identifier of the capture operator.

    # The request / La petición
    url_requested: str = ""
    request_method: str = "GET"

    # Network resolution / Resolución de red
    host_resolved_ip: str = ""           # Dotted IPv4 or IPv6 string.
    host_resolved_at_utc: str = ""        # When DNS resolution happened.

    # TLS evidence / Evidencia TLS
    tls_version: str = ""                 # e.g. "TLSv1.3"
    tls_cipher: str = ""                  # e.g. "TLS_AES_256_GCM_SHA384"
    tls_cert_subject: str = ""            # e.g. "CN=cne.hn"
    tls_cert_issuer: str = ""             # e.g. "CN=DigiCert TLS RSA SHA256 2020 CA1"
    tls_cert_not_before_utc: str = ""
    tls_cert_not_after_utc: str = ""
    tls_cert_sha256_der: str = ""         # Hex SHA-256 of the leaf cert in DER.
    tls_cert_chain_sha256_der: list[str] = field(default_factory=list)

    # HTTP response (received bytes) / Respuesta HTTP (bytes recibidos)
    http_status_code: int = 0
    http_response_headers: dict[str, str] = field(default_factory=dict)
    # Particular headers worth pinning at the schema level for grep-ability:
    # Headers particulares que vale la pena fijar a nivel de esquema:
    server_date_header: str = ""          # The ``Date:`` header from the server.
    server_etag: str = ""
    server_last_modified: str = ""
    server_content_type: str = ""

    # Body integrity / Integridad del body
    response_body_size_bytes: int = 0
    response_body_sha256: str = ""        # SHA-256 of the RAW body bytes.

    # Free-form provenance notes / Notas de procedencia
    capture_tool: str = "centinel-pre-capture-custody"
    capture_tool_version: str = "1.0"
    notes: str = ""

    # Signature (computed last and over a canonical serialization).
    # Firma (computada al final sobre la serialización canónica).
    operator_signature_ed25519_hex: str = ""
    operator_public_key_ed25519_hex: str = ""

    # The previous chain link, if any. This is what hooks the envelope
    # into CENTINEL's hash chain.
    # El eslabón previo de la cadena, si hay. Esto engancha el sobre a
    # la cadena de hashes de CENTINEL.
    previous_chain_link_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Canonical serialization for signing/hashing
# Serialización canónica para firma y hash
# ---------------------------------------------------------------------------


def envelope_canonical_bytes(envelope: CustodyEnvelope) -> bytes:
    """
    Serialize an envelope to canonical JSON for hashing and signing.

    Canonical form: UTF-8 encoded JSON with sorted keys, no whitespace
    other than the JSON separators, and the two signature fields removed
    (so that signing produces a stable input regardless of pre-existing
    signature).

    Forma canónica: JSON en UTF-8 con claves ordenadas, sin espacios en
    blanco aparte de los separadores JSON, y los dos campos de firma
    removidos (para que firmar produzca un input estable sin importar
    una firma previa).
    """
    d = envelope.to_dict()
    # Exclude the signature fields from canonicalization.
    d.pop("operator_signature_ed25519_hex", None)
    d.pop("operator_public_key_ed25519_hex", None)
    return json.dumps(
        d,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def envelope_sha256(envelope: CustodyEnvelope) -> str:
    """Hex SHA-256 of the canonical bytes of the envelope."""
    return hashlib.sha256(envelope_canonical_bytes(envelope)).hexdigest()


# ---------------------------------------------------------------------------
# TLS metadata extraction (capture-side helper)
# Extracción de metadata TLS (helper del lado de la captura)
# ---------------------------------------------------------------------------


def extract_tls_metadata(
    hostname: str,
    port: int = 443,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """
    Connect to ``hostname:port`` via TLS, extract the certificate metadata,
    and return it as a dict ready to be merged into a CustodyEnvelope.

    Conecta a ``hostname:port`` vía TLS, extrae metadata del certificado
    y la retorna como dict listo para integrarse en un CustodyEnvelope.

    This function does NOT fetch the HTTP body — it only inspects the TLS
    layer. The HTTP fetch is done separately by the caller to ensure the
    capture pipeline remains transparent and testable.

    Esta función NO descarga el body HTTP — solo inspecciona la capa TLS.
    La descarga HTTP la hace por separado el llamador.

    Parameters
    ----------
    hostname : str
        DNS name to resolve and connect to.
    port : int
        TCP port (default 443).
    timeout_seconds : float
        Connect/handshake timeout.

    Returns
    -------
    dict
        Dictionary with keys: host_resolved_ip, tls_version, tls_cipher,
        tls_cert_subject, tls_cert_issuer, tls_cert_not_before_utc,
        tls_cert_not_after_utc, tls_cert_sha256_der, tls_cert_chain_sha256_der.

    Raises
    ------
    CustodyError
        If the connection fails or the certificate cannot be parsed.
    """
    try:
        # Resolve the IP first so we capture exactly which IP we hit.
        # Resolvemos la IP primero para capturar exactamente cuál IP usamos.
        addr_info = socket.getaddrinfo(
            hostname, port, type=socket.SOCK_STREAM
        )
        if not addr_info:
            raise CustodyError(f"DNS resolution returned no records for {hostname}")
        family, _, _, _, sockaddr = addr_info[0]
        ip = sockaddr[0]

        # Build TLS context. Use default verification — the certificate
        # MUST validate, otherwise we are talking to an attacker.
        # Construir contexto TLS. Verificación por defecto — el certificado
        # DEBE validar, sino estamos hablando con un atacante.
        context = ssl.create_default_context()
        # Explicitly enforce TLS 1.2+ -- disallow TLSv1/TLSv1.1
        # Aplicar explicitamente TLS 1.2+ -- deshabilitar TLSv1/TLSv1.1
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        # We want the cert chain in DER form, so request binary form below.
        # Queremos la cadena de certificado en DER, así que pedimos binario abajo.

        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout_seconds)
            sock.connect((ip, port))
            with context.wrap_socket(
                sock, server_hostname=hostname
            ) as tls_sock:
                cipher_info = tls_sock.cipher()
                tls_version = tls_sock.version() or ""
                # Get the peer cert in DER (binary) form.
                cert_der: Optional[bytes] = tls_sock.getpeercert(binary_form=True)
                # Get parsed cert info for subject/issuer/validity.
                cert_parsed = tls_sock.getpeercert()

                # The standard library does not expose the FULL chain
                # easily. We compute the SHA-256 of the LEAF cert in DER,
                # plus what we have. To get the full chain we would need
                # to use cryptography.x509 — out of scope here.
                # La librería estándar no expone toda la cadena
                # fácilmente. Computamos SHA-256 del cert HOJA en DER;
                # para toda la cadena habría que usar cryptography.x509.

        if cert_der is None:
            raise CustodyError("Peer presented no certificate")

        cert_sha256 = hashlib.sha256(cert_der).hexdigest()

        def _format_dn(dn_tuple: Any) -> str:
            """Format a parsed cert DN into a readable string."""
            if not dn_tuple:
                return ""
            parts = []
            for rdn in dn_tuple:
                for key, val in rdn:
                    parts.append(f"{key}={val}")
            return ", ".join(parts)

        subject = _format_dn(cert_parsed.get("subject", ()))
        issuer = _format_dn(cert_parsed.get("issuer", ()))

        def _ssl_date_to_iso(s: Optional[str]) -> str:
            """Convert OpenSSL date string to ISO-8601 UTC."""
            if not s:
                return ""
            # OpenSSL format: 'Jun  1 12:00:00 2026 GMT'
            try:
                dt = datetime.strptime(s, "%b %d %H:%M:%S %Y %Z")
                return dt.replace(tzinfo=timezone.utc).isoformat().replace(
                    "+00:00", "Z"
                )
            except ValueError:
                return s  # fall back to raw

        return {
            "host_resolved_ip": ip,
            "tls_version": tls_version,
            "tls_cipher": cipher_info[0] if cipher_info else "",
            "tls_cert_subject": subject,
            "tls_cert_issuer": issuer,
            "tls_cert_not_before_utc": _ssl_date_to_iso(cert_parsed.get("notBefore")),
            "tls_cert_not_after_utc": _ssl_date_to_iso(cert_parsed.get("notAfter")),
            "tls_cert_sha256_der": cert_sha256,
            "tls_cert_chain_sha256_der": [cert_sha256],  # Leaf only; chain TBD.
        }
    except (socket.gaierror, socket.timeout, ssl.SSLError, OSError) as exc:
        raise CustodyError(f"TLS metadata extraction failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Envelope construction / Construcción del sobre
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_envelope(
    *,
    url: str,
    operator_id: str,
    response_body: bytes,
    response_status: int,
    response_headers: Mapping[str, str],
    tls_metadata: Mapping[str, Any],
    previous_chain_link_sha256: str = "",
    notes: str = "",
    captured_at_utc: Optional[str] = None,
) -> CustodyEnvelope:
    """
    Build a pre-capture custody envelope from observed capture data.

    The caller is responsible for ensuring `response_body` is the RAW
    bytes as received from the server, BEFORE any parsing, decoding,
    or transformation. Even gzip-decompressed bodies should not be
    used here — pass the raw on-the-wire bytes.

    Construye un sobre de custodia pre-captura a partir de los datos
    observados. El llamador es responsable de que `response_body` sean
    los bytes CRUDOS recibidos del servidor, ANTES de cualquier parseo,
    decodificación o transformación.

    Parameters
    ----------
    url : str
        The full URL that was requested.
    operator_id : str
        Stable identifier of the operator (free-form).
    response_body : bytes
        The raw response body bytes (pre-parse).
    response_status : int
        HTTP status code observed.
    response_headers : Mapping[str, str]
        Response headers as observed. Header names are case-insensitive
        but stored as received.
    tls_metadata : Mapping[str, Any]
        Output of extract_tls_metadata(), or equivalent dict.
    previous_chain_link_sha256 : str, optional
        SHA-256 of the previous chain link, if part of a chain.
    notes : str, optional
        Free-form notes (will be stored verbatim).
    captured_at_utc : str, optional
        ISO-8601 timestamp override; defaults to "now". Provide for
        deterministic testing only.

    Returns
    -------
    CustodyEnvelope
        Unsigned envelope. Call sign_envelope() to attach a signature.
    """
    if not isinstance(response_body, (bytes, bytearray)):
        raise CustodyError("response_body must be bytes")

    body_sha256 = hashlib.sha256(response_body).hexdigest()
    headers_lower = {k.lower(): v for k, v in response_headers.items()}

    return CustodyEnvelope(
        envelope_version="1.0",
        captured_at_utc=captured_at_utc or _now_utc_iso(),
        operator_id=operator_id,
        url_requested=url,
        request_method="GET",
        host_resolved_ip=str(tls_metadata.get("host_resolved_ip", "")),
        host_resolved_at_utc=captured_at_utc or _now_utc_iso(),
        tls_version=str(tls_metadata.get("tls_version", "")),
        tls_cipher=str(tls_metadata.get("tls_cipher", "")),
        tls_cert_subject=str(tls_metadata.get("tls_cert_subject", "")),
        tls_cert_issuer=str(tls_metadata.get("tls_cert_issuer", "")),
        tls_cert_not_before_utc=str(tls_metadata.get("tls_cert_not_before_utc", "")),
        tls_cert_not_after_utc=str(tls_metadata.get("tls_cert_not_after_utc", "")),
        tls_cert_sha256_der=str(tls_metadata.get("tls_cert_sha256_der", "")),
        tls_cert_chain_sha256_der=list(
            tls_metadata.get("tls_cert_chain_sha256_der", [])
        ),
        http_status_code=int(response_status),
        http_response_headers=dict(response_headers),
        server_date_header=headers_lower.get("date", ""),
        server_etag=headers_lower.get("etag", ""),
        server_last_modified=headers_lower.get("last-modified", ""),
        server_content_type=headers_lower.get("content-type", ""),
        response_body_size_bytes=len(response_body),
        response_body_sha256=body_sha256,
        previous_chain_link_sha256=previous_chain_link_sha256,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Signing and verification / Firma y verificación
# ---------------------------------------------------------------------------


def sign_envelope(
    envelope: CustodyEnvelope,
    private_key: "Ed25519PrivateKey",
) -> CustodyEnvelope:
    """
    Sign an envelope with an Ed25519 private key. Mutates and returns
    the envelope with the signature and public-key fields populated.

    Firma un sobre con una clave privada Ed25519.
    """
    if not _CRYPTO_AVAILABLE:
        raise CustodyError(
            "cryptography library is required for signing — pip install cryptography"
        )

    canonical = envelope_canonical_bytes(envelope)
    signature = private_key.sign(canonical)

    from cryptography.hazmat.primitives import serialization
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    envelope.operator_signature_ed25519_hex = signature.hex()
    envelope.operator_public_key_ed25519_hex = pub_bytes.hex()
    return envelope


def verify_envelope(
    envelope: CustodyEnvelope,
    *,
    expected_public_key: Optional[bytes] = None,
) -> bool:
    """
    Verify the Ed25519 signature of an envelope.

    Verifica la firma Ed25519 de un sobre.

    Parameters
    ----------
    envelope : CustodyEnvelope
        The envelope to verify.
    expected_public_key : bytes, optional
        If provided, also checks that the envelope was signed by exactly
        this public key. Otherwise, only verifies that the signature is
        valid for whatever public key is in the envelope.

    Returns
    -------
    bool
        True if the signature is valid (and matches the expected pubkey
        if one was provided).
    """
    if not _CRYPTO_AVAILABLE:
        raise CustodyError(
            "cryptography library is required for verification"
        )
    if not envelope.operator_signature_ed25519_hex:
        return False
    if not envelope.operator_public_key_ed25519_hex:
        return False

    try:
        pub_bytes = bytes.fromhex(envelope.operator_public_key_ed25519_hex)
        signature = bytes.fromhex(envelope.operator_signature_ed25519_hex)
    except ValueError:
        return False

    if expected_public_key is not None:
        import secrets as _secrets
        if not _secrets.compare_digest(pub_bytes, expected_public_key):
            return False

    try:
        Ed25519PublicKey.from_public_bytes(pub_bytes).verify(
            signature, envelope_canonical_bytes(envelope)
        )
        return True
    except InvalidSignature:
        return False
    except ValueError:
        return False
