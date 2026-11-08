"""A new node asks for a room code and nothing else."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "join.yml"


def _on(doc: dict) -> dict:
    raw = doc.get(True, doc.get("on"))
    return raw if isinstance(raw, dict) else {}


def test_the_workflow_has_one_input() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    inputs = _on(doc)["workflow_dispatch"]["inputs"]
    assert list(inputs) == ["room_code"]
    assert inputs["room_code"]["required"] is True
    assert "schedule" not in _on(doc)
    lowered = text.lower()
    for extra in ("password", "token", "email", "legal name", "cne.hn"):
        assert extra not in lowered
    assert doc["permissions"]["contents"] == "read"


def test_the_node_run_finishes_quickly_and_hides_the_key(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["ROOM_CODE"] = "AB23CD"
    env["RUNNER_TEMP"] = str(tmp_path)
    env["GITHUB_STEP_SUMMARY"] = str(tmp_path / "summary.txt")
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "scripts/swarm_node_run.py"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    assert completed.returncode == 0
    assert elapsed < 2
    assert "YELLOW" in completed.stdout
    assert "Not enough matching copies yet." in completed.stdout
    key = (tmp_path / "vigil-node.key").read_bytes()
    assert key.hex() not in completed.stdout
    assert key.hex() not in (tmp_path / "summary.txt").read_text(encoding="utf-8")
    bad = subprocess.run(
        [sys.executable, "scripts/swarm_node_run.py"],
        cwd=ROOT,
        env={**env, "ROOM_CODE": "nope"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 1
