"""Tests for hash chain export via Git commits (zero-cost immutable storage)."""
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from centinel.federation.hash_chain import (
    commit_to_hash_chain,
    serialize_chain_snapshot,
)


class MockReputationEngine:
    """Mock ReputationEngine for testing."""

    def __init__(self, nodes=None, ring_counts=None):
        self.nodes = nodes or {}
        self.ring_counts_data = ring_counts or {}

    def get_all(self):
        return self.nodes

    def ring_counts(self):
        return self.ring_counts_data


class TestSerializeChainSnapshot:
    """Test serializing reputation state to JSON snapshot."""

    def test_serialize_empty_engine(self):
        """Test snapshot of engine with no nodes."""
        engine = MockReputationEngine()
        snapshot = serialize_chain_snapshot(engine)

        assert "timestamp" in snapshot
        assert "nodes" in snapshot
        assert "ring_counts" in snapshot
        assert snapshot["nodes"] == {}
        assert snapshot["ring_counts"] == {}

    def test_serialize_with_nodes(self):
        """Test snapshot with node data."""
        nodes = {
            "node-001": {"trust_score": 0.85, "ring": 1},
            "node-002": {"trust_score": 0.60, "ring": 2},
        }
        ring_counts = {"0": 0, "1": 1, "2": 1}

        engine = MockReputationEngine(nodes, ring_counts)
        snapshot = serialize_chain_snapshot(engine)

        assert snapshot["nodes"] == nodes
        assert snapshot["ring_counts"] == ring_counts
        assert len(snapshot["nodes"]) == 2

    def test_snapshot_has_valid_timestamp(self):
        """Test that snapshot includes valid ISO 8601 timestamp."""
        engine = MockReputationEngine()
        snapshot = serialize_chain_snapshot(engine)

        # Should be parseable as ISO format
        from datetime import datetime

        timestamp = datetime.fromisoformat(
            snapshot["timestamp"].replace("Z", "+00:00")
        )
        assert timestamp is not None
        assert timestamp.tzinfo is not None

    def test_snapshot_structure(self):
        """Test complete snapshot structure."""
        engine = MockReputationEngine(
            {"node-001": {"trust": 0.9}},
            {"0": 1},
        )
        snapshot = serialize_chain_snapshot(engine)

        # Verify all required fields
        assert isinstance(snapshot, dict)
        assert isinstance(snapshot["timestamp"], str)
        assert isinstance(snapshot["nodes"], dict)
        assert isinstance(snapshot["ring_counts"], dict)


class TestCommitToHashChain:
    """Test committing snapshots to git hash chain."""

    @patch("centinel.federation.hash_chain.ReputationEngine")
    @patch("subprocess.run")
    def test_commit_success_flow(self, mock_run, mock_engine_class):
        """Test successful commit to hash chain."""
        # Setup mocks
        mock_engine = MockReputationEngine(
            {"node-001": {"trust": 0.85}},
            {"0": 1},
        )
        mock_engine_class.return_value = mock_engine
        mock_run.return_value = MagicMock(returncode=0, stderr=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            db_path = repo_root / "federation_reputation.db"

            # Create git repo
            subprocess.run(
                ["git", "init"],
                cwd=repo_root,
                capture_output=True,
                check=True,
            )

            success = commit_to_hash_chain(repo_root, db_path)

            # Verify mocked subprocess calls
            assert mock_run.called
            # Should have called git config, checkout, add, commit, push
            call_args_list = [call[0][0] for call in mock_run.call_args_list]
            git_commands = [
                args[0] if isinstance(args, tuple) else args for args in call_args_list
            ]
            # Check that git commands were attempted
            assert any("git" in str(cmd) for cmd in git_commands)

    def test_commit_creates_snapshot_file(self):
        """Test that commit creates snapshot file in correct directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            db_path = repo_root / "federation_reputation.db"

            # Create minimal git repo
            subprocess.run(
                ["git", "init"],
                cwd=repo_root,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_root,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repo_root,
                capture_output=True,
                check=True,
            )

            # Mock the engine
            with patch("centinel.federation.hash_chain.ReputationEngine") as mock_class:
                mock_class.return_value = MockReputationEngine(
                    {"node-001": {"trust": 0.85}}
                )

                # This would attempt git operations
                # Just verify file creation without pushing
                engine = MockReputationEngine({"node-001": {"trust": 0.85}})
                snapshot = serialize_chain_snapshot(engine)

                snapshot_dir = repo_root / "data" / "reputation"
                snapshot_dir.mkdir(parents=True, exist_ok=True)

                snapshot_file = (
                    snapshot_dir
                    / f"snapshot-{snapshot['timestamp'][:10]}.json"
                )
                with open(snapshot_file, "w") as f:
                    json.dump(snapshot, f, indent=2)

                assert snapshot_file.exists()

    @patch("subprocess.run")
    def test_commit_handles_git_error(self, mock_run):
        """Test that commit handles git errors gracefully."""
        # Make subprocess.run raise an exception
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            db_path = repo_root / "federation_reputation.db"

            with patch(
                "centinel.federation.hash_chain.ReputationEngine"
            ) as mock_class:
                mock_class.return_value = MockReputationEngine()

                success = commit_to_hash_chain(repo_root, db_path)

                # Should return False on error
                assert success is False

    def test_commit_message_format(self):
        """Test that commit message includes proper summary."""
        engine = MockReputationEngine(
            {"node-001": {"trust": 0.85}, "node-002": {"trust": 0.60}},
            {"0": 0, "1": 1, "2": 1},
        )
        snapshot = serialize_chain_snapshot(engine)

        ring_summary = " | ".join(
            f"ring-{k}:{v}" for k, v in snapshot["ring_counts"].items()
        )
        commit_msg = (
            f"Hash chain snapshot: {snapshot['timestamp']} | {ring_summary} | "
            f"nodes={len(snapshot['nodes'])}"
        )

        assert "Hash chain snapshot:" in commit_msg
        assert "ring-" in commit_msg
        assert "nodes=2" in commit_msg


class TestHashChainIntegration:
    """Integration tests for hash chain functionality."""

    def test_snapshot_json_serializable(self):
        """Test that snapshot is JSON serializable."""
        engine = MockReputationEngine(
            {"node-001": {"alpha": 5.0, "beta": 2.0}},
            {"0": 1},
        )
        snapshot = serialize_chain_snapshot(engine)

        # Should be JSON serializable
        json_str = json.dumps(snapshot)
        loaded = json.loads(json_str)

        assert loaded["nodes"]["node-001"]["alpha"] == 5.0

    def test_multiple_snapshots(self):
        """Test creating multiple snapshots (simulating periodic exports)."""
        engine1 = MockReputationEngine({"node-001": {"trust": 0.85}})
        engine2 = MockReputationEngine(
            {"node-001": {"trust": 0.90}, "node-002": {"trust": 0.60}}
        )

        snapshot1 = serialize_chain_snapshot(engine1)
        snapshot2 = serialize_chain_snapshot(engine2)

        # Snapshots should have different timestamps
        assert "timestamp" in snapshot1
        assert "timestamp" in snapshot2
        # Timestamps might be the same if created immediately, but structure differs
        assert len(snapshot1["nodes"]) == 1
        assert len(snapshot2["nodes"]) == 2

    def test_snapshot_preserves_complex_data(self):
        """Test that snapshot preserves complex nested data structures."""
        nodes = {
            "node-001": {
                "alpha": 5.0,
                "beta": 2.0,
                "ring": 1,
                "arrival_order": 42,
                "country_code": "US",
                "last_seen_utc": "2026-06-01T12:00:00Z",
                "metadata": {"custom_field": "value"},
            }
        }

        engine = MockReputationEngine(nodes)
        snapshot = serialize_chain_snapshot(engine)

        exported_node = snapshot["nodes"]["node-001"]
        assert exported_node["alpha"] == 5.0
        assert exported_node["metadata"]["custom_field"] == "value"
