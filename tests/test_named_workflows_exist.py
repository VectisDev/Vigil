"""A workflow path named in the docs is a file in this repository."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
NAMED = re.compile(r"\.github/workflows/([A-Za-z0-9][A-Za-z0-9_.-]*\.yml)")
RUN = re.compile(r"workflow run ([A-Za-z0-9][A-Za-z0-9_.-]*\.yml)")
ABSENT = re.compile(
    r"not present|not implemented|no está presente|no implementado|not in this repository",
    re.IGNORECASE,
)


def test_every_workflow_named_in_docs_exists() -> None:
    present = {path.name for path in WORKFLOWS.glob("*.yml")}
    problems: list[str] = []
    files = [
        ROOT / "README.md",
        ROOT / "README.en.md",
        ROOT / "SECURITY.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "CODE_OF_CONDUCT.md",
    ]
    for folder in (ROOT / "docs", ROOT / "web"):
        files.extend(path for path in folder.rglob("*.md"))
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in (NAMED, RUN):
            for match in pattern.finditer(text):
                start = match.start()
                window = text[max(0, start - 180) : start + 180]
                if ABSENT.search(window):
                    continue
                name = match.group(1)
                if name not in present:
                    problems.append(f"{path.relative_to(ROOT)}: {name}")
    assert problems == []
