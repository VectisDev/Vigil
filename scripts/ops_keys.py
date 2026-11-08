#!/usr/bin/env python3
"""Issue, check, rotate, or revoke ops keys.

The plaintext key is printed once, or read from stdin. It is not written
into the repository. The file that is written holds a salted hash.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vigil.ops_keys import (
    fingerprint,
    issue_keys,
    load_registry,
    revoke,
    rotate,
    save_registry,
    verify_presented,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "ops_keys.yml"


def _active(registry: dict) -> int:
    return sum(1 for row in registry.get("keys") or [] if isinstance(row, dict) and row.get("status") == "active")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ops keys: salted hashes only.")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate")
    generate.add_argument("--count", type=int, default=12)
    generate.add_argument("--force", action="store_true")

    revoke_cmd = sub.add_parser("revoke")
    revoke_cmd.add_argument("key_id")

    rotate_cmd = sub.add_parser("rotate")
    rotate_cmd.add_argument("key_id")

    sub.add_parser("check")

    args = parser.parse_args(argv)
    registry = load_registry(REGISTRY)

    if args.command == "generate":
        if args.count < 1:
            print("Count must be at least 1.")
            return 1
        if _active(registry) and not args.force:
            print("Active keys already exist. Use rotate, revoke, or generate --force.")
            return 1
        if args.force:
            for row in list(registry.get("keys") or []):
                if isinstance(row, dict) and row.get("status") == "active":
                    revoke(registry, str(row.get("id") or ""))
        issued = issue_keys(registry, args.count)
        save_registry(REGISTRY, registry)
        print("Hand these to the team. They are not stored in the repository.")
        for key in issued:
            print(f"{fingerprint(key)} {key}")
        return 0

    if args.command == "revoke":
        if not revoke(registry, args.key_id):
            print("No key with that id.")
            return 1
        save_registry(REGISTRY, registry)
        print(f"Revoked {args.key_id.strip().lower()}. Later actions cannot use it.")
        return 0

    if args.command == "rotate":
        key = rotate(registry, args.key_id)
        if key is None:
            print("No key with that id.")
            return 1
        save_registry(REGISTRY, registry)
        print("The previous id is revoked. Hand this new key out once.")
        print(f"{fingerprint(key)} {key}")
        return 0

    presented = sys.stdin.readline().strip()
    found = verify_presented(presented, registry)
    if found is None:
        print("no match")
        return 1
    print(found)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
