"""Reputation from signed hashes. Not yet production.

The score uses only four facts: the signed hash matched the room, it
matched but arrived late, it was missing, or it conflicted. The same
facts always give the same integer. Older facts count for less.
"""

from __future__ import annotations

from collections.abc import Sequence

# Full weight at age 0. Each older window halves the points, toward zero.
# Age 4 and older counts as nothing.
_MATCH = 8
_LATE = -4
_MISSING = -4
_CONFLICT = -8
_POINTS = {
    "match": _MATCH,
    "late": _LATE,
    "missing": _MISSING,
    "conflict": _CONFLICT,
}
_MAX_AGE = 4


def _halve_toward_zero(value: int, times: int) -> int:
    for _ in range(times):
        if value < 0:
            value = -((-value) // 2)
        else:
            value = value // 2
    return value


def fact_for(published_hash: str | None, agreed: str, in_window: bool) -> str:
    """Classify one signed hash against the hash the room already agreed.

    ``agreed`` comes from ``agreed_hash`` (k of n). This function does not
    decide that the signature was valid. The caller does that first.
    """
    if not agreed.strip():
        raise ValueError("agreed hash is empty")
    published = (published_hash or "").strip()
    if not published:
        return "missing"
    if published != agreed.strip():
        return "conflict"
    if in_window:
        return "match"
    return "late"


def reputation(events: Sequence[tuple[str, int]]) -> int:
    """Sum decayed points. Order does not matter. No events means 0.

    Each event is ``(fact, age)`` where age is how many windows ago it
    happened. A new key has an empty list and therefore score 0. It does
    not inherit anyone else's score.
    """
    total = 0
    for fact, age in events:
        if fact not in _POINTS:
            raise ValueError("unknown fact")
        if age < 0:
            raise ValueError("age is negative")
        if age >= _MAX_AGE:
            continue
        total += _halve_toward_zero(_POINTS[fact], age)
    return total


def aggregate(source: str, window: str, agreed: str, k: int, n: int, matched: int) -> dict[str, str | int]:
    """The only record one room hands another room.

    Counts and the agreed hash. No node id, no score, no story.
    """
    if k < 1 or n < 1 or matched < 0 or matched > n or k > n:
        raise ValueError("bad counts")
    if not source.strip() or not window.strip() or not agreed.strip():
        raise ValueError("source, window, and hash are required")
    return {
        "source": source.strip(),
        "window": window.strip(),
        "hash": agreed.strip(),
        "k": k,
        "n": n,
        "matched": matched,
    }
