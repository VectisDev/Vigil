#!/usr/bin/env python3
"""GPU batch validation - accumulate and process validations in parallel."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vigil.gpu_batching")


class ValidationBatch:
    """Accumulate validations for batch processing."""

    def __init__(self, batch_id: str, max_size: int = 20):
        self.batch_id = batch_id
        self.max_size = max_size
        self.items = []
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add(self, node_id: str, fingerprint: dict, consensus: dict) -> bool:
        """Add a validation item. Return True if batch is ready."""
        if len(self.items) >= self.max_size:
            return False
        self.items.append(
            {
                "node_id": node_id,
                "fingerprint": fingerprint,
                "consensus": consensus,
                "added_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return len(self.items) >= self.max_size

    def is_ready(self) -> bool:
        """Check if batch should be processed."""
        return len(self.items) >= self.max_size or (len(self.items) > 0 and self._age_minutes() > 60)

    def _age_minutes(self) -> float:
        """Age of batch in minutes."""
        created = datetime.fromisoformat(self.created_at)
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() / 60.0

    def to_dict(self) -> dict:
        """Serialize batch for storage."""
        return {
            "batch_id": self.batch_id,
            "created_at": self.created_at,
            "item_count": len(self.items),
            "items": self.items,
        }


def load_or_create_batch(batch_dir: Path, batch_id: str) -> ValidationBatch:
    """Load existing batch or create new one."""
    batch_file = batch_dir / f"{batch_id}.json"
    if batch_file.exists():
        try:
            with open(batch_file) as f:
                data = json.load(f)
            batch = ValidationBatch(batch_id)
            batch.items = data.get("items", [])
            batch.created_at = data.get("created_at", batch.created_at)
            return batch
        except Exception as exc:
            logger.warning("batch_load_failed batch_id=%s error=%s", batch_id, exc)
    return ValidationBatch(batch_id)


def save_batch(batch: ValidationBatch, batch_dir: Path) -> bool:
    """Save batch to disk."""
    try:
        batch_dir.mkdir(parents=True, exist_ok=True)
        batch_file = batch_dir / f"{batch.batch_id}.json"
        with open(batch_file, "w") as f:
            json.dump(batch.to_dict(), f, indent=2)
        logger.info("batch_saved batch_id=%s items=%d", batch.batch_id, len(batch.items))
        return True
    except Exception as exc:
        logger.error("batch_save_failed batch_id=%s error=%s", batch.batch_id, exc)
        return False


def generate_batch_matrix(batch: ValidationBatch, parallel_jobs: int = 20) -> list[dict]:
    """Generate GitHub Actions matrix for parallel validation."""
    matrix = []
    for i, item in enumerate(batch.items):
        matrix.append(
            {
                "job_id": i,
                "node_id": item["node_id"],
                "fingerprint": json.dumps(item["fingerprint"]),
                "consensus": json.dumps(item["consensus"]),
            }
        )
    return matrix


if __name__ == "__main__":
    batch_dir = Path("/tmp/validation_batches")  # nosec B108
    batch = load_or_create_batch(batch_dir, "batch-001")
    if save_batch(batch, batch_dir):
        print(f"✓ Batch ready: {batch.batch_id}")
