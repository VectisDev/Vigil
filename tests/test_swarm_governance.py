"""The seating is the same on every machine. Not a network test."""

from __future__ import annotations

import pytest

from vigil.swarm.governance import (
    agreed_hash,
    assign_roles,
    faulty_bound,
    join,
    leave,
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
    assert [role for _, role in left.roles] == ["member", "member", "member"]
    assert left.roles[0][0] == "n-a"
    assert left.quorum == quorum_size(3) == 3


def test_a_bad_code_seats_nobody() -> None:
    with pytest.raises(ValueError):
        assign_roles(["n-a"], "OOOOOO")


def test_a_thirteenth_member_is_refused() -> None:
    code = room_code_from_seed(b"123456")
    members = [f"n-{index:02d}" for index in range(13)]
    with pytest.raises(ValueError):
        assign_roles(members, code)


def test_twelve_need_nine_matching_hashes() -> None:
    code = room_code_from_seed(b"123456")
    seating = assign_roles([f"n-{index:02d}" for index in range(12)], code)
    assert seating.quorum == 9
    hashes = ["aa"] * 9 + ["bb"] * 3
    assert agreed_hash(hashes, seating.quorum) == "aa"
    assert agreed_hash(["aa"] * 8 + ["bb"] * 4, seating.quorum) is None


def test_one_member_is_not_a_group() -> None:
    code = room_code_from_seed(b"abcdef")
    seating = assign_roles(["solo"], code)
    assert seating.quorum == 1
    assert agreed_hash(["aa"], seating.quorum) == "aa"


def test_join_and_leave_reseat_the_same_way() -> None:
    code = room_code_from_seed(b"abcdef")
    seated = join(join([], "n-b", code).roles and ["n-b"], "n-a", code)
    again = join(["n-b"], "n-a", code)
    assert seated == again
    assert [role for _, role in seated.roles] == ["member", "member"]
    assert quorum_size(12) >= 2 * faulty_bound(12) + 1
    left = leave([name for name, _role in seated.roles], "n-b", code)
    assert [name for name, _role in left.roles] == ["n-a"]
    current: list[str] = []
    for index in range(12):
        current = [name for name, _role in join(current, f"n-{index}", code).roles]
    with pytest.raises(ValueError):
        join(current, "n-extra", code)


def test_seed_is_stable() -> None:
    assert room_code_from_seed(b"abcdef") == room_code_from_seed(b"abcdef")
