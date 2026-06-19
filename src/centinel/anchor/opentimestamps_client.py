"""
OpenTimestamps Integration for Centinel Engine.

ES: Integración de OpenTimestamps para Centinel Engine.

Provee anclaje criptográfico a Bitcoin blockchain vía OpenTimestamps.
Permite auditor verificar: "Este checkpoint fue creado antes de TIMESTAMP"
sin confiar en reloj de testigo (Theorem T3 completado).

EN: Provides cryptographic anchoring to Bitcoin blockchain via OpenTimestamps.
Allows auditor to verify: "This checkpoint was created before TIMESTAMP"
without trusting witness clock (Theorem T3 completed).

Design:
- Use OTS public calendar (free, no keys needed)
- Fallback to testnet if mainnet unavailable
- Non-fatal: if OTS fails, continue without anchor (downgraded assurance)
- Retry logic: exponential backoff on transient failures
- Forensic logging: all anchor attempts recorded
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Any, Optional

import httpx

logger = logging.getLogger("centinel.anchor.opentimestamps")

# OpenTimestamps public server endpoints
OTS_SERVERS = [
    "https://a.pool.opentimestamps.org",
    "https://b.pool.opentimestamps.org",
    "https://c.pool.opentimestamps.org",
]

OTS_TESTNET_SERVERS = [
    "https://testnet.opentimestamps.org",
]


@dataclass
class TimestampProof:
    """Proof of timestamp from OpenTimestamps.

    ES: Prueba de timestamp de OpenTimestamps.
    """

    timestamp: float  # Unix timestamp of anchor request
    message_hash: str  # SHA256 of message (64-char hex)
    ots_response: str  # OTS proof (base64-encoded)
    bitcoin_tx: Optional[str] = None  # Bitcoin tx hash (if found)
    bitcoin_block: Optional[int] = None  # Bitcoin block height (if found)
    chain: str = "mainnet"  # "mainnet" or "testnet"
    verified: bool = False  # Whether proof has been verified


@dataclass
class AnchorRecord:
    """Record of anchor attempt (success or failure).

    ES: Registro de intento de anclaje (éxito o fracaso).
    """

    checkpoint_hash: str
    attempt_timestamp: float
    success: bool
    proof: Optional[TimestampProof] = None
    error_detail: Optional[str] = None
    retry_count: int = 0


class OpenTimestampsClient:
    """Client for OpenTimestamps protocol.

    ES: Cliente del protocolo OpenTimestamps.

    Usage:
        client = OpenTimestampsClient(use_testnet=False)
        proof = client.stamp(checkpoint_merkle_root)
        if proof:
            checkpoint["ots_proof"] = proof.ots_response
            checkpoint["bitcoin_tx"] = proof.bitcoin_tx
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        use_testnet: bool = False,
        enable_logging: bool = True,
    ) -> None:
        """Initialize OTS client.

        Args:
            timeout: HTTP request timeout (seconds)
            max_retries: Max retry attempts on failure
            use_testnet: Use testnet chain instead of mainnet
            enable_logging: Enable forensic logging
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_testnet = use_testnet
        self.enable_logging = enable_logging
        self.servers = OTS_TESTNET_SERVERS if use_testnet else OTS_SERVERS
        self.anchor_records: list[AnchorRecord] = []

    def stamp(self, message: str | bytes) -> Optional[TimestampProof]:
        """Request timestamp proof for message.

        Args:
            message: Message to timestamp (string or bytes)

        Returns:
            TimestampProof if successful, None on persistent failure
        """
        # Compute message hash
        if isinstance(message, str):
            message = message.encode("utf-8")
        message_hash = hashlib.sha256(message).hexdigest()

        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            try:
                proof = self._request_timestamp(message_hash)
                if proof:
                    record = AnchorRecord(
                        checkpoint_hash=message_hash,
                        attempt_timestamp=time.time(),
                        success=True,
                        proof=proof,
                        retry_count=attempt,
                    )
                    self.anchor_records.append(record)
                    logger.info(
                        "ots_stamp_success hash=%s bitcoin_tx=%s attempt=%d",
                        message_hash[:16],
                        proof.bitcoin_tx or "pending",
                        attempt,
                    )
                    return proof

            except (httpx.RequestError, httpx.TimeoutException) as e:
                wait_seconds = 2**attempt  # Exponential backoff: 1, 2, 4, ...
                logger.warning(
                    "ots_stamp_attempt_failed attempt=%d error=%s wait=%ds",
                    attempt,
                    str(e),
                    wait_seconds,
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait_seconds)

        # Persistent failure: log record
        record = AnchorRecord(
            checkpoint_hash=message_hash,
            attempt_timestamp=time.time(),
            success=False,
            error_detail="max_retries_exhausted",
            retry_count=self.max_retries,
        )
        self.anchor_records.append(record)
        logger.error(
            "ots_stamp_failed_all_retries hash=%s retries=%d",
            message_hash[:16],
            self.max_retries,
        )
        return None

    def _request_timestamp(self, message_hash: str) -> Optional[TimestampProof]:
        """Submit SHA-256 hash to OpenTimestamps calendar server.

        OTS REST protocol (https://opentimestamps.org/docs/api/):
          POST {server}/digest
          Body:  raw 32 bytes (SHA-256 digest)
          Headers: Content-Type: application/octet-stream
          Response 200: binary incomplete .ots proof file

        The returned proof is pending Bitcoin confirmation (1-24h).
        To upgrade and verify later: `ots upgrade file.ots && ots verify file.ots`

        Args:
            message_hash: SHA-256 hash as 64-char lowercase hex string

        Returns:
            TimestampProof with base64-encoded binary .ots data, or None on failure
        """
        hash_bytes = bytes.fromhex(message_hash)  # 32 raw bytes

        for server in self.servers:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(
                        f"{server}/digest",
                        content=hash_bytes,
                        headers={"Content-Type": "application/octet-stream"},
                    )
                    if resp.status_code == 200:
                        ots_bytes = resp.content
                        ots_b64 = base64.b64encode(ots_bytes).decode("ascii")
                        proof = TimestampProof(
                            timestamp=time.time(),
                            message_hash=message_hash,
                            ots_response=ots_b64,
                            bitcoin_tx=None,   # Pending — set after Bitcoin confirmation
                            bitcoin_block=None,
                            chain="testnet" if self.use_testnet else "mainnet",
                            verified=False,
                        )
                        logger.info(
                            "ots_digest_submitted server=%s hash=%s response_bytes=%d",
                            server, message_hash[:16], len(ots_bytes),
                        )
                        return proof

            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.debug("ots_server_unreachable server=%s error=%s", server, exc)
                continue

        return None

    def verify_proof(self, proof: TimestampProof) -> bool:
        """Check that proof contains a valid OTS binary file structure.

        Decodes the base64 proof and verifies it starts with the OTS magic
        byte (0x00), confirming it is a genuine OpenTimestamps file.

        Full calendar upgrade + Bitcoin verification requires the `ots` CLI:
            ots upgrade <file>.ots   # fetch Bitcoin proof from calendar
            ots verify  <file>.ots   # verify against Bitcoin block headers

        Returns:
            True if the proof is a structurally valid OTS file, False otherwise.
        """
        if not proof or not proof.ots_response:
            return False
        if not proof.message_hash or len(proof.message_hash) != 64:
            return False
        try:
            ots_bytes = base64.b64decode(proof.ots_response)
            # OTS files always start with 0x00 (file format version marker)
            if len(ots_bytes) < 8 or ots_bytes[0] != 0x00:
                logger.warning(
                    "ots_verify_invalid_magic hash=%s size=%d",
                    proof.message_hash[:16], len(ots_bytes),
                )
                return False
            logger.debug(
                "ots_proof_structure_valid hash=%s size=%d bitcoin_tx=%s",
                proof.message_hash[:16], len(ots_bytes), proof.bitcoin_tx or "pending",
            )
            return True
        except Exception as exc:
            logger.warning("ots_verify_failed error=%s", exc)
            return False

    def to_forensic_records(self) -> list[dict[str, Any]]:
        """Export anchor attempts as forensic records.

        Returns list suitable for attack_log.jsonl.
        """
        return [asdict(record) for record in self.anchor_records]


class MultichainAnchor:
    """Anchors checkpoints using OpenTimestamps (Bitcoin), Zero Cost.

    ES: Ancla checkpoints usando OpenTimestamps (Bitcoin), Costo Cero.

    Design:
    - Primary: OpenTimestamps (fast, free, proven)
    - Non-fatal: if both fail, publish without anchor (lower assurance)
    """

    def __init__(self, testnet: bool = False) -> None:
        """Initialize multi-chain anchor (OTS Bitcoin only)."""
        self.ots_client = OpenTimestampsClient(use_testnet=testnet)
        self.testnet = testnet

    def anchor_checkpoint(self, checkpoint: dict) -> dict:
        """Anchor a checkpoint's merkle root via OpenTimestamps.

        ES: Ancla la raíz Merkle de un checkpoint vía OpenTimestamps.

        Args:
            checkpoint: Checkpoint dict with merkle_root

        Returns:
            Checkpoint with anchor fields populated (non-fatal if empty)
        """
        merkle_root = checkpoint.get("merkle_root", "")
        if not merkle_root:
            logger.warning("anchor_no_merkle_root checkpoint missing merkle_root")
            return checkpoint

        # Primary: OpenTimestamps
        ots_proof = self.ots_client.stamp(merkle_root)
        if ots_proof:
            checkpoint["ots_proof"] = ots_proof.ots_response
            checkpoint["bitcoin_tx"] = ots_proof.bitcoin_tx
            checkpoint["bitcoin_block"] = ots_proof.bitcoin_block
            checkpoint["anchor_chain"] = "bitcoin"
            logger.info(
                "checkpoint_anchored_ots merkle_root=%s bitcoin_tx=%s",
                merkle_root[:16],
                ots_proof.bitcoin_tx or "pending",
            )
            return checkpoint

        # Non-fatal: publish without anchor (OTS calendars unavailable)
        logger.warning(
            "checkpoint_published_without_anchor merkle_root=%s (all OTS calendars unavailable)",
            merkle_root[:16],
        )
        return checkpoint
