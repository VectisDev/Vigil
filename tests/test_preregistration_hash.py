"""The pre-registration page must quote the file it claims to lock.

La página de umbrales tiene que citar el archivo que dice estar fijando.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "command_center" / "rules.yaml"
DOC = ROOT / "docs" / "research" / "THRESHOLD_PREREGISTRATION.md"
STALE = "a15df9d95d96e5f10a6935b2e5a18b71640a6008e1bcd649882453924625493f"


def test_current_rules_yaml_hash_is_the_one_in_the_document() -> None:
    digest = hashlib.sha256(RULES.read_bytes()).hexdigest()
    text = DOC.read_text(encoding="utf-8")
    assert digest in text
    assert digest != STALE


def test_old_lock_is_labeled_as_not_matching() -> None:
    text = DOC.read_text(encoding="utf-8").lower()
    assert STALE in text
    assert "does not match" in text or "no longer matches" in text
