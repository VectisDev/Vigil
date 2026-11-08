#!/usr/bin/env python3
"""One room code in, one color out. The key is not printed.

The built-in workflow token cannot create a repository secret, so the
private key is written only under the runner's temp directory and is
not committed. A personal token would be a second question, so this
does not ask for one.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vigil.swarm.governance import valid_room_code
from vigil.swarm.lights import SENTENCE, traffic_light


def new_key() -> tuple[str, bytes]:
    raw = secrets.token_bytes(32)
    return hashlib.sha256(raw).hexdigest(), raw


def main() -> int:
    code = os.environ.get("ROOM_CODE", "")
    if not valid_room_code(code):
        print("That code does not work.")
        return 1
    public, private = new_key()
    folder = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir()))
    path = folder / "vigil-node.key"
    path.write_bytes(private)
    path.chmod(0o600)
    color = traffic_light([], [], "", "")
    sentence = SENTENCE[color]
    lines = [
        color.upper(),
        sentence,
        f"Public id {public}",
        "The key was not saved in the repository.",
    ]
    print("\n".join(lines))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
