"""Room codes and a fixed seating for at most 12 members.

Not yet production. Every caller with the same members and the same code
gets the same seating. There is no server in this module.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# No 0/O or 1/I, so a code can be read aloud.
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
MAX_MEMBERS = 12

# Slot i in the sorted member list gets this job. The list is the rule.
ROLE_TABLE = (
    "host",
    "witness",
    "witness",
    "witness",
    "archivist",
    "archivist",
    "checker",
    "checker",
    "checker",
    "checker",
    "reserve",
    "reserve",
)


@dataclass(frozen=True)
class Seating:
    code: str
    roles: tuple[tuple[str, str], ...]
    waiting: tuple[str, ...]
    quorum: int


def normalize_code(code: str) -> str:
    return code.strip().upper().replace("-", "").replace(" ", "")


def valid_room_code(code: str) -> bool:
    text = normalize_code(code)
    return len(text) == CODE_LENGTH and all(ch in ALPHABET for ch in text)


def room_code_from_seed(seed: bytes) -> str:
    """Turn 6 bytes into a room code. The same seed always gives the same code."""
    if len(seed) < CODE_LENGTH:
        raise ValueError("seed needs 6 bytes")
    return "".join(ALPHABET[byte % len(ALPHABET)] for byte in seed[:CODE_LENGTH])


def quorum_size(seated: int) -> int:
    """How many matching hashes are required. Two thirds, rounded up."""
    if seated < 1:
        return 1
    return (2 * seated + 2) // 3


def assign_roles(members: list[str] | tuple[str, ...], code: str) -> Seating:
    """Seat up to 12 members. Order of the input does not matter."""
    if not valid_room_code(code):
        raise ValueError("room code is not valid")
    clean = []
    seen = set()
    for raw in members:
        name = str(raw).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        clean.append(name)
    ordered = tuple(sorted(clean))
    seated = ordered[:MAX_MEMBERS]
    waiting = ordered[MAX_MEMBERS:]
    roles = tuple((member, ROLE_TABLE[index]) for index, member in enumerate(seated))
    return Seating(
        code=normalize_code(code),
        roles=roles,
        waiting=waiting,
        quorum=quorum_size(len(seated)),
    )


def agreed_hash(hashes: list[str] | tuple[str, ...], k: int) -> str | None:
    """Return the hash that appears at least k times, or None."""
    if k < 1:
        raise ValueError("quorum must be at least 1")
    counts = Counter(item.strip() for item in hashes if str(item).strip())
    if not counts:
        return None
    best, count = counts.most_common(1)[0]
    if count >= k:
        return best
    return None
