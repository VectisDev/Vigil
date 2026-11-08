"""A room label and a fixed seating for at most 12 members.

Not yet production. The same members and the same code always give the
same seating. There is no server in this module, and every seat has the
same job.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# No 0/O or 1/I, so a code can be read aloud. It is a label, not a secret.
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
MAX_MEMBERS = 12
ROLE = "member"


@dataclass(frozen=True)
class Seating:
    code: str
    roles: tuple[tuple[str, str], ...]
    quorum: int


def normalize_code(code: str) -> str:
    return code.strip().upper().replace("-", "").replace(" ", "")


def valid_room_code(code: str) -> bool:
    text = normalize_code(code)
    return len(text) == CODE_LENGTH and all(character in ALPHABET for character in text)


def room_code_from_seed(seed: bytes) -> str:
    """Turn 6 bytes into a room label. The same seed always gives the same code."""
    if len(seed) < CODE_LENGTH:
        raise ValueError("seed needs 6 bytes")
    return "".join(ALPHABET[byte % len(ALPHABET)] for byte in seed[:CODE_LENGTH])


def quorum_size(seated: int) -> int:
    """How many matching hashes are required. Two thirds, rounded up.

    Zero members means no agreement is possible. One member means that
    member's own hash, which is not a group result.
    """
    if seated < 1:
        return 0
    return (2 * seated + 2) // 3


def assign_roles(members: list[str] | tuple[str, ...], code: str) -> Seating:
    """Seat every id, or refuse. Order of the input does not matter.

    Join is adding an id. Leave is removing one. Both are a new call with
    the new list. More than 12 ids is an error, not a silent cut.
    """
    if not valid_room_code(code):
        raise ValueError("room code is not valid")
    clean: list[str] = []
    seen: set[str] = set()
    for raw in members:
        name = str(raw).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        clean.append(name)
    if len(clean) > MAX_MEMBERS:
        raise ValueError("at most 12 members")
    ordered = tuple(sorted(clean))
    roles = tuple((member, ROLE) for member in ordered)
    return Seating(
        code=normalize_code(code),
        roles=roles,
        quorum=quorum_size(len(ordered)),
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
