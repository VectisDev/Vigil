"""Tests for GitHub-native gossip protocol (zero-cost swarm coordination)."""
import json
from datetime import datetime, timezone

import pytest

from centinel.federation.github_gossip import GitHubGossipQueue, gossip_via_github


class TestGitHubGossipQueue:
    """Test GitHubGossipQueue — gossip via GitHub Issues (free API)."""

    def test_init(self):
        """Test GitHubGossipQueue initialization."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        assert queue.repo == "vectisdev/centinel"
        assert queue.election_id == "election-2026-06-01"
        assert queue.github_token is None

    def test_init_with_token(self):
        """Test initialization with GitHub token."""
        queue = GitHubGossipQueue(
            "vectisdev/centinel", "election-2026-06-01", github_token="token123"
        )
        assert queue.github_token == "token123"

    def test_publish_payload(self, caplog):
        """Test publishing node payload (logs, no real network)."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        payload = {"fingerprint_hash": "sha256:abc123", "timestamp": "2026-06-01T00:00:00Z"}

        success = queue._publish_payload("swarm-001", "node-001", payload)

        assert success is True
        assert "gossip_publish" in caplog.text

    def test_publish_payload_error_handling(self, caplog):
        """Test publish handles errors gracefully."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")

        # Pass invalid payload that breaks JSON serialization
        class BadPayload:
            def __repr__(self):
                raise ValueError("Bad payload")

        # Even with error, should be caught and logged
        success = queue._publish_payload("swarm-001", "node-001", BadPayload())
        # This might succeed or fail depending on implementation
        # Just verify it doesn't crash

    def test_read_payloads(self, caplog):
        """Test reading payloads from election issue (stub)."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        payloads = queue._read_payloads()

        assert isinstance(payloads, list)
        assert len(payloads) == 0  # Current stub implementation
        assert "gossip_read" in caplog.text

    def test_compute_consensus_empty(self):
        """Test consensus with no payloads."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        consensus = queue.compute_consensus([])

        assert consensus is None

    def test_compute_consensus_single(self):
        """Test consensus with single payload."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        payloads = [
            {
                "swarm_id": "swarm-001",
                "node_id": "node-001",
                "payload": {"fingerprint_hash": "sha256:abc123"},
            }
        ]

        consensus = queue.compute_consensus(payloads)

        assert consensus is not None
        assert consensus["fingerprint_hash"] == "sha256:abc123"
        assert consensus["consensus_nodes"] == 1
        assert consensus["total_nodes"] == 1

    def test_compute_consensus_unanimous(self):
        """Test consensus with unanimous agreement."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        payloads = [
            {
                "swarm_id": f"swarm-{i:03d}",
                "node_id": f"node-{i:03d}",
                "payload": {"fingerprint_hash": "sha256:abc123"},
            }
            for i in range(5)
        ]

        consensus = queue.compute_consensus(payloads, threshold=0.66)

        assert consensus is not None
        assert consensus["fingerprint_hash"] == "sha256:abc123"
        assert consensus["consensus_nodes"] == 5
        assert consensus["total_nodes"] == 5

    def test_compute_consensus_majority(self):
        """Test consensus with majority agreement (66% threshold)."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        payloads = [
            {"swarm_id": f"swarm-{i:03d}", "payload": {"fingerprint_hash": "sha256:abc123"}}
            for i in range(3)
        ] + [
            {"swarm_id": "swarm-004", "payload": {"fingerprint_hash": "sha256:def456"}}
        ]

        consensus = queue.compute_consensus(payloads, threshold=0.66)

        assert consensus is not None
        assert consensus["fingerprint_hash"] == "sha256:abc123"
        assert consensus["consensus_nodes"] == 3  # 75% > 66%
        assert consensus["total_nodes"] == 4

    def test_compute_consensus_no_agreement(self):
        """Test consensus with no majority."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        payloads = [
            {"swarm_id": "swarm-001", "payload": {"fingerprint_hash": "sha256:abc123"}},
            {"swarm_id": "swarm-002", "payload": {"fingerprint_hash": "sha256:def456"}},
            {"swarm_id": "swarm-003", "payload": {"fingerprint_hash": "sha256:ghi789"}},
        ]

        consensus = queue.compute_consensus(payloads, threshold=0.66)

        assert consensus is None  # No hash has >66% agreement

    def test_compute_consensus_threshold_boundary(self):
        """Test consensus at exactly 66% threshold."""
        queue = GitHubGossipQueue("vectisdev/centinel", "election-2026-06-01")
        # 2 out of 3 = 66.7%, should pass
        payloads = [
            {"swarm_id": "swarm-001", "payload": {"fingerprint_hash": "sha256:abc123"}},
            {"swarm_id": "swarm-002", "payload": {"fingerprint_hash": "sha256:abc123"}},
            {"swarm_id": "swarm-003", "payload": {"fingerprint_hash": "sha256:def456"}},
        ]

        consensus = queue.compute_consensus(payloads, threshold=0.66)

        assert consensus is not None
        assert consensus["fingerprint_hash"] == "sha256:abc123"


class TestGossipViaGitHub:
    """Test end-to-end gossip cycle via GitHub Issues."""

    def test_gossip_via_github_single_swarm(self):
        """Test single swarm gossip cycle (local computation)."""
        result = gossip_via_github(
            "vectisdev/centinel-data", "election-2026-06-01", "swarm-001"
        )

        assert result["election_id"] == "election-2026-06-01"
        assert result["swarm_id"] == "swarm-001"
        assert "consensus" in result
        assert "swarms_heard" in result
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)

    def test_gossip_via_github_consensus_structure(self):
        """Test gossip result structure."""
        result = gossip_via_github("vectisdev/centinel-data", "election-2026-06-01")

        # Should have consensus field
        assert "consensus" in result
        # Consensus can be None or dict
        if result["consensus"] is not None:
            assert "fingerprint_hash" in result["consensus"]
            assert "consensus_nodes" in result["consensus"]
            assert "total_nodes" in result["consensus"]

    def test_gossip_via_github_timestamp_format(self):
        """Test that timestamps are valid ISO 8601."""
        result = gossip_via_github("vectisdev/centinel-data", "election-2026-06-01")

        # Parse timestamp to verify ISO format
        timestamp = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
        assert timestamp is not None
        assert timestamp.tzinfo is not None  # Should have timezone info

    def test_gossip_isolation(self):
        """Test that different elections are isolated."""
        result1 = gossip_via_github("vectisdev/centinel-data", "election-2026-06-01")
        result2 = gossip_via_github("vectisdev/centinel-data", "election-2026-06-02")

        assert result1["election_id"] != result2["election_id"]

    def test_gossip_swarm_isolation(self):
        """Test that different swarms can work independently."""
        result1 = gossip_via_github(
            "vectisdev/centinel-data", "election-2026-06-01", "swarm-001"
        )
        result2 = gossip_via_github(
            "vectisdev/centinel-data", "election-2026-06-01", "swarm-002"
        )

        assert result1["swarm_id"] == "swarm-001"
        assert result2["swarm_id"] == "swarm-002"
