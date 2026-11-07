"""Review indexes must point at files that exist.

Los índices de revisión tienen que apuntar a archivos que existen.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEXES = [
    ROOT / "docs" / "review-for-academic" / "README.md",
    ROOT / "docs" / "whitepaper" / "centinel-engine-whitepaper-v1.tex",
]


def test_cited_source_paths_exist_and_are_not_the_old_tree() -> None:
    missing: list[str] = []
    for path in INDEXES:
        text = path.read_text(encoding="utf-8")
        assert "src/centinel/" not in text, path.name
        for match in re.finditer(r"src/vigil/[\w./-]+\.py", text):
            rel = match.group(0)
            if not (ROOT / rel).is_file():
                missing.append(f"{path.name}: {rel}")
    assert missing == []
