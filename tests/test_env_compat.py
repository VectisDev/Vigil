"""VIGIL_* environment variables, with the pre-rename CENTINEL_* names as fallback."""

from __future__ import annotations

import os

import pytest

from vigil.core import profiles

_NAMES = ("MODE", "REQUIRE_SIGNATURE", "DISABLE_OPENTIMESTAMPS")


@pytest.fixture(autouse=True)
def _clean_env():
    keys = [f"{prefix}_{name}" for prefix in ("VIGIL", "CENTINEL") for name in _NAMES]
    saved = {k: os.environ.pop(k) for k in keys if k in os.environ}
    yield
    for k in keys:
        os.environ.pop(k, None)  # apply_profile_defaults writes straight to os.environ
    os.environ.update(saved)


def test_legacy_name_still_works():
    os.environ["CENTINEL_MODE"] = "election"
    assert profiles.resolve_mode() == "election"


def test_new_name_wins_over_legacy():
    os.environ["CENTINEL_MODE"] = "election"
    os.environ["VIGIL_MODE"] = "monitoring"
    assert profiles.resolve_mode() == "monitoring"


def test_profile_default_does_not_override_explicit_legacy_choice():
    os.environ["VIGIL_MODE"] = "election"  # election requires signatures by default
    os.environ["CENTINEL_REQUIRE_SIGNATURE"] = "false"  # operator opted out, pre-rename name

    summary = profiles.apply_profile_defaults()

    assert "VIGIL_REQUIRE_SIGNATURE" not in summary["defaults_applied"]
    assert "VIGIL_REQUIRE_SIGNATURE" not in os.environ
    assert os.environ["CENTINEL_REQUIRE_SIGNATURE"] == "false"


def test_profile_default_applies_new_name_when_nothing_is_set():
    os.environ["VIGIL_MODE"] = "election"

    summary = profiles.apply_profile_defaults()

    assert summary["defaults_applied"]["VIGIL_REQUIRE_SIGNATURE"] == "true"
    assert os.environ["VIGIL_REQUIRE_SIGNATURE"] == "true"
