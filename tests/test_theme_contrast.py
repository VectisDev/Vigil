"""El rojo de cada modo cumple AA sobre el único fondo de ese modo.

Light mode paints #D7262E on white. Dark mode paints #FF4D55 on black.
White text on the dark red fails AA, so dark-mode fills use black text.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
THEME = REPO / "web" / "shared" / "vigil-theme.css"


def _channel(value: float) -> float:
    value = value / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def contrast(foreground: str, background: str) -> float:
    def luminance(hex_color: str) -> float:
        hex_color = hex_color.lstrip("#")
        red, green, blue = (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )
        return (
            0.2126 * _channel(red)
            + 0.7152 * _channel(green)
            + 0.0722 * _channel(blue)
        )

    lighter = max(luminance(foreground), luminance(background))
    darker = min(luminance(foreground), luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def test_both_reds_pass_aa_on_their_background():
    assert contrast("#D7262E", "#FFFFFF") >= 4.5
    assert contrast("#FFFFFF", "#D7262E") >= 4.5
    assert contrast("#FF4D55", "#000000") >= 4.5
    assert contrast("#000000", "#FF4D55") >= 4.5
    # White on the dark-mode red is below AA for normal text.
    assert contrast("#FFFFFF", "#FF4D55") < 4.5


def test_secondary_ink_passes_aa():
    assert contrast("#1A1A1A", "#FFFFFF") >= 4.5
    assert contrast("#F2F2F2", "#000000") >= 4.5


def test_stylesheet_names_the_two_reds_and_both_backgrounds():
    text = THEME.read_text(encoding="utf-8")
    assert "#D7262E" in text
    assert "#FF4D55" in text
    assert "--bg: #ffffff" in text
    assert "--bg: #000000" in text
    assert "--on-red: #ffffff" in text
    assert "--on-red: #000000" in text
