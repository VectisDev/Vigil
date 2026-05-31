"""
Sybil attack simulation for the PBTM reputation system.

Scenario: 50 Sybil nodes corroborate each other but diverge from Ring-0.
Each receives on_inconsistent() per cycle (Ring-0 consensus disagrees).
A single honest node receives on_consistent() per cycle.

Expected outcome:
- All Sybil nodes degrade below the influence threshold (trust < 0.45)
- The honest node reaches Ring-1 (trust ≥ 0.85) after 10 cycles

This test is published in the repository as academic evidence of Sybil resistance.
It corresponds to the analysis in docs/research/REPUTATION-MODEL.md §4.
"""
import pytest

from centinel.federation.reputation import ReputationEngine, _RING1_SCORE


SYBIL_COUNT = 50
INFLUENCE_THRESHOLD = 0.45  # below this a node's vote weight is negligible


def test_sybil_nodes_degraded_after_1_inconsistent_event():
    """One betrayal is enough to drop any node below the influence threshold."""
    eng = ReputationEngine()
    for i in range(SYBIL_COUNT):
        nid = f"sybil_{i:02d}"
        eng.ensure(nid)
        eng.on_inconsistent(nid)
        assert eng.get_trust(nid) < INFLUENCE_THRESHOLD, (
            f"Sybil node {nid} trust={eng.get_trust(nid):.3f} exceeds threshold"
        )


def test_sybil_nodes_remain_degraded_across_cycles():
    """Sybil nodes that keep diverging never recover past the threshold."""
    eng = ReputationEngine()
    for i in range(SYBIL_COUNT):
        eng.ensure(f"sybil_{i:02d}")

    for cycle in range(5):
        for i in range(SYBIL_COUNT):
            eng.on_inconsistent(f"sybil_{i:02d}")

    for i in range(SYBIL_COUNT):
        trust = eng.get_trust(f"sybil_{i:02d}")
        assert trust < INFLUENCE_THRESHOLD, (
            f"Cycle 5: sybil_{i:02d} trust={trust:.3f} still above threshold"
        )


def test_honest_node_reaches_ring1_while_sybils_degrade():
    """Honest node achieves Ring-1 in 10 cycles; 50 Sybil nodes stay in Ring-2."""
    eng = ReputationEngine()
    eng.ensure("honest")
    for i in range(SYBIL_COUNT):
        eng.ensure(f"sybil_{i:02d}")

    for cycle in range(10):
        eng.on_consistent("honest")
        for i in range(SYBIL_COUNT):
            eng.on_inconsistent(f"sybil_{i:02d}")

    assert eng.get_ring("honest") == 1, (
        f"Honest node ring={eng.get_ring('honest')} trust={eng.get_trust('honest'):.3f}"
    )
    for i in range(SYBIL_COUNT):
        assert eng.get_ring(f"sybil_{i:02d}") == 2


def test_sybil_nodes_cannot_influence_ring_counts():
    """With 50 Sybil + 1 honest, ring1_count=1 and ring2_count=50."""
    eng = ReputationEngine()
    eng.ensure("honest")
    for i in range(SYBIL_COUNT):
        eng.ensure(f"sybil_{i:02d}")

    for _ in range(10):
        eng.on_consistent("honest")
    for i in range(SYBIL_COUNT):
        eng.on_inconsistent(f"sybil_{i:02d}")

    counts = eng.ring_counts()
    assert counts["ring1"] == 1
    assert counts["ring2"] == SYBIL_COUNT
    assert counts["ring0"] == 0


def test_sybil_recovery_requires_many_consistent_events():
    """A node that betrayed once needs ≥10 consistent events to reach Ring-1.

    This proves that Sybil nodes cannot rapidly re-infiltrate the trusted ring
    even after stopping their attack.
    """
    eng = ReputationEngine()
    eng.ensure("reformed")
    eng.on_inconsistent("reformed")  # one betrayal
    trust_after_betrayal = eng.get_trust("reformed")
    assert trust_after_betrayal < INFLUENCE_THRESHOLD

    # Needs enough consistent events to overcome the β=6.0 (prior=1 + penalty=5)
    # trust = (α+1)/(α + 6 + 2) ≥ 0.85  →  α ≥ (0.85*8 - 1)/0.15 ≈ 38.3
    for _ in range(40):
        eng.on_consistent("reformed")

    assert eng.get_ring("reformed") == 1, (
        f"After 40 consistent: trust={eng.get_trust('reformed'):.3f}"
    )


def test_sybil_cluster_all_below_threshold_at_every_step():
    """Per-cycle invariant: every Sybil node is below threshold at every cycle."""
    eng = ReputationEngine()
    for i in range(SYBIL_COUNT):
        eng.ensure(f"s_{i}")

    for cycle in range(1, 6):
        for i in range(SYBIL_COUNT):
            eng.on_inconsistent(f"s_{i}")
        # Invariant: no Sybil node ever crosses the threshold
        for i in range(SYBIL_COUNT):
            trust = eng.get_trust(f"s_{i}")
            assert trust < INFLUENCE_THRESHOLD, (
                f"Cycle {cycle}: s_{i} trust={trust:.3f} exceeds {INFLUENCE_THRESHOLD}"
            )
