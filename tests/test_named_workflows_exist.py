"""A workflow file named in the docs is a file in this repository."""

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


def _named(text: str) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for pattern in (NAMED, RUN):
        for match in pattern.finditer(text):
            found.append((match.group(1), match.start()))
    return found


def test_every_workflow_named_in_docs_exists() -> None:
    present = {path.name for path in WORKFLOWS.glob("*.yml")}
    problems: list[str] = []
    roots = [ROOT / "docs", ROOT / "web", ROOT / ".github" / "SECURITY.md", ROOT / "README.md"]
    files: list[Path] = []
    for item in roots:
        if item.is_file():
            files.append(item)
        elif item.is_dir():
            files.extend(path for path in item.rglob("*") if path.suffix.lower() in {".md", ".html"})
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, start in _named(text):
            window = text[max(0, start - 180) : start + 180]
            if ABSENT.search(window):
                continue
            if name not in present:
                problems.append(f"{path.relative_to(ROOT)}: {name}")
    assert problems == []
