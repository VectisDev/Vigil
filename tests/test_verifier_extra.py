"""Playwright and WeasyPrint are not required to verify the sample.

Playwright y WeasyPrint no hacen falta para verificar la muestra.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_report_tools_are_optional_extras() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = project["tool"]["poetry"]["dependencies"]
    for name in ("playwright", "playwright-stealth", "WeasyPrint"):
        spec = deps[name]
        assert isinstance(spec, dict) and spec.get("optional") is True, name
    extra = project["tool"]["poetry"]["extras"]["reports"]
    assert set(extra) == {"playwright", "playwright-stealth", "WeasyPrint"}


def test_verify_requirements_install_nothing() -> None:
    lines = [
        line.strip()
        for line in (ROOT / "requirements" / "verify.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert lines == []
