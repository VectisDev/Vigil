"""Ningún control del panel se pinta a fuego: todo el color pasa por el tema.

No control in the panel is painted literally: every colour goes through a token.

`ops-v4.css` nació como una hoja de un solo modo y escribía `#000` y `#fff`
directamente en 38 reglas. `vigil-theme.css` da color a los contenedores —body,
`.card`, `.metric`— pero nunca tuvo una regla para `button`, `input` ni
`select`, así que en modo noche el fondo de la página se oscurecía y **cada
botón seguía siendo blanco puro con texto negro**. Dieciséis controles
flotando como pegatinas sobre negro, y el borde `1px solid #000` de `.hero` y
de las tarjetas quedaba negro sobre negro, es decir invisible: la estructura
de la página desaparecía justo en el modo donde más se nota.

Lo mismo valía al revés para el anillo de foco: `outline:3px solid #000` sobre
fondo negro no se ve, y ése es el único indicador que tiene quien navega con
teclado.

Tres invariantes:

1. **Estática** — en `ops-v4.css` un literal de color solo puede ser el valor
   de una propiedad personalizada. Un `background:#fff` suelto vuelve a
   romperlo, y aquí falla.
2. **Estática** — cada token que la hoja consume está definido en los DOS
   modos de `vigil-theme.css`. Uno definido solo en el respaldo claro daría
   color claro en modo noche sin que nada avisara.
3. **De navegador** — con el panel abierto de verdad, ningún control visible
   lleva el fondo del modo contrario, el texto llega a 4.5:1 contra su propio
   fondo y el borde a 3:1 contra la página, salvo que sea transparente a
   propósito, como las pestañas.

La tercera es la que vale: las dos primeras leen el archivo, y un color puede
entrar por cualquier otra hoja. Ésta mide lo que se ve.

English: `ops-v4.css` was born single-mode and wrote `#000`/`#fff` into 38
rules. The theme sheet colours containers but never had a rule for `button`,
`input` or `select`, so in dark mode the page went dark and every button stayed
pure white -- sixteen controls floating like stickers -- while the `1px solid
#000` borders went black-on-black, invisible. The focus ring had the same fault,
and it is the only indicator a keyboard user gets. The third test is the one
that counts: the first two read a file, and colour can arrive from any sheet.
"""

from __future__ import annotations

import functools
import http.server
import os
import re
import socket
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB = REPO_ROOT / "web"
HOJA_OPS = WEB / "ops" / "ops-v4.css"
HOJA_TEMA = WEB / "shared" / "vigil-theme.css"
CHROMIUM = Path("/opt/pw-browsers/chromium")

REQUIRE_BROWSER = os.environ.get("VIGIL_REQUIRE_BROWSER") == "1"

BLOQUE = re.compile(r"\{([^{}]*)\}")
LITERAL = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:white|black)\b", re.IGNORECASE)
USO_DE_TOKEN = re.compile(r"var\(\s*(--[\w-]+)")

# Mide cada control visible dentro del panel ya abierto.
_SONDA_DE_CONTROLES = """
        () => {
          const salida = [];
          for (const el of document.querySelectorAll('button,input,select')) {
            const caja = el.getBoundingClientRect();
            if (!caja.width || !caja.height) continue;
            const cs = getComputedStyle(el);
            salida.push({
              texto: (el.textContent || el.type || '').trim().slice(0, 30),
              clase: el.className || '(sin clase)',
              fondo: cs.backgroundColor,
              tinta: cs.color,
              borde: cs.borderTopColor
            });
          }
          return salida;
        }
        """

_ABRIR_PANEL = "() => window.showAdminShell()"


def _rgb(valor: str) -> tuple[int, int, int]:
    numeros = [int(n) for n in re.findall(r"\d+", valor or "")[:3]]
    return tuple(numeros) if len(numeros) == 3 else (0, 0, 0)  # type: ignore[return-value]


def _es_transparente(valor: str) -> bool:
    encontrado = re.search(r"rgba\([^)]*,\s*0\s*\)$", valor or "")
    return encontrado is not None


def _luminancia(color: tuple[int, int, int]) -> float:
    canales = []
    for bruto in color:
        c = bruto / 255
        canales.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canales[0] + 0.7152 * canales[1] + 0.0722 * canales[2]


def _contraste(uno: tuple[int, int, int], otro: tuple[int, int, int]) -> float:
    alto, bajo = sorted((_luminancia(uno), _luminancia(otro)), reverse=True)
    return (alto + 0.05) / (bajo + 0.05)


def _declaraciones(css: str) -> list[tuple[str, str, str]]:
    """Cada `propiedad: valor` de la hoja, con el bloque del que viene."""
    salida = []
    for bloque in BLOQUE.findall(css):
        for trozo in bloque.split(";"):
            if ":" not in trozo:
                continue
            propiedad, _, valor = trozo.partition(":")
            salida.append((propiedad.strip(), valor.strip(), bloque))
    return salida


def _tokens_del_tema(modo: str) -> set[str]:
    css = HOJA_TEMA.read_text(encoding="utf-8")
    encontrado = re.search(r'html\[data-theme="%s"\]\s*\{([^{}]*)\}' % modo, css)
    assert encontrado, f"vigil-theme.css no declara el modo {modo}"
    return set(re.findall(r"(--[\w-]+)\s*:", encontrado.group(1)))


# ── lo que se puede leer del archivo ──────────────────────────────────────────


def test_el_color_literal_solo_vive_en_las_propiedades_personalizadas() -> None:
    """Un `background:#fff` suelto es un control que ignora el modo noche."""
    culpables = []
    for propiedad, valor, _ in _declaraciones(HOJA_OPS.read_text(encoding="utf-8")):
        if propiedad.startswith("--"):
            continue  # el respaldo claro, para cuando la hoja de tema no carga
        # `var(--bg, #ffffff)` lleva el literal DENTRO del token, como
        # respaldo por si no esta definido. Ese patron es correcto y no cuenta.
        sin_respaldos = re.sub(r"var\([^()]*\)", "", valor)
        if LITERAL.search(sin_respaldos):
            culpables.append(f"{propiedad}: {valor}")

    assert not culpables, (
        "estas declaraciones de ops-v4.css escriben el color a fuego, así que no "
        f"cambian con el modo: {culpables}. El color va por var(--fg), var(--bg), "
        "var(--border) o var(--hairline); los literales solo como respaldo en :root."
    )


def test_la_hoja_del_panel_consume_los_tokens_del_tema() -> None:
    """Si no los usara, la invariante anterior se cumpliría sin hacer nada."""
    css = HOJA_OPS.read_text(encoding="utf-8")
    usados = set(USO_DE_TOKEN.findall(css))
    for token in ("--fg", "--bg", "--border", "--hairline"):
        assert token in usados, f"ops-v4.css no usa {token} en ninguna parte"


def test_cada_token_que_usa_el_panel_existe_en_los_dos_modos() -> None:
    """Uno definido solo en el respaldo daría color claro de noche, en silencio."""
    css = HOJA_OPS.read_text(encoding="utf-8")
    usados = set(USO_DE_TOKEN.findall(css))
    claro, oscuro = _tokens_del_tema("light"), _tokens_del_tema("dark")

    faltan = {t: [] for t in sorted(usados)}
    for token in sorted(usados):
        if token not in claro:
            faltan[token].append("light")
        if token not in oscuro:
            faltan[token].append("dark")
    huerfanos = {t: m for t, m in faltan.items() if m}

    assert not huerfanos, (
        f"ops-v4.css consume tokens que vigil-theme.css no define: {huerfanos}. "
        "Un token sin definir cae en el respaldo claro de :root y el modo noche "
        "se pinta de día sin que nada falle."
    )


# ── lo que solo se puede ver en un navegador ──────────────────────────────────
#
# El marcador va escrito entero en cada prueba y no como alias: el candado de
# `test_browser_tests_run_in_ci.py` lo busca por TEXTO, y un alias se le
# escapa. Tampoco va como `pytestmark` de modulo, porque el job normal corre
# `pytest -q` sin filtro y alli las de navegador se omiten: marcar el modulo
# entero omitiria tambien las tres pruebas estaticas de arriba, que si pueden
# correr en cualquier sitio.


@pytest.fixture(scope="module")
def site() -> str:
    """Sirve `web/` por HTTP: con `file://` los scripts del panel no arrancan."""
    with socket.socket() as sonda:
        sonda.bind(("127.0.0.1", 0))
        puerto = sonda.getsockname()[1]

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB))
    handler.log_message = lambda *args, **kwargs: None  # type: ignore[assignment]
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", puerto), handler)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        yield f"http://127.0.0.1:{puerto}"
    finally:
        servidor.shutdown()
        servidor.server_close()


@pytest.fixture(scope="module")
def browser():
    """El navegador, u omitir si no hay uno utilizable.

    Se caza solo el fallo de ARRANQUE, nunca lo que pase dentro de la prueba:
    una guarda más ancha convertiría un fallo real en una omisión, que es la
    peor de las dos salidas porque se ve igual que un verde.
    """
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    opciones = {"args": ["--no-sandbox"]}
    if CHROMIUM.exists():
        opciones["executable_path"] = str(CHROMIUM)
    with sync_playwright() as play:
        try:
            instancia = play.chromium.launch(**opciones)
        except Exception as exc:  # pragma: no cover - entorno sin navegador
            if REQUIRE_BROWSER:
                raise AssertionError(
                    "VIGIL_REQUIRE_BROWSER=1 pero el navegador no arranca, asi que "
                    f"la instalacion de Chromium fallo en este job: {exc}"
                ) from exc
            pytest.skip(f"no hay navegador utilizable: {exc}")
        try:
            yield instancia
        finally:
            instancia.close()


def _panel_abierto(browser, site: str, modo: str):
    """Abre el panel ya autenticado, con el modo fijado ANTES de cargar.

    El modo se deja en `localStorage` con un guion de inicio y no con un
    `evaluate` posterior: `vigil-theme.js` corre al cargar la pagina, asi que
    fijarlo despues cambia el atributo pero deja la etiqueta del conmutador
    diciendo lo contrario de lo que esta puesto.
    """
    contexto = browser.new_context()
    pagina = contexto.new_page()
    pagina.add_init_script(script="try { localStorage.setItem('vigil-theme', '%s'); } catch (e) {}" % modo)
    pagina.goto(f"{site}/ops/")
    pagina.evaluate(_ABRIR_PANEL)
    pagina.wait_for_timeout(600)
    return contexto, pagina


@pytest.mark.browser
@pytest.mark.parametrize("modo", ["light", "dark"])
def test_ningun_control_visible_se_pinta_del_modo_contrario(browser, site: str, modo: str) -> None:
    """El fallo que se veía: dieciséis botones blancos sobre fondo negro."""
    contexto, pagina = _panel_abierto(browser, site, modo)

    assert pagina.evaluate("() => document.documentElement.getAttribute('data-theme')") == modo
    fondo_pagina = _rgb(pagina.evaluate("() => getComputedStyle(document.body).backgroundColor"))
    controles = pagina.evaluate(_SONDA_DE_CONTROLES)
    contexto.close()

    assert controles, "el panel no mostró ningún control: la sonda no mediría nada"

    quejas = []
    for control in controles:
        fondo = _rgb(control["fondo"]) if not _es_transparente(control["fondo"]) else fondo_pagina
        tinta = _rgb(control["tinta"])
        etiqueta = f'"{control["texto"]}" [{control["clase"]}]'

        # Un control invertido a propósito —la acción principal, la barra de
        # simulación— sí lleva el fondo contrario. El resto, no.
        invertido = fondo[0] > 200 if modo == "dark" else fondo[0] < 60
        a_proposito = re.search(r"primary|solid|sim|btn-login", control["clase"] + control["texto"])
        if invertido and not a_proposito:
            quejas.append(f"{etiqueta} lleva el fondo del modo contrario: {control['fondo']}")

        razon = _contraste(tinta, fondo)
        if razon < 4.5:
            quejas.append(f"{etiqueta} tiene el texto a {razon:.2f}:1 sobre su fondo")

        if not _es_transparente(control["borde"]):
            razon_borde = _contraste(_rgb(control["borde"]), fondo_pagina)
            if razon_borde < 3.0:
                quejas.append(f"{etiqueta} tiene el borde a {razon_borde:.2f}:1 contra la página")

    assert not quejas, "modo " + modo + ":\n  " + "\n  ".join(quejas)


@pytest.mark.browser
@pytest.mark.parametrize("modo", ["light", "dark"])
def test_el_anillo_de_foco_se_ve_en_los_dos_modos(browser, site: str, modo: str) -> None:
    """Era `outline:3px solid #000`: sobre negro, invisible."""
    contexto, pagina = _panel_abierto(browser, site, modo)

    fondo_pagina = _rgb(pagina.evaluate("() => getComputedStyle(document.body).backgroundColor"))
    contorno = pagina.evaluate(
        "() => { const b = document.querySelector('#admin-shell button'); b.focus();"
        " return getComputedStyle(b).outlineColor; }"
    )
    contexto.close()

    razon = _contraste(_rgb(contorno), fondo_pagina)
    assert razon >= 3.0, (
        f"en modo {modo} el anillo de foco queda a {razon:.2f}:1 contra la página "
        f"({contorno}). Es el único indicador de quien navega con teclado."
    )
