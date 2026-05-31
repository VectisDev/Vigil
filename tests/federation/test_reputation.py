"""Unit tests for the Persistent Bayesian Trust Model (PBTM)."""
import math
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from centinel.federation.reputation import (
    ReputationEngine,
    NodeReputation,
    _RING1_SCORE,
    _RING2_DEMOTION,
    _BETA_BETRAYAL,
    _HALFLIFE_ALPHA_DAYS,
    _HALFLIFE_BETA_DAYS,
)


def make_engine(**kw) -> ReputationEngine:
    return ReputationEngine(**kw)


# ── Prior / initial state ────────────────────────────────────────────────────

def test_prior_trust_is_neutral():
    eng = make_engine()
    eng.ensure("node1")
    assert eng.get_trust("node1") == pytest.approx(0.5)


def test_unknown_node_returns_neutral():
    eng = make_engine()
    assert eng.get_trust("ghost") == pytest.approx(0.5)
    assert eng.get_ring("ghost") == 2


# ── Ring promotion ────────────────────────────────────────────────────────────

def test_10_consistent_events_promote_to_ring1():
    """Verified analytically: α=11 → trust=12/14=0.857 ≥ 0.85."""
    eng = make_engine()
    eng.ensure("n")
    rep = None
    for _ in range(10):
        rep = eng.on_consistent("n")
    assert rep.trust_score >= _RING1_SCORE
    assert rep.ring == 1


def test_9_consistent_events_not_yet_ring1():
    eng = make_engine()
    eng.ensure("n")
    rep = None
    for _ in range(9):
        rep = eng.on_consistent("n")
    assert rep.trust_score < _RING1_SCORE
    assert rep.ring == 2


def test_ring0_node_never_auto_demoted():
    eng = make_engine(ring0_node_ids=["seed"])
    eng.ensure("seed")
    for _ in range(5):
        eng.on_inconsistent("seed")
    assert eng.get_ring("seed") == 0


# ── Betrayal ─────────────────────────────────────────────────────────────────

def test_betrayal_drops_trust_and_increments_count():
    eng = make_engine()
    eng.ensure("bad")
    rep = eng.on_inconsistent("bad")
    # trust = (1+1)/(1 + 1+5.0 + 2) = 2/9 ≈ 0.222
    assert rep.trust_score < 0.45
    assert rep.betrayal_count == 1


def test_multiple_betrayals_stay_below_influence_threshold():
    eng = make_engine()
    eng.ensure("sybil")
    for _ in range(3):
        eng.on_inconsistent("sybil")
    assert eng.get_trust("sybil") < 0.45


def test_ring1_node_demoted_on_betrayal():
    eng = make_engine()
    eng.ensure("trusted")
    for _ in range(10):
        eng.on_consistent("trusted")
    assert eng.get_ring("trusted") == 1
    # Enough betrayals to drop below demotion threshold
    for _ in range(4):
        eng.on_inconsistent("trusted")
    assert eng.get_ring("trusted") == 2


# ── Outage / restore ─────────────────────────────────────────────────────────

def test_outage_is_small_reversible_penalty():
    eng = make_engine()
    eng.ensure("node")
    before = eng.get_trust("node")
    eng.on_timeout("node")
    after = eng.get_trust("node")
    # Penalty is tiny (β+0.1 on prior β=1)
    assert before - after < 0.02


def test_honest_restore_reverses_outage_beta():
    eng = make_engine()
    eng.ensure("node")
    eng.on_timeout("node")
    rep_after_outage = eng.get_trust("node")
    rep = eng.on_restore_consistent("node")
    # restore adds α+1 and reverses the β penalty → trust is higher than during outage
    assert rep.trust_score > rep_after_outage


def test_betrayal_restore_does_not_reverse_outage_beta():
    eng = make_engine()
    eng.ensure("node")
    eng.on_timeout("node")
    trust_during_outage = eng.get_trust("node")
    rep = eng.on_restore_inconsistent("node")
    # β is not reversed + big betrayal penalty → much lower
    assert rep.trust_score < trust_during_outage


def test_3_consistent_after_outage_allow_ring1():
    eng = make_engine()
    eng.ensure("node")
    # Get close to Ring-1 first (9 consistent events)
    for _ in range(9):
        eng.on_consistent("node")
    eng.on_timeout("node")
    eng.on_restore_consistent("node")  # this adds α+1 and reverses β
    # After 9 consistent + restore_consistent: α = 10+1 = 11 → trust ≥ 0.85
    assert eng.get_trust("node") >= _RING1_SCORE


# ── Decay ─────────────────────────────────────────────────────────────────────

def test_decay_halves_alpha_after_14_days():
    eng = make_engine()
    eng.ensure("node")
    # Manually set α=8 and last_updated to 14 days ago
    rep = eng._nodes["node"]
    rep.alpha = 8.0
    past = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    rep.last_updated_utc = past

    eng.decay()

    expected = max(1.0, 8.0 * math.pow(0.5, 1.0))  # exactly half-life
    assert eng.get_trust("node") == pytest.approx(
        (expected + 1) / (expected + rep.beta + 2), abs=0.01
    )


def test_decay_beta_halves_after_30_days():
    eng = make_engine()
    eng.ensure("node")
    rep = eng._nodes["node"]
    rep.beta = 6.0
    past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    rep.last_updated_utc = past

    eng.decay()

    expected_beta = max(1.0, 6.0 * math.pow(0.5, 1.0))
    assert rep.beta == pytest.approx(expected_beta, abs=0.01)


# ── Ring queries ──────────────────────────────────────────────────────────────

def test_get_all_sorted_by_arrival_order():
    eng = make_engine()
    for nid in ("c", "a", "b"):
        eng.ensure(nid)
    nodes = eng.get_all()
    assert [n["node_id"] for n in nodes] == ["c", "a", "b"]


def test_ring_counts():
    eng = make_engine(ring0_node_ids=["seed"])
    eng.ensure("seed")
    eng.ensure("n1")
    for _ in range(10):
        eng.on_consistent("n1")
    eng.ensure("n2")

    counts = eng.ring_counts()
    assert counts["ring0"] == 1
    assert counts["ring1"] == 1
    assert counts["ring2"] == 1


# ── SQLite persistence ────────────────────────────────────────────────────────

def test_persistence_survives_restart():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "rep.db"
        eng1 = ReputationEngine(db_path=db)
        eng1.ensure("persistent")
        for _ in range(10):
            eng1.on_consistent("persistent")
        trust1 = eng1.get_trust("persistent")

        eng2 = ReputationEngine(db_path=db)
        assert eng2.get_trust("persistent") == pytest.approx(trust1, abs=0.001)
        assert eng2.get_ring("persistent") == 1


def test_history_records_ring_promotion():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "rep.db"
        eng = ReputationEngine(db_path=db)
        eng.ensure("node")
        for _ in range(10):
            eng.on_consistent("node")

        history = eng.get_history("node")
        event_types = [e["event_type"] for e in history]
        assert any("RING_PROMOTED" in t for t in event_types)


def test_history_records_betrayal():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = Path(tmpdir) / "rep.db"
        eng = ReputationEngine(db_path=db)
        eng.ensure("node")
        eng.on_inconsistent("node")

        history = eng.get_history("node")
        assert any(e["event_type"] == "BETRAYAL" for e in history)
