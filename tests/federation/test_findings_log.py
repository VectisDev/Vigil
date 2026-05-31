"""Unit tests for FederationAnomalyLog and FederationAttackLog."""
import pytest

from centinel.federation.findings_log import FederationAnomalyLog
from centinel.federation.attack_log import FederationAttackLog


def _finding(fid="f001", node="n1", severity="HIGH", ftype="anomaly", rule="benford"):
    """Create a minimal FindingPayload-like object via the gossip dataclass."""
    from centinel.federation.gossip import FindingPayload
    return FindingPayload(
        finding_id=fid,
        node_id=node,
        country_code="HN",
        finding_type=ftype,
        severity=severity,
        rule_key=rule,
        summary="test finding",
        snapshot_id="snap_001",
        timestamp_utc="2025-12-08T14:00:00+00:00",
        signature="",
    )


# ── FederationAnomalyLog ──────────────────────────────────────────────────────

def test_add_returns_true_for_new_finding():
    log = FederationAnomalyLog()
    assert log.add(_finding()) is True


def test_add_returns_false_for_duplicate():
    log = FederationAnomalyLog()
    f = _finding()
    log.add(f)
    assert log.add(f) is False


def test_rejects_low_severity():
    log = FederationAnomalyLog()
    assert log.add(_finding(severity="LOW")) is False
    assert log.add(_finding(severity="MEDIUM")) is False


def test_rejects_unknown_finding_type():
    log = FederationAnomalyLog()
    assert log.add(_finding(ftype="source_throttle")) is False
    assert log.add(_finding(ftype="unknown")) is False


def test_accepts_high_and_critical():
    log = FederationAnomalyLog()
    assert log.add(_finding(severity="HIGH")) is True
    assert log.add(_finding(fid="f002", severity="CRITICAL")) is True


def test_query_returns_added_findings():
    log = FederationAnomalyLog()
    log.add(_finding(fid="f001", node="n1"))
    log.add(_finding(fid="f002", node="n2"))
    results = log.query(limit=10)
    assert len(results) == 2


def test_query_filters_by_node_id():
    log = FederationAnomalyLog()
    log.add(_finding(fid="f001", node="n1"))
    log.add(_finding(fid="f002", node="n2"))
    results = log.query(node_id="n1")
    assert len(results) == 1
    assert results[0]["node_id"] == "n1"


def test_query_filters_by_severity():
    log = FederationAnomalyLog()
    log.add(_finding(fid="f001", severity="HIGH"))
    log.add(_finding(fid="f002", severity="CRITICAL"))
    results = log.query(severity="CRITICAL")
    assert len(results) == 1
    assert results[0]["severity"] == "CRITICAL"


def test_query_filters_by_rule_key():
    log = FederationAnomalyLog()
    log.add(_finding(fid="f001", rule="benford"))
    log.add(_finding(fid="f002", rule="zscore"))
    results = log.query(rule_key="benford")
    assert len(results) == 1


def test_stats_returns_count():
    log = FederationAnomalyLog()
    log.add(_finding(fid="f001"))
    log.add(_finding(fid="f002"))
    stats = log.stats()
    assert stats["total"] >= 2


def test_eviction_respects_max_capacity():
    log = FederationAnomalyLog(max_findings=3)
    for i in range(5):
        log.add(_finding(fid=f"f{i:03d}"))
    results = log.query(limit=100)
    assert len(results) <= 3


def test_eviction_keeps_newest():
    from centinel.federation.gossip import FindingPayload

    def _ts_finding(fid, ts):
        return FindingPayload(
            finding_id=fid, node_id="n1", country_code="HN",
            finding_type="anomaly", severity="HIGH", rule_key="benford",
            summary="test", snapshot_id="snap", timestamp_utc=ts, signature="",
        )

    log = FederationAnomalyLog(max_findings=2)
    log.add(_ts_finding("old",    "2025-12-08T10:00:00+00:00"))
    log.add(_ts_finding("newer",  "2025-12-08T11:00:00+00:00"))
    log.add(_ts_finding("newest", "2025-12-08T12:00:00+00:00"))
    results = log.query(limit=100)
    ids = {r["finding_id"] for r in results}
    assert "old" not in ids
    assert "newest" in ids


def test_consensus_summary_requires_min_nodes():
    log = FederationAnomalyLog()
    log.add(_finding(fid="f001", node="n1", rule="benford"))
    log.add(_finding(fid="f002", node="n2", rule="benford"))
    log.add(_finding(fid="f003", node="n3", rule="benford"))

    # Needs min 2 nodes
    results = log.get_consensus_summary(min_nodes=2)
    assert len(results) >= 1

    # Needs min 4 nodes (we only have 3 distinct) — should be empty
    results = log.get_consensus_summary(min_nodes=4)
    assert len(results) == 0


# ── FederationAttackLog ───────────────────────────────────────────────────────

def _attack(fid="a001", node="n1", rule="replay_attack"):
    from centinel.federation.gossip import FindingPayload
    return FindingPayload(
        finding_id=fid,
        node_id=node,
        country_code="HN",
        finding_type="swarm_attack",
        severity="HIGH",
        rule_key=rule,
        summary="attack detected",
        snapshot_id="snap_001",
        timestamp_utc="2025-12-08T14:00:00+00:00",
        signature="",
    )


def test_attack_log_add_and_query():
    log = FederationAttackLog()
    assert log.add(_attack()) is True
    results = log.query(limit=10)
    assert len(results) == 1


def test_attack_log_no_duplicate():
    log = FederationAttackLog()
    f = _attack()
    log.add(f)
    assert log.add(f) is False


def test_attack_log_filters_by_node():
    log = FederationAttackLog()
    log.add(_attack(fid="a1", node="n1"))
    log.add(_attack(fid="a2", node="n2"))
    results = log.query(node_id="n1")
    assert len(results) == 1
    assert results[0]["node_id"] == "n1"


def test_attack_log_stats():
    log = FederationAttackLog()
    log.add(_attack(fid="a1"))
    log.add(_attack(fid="a2"))
    stats = log.stats()
    assert stats["total"] >= 2
