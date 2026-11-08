"""Quorum math and equivocation. Not a network test."""

from __future__ import annotations

from vigil.swarm.bft import Attestation, confirm, equivocating_nodes
from vigil.swarm.governance import faulty_bound, quorum_size
from vigil.swarm.reputation import vote_weight


def _keys(count: int) -> list[str]:
    return [f"k{index}" for index in range(count)]


def _sign(node: str, digest: str, window: str = "t") -> Attestation:
    return Attestation(node, "src", window, digest)


def test_twelve_nodes_tolerate_three_and_need_nine() -> None:
    assert faulty_bound(12) == 3
    assert quorum_size(12) == 9
    assert quorum_size(12) >= 2 * faulty_bound(12) + 1
    assert faulty_bound(4) == 1
    assert quorum_size(4) == 3
    assert faulty_bound(1) == 0
    assert quorum_size(1) == 1


def test_nine_confirm_and_eight_do_not() -> None:
    members = _keys(12)
    nine = [_sign(f"k{index}", "aa") for index in range(9)]
    eight = [_sign(f"k{index}", "aa") for index in range(8)]
    assert confirm(nine, members, "src", "t") == "aa"
    assert confirm(eight, members, "src", "t") is None


def test_a_high_score_does_not_replace_a_signature() -> None:
    members = _keys(12)
    eight = [_sign(f"k{index}", "aa") for index in range(8)]
    assert vote_weight(10_000) == 1
    assert confirm(eight, members, "src", "t") is None


def test_duplicates_count_once() -> None:
    members = _keys(12)
    flood = [_sign("k0", "aa") for _ in range(30)]
    flood += [_sign(f"k{index}", "aa") for index in range(1, 9)]
    assert confirm(flood, members, "src", "t") == "aa"
    short = [_sign("k0", "aa") for _ in range(30)]
    short += [_sign(f"k{index}", "aa") for index in range(1, 8)]
    assert confirm(short, members, "src", "t") is None


def test_equivocation_removes_that_key_from_both_hashes() -> None:
    members = _keys(12)
    signed = [_sign(f"k{index}", "aa") for index in range(9)]
    signed.append(_sign("k8", "bb"))
    assert equivocating_nodes(signed, "src", "t") == ("k8",)
    assert confirm(signed, members, "src", "t") is None


def test_another_window_is_not_this_round() -> None:
    members = _keys(12)
    old = [_sign(f"k{index}", "aa", window="yesterday") for index in range(12)]
    assert confirm(old, members, "src", "t") is None


def test_a_key_outside_the_room_does_not_count() -> None:
    members = _keys(12)
    signed = [_sign(f"k{index}", "aa") for index in range(8)]
    signed += [_sign(f"outsider{index}", "aa") for index in range(5)]
    assert confirm(signed, members, "src", "t") is None
