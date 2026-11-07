"""Workflow tokens default to read. A job that pushes opts in."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def test_every_workflow_defaults_to_read() -> None:
    problems: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if "pull_request_target" in text:
            problems.append(f"{path.name}: pull_request_target")
        if "write-all" in text:
            problems.append(f"{path.name}: write-all")
        doc = yaml.safe_load(text)
        perms = doc.get("permissions")
        if not isinstance(perms, dict) or perms.get("contents") != "read":
            problems.append(f"{path.name}: top-level contents is not read")
    assert problems == []
