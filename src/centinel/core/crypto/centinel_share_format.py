"""
CENTINEL — Share serialization (ASCII-armored format)
======================================================

Serialize/deserialize Shamir shares in a printable, paper-archivable format
inspired by PGP/SSH key armoring. Designed for:

- Printing on paper for offline custody.
- Sending over text channels (email, encrypted messengers).
- Manual re-entry with checksum validation.

Serializa/deserializa shares de Shamir en formato imprimible y archivable
en papel, inspirado en el formato armored de PGP/SSH. Diseñado para:

- Impresión en papel para custodia offline.
- Envío por canales de texto (correo, mensajería cifrada).
- Re-ingreso manual con validación por checksum.

Format
------
::

    -----BEGIN CENTINEL SHAMIR SHARE-----
    Version: 1
    Custodian: <human-readable name>
    Share-Id: <x-coordinate>
    Threshold: <k>
    Total: <n>
    Created: <ISO8601 UTC timestamp>
    Key-Type: ed25519
    Secret-Hash-SHA256: <hex hash of original secret, used to verify reconstruction>
    Share-Hash-SHA256: <hex hash of this share's bytes, used to verify share integrity>

    <base64-encoded share bytes, wrapped at 64 chars>
    -----END CENTINEL SHAMIR SHARE-----

License: AGPL-3.0
"""

from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


__all__ = ["Share", "ShareFormatError", "serialize_share", "parse_share"]


BEGIN_MARKER = "-----BEGIN CENTINEL SHAMIR SHARE-----"
END_MARKER = "-----END CENTINEL SHAMIR SHARE-----"


class ShareFormatError(ValueError):
    """Raised when a share cannot be parsed or fails integrity checks."""


@dataclass
class Share:
    """
    Structured representation of a single share.

    Representación estructurada de un share individual.

    Attributes
    ----------
    version : int
        Format version (currently always 1).
    custodian : str
        Human-readable name of the custodian holding this share.
    share_id : int
        The x-coordinate of this share (1..n), same as share_bytes[0].
    threshold : int
        Number of shares required for reconstruction (k).
    total : int
        Total number of shares originally created (n).
    created : str
        ISO-8601 UTC timestamp of creation.
    key_type : str
        Type of the underlying secret (e.g., "ed25519").
    secret_hash : str
        Hex SHA-256 of the original secret (used to verify reconstruction).
    share_bytes : bytes
        The raw share bytes as produced by centinel_shamir.split_secret().
        First byte is the x-coordinate, rest are y-values.
    share_hash : str
        Hex SHA-256 of share_bytes (computed at serialization).
    notes : str
        Optional free-form notes about this share's custody.
    """

    version: int
    custodian: str
    share_id: int
    threshold: int
    total: int
    created: str
    key_type: str
    secret_hash: str
    share_bytes: bytes
    share_hash: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.share_hash:
            self.share_hash = hashlib.sha256(self.share_bytes).hexdigest()


def _now_utc_iso() -> str:
    """Current UTC time as ISO-8601 string. / Hora UTC actual en ISO-8601."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def serialize_share(
    share_bytes: bytes,
    custodian: str,
    threshold: int,
    total: int,
    secret_hash: str,
    key_type: str = "ed25519",
    created: Optional[str] = None,
    notes: str = "",
) -> str:
    """
    Serialize a share into ASCII-armored text format.

    Serializa un share en formato ASCII-armored.

    Parameters
    ----------
    share_bytes : bytes
        Output of centinel_shamir.split_secret() for one share.
    custodian : str
        Human-readable custodian name.
    threshold : int
        Reconstruction threshold (k).
    total : int
        Total shares (n).
    secret_hash : str
        Hex SHA-256 of the original secret.
    key_type : str
        Type of underlying secret (default "ed25519").
    created : str, optional
        ISO timestamp override (for deterministic testing). Default: now UTC.
    notes : str, optional
        Optional notes (must not contain newlines).

    Returns
    -------
    str
        The ASCII-armored share, suitable for printing on paper.
    """
    if not share_bytes:
        raise ShareFormatError("Empty share bytes")
    if len(share_bytes) < 2:
        raise ShareFormatError("Share too short")
    if "\n" in notes or "\r" in notes:
        raise ShareFormatError("Notes must not contain line breaks")

    share_id = share_bytes[0]
    if not (1 <= share_id <= 255):
        raise ShareFormatError("Invalid share_id (first byte)")

    share = Share(
        version=1,
        custodian=custodian,
        share_id=share_id,
        threshold=threshold,
        total=total,
        created=created or _now_utc_iso(),
        key_type=key_type,
        secret_hash=secret_hash,
        share_bytes=share_bytes,
        notes=notes,
    )

    b64 = base64.b64encode(share_bytes).decode("ascii")
    # Wrap base64 at 64 characters per line — same convention as PEM.
    # Envolver base64 a 64 caracteres por línea — misma convención que PEM.
    wrapped = "\n".join(b64[i : i + 64] for i in range(0, len(b64), 64))

    lines = [
        BEGIN_MARKER,
        f"Version: {share.version}",
        f"Custodian: {share.custodian}",
        f"Share-Id: {share.share_id}",
        f"Threshold: {share.threshold}",
        f"Total: {share.total}",
        f"Created: {share.created}",
        f"Key-Type: {share.key_type}",
        f"Secret-Hash-SHA256: {share.secret_hash}",
        f"Share-Hash-SHA256: {share.share_hash}",
    ]
    if share.notes:
        lines.append(f"Notes: {share.notes}")
    lines.append("")  # Blank line separating headers from body.
    lines.append(wrapped)
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


_HEADER_RE = re.compile(r"^([A-Za-z0-9\-]+):\s*(.*)$")


def parse_share(text: str) -> Share:
    """
    Parse an ASCII-armored share, validating its integrity.

    Parsea un share ASCII-armored, validando su integridad.

    Raises
    ------
    ShareFormatError
        If the text is not a valid CENTINEL share or fails integrity checks.
    """
    # Locate the armor block. / Localizar el bloque armored.
    if BEGIN_MARKER not in text or END_MARKER not in text:
        raise ShareFormatError("Missing CENTINEL share markers")
    start = text.index(BEGIN_MARKER) + len(BEGIN_MARKER)
    end = text.index(END_MARKER)
    body = text[start:end].strip()

    # Split headers from base64 body. Headers end at first blank line.
    sections = body.split("\n\n", 1)
    if len(sections) != 2:
        raise ShareFormatError(
            "Expected blank line between headers and body in share"
        )
    header_text, b64_text = sections
    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _HEADER_RE.match(line)
        if not m:
            raise ShareFormatError(f"Invalid header line: {line!r}")
        headers[m.group(1).strip()] = m.group(2).strip()

    required = {
        "Version",
        "Custodian",
        "Share-Id",
        "Threshold",
        "Total",
        "Created",
        "Key-Type",
        "Secret-Hash-SHA256",
        "Share-Hash-SHA256",
    }
    missing = required - headers.keys()
    if missing:
        raise ShareFormatError(f"Missing required headers: {sorted(missing)}")

    try:
        version = int(headers["Version"])
        share_id = int(headers["Share-Id"])
        threshold = int(headers["Threshold"])
        total = int(headers["Total"])
    except ValueError as exc:
        raise ShareFormatError(f"Non-integer header value: {exc}") from exc

    if version != 1:
        raise ShareFormatError(f"Unsupported share version: {version}")

    b64_clean = "".join(b64_text.split())  # Remove all whitespace.
    try:
        share_bytes = base64.b64decode(b64_clean, validate=True)
    except Exception as exc:
        raise ShareFormatError(f"Invalid base64 body: {exc}") from exc

    # Integrity check 1: share_id matches first byte of payload.
    if not share_bytes or share_bytes[0] != share_id:
        raise ShareFormatError(
            "Share-Id header does not match first byte of payload"
        )

    # Integrity check 2: share hash matches.
    computed_hash = hashlib.sha256(share_bytes).hexdigest()
    declared_hash = headers["Share-Hash-SHA256"].lower()
    if computed_hash != declared_hash:
        raise ShareFormatError(
            f"Share hash mismatch (computed {computed_hash}, declared {declared_hash})"
        )

    return Share(
        version=version,
        custodian=headers["Custodian"],
        share_id=share_id,
        threshold=threshold,
        total=total,
        created=headers["Created"],
        key_type=headers["Key-Type"],
        secret_hash=headers["Secret-Hash-SHA256"].lower(),
        share_bytes=share_bytes,
        share_hash=computed_hash,
        notes=headers.get("Notes", ""),
    )
