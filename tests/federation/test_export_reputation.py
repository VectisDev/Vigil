"""Tests for reputation export to JSON (zero-cost forensic trails)."""

import json
import tempfile
from pathlib import Path

import pytest

from centinel.federation.export_reputation import export_events_json, export_forensic_trail


class MockReputationEngine:
    """Mock ReputationEngine for testing."""

    def __init__(self, nodes=None, ring_counts=None):
        self.nodes = nodes or {}
        self.ring_counts_data = ring_counts or {}

    def get_all(self):
        return self.nodes

    def ring_counts(self):
        return self.ring_counts_data


class TestExportEventsJson:
    """Test exporting reputation events to JSON."""

    def test_export_empty_engine(self):
        """Test exporting engine with no nodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine()
            output_path = Path(tmpdir) / "nodes.json"

            success = export_events_json(engine, output_path)

            assert success is True
            assert output_path.exists()

            # Verify JSON structure
            with open(output_path) as f:
                data = json.load(f)

            assert "exported_at" in data
            assert "nodes" in data
            assert "ring_counts" in data
            assert "summary" in data
            assert data["summary"]["total_nodes"] == 0

    def test_export_with_nodes(self):
        """Test exporting engine with nodes."""
        nodes = {
            "node-001": {"trust_score": 0.85, "ring": 1},
            "node-002": {"trust_score": 0.60, "ring": 2},
            "node-003": {"trust_score": 0.95, "ring": 0},
        }
        ring_counts = {"0": 1, "1": 1, "2": 1}

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine(nodes, ring_counts)
            output_path = Path(tmpdir) / "nodes.json"

            success = export_events_json(engine, output_path)

            assert success is True
            assert output_path.exists()

            # Verify content
            with open(output_path) as f:
                data = json.load(f)

            assert data["summary"]["total_nodes"] == 3
            assert len(data["nodes"]) == 3
            assert data["ring_counts"]["0"] == 1

    def test_export_creates_parent_directories(self):
        """Test that export creates missing parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine()
            output_path = Path(tmpdir) / "deep" / "nested" / "path" / "nodes.json"

            success = export_events_json(engine, output_path)

            assert success is True
            assert output_path.exists()
            assert output_path.parent.exists()

    def test_export_json_valid(self):
        """Test that exported JSON is properly formatted."""
        nodes = {
            "node-001": {
                "trust_score": 0.85,
                "ring": 1,
                "last_seen": "2026-06-01T00:00:00Z",
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine(nodes)
            output_path = Path(tmpdir) / "nodes.json"

            export_events_json(engine, output_path)

            # Verify valid JSON
            with open(output_path) as f:
                content = f.read()
                data = json.loads(content)  # Will raise if not valid JSON

            assert isinstance(data, dict)
            assert "exported_at" in data


class TestExportForensicTrail:
    """Test exporting forensic audit trail."""

    def test_export_forensic_trail_empty(self):
        """Test exporting forensic trail with no nodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine()
            output_dir = Path(tmpdir)

            success = export_forensic_trail(engine, output_dir)

            assert success is True
            # Check that file was created
            files = list(output_dir.glob("forensic-trail-*.json"))
            assert len(files) == 1

    def test_export_forensic_trail_with_nodes(self):
        """Test exporting forensic trail with node data."""
        nodes = {"node-001": {"trust": 0.85}, "node-002": {"trust": 0.60}}
        ring_counts = {"0": 0, "1": 1, "2": 1}

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine(nodes, ring_counts)
            output_dir = Path(tmpdir)

            success = export_forensic_trail(engine, output_dir)

            assert success is True

            # Read forensic file
            files = list(output_dir.glob("forensic-trail-*.json"))
            assert len(files) == 1

            with open(files[0]) as f:
                data = json.load(f)

            assert "timestamp" in data
            assert "nodes" in data
            assert len(data["nodes"]) == 2
            assert data["ring_summary"]["1"] == 1

    def test_export_forensic_creates_directory(self):
        """Test that export creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine()
            output_dir = Path(tmpdir) / "new" / "output" / "dir"

            success = export_forensic_trail(engine, output_dir)

            assert success is True
            assert output_dir.exists()

    def test_export_forensic_trail_filename_format(self):
        """Test that forensic trail filename includes timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine()
            output_dir = Path(tmpdir)

            export_forensic_trail(engine, output_dir)

            files = list(output_dir.glob("forensic-trail-*.json"))
            assert len(files) == 1

            # Filename should be forensic-trail-YYYY-MM-DD...
            filename = files[0].name
            assert filename.startswith("forensic-trail-")
            assert filename.endswith(".json")


class TestExportIntegration:
    """Integration tests for reputation export."""

    def test_export_consistency(self):
        """Test that multiple exports of same engine produce consistent results."""
        nodes = {"node-001": {"trust": 0.85}}
        ring_counts = {"1": 1}

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine(nodes, ring_counts)
            path1 = Path(tmpdir) / "export1.json"
            path2 = Path(tmpdir) / "export2.json"

            export_events_json(engine, path1)
            export_events_json(engine, path2)

            with open(path1) as f:
                data1 = json.load(f)

            with open(path2) as f:
                data2 = json.load(f)

            # Both exports should have same nodes
            assert data1["nodes"] == data2["nodes"]
            assert data1["ring_counts"] == data2["ring_counts"]

    def test_export_preserves_node_data(self):
        """Test that export preserves all node data correctly."""
        nodes = {
            "node-001": {
                "alpha": 5.0,
                "beta": 2.0,
                "ring": 1,
                "country": "US",
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = MockReputationEngine(nodes)
            output_path = Path(tmpdir) / "nodes.json"

            export_events_json(engine, output_path)

            with open(output_path) as f:
                data = json.load(f)

            exported_node = data["nodes"]["node-001"]
            assert exported_node["alpha"] == 5.0
            assert exported_node["beta"] == 2.0
            assert exported_node["ring"] == 1
