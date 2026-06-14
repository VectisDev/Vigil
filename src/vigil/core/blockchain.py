"""
DEPRECATED — Este módulo fue eliminado por violar el principio de Costo Cero.
DEPRECATED — This module was removed for violating the Zero Cost principle.

El anclaje criptográfico de CENTINEL usa exclusivamente OpenTimestamps / Bitcoin,
que es gratuito, no requiere claves privadas ni pago de gas fees.

CENTINEL's cryptographic anchoring uses exclusively OpenTimestamps / Bitcoin,
which is free, requires no private keys, and incurs no gas fees.

Migración / Migration:
    # ANTES (viola costo cero — requiere gas fees en Arbitrum):
    # from vigil.core.blockchain import publish_hash_to_chain
    # publish_hash_to_chain(hash, config)

    # DESPUÉS (costo cero — Bitcoin via OpenTimestamps):
    from vigil.core.anchoring import anchor_snapshot_chain
    result = anchor_snapshot_chain("tests/fixtures/hnd_2025/")

Referencia / Reference:
    docs/finances/zero-cost-ledger.md
    src/centinel/core/anchoring.py
    tests/fixtures/hnd_2025/MERKLE_ROOT_HN2025.ots

Removido en: dev-v12 / 2026-06-07
Razón: web3 + Arbitrum requieren ARBITRUM_PRIVATE_KEY + gas fees (ETH).
       Viola el principio sagrado de operación a costo cero absoluto.
"""

from __future__ import annotations


def publish_hash_to_chain(*args, **kwargs) -> None:  # noqa: ANN002
    """DEPRECATED. Use vigil.core.anchoring.anchor_snapshot_chain() instead."""
    raise NotImplementedError(
        "blockchain.publish_hash_to_chain() is removed (violates Zero Cost principle). "
        "Use vigil.core.anchoring.anchor_snapshot_chain() instead. "
        "See: src/centinel/core/anchoring.py"
    )


def publish_cid_to_chain(*args, **kwargs) -> None:  # noqa: ANN002
    """DEPRECATED. IPFS + blockchain anchoring removed (violates Zero Cost)."""
    raise NotImplementedError(
        "blockchain.publish_cid_to_chain() is removed (violates Zero Cost principle). "
        "IPFS nodes and blockchain transactions require paid infrastructure. "
        "Use vigil.core.anchoring.anchor_snapshot_chain() instead."
    )


def is_blockchain_enabled(*args, **kwargs) -> bool:  # noqa: ANN002
    """Always returns False — Arbitrum anchoring is permanently disabled."""
    return False
