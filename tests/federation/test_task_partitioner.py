"""Unit tests for the deterministic task partitioner."""

import pytest

from vigil.federation.task_partitioner import TaskPartitioner, HN_SOURCES


TOTAL_SOURCES = len(HN_SOURCES)  # 19


def make_nodes(n: int) -> list[tuple[str, int]]:
    return [(f"node_{i:02d}", i) for i in range(n)]


# ── Basic assignment ──────────────────────────────────────────────────────────


def test_single_node_gets_all_sources():
    tp = TaskPartitioner()
    slices = tp.assign(make_nodes(1))
    assert len(slices) == 1
    assert set(slices[0].sources) == set(HN_SOURCES)


def test_two_nodes_cover_all_sources():
    tp = TaskPartitioner()
    slices = tp.assign(make_nodes(2))
    all_assigned = set()
    for s in slices:
        all_assigned.update(s.sources)
    assert all_assigned == set(HN_SOURCES)


def test_no_source_assigned_twice():
    for n in range(2, 13):
        tp = TaskPartitioner()
        slices = tp.assign(make_nodes(n))
        all_sources = [s for sl in slices for s in sl.sources]
        assert len(all_sources) == len(set(all_sources)), f"N={n}: duplicate sources"


def test_all_sources_assigned_for_every_n():
    for n in range(1, 13):
        tp = TaskPartitioner()
        slices = tp.assign(make_nodes(n))
        assigned = set(s for sl in slices for s in sl.sources)
        assert assigned == set(HN_SOURCES), f"N={n}: missing sources"


# ── Odd node counts ───────────────────────────────────────────────────────────


def test_n3_load_distribution():
    """With 19 sources and 3 nodes: node-0 gets 7, nodes 1 and 2 get 6."""
    tp = TaskPartitioner()
    slices = tp.assign(make_nodes(3))
    counts = sorted([len(s.sources) for s in slices], reverse=True)
    assert counts == [7, 6, 6]


def test_n5_load_distribution():
    """With 19 sources and 5 nodes: 4 nodes get 4, 1 node gets 3."""
    tp = TaskPartitioner()
    slices = tp.assign(make_nodes(5))
    counts = sorted([len(s.sources) for s in slices], reverse=True)
    assert counts == [4, 4, 4, 4, 3]


def test_n7_load_distribution():
    """With 19 sources and 7 nodes: 5 get 3, 2 get 2."""
    tp = TaskPartitioner()
    slices = tp.assign(make_nodes(7))
    counts = sorted([len(s.sources) for s in slices], reverse=True)
    assert counts == [3, 3, 3, 3, 3, 2, 2]


def test_n12_load_distribution():
    """With 19 sources and 12 nodes: 7 get 2, 5 get 1."""
    tp = TaskPartitioner()
    slices = tp.assign(make_nodes(12))
    counts = sorted([len(s.sources) for s in slices], reverse=True)
    assert counts == [2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1]


# ── Determinism ───────────────────────────────────────────────────────────────


def test_same_input_same_output():
    nodes = make_nodes(6)
    tp = TaskPartitioner()
    result_a = tp.assign(nodes)
    result_b = tp.assign(nodes)
    assert [(s.node_id, s.sources) for s in result_a] == [(s.node_id, s.sources) for s in result_b]


def test_assignment_stable_across_instances():
    nodes = make_nodes(6)
    result_a = TaskPartitioner().assign(nodes)
    result_b = TaskPartitioner().assign(nodes)
    assert [(s.node_id, s.sources) for s in result_a] == [(s.node_id, s.sources) for s in result_b]


# ── Node failure coverage ─────────────────────────────────────────────────────


def test_survivor_covers_all_when_node_drops():
    """When a node drops, survivors cover orphaned sources (no coordination needed)."""
    tp = TaskPartitioner()

    full = tp.assign(make_nodes(3))
    # Simulate node_01 dropping — reassign with 2 survivors
    survivors = [n for n in make_nodes(3) if n[0] != "node_01"]
    reduced = tp.assign(survivors)

    assigned = set(s for sl in reduced for s in sl.sources)
    assert assigned == set(HN_SOURCES)


def test_empty_nodes_returns_empty():
    tp = TaskPartitioner()
    slices = tp.assign([])
    assert slices == []


# ── Custom sources ────────────────────────────────────────────────────────────


def test_custom_sources():
    sources = ("A", "B", "C", "D", "E")
    tp = TaskPartitioner(sources=sources)
    slices = tp.assign(make_nodes(2))
    assigned = set(s for sl in slices for s in sl.sources)
    assert assigned == set(sources)


def test_assignment_summary_matches_assign():
    tp = TaskPartitioner()
    nodes = make_nodes(4)
    slices = tp.assign(nodes)
    summary = tp.assignment_summary(nodes)

    slice_map = {s.node_id: set(s.sources) for s in slices}
    for item in summary:
        assert set(item["sources"]) == slice_map[item["node_id"]]
