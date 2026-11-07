"""A CRITICAL rule is not settled just because it fired on the 2025 sample.

Una regla CRITICAL no queda asentada solo porque disparó en la muestra de 2025.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "command_center" / "rules.yaml"
PROMOTION = ROOT / "tests" / "fixtures" / "promotion"


def test_critical_rules_stay_exploratory_without_an_outside_fixture() -> None:
    document = yaml.safe_load(RULES.read_text(encoding="utf-8"))
    rules = document["rules"]
    problems: list[str] = []
    for key, cfg in rules.items():
        if not isinstance(cfg, dict):
            continue
        if str(cfg.get("severity", "")).upper() != "CRITICAL":
            continue
        outside = PROMOTION / f"{key}.json"
        declared = str(cfg.get("promotion", "")).lower()
        if outside.is_file():
            continue
        if declared != "exploratory":
            problems.append(f"{key}: severity CRITICAL, promotion={declared or 'missing'}, no {outside.name}")
    assert problems == []
