#!/usr/bin/env python3
"""Refuse a pace past the lock unless GitHub reports the commit verified.

The file may be absent. A pace inside the lock needs no signature.
A file under rate_override.yml or audit/ceiling-unlock/*.yml can pass the
lock only when verification.verified is true, the responsibility line is
present, and the key id is active.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vigil.ops_keys import key_is_active, load_registry
from vigil.pace import override_files, verified_override_text

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if not override_files(ROOT):
        print("Pace lock holds. No override file.")
        return 0
    registry = load_registry(ROOT / "config" / "ops_keys.yml")
    ok, _text = verified_override_text(ROOT, lambda key_id: key_is_active(registry, key_id))
    if not ok:
        print("Pace override needs verification.verified, the responsibility line, and an active key id.")
        return 1
    print("Pace override is verified, names an active key id, and states the responsibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
