#!/usr/bin/env python3
"""Export reputation events to JSON for GitHub Release archive."""
import json
import logging
import sys
from pathlib import Path
from centinel.federation.reputation import ReputationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("centinel.export_reputation")


def export_events(db_path: Path, output_path: Path) -> bool:
    """Export reputation events from database to JSON file."""
    try:
        engine = ReputationEngine(db_path=db_path)
        events_data = engine.export_events_json()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(events_data, f, indent=2)

        logger.info("reputation_events_exported path=%s count=%d", output_path, events_data.get("event_count", 0))
        return True
    except Exception as exc:
        logger.error("reputation_events_export_failed error=%s", exc)
        return False


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent.parent.parent
    db_path = repo_root / "var" / "federation_reputation.db"
    output_path = repo_root / "forensic_trail.json"

    if not export_events(db_path, output_path):
        sys.exit(1)

    print(f"✓ Exported to {output_path}")
