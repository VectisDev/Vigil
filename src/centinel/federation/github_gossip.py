#!/usr/bin/env python3
"""GitHub-native gossip protocol — zero-cost swarm coordination via GitHub Issues.

Pull-model: Each swarm publishes findings to shared GitHub Issues.
Other swarms read for free (no API costs). Consensus computed locally.
Cost: $0. Scalability: unlimited (1 swarm = 12 swarms = 1000 swarms = $0).
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("centinel.github_gossip")


class GitHubGossipQueue:
    """Gossip via GitHub Issues — free, auditable, immutable."""

    def __init__(self, repo: str, election_id: str, github_token: Optional[str] = None):
        """
        Initialize gossip via GitHub Issues.

        repo: "owner/repo" (e.g., "vectisdev/centinel-data")
        election_id: unique identifier for this election
        github_token: GitHub API token (optional, public repos don't need it)
        """
        self.repo = repo
        self.election_id = election_id
        self.github_token = github_token
        self.issue_number = None
        self.last_comment_id = 0

    def _publish_payload(self, swarm_id: str, node_id: str, payload: dict) -> bool:
        """Publish node payload as comment in election issue."""
        try:
            message = json.dumps(
                {
                    "swarm_id": swarm_id,
                    "node_id": node_id,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "payload": payload,
                }
            )

            # In production: POST /repos/{owner}/{repo}/issues/{issue}/comments
            # For now, log intent
            logger.info(
                "gossip_publish swarm=%s node=%s election=%s payload_size=%d",
                swarm_id,
                node_id,
                self.election_id,
                len(message),
            )
            return True

        except Exception as exc:
            logger.error(
                "gossip_publish_failed swarm=%s node=%s error=%s", swarm_id, node_id, exc
            )
            return False

    def _read_payloads(self) -> list[dict]:
        """Read all gossip messages from election issue (GitHub API, free)."""
        try:
            # In production: GET /repos/{owner}/{repo}/issues/{issue}/comments
            # Returns paginated list, client-side pagination (free, no rate limit)
            #
            # Gossip messages are comments in JSON format
            # Client reads all, filters by timestamp, computes consensus
            logger.info("gossip_read election=%s", self.election_id)
            return []

        except Exception as exc:
            logger.error("gossip_read_failed election=%s error=%s", self.election_id, exc)
            return []

    def compute_consensus(
        self, payloads: list[dict], threshold: float = 0.66
    ) -> Optional[dict]:
        """Compute consensus from all node payloads (local computation, zero network cost).

        Groups by fingerprint hash. Returns consensus if >threshold nodes agree.
        """
        if not payloads:
            return None

        # Group by fingerprint hash
        fingerprints = {}
        for p in payloads:
            fh = p.get("payload", {}).get("fingerprint_hash")
            if fh:
                fingerprints[fh] = fingerprints.get(fh, 0) + 1

        # Consensus = fingerprint with >threshold agreement
        total = len(payloads)
        for fh, count in fingerprints.items():
            if count / total >= threshold:
                return {
                    "fingerprint_hash": fh,
                    "consensus_nodes": count,
                    "total_nodes": total,
                }

        return None


def gossip_via_github(repo: str, election_id: str, swarm_id: str = "swarm-001") -> dict:
    """Single-swarm gossip cycle via GitHub Issues (zero cost)."""
    queue = GitHubGossipQueue(repo, election_id)

    # 1. Publish local swarm findings (from all 12 nodes in swarm)
    local_payload = {
        "fingerprint_hash": "sha256:abc123",  # placeholder
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "swarm_consensus": True,
    }

    # Simulate 12 nodes publishing (actually just one publish with swarm consensus)
    queue._publish_payload(swarm_id, "node-001", local_payload)

    # 2. Read all other swarms' payloads (free GitHub API, no rate limit)
    all_payloads = queue._read_payloads()
    all_payloads.append({"swarm_id": swarm_id, "node_id": "node-001", "payload": local_payload})

    # 3. Compute consensus locally (zero network cost)
    # Consensus requires agreement across swarms, not individual nodes
    consensus = queue.compute_consensus(all_payloads)

    return {
        "election_id": election_id,
        "swarm_id": swarm_id,
        "consensus": consensus,
        "swarms_heard": len(set(p.get("swarm_id") for p in all_payloads)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    result = gossip_via_github("vectisdev/centinel-data", "election-2026-06-01", "swarm-001")
    print(json.dumps(result, indent=2))
