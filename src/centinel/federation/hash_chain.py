#!/usr/bin/env python3
"""Hash chain export for GitHub commit-based storage."""
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from centinel.federation.reputation import ReputationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("centinel.hash_chain")


def serialize_chain_snapshot(engine: ReputationEngine) -> dict:
    """Serialize reputation state as a hash chain snapshot."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nodes": engine.get_all(),
        "ring_counts": engine.ring_counts(),
    }


def commit_to_hash_chain(
    repo_root: Path,
    db_path: Path,
    branch: str = "data/reputation",
) -> bool:
    """Commit reputation snapshot to hash chain branch."""
    try:
        engine = ReputationEngine(db_path=db_path)
        snapshot = serialize_chain_snapshot(engine)

        chain_file = repo_root / "data" / "reputation" / "snapshot.json"
        chain_file.parent.mkdir(parents=True, exist_ok=True)

        with open(chain_file, "w") as f:
            json.dump(snapshot, f, indent=2)

        subprocess.run(
            ["git", "config", "user.name", "centinel-bot"],
            cwd=repo_root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "bot@centinel.local"],
            cwd=repo_root,
            check=True,
        )

        subprocess.run(["git", "checkout", "-B", branch], cwd=repo_root, check=True)
        subprocess.run(["git", "add", str(chain_file)], cwd=repo_root, check=True)

        timestamp = datetime.now(timezone.utc).isoformat()
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"Hash chain snapshot: {timestamp}\n\nNodes: {len(snapshot['nodes'])}\nRing-0: {snapshot['ring_counts']['ring0']}\nRing-1: {snapshot['ring_counts']['ring1']}\nRing-2: {snapshot['ring_counts']['ring2']}",
            ],
            cwd=repo_root,
            check=True,
        )

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = result.stdout.strip()

        logger.info("hash_chain_commit branch=%s sha=%s nodes=%d", branch, commit_sha, len(snapshot['nodes']))
        return True

    except Exception as exc:
        logger.error("hash_chain_commit_failed error=%s", exc)
        return False


if __name__ == "__main__":
    import sys

    repo_root = Path(__file__).parent.parent.parent.parent
    db_path = repo_root / "var" / "federation_reputation.db"

    if not commit_to_hash_chain(repo_root, db_path):
        sys.exit(1)

    print("✓ Hash chain snapshot committed")
