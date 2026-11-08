"""Confirm a snapshot hash, or refuse. Not yet production.

A room of n keys, n at most 12, tolerates f = floor((n-1)/3) faulty keys.
A hash is confirmed only by at least n-f distinct seated keys signing it
for the same source and window. For 12 keys that number is 9.
Reputation is not an input.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from vigil.swarm.governance import MAX_MEMBERS, quorum_size


@dataclass(frozen=True)
class Attestation:
    node_id: str
    source: str
    window: str
    digest: str


def equivocating_nodes(
    attestations: Sequence[Attestation],
    source: str,
    window: str,
) -> tuple[str, ...]:
    """Keys that signed two different hashes for one source and window."""
    seen: dict[str, set[str]] = {}
    for item in attestations:
        if item.source != source or item.window != window:
            continue
        digest = item.digest.strip()
        if not digest:
            continue
        seen.setdefault(item.node_id, set()).add(digest)
    return tuple(sorted(node for node, digests in seen.items() if len(digests) > 1))


def confirm(
    attestations: Sequence[Attestation],
    members: Sequence[str],
    source: str,
    window: str,
) -> str | None:
    """Return the confirmed digest, or None.

    A repeated file from the same key counts once. A key that signed two
    hashes counts for neither. A key outside the member list counts for
    neither. Another window does not count.
    """
    seated = tuple(dict.fromkeys(member.strip() for member in members if member.strip()))
    if not seated or len(seated) > MAX_MEMBERS:
        raise ValueError("room size must be from 1 to 12")
    allowed = set(seated)
    bad = set(equivocating_nodes(attestations, source, window))
    votes: dict[str, set[str]] = {}
    for item in attestations:
        if item.source != source or item.window != window:
            continue
        if item.node_id not in allowed or item.node_id in bad:
            continue
        digest = item.digest.strip()
        if not digest:
            continue
        votes.setdefault(digest, set()).add(item.node_id)
    need = quorum_size(len(seated))
    winners = [digest for digest, nodes in votes.items() if len(nodes) >= need]
    if len(winners) == 1:
        return winners[0]
    return None
