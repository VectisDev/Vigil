"""
Gossip protocol engine for Centinel P2P node network.

Each node broadcasts its signed attestation (NodePayload) to known peers
via HTTP POST. When a node receives a new attestation it fans out to 2
random peers (epidemic propagation). Peer discovery uses three zero-cost
bootstrap layers in order:
  1. GitHub Pages peer list (country-specific JSON)
  2. mDNS UDP multicast on local network
  3. Hardcoded project bootstrap seeds
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import socket
import struct
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger("centinel.federation.gossip")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_KEYS_DIR = _REPO_ROOT / "keys"

_BOOTSTRAP_URL_TEMPLATE = (
    "https://vectisdev.github.io/centinel/peers/{country}.json"
)

_HARDCODED_SEEDS: list[str] = [
    # Well-known project bootstrap nodes — add public URLs here as the network grows
]

_MDNS_ADDR = "224.0.0.251"
_MDNS_PORT = 5353
_MDNS_TIMEOUT = 3.0
_CENTINEL_MDNS_SERVICE = b"_centinel._tcp.local"

_FAN_OUT = 2
_GOSSIP_VERSION = 1


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass
class NodePayload:
    """Signed attestation broadcast by a Centinel node."""

    node_id: str           # sha256(public_key_hex)[:16]
    public_key_hex: str    # Ed25519 public key (64 hex chars)
    country_code: str      # ISO-2 country code, e.g. "HN"
    merkle_root: str       # SHA256 hex of entire snapshot chain
    chain_length: int      # Number of snapshots in chain
    timestamp_utc: str     # ISO 8601
    my_url: Optional[str]  # Public base URL if node is reachable, else None
    signature: str         # Ed25519(sha256(canonical JSON without this field))
    version: int = _GOSSIP_VERSION

    def canonical_bytes(self) -> bytes:
        """Serialise deterministically for signing/verification (excludes signature)."""
        d = asdict(self)
        d.pop("signature", None)
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "NodePayload":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ── Helpers ───────────────────────────────────────────────────────────────────


def _derive_node_id(public_key_hex: str) -> str:
    return hashlib.sha256(public_key_hex.encode()).hexdigest()[:16]


def _load_or_generate_keypair() -> tuple[str, str, Path]:
    """Return (public_key_hex, node_id, private_key_path), generating if needed."""
    from centinel.core.custody import (  # local import to avoid circular deps
        generate_operator_keypair,
        _load_operator_public_key,
    )

    private_path = _KEYS_DIR / "operator_private.pem"
    public_path = _KEYS_DIR / "operator_public.pem"

    if not private_path.exists():
        result = generate_operator_keypair(key_dir=_KEYS_DIR)
        pub_hex = result["public_key_hex"]
    else:
        pub_key = _load_operator_public_key(public_path)
        pub_hex = pub_key.public_bytes_raw().hex()

    node_id = _derive_node_id(pub_hex)
    return pub_hex, node_id, private_path


def _sign_payload(payload: NodePayload, key_path: Path) -> str:
    """Return hex Ed25519 signature over canonical bytes of payload."""
    from centinel.core.custody import sign_snapshot

    result = sign_snapshot(payload.canonical_bytes(), key_path=key_path)
    return result.signature_hex


def _verify_payload_sig(payload: NodePayload) -> bool:
    """Return True if the payload's signature is valid."""
    from centinel.core.custody import verify_snapshot_signature

    try:
        return verify_snapshot_signature(
            payload.canonical_bytes(),
            payload.signature,
            public_key_hex=payload.public_key_hex,
        )
    except Exception:
        return False


def _current_merkle_root() -> tuple[str, int]:
    """Return (merkle_root_hex, chain_length) from the local snapshot DB, or zeros."""
    try:
        import sqlite3

        db = _REPO_ROOT / "data" / "snapshots.db"
        if not db.exists():
            return "0" * 64, 0
        with sqlite3.connect(str(db)) as conn:
            row = conn.execute(
                "SELECT hash, id FROM snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not row:
                return "0" * 64, 0
            count = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
            return row[0], count
    except Exception:
        return "0" * 64, 0


# ── Bootstrap helpers ─────────────────────────────────────────────────────────


async def _bootstrap_from_github(country: str) -> list[str]:
    """Fetch peer URLs from GitHub Pages bootstrap JSON. Returns list of base URLs."""
    url = _BOOTSTRAP_URL_TEMPLATE.format(country=country.upper())
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return []
            data = r.json()
            peers = data.get("peers", [])
            return [p["url"] for p in peers if p.get("url")]
    except Exception as exc:
        logger.debug("github_bootstrap_failed url=%s error=%s", url, exc)
        return []


def _bootstrap_from_mdns() -> list[str]:
    """Discover local Centinel nodes via UDP multicast. Returns list of base URLs."""
    urls: list[str] = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(_MDNS_TIMEOUT)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Join multicast group
        group = struct.pack("4sL", socket.inet_aton(_MDNS_ADDR), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group)
        sock.bind(("", _MDNS_PORT))

        # Send a simple discovery probe: the service name as UTF-8
        sock.sendto(_CENTINEL_MDNS_SERVICE, (_MDNS_ADDR, _MDNS_PORT))

        deadline = time.monotonic() + _MDNS_TIMEOUT
        while time.monotonic() < deadline:
            try:
                data, addr = sock.recvfrom(512)
                if data.startswith(b"centinel://"):
                    url = data.decode(errors="replace").strip()
                    if url not in urls:
                        urls.append(url.replace("centinel://", "http://"))
            except socket.timeout:
                break
        sock.close()
    except Exception as exc:
        logger.debug("mdns_discovery_failed error=%s", exc)
    return urls


# ── Gossip Engine ─────────────────────────────────────────────────────────────


class GossipEngine:
    """Push-pull epidemic gossip engine.

    Each active node periodically broadcasts its own NodePayload to known
    peers. Received payloads are verified and fanned out to _FAN_OUT random
    peers, achieving O(log N) convergence.
    """

    def __init__(
        self,
        country_code: str,
        my_url: Optional[str] = None,
        broadcast_interval: float = 60.0,
        max_peers: int = 50,
    ) -> None:
        self.country_code = country_code.upper()
        self.my_url = my_url
        # Privacy mode: suppress my_url so this node's address is never broadcast
        # in gossip attestations. The node remains a full gossip participant
        # (receives/forwards payloads) but is not discoverable by URL via peers.
        if my_url and os.getenv("CENTINEL_PRIVACY_MODE", "").strip().lower() in ("1", "true", "yes"):
            logger.info("gossip_privacy_mode_active my_url_suppressed")
            self.my_url = None
        self.broadcast_interval = broadcast_interval
        self.max_peers = max_peers

        self._peers: dict[str, str] = {}   # node_id → base_url
        self._known: dict[str, NodePayload] = {}  # node_id → latest payload
        self._pub_hex: str = ""
        self._node_id: str = ""
        self._key_path: Optional[Path] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_broadcast: Optional[float] = None

    # ── lifecycle ──────────────────────────────────────────────────────────────

    async def start(self) -> None:
        if self._running:
            return
        self._pub_hex, self._node_id, self._key_path = _load_or_generate_keypair()
        logger.info("gossip_start node_id=%s country=%s", self._node_id, self.country_code)

        # Bootstrap peer discovery
        peer_urls: list[str] = []
        peer_urls.extend(await _bootstrap_from_github(self.country_code))
        peer_urls.extend(_bootstrap_from_mdns())
        peer_urls.extend(_HARDCODED_SEEDS)

        for url in peer_urls:
            await self._fetch_checkpoint(url)

        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("gossip_stop node_id=%s peers=%d", self._node_id, len(self._peers))

    # ── public API ─────────────────────────────────────────────────────────────

    async def receive_attestation(self, payload_dict: dict) -> bool:
        """Accept an incoming NodePayload from a peer HTTP POST."""
        try:
            payload = NodePayload.from_dict(payload_dict)
        except (TypeError, KeyError) as exc:
            logger.debug("gossip_recv_bad_payload error=%s", exc)
            return False

        if not _verify_payload_sig(payload):
            logger.debug("gossip_recv_invalid_sig node_id=%s", payload_dict.get("node_id"))
            return False

        node_id = payload.node_id
        existing = self._known.get(node_id)
        if existing and existing.timestamp_utc >= payload.timestamp_utc:
            return True  # Already up to date

        self._known[node_id] = payload
        if payload.my_url:
            self._peers[node_id] = payload.my_url.rstrip("/")
            if len(self._peers) > self.max_peers:
                oldest = next(iter(self._peers))
                del self._peers[oldest]

        logger.info(
            "gossip_recv_accepted node_id=%s chain=%d merkle=%.8s",
            node_id, payload.chain_length, payload.merkle_root,
        )

        # Fan-out to 2 random peers (exclude sender)
        candidates = [u for nid, u in self._peers.items() if nid != node_id]
        for url in random.sample(candidates, min(_FAN_OUT, len(candidates))):
            asyncio.create_task(self._push_payload(url, payload))

        return True

    def get_status(self) -> dict:
        peers = list(self._known.values())
        consensus_root, consensus_count = self._compute_consensus(peers)
        return {
            "running": self._running,
            "node_id": self._node_id,
            "public_key_hex": self._pub_hex,
            "my_url": self.my_url,
            "country_code": self.country_code,
            "connected_peers": len(self._known),
            "consensus_root": consensus_root,
            "consensus_count": consensus_count,
            "consensus_reached": consensus_count >= max(2, int(len(peers) * 0.75)),
            "last_broadcast_utc": (
                datetime.fromtimestamp(self._last_broadcast, tz=timezone.utc).isoformat()
                if self._last_broadcast else None
            ),
            "peers": [
                {
                    "node_id": p.node_id,
                    "country_code": p.country_code,
                    "chain_length": p.chain_length,
                    "merkle_root": p.merkle_root,
                    "timestamp_utc": p.timestamp_utc,
                    "url": p.my_url,
                }
                for p in peers
            ],
        }

    def build_my_attestation(self) -> dict:
        """Build and sign this node's current NodePayload. Used by /api/checkpoint."""
        merkle_root, chain_length = _current_merkle_root()
        payload = NodePayload(
            node_id=self._node_id,
            public_key_hex=self._pub_hex,
            country_code=self.country_code,
            merkle_root=merkle_root,
            chain_length=chain_length,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            my_url=self.my_url,
            signature="",
        )
        if self._key_path:
            payload.signature = _sign_payload(payload, self._key_path)
        return payload.to_dict()

    # ── internals ──────────────────────────────────────────────────────────────

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.broadcast_my_attestation()
            except Exception as exc:
                logger.warning("gossip_broadcast_error error=%s", exc)
            await asyncio.sleep(self.broadcast_interval)

    async def broadcast_my_attestation(self) -> int:
        if not self._node_id:
            return 0
        attestation = self.build_my_attestation()
        payload = NodePayload.from_dict(attestation)

        targets = list(self._peers.values())
        random.shuffle(targets)
        targets = targets[:10]

        acks = 0
        for url in targets:
            ok = await self._push_payload(url, payload)
            if ok:
                acks += 1

        self._last_broadcast = time.time()
        logger.info(
            "gossip_broadcast sent=%d acked=%d merkle=%.8s",
            len(targets), acks, payload.merkle_root,
        )
        return acks

    async def _push_payload(self, base_url: str, payload: NodePayload) -> bool:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.post(
                    f"{base_url}/api/swarm/attest",
                    json=payload.to_dict(),
                    headers={"Content-Type": "application/json"},
                )
                return r.status_code == 200
        except Exception as exc:
            logger.debug("gossip_push_failed url=%s error=%s", base_url, exc)
            return False

    async def _fetch_checkpoint(self, base_url: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(f"{base_url.rstrip('/')}/api/checkpoint")
                if r.status_code == 200:
                    await self.receive_attestation(r.json())
        except Exception as exc:
            logger.debug("gossip_fetch_checkpoint_failed url=%s error=%s", base_url, exc)

    @staticmethod
    def _compute_consensus(peers: list[NodePayload]) -> tuple[Optional[str], int]:
        if not peers:
            return None, 0
        counts: dict[str, int] = {}
        for p in peers:
            counts[p.merkle_root] = counts.get(p.merkle_root, 0) + 1
        best_root = max(counts, key=lambda r: counts[r])
        return best_root, counts[best_root]
