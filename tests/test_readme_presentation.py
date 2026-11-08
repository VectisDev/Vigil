"""The front page keeps the approved brand lines.

La portada conserva las frases de marca ya aprobadas.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spanish_readme_keeps_the_brand_lines() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for line in (
        "Integridad electoral verificable",
        "Tres maneras de empezar",
        "Verificable por cualquiera. Sin pedirnos permiso.",
        "docs/brand/banner-claro.svg",
        "docs/brand/banner-oscuro.svg",
        "docs/images/panel-claro.png",
        "docs/images/panel-oscuro.png",
    ):
        assert line in text, line
    assert "2b6cb0" not in text
    assert "2f855a" not in text


def test_english_readme_mirrors_the_brand() -> None:
    text = (ROOT / "README.en.md").read_text(encoding="utf-8")
    for line in (
        "Verifiable electoral integrity",
        "Three ways to start",
        "Anyone can verify it. You do not need our permission.",
        "docs/brand/banner-claro.svg",
        "docs/images/panel-oscuro.png",
    ):
        assert line in text, line
    assert "2b6cb0" not in text
    assert "2f855a" not in text
