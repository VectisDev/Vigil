"""Cada modo cumple AA, y el oscuro no es el modo de alto contraste.

Each mode meets AA, and the dark one is not the high-contrast mode.

Esta versión **lee los valores de la hoja** en vez de repetirlos. La anterior
los tenía escritos a mano en tres pruebas, y al cambiar la paleta falló por
decir `#000000` donde ya ponía otra cosa — que es la forma en que una prueba
de valores literales avisa de que se quedó atrás, en el mejor de los casos; en
el peor sigue pasando mientras describe una hoja que ya no existe.

Lo que se comprueba es la propiedad: contraste suficiente para leer, jerarquía
entre lo principal y lo secundario, y un borde de control visible. Cambiar la
paleta por otra igual de legible pasa; volver a blanco puro sobre negro puro,
no.

Corre sin navegador, así que vale en todos los jobs. La de
`test_theme.py::test_the_dark_theme_is_not_the_high_contrast_theme` mide lo
mismo sobre lo que el navegador pinta de verdad; ésta mira la fuente. Hacen
falta las dos: una hoja correcta puede pintarse mal, y una hoja equivocada
puede verse bien hasta que alguien cambia otra cosa.

English: this reads the values out of the stylesheet instead of repeating
them. The previous version had them hand-written in three tests and broke when
the palette changed -- which is a literal-value test telling you it fell
behind, in the best case; in the worst it keeps passing while describing a
sheet that no longer exists. What is checked is the property: enough contrast
to read, hierarchy between primary and secondary, and a visible control
border.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
THEME = REPO / "web" / "shared" / "vigil-theme.css"


def _channel(value: float) -> float:
    value = value / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    red, green, blue = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast(foreground: str, background: str) -> float:
    lighter = max(_luminance(foreground), _luminance(background))
    darker = min(_luminance(foreground), _luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def tokens(theme: str) -> dict[str, str]:
    """Los tokens hexadecimales que la hoja declara para un modo."""
    text = THEME.read_text(encoding="utf-8")
    block = re.search(rf'html\[data-theme="{theme}"\]\s*\{{(.*?)\}}', text, re.S)
    assert block, f"la hoja no declara el modo {theme!r}"
    return {
        name: value.lower() for name, value in re.findall(r"(--[a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;", block.group(1))
    }


THEMES = ("light", "dark")


# ── lo que hay que poder leer ────────────────────────────────────────────────


@pytest.mark.parametrize("theme", THEMES)
def test_body_text_passes_aaa(theme: str):
    """AAA para el texto corrido: 7:1. Es texto que se lee entero, no un rótulo."""
    t = tokens(theme)
    ratio = contrast(t["--fg"], t["--bg"])
    assert ratio >= 7.0, f"{theme}: texto principal {ratio:.2f}:1"


@pytest.mark.parametrize("theme", THEMES)
def test_secondary_text_passes_aa(theme: str):
    t = tokens(theme)
    ratio = contrast(t["--muted"], t["--bg"])
    assert ratio >= 4.5, f"{theme}: texto secundario {ratio:.2f}:1"


@pytest.mark.parametrize("theme", THEMES)
def test_the_red_passes_aa_on_its_background(theme: str):
    t = tokens(theme)
    ratio = contrast(t["--red"], t["--bg"])
    assert ratio >= 4.5, f"{theme}: el rojo sobre el fondo {ratio:.2f}:1"


@pytest.mark.parametrize("theme", THEMES)
def test_the_text_on_a_red_fill_passes_aa(theme: str):
    """Un botón relleno de rojo necesita que su texto se lea sobre el rojo."""
    t = tokens(theme)
    ratio = contrast(t["--on-red"], t["--red"])
    assert ratio >= 4.5, f"{theme}: texto sobre relleno rojo {ratio:.2f}:1"


@pytest.mark.parametrize("theme", THEMES)
def test_the_control_border_is_visible(theme: str):
    """WCAG 1.4.11: 3:1 para que el borde de un control se vea."""
    t = tokens(theme)
    ratio = contrast(t["--border"], t["--bg"])
    assert ratio >= 3.0, f"{theme}: borde de control {ratio:.2f}:1"


# ── lo que no debe volver a pasar ────────────────────────────────────────────


def test_the_dark_mode_is_not_maximum_contrast():
    """21:1 es blanco puro sobre negro puro, y eso es otra cosa.

    El modo de alto contraste lo ofrece el sistema operativo, aparte, a quien
    lo necesita y lo pide. Como estilo por defecto produce halación y, en
    OLED, arrastre al desplazarse.
    """
    t = tokens("dark")
    ratio = contrast(t["--fg"], t["--bg"])
    assert ratio <= 19.0, (
        f"el texto esta en {ratio:.2f}:1, practicamente el maximo de 21. "
        f"Eso es el modo de alto contraste, no un tema oscuro legible."
    )
    assert t["--bg"] != "#000000", "el negro puro arrastra en OLED y maximiza la halacion"
    assert t["--fg"] != "#ffffff", "el blanco puro sobre un fondo oscuro brilla en los bordes"


@pytest.mark.parametrize("theme", THEMES)
def test_there_is_a_hierarchy_between_primary_and_secondary(theme: str):
    """Si lo secundario contrasta casi igual, la página entera grita igual.

    Era el fallo invisible del modo noche: `--muted` a #f2f2f2 daba 18.76:1
    frente a los 21:1 del texto principal. Una relación de 1.12x no es una
    jerarquía, es el mismo volumen dos veces.

    English: the dark mode's invisible fault -- muted at 18.76:1 against the
    primary's 21:1 is a ratio of 1.12x, which is not a hierarchy but the same
    volume twice.
    """
    t = tokens(theme)
    primary = contrast(t["--fg"], t["--bg"])
    secondary = contrast(t["--muted"], t["--bg"])
    assert primary / secondary >= 1.5, (
        f"{theme}: principal {primary:.2f}:1 y secundario {secondary:.2f}:1 "
        f"son casi lo mismo ({primary / secondary:.2f}x)"
    )


def test_white_on_the_dark_red_still_fails_aa():
    """Por esto el relleno rojo del modo oscuro no lleva texto blanco.

    English: this is why the dark mode's red fill does not carry white text.
    """
    assert contrast("#FFFFFF", tokens("dark")["--red"]) < 4.5


@pytest.mark.parametrize("theme", THEMES)
def test_the_stylesheet_declares_every_token_these_tests_read(theme: str):
    """Una prueba que no encuentra el token pasaría sin comprobar nada."""
    t = tokens(theme)
    for name in ("--bg", "--fg", "--muted", "--red", "--on-red", "--border"):
        assert name in t, f"{theme}: la hoja no declara {name}"
