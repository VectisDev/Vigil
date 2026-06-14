#!/usr/bin/env python3
"""Hash chain via Git commits — immutable state storage, zero cost.

Each snapshot is committed to git as a JSON file.
Git provides: immutability (content-addressed), auditability (git log),
and free storage (GitHub repo). Cost: $0. Storage: unlimited.
"""
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("vigil.hash_chain")


def serialize_chain_snapshot(engine) -> dict:
    """Serialize reputation engine state as JSON snapshot.

    Args:
        engine: ReputationEngine instance

    Returns:
        dict with timestamp, nodes data, ring_counts
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nodes": engine.get_all() if hasattr(engine, "get_all") else {},
        "ring_counts": engine.ring_counts() if hasattr(engine, "ring_counts") else {},
    }


def commit_to_hash_chain(repo_root: Path, db_path: Path, branch: str = "data/reputation") -> bool:
    """Commit reputation snapshot to git hash chain.

    Creates immutable record via git commits on specified branch.
    Uses force-with-lease for safety (prevents accidental overwrites).

    Args:
        repo_root: Path to git repository
        db_path: Path to reputation.db
        branch: Git branch for hash chain (default: data/reputation)

    Returns:
        True if commit succeeded, False otherwise
    """
    try:
        # Import here to avoid circular dependency
        from vigil.federation.reputation import ReputationEngine

        # Load current state
        engine = ReputationEngine(db_path=db_path)
        snapshot = serialize_chain_snapshot(engine)

        # Write snapshot to JSON file on data branch
        snapshot_dir = repo_root / "data" / "reputation"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot_file = snapshot_dir / f"snapshot-{snapshot['timestamp'][:10]}.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)

        # Commit to git
        subprocess.run(
            ["git", "config", "user.name", "centinel-bot"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "bot@vigil.local"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

        # Ensure we're on the right branch
        subprocess.run(
            ["git", "checkout", "-B", branch],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

        # Stage and commit
        subprocess.run(
            ["git", "add", str(snapshot_file)],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

        ring_summary = " | ".join(f"ring-{k}:{v}" for k, v in snapshot["ring_counts"].items())
        commit_msg = (
            f"Hash chain snapshot: {snapshot['timestamp']} | {ring_summary} | " f"nodes={len(snapshot['nodes'])}"
        )

        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

        # Push with force-with-lease (safe force push)
        subprocess.run(
            ["git", "push", "origin", branch, "--force-with-lease"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

        logger.info(
            "hash_chain_commit branch=%s timestamp=%s nodes=%d",
            branch,
            snapshot["timestamp"],
            len(snapshot["nodes"]),
        )
        return True

    except subprocess.CalledProcessError as e:
        logger.error(
            "hash_chain_git_failed error=%s stderr=%s",
            str(e),
            e.stderr.decode() if e.stderr else "unknown",
        )
        return False
    except Exception as e:
        logger.error("hash_chain_commit_failed error=%s", str(e))
        return False


if __name__ == "__main__":
    repo_root = Path.cwd()
    db_path = repo_root / "var" / "federation_reputation.db"

    success = commit_to_hash_chain(repo_root, db_path)
    print(f"Hash chain commit: {'SUCCESS' if success else 'FAILED'}")
