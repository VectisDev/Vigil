#!/usr/bin/env python3
"""Generate ops keys and write hashes to web/access.json.

Plaintext keys go to a 0600 file under RUNNER_TEMP. This script does not
print them. The regenerate workflow may upload that file as a one-day artifact.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from vigil.ops_keys import empty_registry, fingerprint, issue_keys  # noqa: E402

SEEDS_PATH = Path(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()) / "vigil-seeds.txt"
ACCESS_JSON = ROOT / "web" / "access.json"


def write_seeds_file(text: str) -> None:
    """Write the key file as mode 0600 at creation, with no wider window."""
    SEEDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(SEEDS_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def _existing_count() -> int:
    if not ACCESS_JSON.is_file():
        return 0
    try:
        loaded = json.loads(ACCESS_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    keys = loaded.get("keys") if isinstance(loaded, dict) else None
    if not isinstance(keys, list):
        return 0
    return sum(1 for row in keys if isinstance(row, dict) and row.get("status") == "active")


def main() -> int:
    if _existing_count() and os.environ.get("FORCE_REGENERATE") != "true":
        print("Hashes already exist — skipping generation.")
        write_seeds_file(
            "Hashes were already configured.\n"
            "Set FORCE_REGENERATE=true to replace them.\n"
        )
        return 0
    registry = empty_registry()
    issued = issue_keys(registry, 12)
    ACCESS_JSON.parent.mkdir(parents=True, exist_ok=True)
    ACCESS_JSON.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    lines = [
        "VIGIL ops keys. Hand these out. Do not commit this file.",
        "Each line is: public-id secret",
        "web/access.json stores a salted hash only.",
        "",
    ]
    for key in issued:
        lines.append(f"{fingerprint(key)} {key}")
    write_seeds_file("\n".join(lines) + "\n")
    print(f"web/access.json written with {len(issued)} hashes")
    print("Key file written. This script does not print the keys.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
