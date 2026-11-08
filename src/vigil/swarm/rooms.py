"""Room codes for the HTTP swarm API.

A code is generated here. Callers do not choose it. It expires.
Presenting a code does not make a peer trusted. Trust is a quorum
of signed attestations, and reputation only affects the next room.
"""

from __future__ import annotations

import secrets

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 12
TTL_SECONDS = 24 * 60 * 60


def generate_room_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def expiry(now: float, ttl: float = TTL_SECONDS) -> float:
    return float(now) + float(ttl)


def is_current(expires_at: float, now: float) -> bool:
    return float(now) < float(expires_at)


def code_grants_trust() -> bool:
    """A room code never grants trust by itself."""
    return False
