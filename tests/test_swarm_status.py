"""The swarm command tells the truth and does not open a port."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_swarm_status_says_not_production() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/swarm_status.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout
    assert "not yet production" in text
    assert "does not open a port" in text
