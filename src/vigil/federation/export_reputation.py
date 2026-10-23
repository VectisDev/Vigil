#!/usr/bin/env python3
"""Reputation engine export — JSON API for zero-cost consensus.

Exports all reputation events to JSON for:
- Forensic audit trail (immutable, permanent)
- Cross-swarm consensus (read via raw.githubusercontent.com)
- Cost: $0 (GitHub storage)
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("vigil.export_reputation")


def export_events_json(engine, output_path: Path) -> bool:
    """Export all reputation events to JSON file.

    Args:
        engine: ReputationEngine instance
        output_path: Path to write JSON file

    Returns:
        True if export succeeded, False otherwise
    """
    try:
        # Get all nodes and their reputation
        nodes = engine.get_all() if hasattr(engine, "get_all") else {}

        # Prepare export structure
        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "nodes": nodes,
            "ring_counts": engine.ring_counts() if hasattr(engine, "ring_counts") else {},
            "summary": {
                "total_nodes": len(nodes),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(
            "reputation_export nodes=%d output=%s",
            len(nodes),
            output_path,
        )
        return True

    except Exception as e:
        logger.error("reputation_export_failed error=%s", str(e))
        return False


def export_forensic_trail(engine, output_dir: Path) -> bool:
    """Export forensic audit trail for immutable archival.

    Args:
        engine: ReputationEngine instance
        output_dir: Directory to write forensic files

    Returns:
        True if export succeeded, False otherwise
    """
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Create forensic file
        forensic_path = output_dir / f"forensic-trail-{timestamp}.json"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Gather forensic data
        nodes = engine.get_all() if hasattr(engine, "get_all") else {}
        forensic_data = {
            "timestamp": timestamp,
            "nodes": nodes,
            "ring_summary": engine.ring_counts() if hasattr(engine, "ring_counts") else {},
        }

        with open(forensic_path, "w") as f:
            json.dump(forensic_data, f, indent=2)

        logger.info("forensic_trail_created path=%s nodes=%d", forensic_path, len(nodes))
        return True

    except Exception as e:
        logger.error("forensic_trail_failed error=%s", str(e))
        return False


if __name__ == "__main__":
    from vigil.federation.reputation import ReputationEngine

    repo_root = Path.cwd()
    db_path = repo_root / "var" / "federation_reputation.db"

    engine = ReputationEngine(db_path=db_path)

    # Export reputation as JSON
    output_path = repo_root / "data" / "reputation" / "nodes.json"
    success = export_events_json(engine, output_path)

    print(f"Export reputation: {'SUCCESS' if success else 'FAILED'}")
