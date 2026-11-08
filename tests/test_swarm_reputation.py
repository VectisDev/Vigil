"""Reputation is an integer from hashes, not a story."""

from __future__ import annotations

import pytest

from vigil.swarm.reputation import aggregate, fact_for, reputation


def test_the_same_facts_in_any_order_score_the_same() -> None:
    left = reputation([("match", 0), ("conflict", 1), ("missing", 2)])
    right = reputation([("missing", 2), ("match", 0), ("conflict", 1)])
    assert left == right
    # 8 + (-4) + (-1) = 3
    assert left == 3


def test_old_facts_expire_and_a_new_key_starts_at_zero() -> None:
    assert reputation([]) == 0
    assert reputation([("match", 0)]) == 8
    assert reputation([("match", 1)]) == 4
    assert reputation([("conflict", 0)]) == -8
    assert reputation([("match", 4)]) == 0
    assert reputation([("late", 0), ("missing", 0)]) == -8


def test_facts_come_from_the_agreed_hash() -> None:
    assert fact_for("aa", "aa", True) == "match"
    assert fact_for("aa", "aa", False) == "late"
    assert fact_for("bb", "aa", True) == "conflict"
    assert fact_for(None, "aa", True) == "missing"
    assert fact_for("  ", "aa", True) == "missing"


def test_unknown_fact_is_refused() -> None:
    with pytest.raises(ValueError):
        reputation([("nice", 0)])


def test_one_room_shares_counts_not_identities() -> None:
    record = aggregate("cne-hn", "2025-12-04T15", "aa", 8, 12, 9)
    assert record == {
        "source": "cne-hn",
        "window": "2025-12-04T15",
        "hash": "aa",
        "k": 8,
        "n": 12,
        "matched": 9,
    }
    assert "node" not in record
    assert "score" not in record
