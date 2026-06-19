#!/usr/bin/env python3
"""Stamp the latest hash chain root to Bitcoin via OpenTimestamps.

Called by the ots-anchor GitHub Actions workflow (manual dispatch from panel)
and optionally by the pipeline after each snapshot batch.

Exit codes:
  0 — proof submitted to OTS calendars (pending Bitcoin confirmation, ~hours)
  1 — OTS calendars unreachable (non-fatal; chain still valid, anchor pending)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from centinel.anchor.opentimestamps_client import MultichainAnchor  # noqa: E402


def _chain_head_hash() -> tuple[str, int]:
    """Return (sha256_of_chain_head, chain_length) from data/reputation branch."""
    result = subprocess.run(
        ["git", "log", "origin/data/reputation", "--format=%H", "--no-walk=unsorted"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0 or not result.stdout.strip():
        # Fallback: try local branch
        result = subprocess.run(
            ["git", "log", "data/reputation", "--format=%H"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if commits:
        head = commits[0]
        return hashlib.sha256(head.encode()).hexdigest(), len(commits)
    # Last-resort: hash the current UTC timestamp
    fallback = hashlib.sha256(datetime.now(timezone.utc).isoformat().encode()).hexdigest()
    return fallback, 0


def main() -> int:
    root_hash, chain_length = _chain_head_hash()
    print(f"[ots] stamping root_hash={root_hash[:16]}... chain_length={chain_length}")

    anchor = MultichainAnchor()
    checkpoint = anchor.anchor_checkpoint(
        {"merkle_root": root_hash, "chain_length": chain_length}
    )

    ots_dir = REPO_ROOT / "logs" / "anchors" / "ots"
    ots_dir.mkdir(parents=True, exist_ok=True)

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{ts_slug}_{root_hash[:12]}"
    ots_path = ots_dir / f"{stem}.ots"
    meta_path = ots_dir / f"{stem}.json"

    ots_proof = checkpoint.get("ots_proof", "")
    ots_path.write_text(str(ots_proof), encoding="utf-8")

    meta = {
        "ts": ts_slug,
        "merkle_root": root_hash,
        "chain_length": chain_length,
        "ots_status": "confirmed" if checkpoint.get("bitcoin_tx") else "pending",
        "bitcoin_tx": checkpoint.get("bitcoin_tx"),
        "bitcoin_block": checkpoint.get("bitcoin_block"),
        "anchor_chain": checkpoint.get("anchor_chain", "none"),
    }
    meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    anchored = checkpoint.get("anchor_chain") == "bitcoin"
    print(f"[ots] {'✓ proof saved' if anchored else '⚠ OTS unavailable — stub saved'}: {ots_path.name}")
    print(f"[ots] bitcoin_tx={meta['bitcoin_tx']} status={meta['ots_status']}")
    return 0 if anchored else 1


if __name__ == "__main__":
    sys.exit(main())
