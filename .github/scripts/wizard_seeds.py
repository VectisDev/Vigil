#!/usr/bin/env python3
"""Generate ops keys and write salted hashes to config/ops_keys.yml.

The plaintext keys go to a 0600 file under RUNNER_TEMP. That file must
never be uploaded as an Actions artifact. On a public repository an
artifact can be downloaded for as long as it is retained.

This script does not write a file under web/ and does not commit the keys.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from vigil.ops_keys import (  # noqa: E402
    fingerprint,
    issue_keys,
    load_registry,
    revoke,
    save_registry,
)

SEEDS_PATH = Path(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()) / "vigil-seeds.txt"
REGISTRY = ROOT / "config" / "ops_keys.yml"


def write_seeds_file(text: str) -> None:
    """Write the key file as mode 0600 at creation, with no wider window."""
    SEEDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(SEEDS_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def main() -> int:
    registry = load_registry(REGISTRY)
    active = [row for row in registry.get("keys") or [] if isinstance(row, dict) and row.get("status") == "active"]
    if active and os.environ.get("FORCE_REGENERATE") != "true":
        print("Keys already exist — skipping generation.")
        write_seeds_file(
            "Keys were already configured.\n"
            "Rotate one with scripts/ops_keys.py rotate, or set FORCE_REGENERATE=true.\n"
        )
        return 0
    if active:
        for row in active:
            revoke(registry, str(row.get("id") or ""))
    issued = issue_keys(registry, 12)
    save_registry(REGISTRY, registry)
    lines = [
        "VIGIL ops keys. Hand these out. Do not commit this file.",
        "Each line is: public-id secret",
        "The secret is 12 characters, about 71 bits. The id is a fingerprint.",
        "config/ops_keys.yml stores a salted hash only.",
        "",
    ]
    for key in issued:
        lines.append(f"{fingerprint(key)} {key}")
    write_seeds_file("\n".join(lines) + "\n")
    print(f"config/ops_keys.yml written with {len(issued)} hashes")
    print(f"Keys file written to {SEEDS_PATH} (mode 0600, do NOT upload as artifact)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
