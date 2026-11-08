"""Default fetches name themselves and do not hide."""

from __future__ import annotations

import tomllib
from pathlib import Path

import yaml

from vigil.identity import STEALTH_FOR_SOURCE, USER_AGENT, VERSION

ROOT = Path(__file__).resolve().parents[1]


def test_default_user_agent_names_this_version() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert VERSION == project["tool"]["poetry"]["version"]
    assert USER_AGENT == f"VIGIL/{VERSION} (+https://github.com/VectisDev/Vigil)"
    assert STEALTH_FOR_SOURCE is False


def test_published_config_uses_that_name_and_leaves_stealth_off() -> None:
    config = yaml.safe_load((ROOT / "command_center" / "config.yaml").read_text(encoding="utf-8"))
    assert config["headers"]["User-Agent"] == USER_AGENT
    assert config["playwright_stealth"] is False
    security = yaml.safe_load((ROOT / "command_center" / "advanced_security_config.yaml").read_text(encoding="utf-8"))
    assert security["user_agents_list"] == [USER_AGENT]


def test_source_scraper_does_not_use_stealth() -> None:
    text = (ROOT / "src" / "vigil" / "core" / "scraping.py").read_text(encoding="utf-8")
    assert "playwright_stealth" not in text
    assert "playwright-stealth" not in text
    assert "webdriver" not in text
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "playwright-stealth" not in deps["tool"]["poetry"]["dependencies"]
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "playwright-stealth" not in requirements
