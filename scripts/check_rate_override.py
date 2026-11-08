#!/usr/bin/env python3
"""Refuse a pace past the lock unless the commit is signed.

The file may be absent. A pace inside the lock needs no signature.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vigil.pace import git_override_is_signed, override_is_refused, read_override

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = ROOT / "rate_override.yml"


def _signed() -> bool:
    if not git_override_is_signed(ROOT):
        return False
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return True
    listed = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "rate_override.yml"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    sha = listed.stdout.strip()
    asked = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits/{sha}", "--jq", ".commit.verification.verified"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GH_TOKEN": token},
    )
    return asked.returncode == 0 and asked.stdout.strip() == "true"


def main() -> int:
    if not OVERRIDE.is_file():
        print("Pace lock holds. No override file.")
        return 0
    text = read_override(ROOT) or ""
    if override_is_refused(text, _signed()):
        print("Unsigned or incomplete pace override. The lock stays.")
        return 1
    print("Pace override is signed and states the responsibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
