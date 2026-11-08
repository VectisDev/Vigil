"""A plain status for one public item. Not yet production.

Green means enough copies match. Yellow means not enough yet.
Red means the copies disagree. The words do not mention the count.
"""

from __future__ import annotations

from collections.abc import Sequence

from vigil.swarm.bft import Attestation, confirm, equivocating_nodes

SENTENCE = {
    "green": "The copies match.",
    "yellow": "Not enough matching copies yet.",
    "red": "The copies disagree.",
}


def traffic_light(
    attestations: Sequence[Attestation],
    members: Sequence[str],
    source: str,
    window: str,
) -> str:
    """Return green, yellow, or red. An empty room is yellow."""
    seated = [member.strip() for member in members if member.strip()]
    if not seated:
        return "yellow"
    if confirm(attestations, seated, source, window):
        return "green"
    if equivocating_nodes(attestations, source, window):
        return "red"
    allowed = set(seated)
    digests = {
        item.digest.strip()
        for item in attestations
        if item.source == source and item.window == window and item.node_id in allowed and item.digest.strip()
    }
    if len(digests) > 1:
        return "red"
    return "yellow"
