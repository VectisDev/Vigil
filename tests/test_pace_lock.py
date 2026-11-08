"""The respectful pace holds unless a signed commit accepts it."""

from __future__ import annotations

from pathlib import Path

import yaml

from vigil.pace import (
    STATEMENTS,
    apply_pace,
    override_is_refused,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pace-lock.yml"


def test_inside_the_lock_needs_no_signature() -> None:
    assert apply_pace(240, 10, 3, None, False) == (240, 10, 3)
    assert override_is_refused(None, False) is False


def test_past_the_lock_is_clamped_without_a_signed_statement() -> None:
    assert apply_pace(900, 0.2, 20, None, False) == (480, 1.0, 8)
    text = "max_requests_per_hour: 900\n" + f"responsibility: {STATEMENTS[0]}\n"
    assert override_is_refused(text, False) is True
    assert apply_pace(900, 0.2, 20, text, False) == (480, 1.0, 8)


def test_a_signed_statement_is_the_only_way_past_the_lock() -> None:
    text = "max_requests_per_hour: 900\nmin_interval_seconds: 0.5\nmax_burst: 12\n"
    text += f"responsibility: {STATEMENTS[1]}\n"
    assert override_is_refused(text, True) is False
    assert apply_pace(900, 0.5, 12, text, True) == (900, 0.5, 12)


def test_a_signed_file_without_the_statement_is_refused() -> None:
    text = "max_requests_per_hour: 900\nresponsibility: I meant well.\n"
    assert override_is_refused(text, True) is True


def test_the_action_checks_the_override_file() -> None:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    on = doc.get(True, doc.get("on"))
    assert "schedule" not in on
    assert doc["permissions"]["contents"] == "read"
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "scripts/check_rate_override.py" in text
    page = (ROOT / "web" / "ops" / "index.html").read_text(encoding="utf-8")
    assert "This lock exists to be respectful." in page
    assert 'type="password"' not in page
    assert "480" in page
