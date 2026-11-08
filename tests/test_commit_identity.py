"""Automated commits record the maintainer at the account noreply address."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMAIL = "287128931+VectisDev@users.noreply.github.com"
SHORT = "VectisDev@users.noreply.github.com"


def test_workflows_and_hash_chain_use_the_account_noreply() -> None:
    for path in (ROOT / ".github" / "workflows").glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        if "user.email" not in text:
            continue
        assert EMAIL in text, path.name
        assert f'"{SHORT}"' not in text, path.name
        assert f"'{SHORT}'" not in text, path.name
    chain = (ROOT / "src" / "vigil" / "federation" / "hash_chain.py").read_text(encoding="utf-8")
    assert EMAIL in chain
    assert f'"{SHORT}"' not in chain
