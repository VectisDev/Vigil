"""The seating is the same on every machine. Not a network test."""

from __future__ import annotations

import pytest

from vigil.swarm.governance import (
    MAX_MEMBERS,
    agreed_hash,
    assign_roles,
    quorum_size,
    room_code_from_seed,
    valid_room_code,
)


def test_same_members_and_code_always_seat_the_same_way() -> None:
    code = room_code_from_seed(b"abcdef")
    assert valid_room_code(code)
    left = assign_roles(["n-b", "n-a", "n-c"], code)
    right = assign_roles(["n-c", "n-a", "n-b"], code)
    assert left == right
    assert left.roles[0] == ("n-a", "host")
    assert left.roles[1][1] == "witness"
    assert left.quorum == quorum_size(3)


def test_a_bad_code_seats_nobody() -> None:
    with pytest.raises(ValueError):
        assign_roles(["n-a"], "OOOOOO")


def test_only_twelve_are_seated() -> None:
    code = room_code_from_seed(b"123456")
    members = [f"n-{index:02d}" for index in range(15)]
    seating = assign_roles(members, code)
    assert len(seating.roles) == MAX_MEMBERS
    assert len(seating.waiting) == 3
    assert seating.quorum == 8


def test_eight_matching_hashes_agree_and_seven_do_not() -> None:
    hashes = ["aa"] * 8 + ["bb"] * 4
    assert agreed_hash(hashes, 8) == "aa"
    assert agreed_hash(["aa"] * 7 + ["bb"] * 5, 8) is None


def test_seed_is_stable() -> None:
    assert room_code_from_seed(b"abcdef") == room_code_from_seed(b"abcdef")
