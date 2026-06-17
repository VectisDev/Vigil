"""Pure SHA-256 hash-chain primitives for Centinel Engine.

Primitivas puras de cadena hash SHA-256 para Centinel Engine.

Contains only deterministic, side-effect-free functions so they can be
imported by scripts/download_and_hash.py (data layer) and by any future
verification tool (verify_chain.py, observers) without pulling in HTTP
dependencies.

Contiene únicamente funciones deterministas y sin efectos secundarios, para
que puedan ser importadas por scripts/download_and_hash.py y por cualquier
herramienta de verificación futura sin importar dependencias HTTP.

ABSOLUTE RESTRICTION: The hash computation logic in this module is audited.
Do NOT change the algorithm, byte encoding, or concatenation order —
any modification breaks the chain for all existing evidence files.
See CLAUDE.md: SHA-256 hash chaining and Merkle root are protected.

RESTRICCIÓN ABSOLUTA: La lógica de hash en este módulo es auditada.
NO cambiar algoritmo, encoding de bytes, ni orden de concatenación —
cualquier modificación rompe la cadena de todas las evidencias existentes.

ponytail: Phase 6a — full extraction of _persist_snapshot_payload from
scripts/download_and_hash.py into this module deferred. That function
also handles Ed25519 signing, file I/O, and backup triggers; extracting
it cleanly requires test coverage of the boundary before moving. The
two core primitives below are extracted and bit-identical.
"""

from __future__ import annotations

import hashlib


def compute_hash(data: bytes) -> str:
    """Return the SHA-256 hex digest of ``data``.

    Bilingual: Retorna el hash SHA-256 hex de ``data``.

    This is the canonical hash primitive for the entire evidence chain.
    Never replace with a different algorithm or truncation.

    Args:
        data: Raw bytes to hash.

    Returns:
        str: 64-character lowercase hex string.
    """
    return hashlib.sha256(data).hexdigest()


def chain_hash(previous_hash: str, current_data: bytes) -> str:
    """Return SHA-256 of ``previous_hash`` concatenated with ``current_data``.

    Bilingual: Retorna SHA-256 de ``previous_hash`` concatenado con ``current_data``.

    Concatenation encoding: previous_hash (UTF-8 str) + current_data
    decoded as UTF-8 (with ``errors="ignore"``), then re-encoded to UTF-8.
    This exact encoding must be preserved for chain integrity.

    Args:
        previous_hash: Hex digest of the preceding chain entry.
        current_data: Raw bytes of the current snapshot.

    Returns:
        str: 64-character lowercase hex string linking previous to current.
    """
    combined = (previous_hash + current_data.decode("utf-8", errors="ignore")).encode("utf-8")
    return compute_hash(combined)
