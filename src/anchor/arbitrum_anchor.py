"""Arbitrum/EVM blockchain anchor stub for Centinel Engine.

Provides privacy-safe identifier obfuscation and a batch anchoring interface.
The real Web3/Arbitrum integration is activated when ARBITRUM_RPC_URL and
ARBITRUM_PRIVATE_KEY environment variables are present.
"""

from __future__ import annotations

import os
from typing import Any


# ── Privacy helpers ───────────────────────────────────────────────────────────

_OBFUSCATE_THRESHOLD = 12


def _obfuscate_identifier(value: str) -> str:
    """Return value unchanged if short; mask the middle if long.

    Short identifiers (≤ _OBFUSCATE_THRESHOLD chars) pass through unmodified.
    Long identifiers (e.g. Ethereum addresses, tx hashes) are shown as
    first-6 + "…" + last-4 to preserve context without leaking the full value.

    Examples:
        "abc123"              → "abc123"          (passthrough)
        "0x1234567890abcdef"  → "0x1234…cdef"     (masked)
    """
    if len(value) <= _OBFUSCATE_THRESHOLD:
        return value
    return f"{value[:6]}…{value[-4:]}"


# ── Web3 / Arbitrum internals (stubbed; real impl requires web3 package) ──────

class Account:
    """Thin stub for eth_account.Account used in signing operations."""

    @classmethod
    def from_key(cls, private_key: str) -> "Account":
        instance = cls()
        instance._key = private_key  # noqa: SLF001
        return instance

    @staticmethod
    def sign_transaction(tx: dict[str, Any], private_key: str) -> Any:
        from types import SimpleNamespace
        return SimpleNamespace(rawTransaction=b"stub_signed_tx")


def _load_arbitrum_settings() -> dict[str, str]:
    """Load Arbitrum connection settings from environment variables."""
    return {
        "rpc_url": os.environ.get("ARBITRUM_RPC_URL", ""),
        "private_key": os.environ.get("ARBITRUM_PRIVATE_KEY", ""),
        "contract_address": os.environ.get("ARBITRUM_CONTRACT_ADDRESS", ""),
    }


def _build_web3_client(rpc_url: str) -> Any:
    """Build a Web3 client. Requires the `web3` package at runtime."""
    try:
        from web3 import Web3  # type: ignore[import-untyped]
        return Web3(Web3.HTTPProvider(rpc_url))
    except ImportError:
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def anchor_batch(hashes: list[str]) -> dict[str, Any]:
    """Anchor a batch of SHA-256 hashes to the Arbitrum blockchain.

    Requires ARBITRUM_RPC_URL and ARBITRUM_PRIVATE_KEY (via env or settings).
    Returns a result dict with tx_hash and anchored count, or an error/skipped
    dict if the web3 package or credentials are unavailable.
    """
    settings = _load_arbitrum_settings()
    rpc_url = settings.get("rpc_url", "")
    private_key = settings.get("private_key", "") or os.environ.get("ARBITRUM_PRIVATE_KEY", "")

    if not rpc_url or not private_key:
        return {"status": "skipped", "reason": "ARBITRUM_RPC_URL or ARBITRUM_PRIVATE_KEY not set", "count": 0}

    w3 = _build_web3_client(rpc_url)
    if w3 is None:
        return {"status": "error", "reason": "web3 package not installed", "count": 0}

    account = Account.from_key(private_key)
    contract_address = w3.to_checksum_address(settings.get("contract_address", "0x" + "0" * 40))
    contract = w3.eth.contract(address=contract_address, abi=[])

    anchor_fn = contract.functions.anchor(hashes)
    gas = anchor_fn.estimate_gas({"from": account.address})
    tx = anchor_fn.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": gas,
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id,
    })

    signed = Account.sign_transaction(tx, private_key)
    raw_receipt = w3.eth.send_raw_transaction(signed.rawTransaction)
    tx_hash = w3.to_hex(raw_receipt)

    return {"status": "ok", "tx_hash": tx_hash, "count": len(hashes)}
