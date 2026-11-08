"""El panel dice una sola cosa, y no sondea una API que no existe.

The panel says one thing, and does not probe an API that is not there.

Estas pruebas fijan las dos funciones que la fase 0 y la fase 2 introdujeron
en `web/ops/`, y existen por fallos concretos y observados:

`detectMode()` — el panel se publica en GitHub Pages, donde no hay servidor, y
aun así llamaba a `/api/...` desde treinta y un sitios. Cada uno fallaba por su
cuenta y con un mensaje distinto, y un visitante concluía razonablemente que el
sistema estaba roto. No lo estaba: le faltaba el nodo encendido, que es un
estado esperado y no un fallo.

`computeOverallState()` — el encabezado decía «NORMAL / INACTIVO», las tarjetas
decían «CERRADO / NORMAL / PENDIENTE» y encima podía aparecer un error, todo a
la vez y en la misma pantalla. Tres respuestas a la misma pregunta.

Se ejecutan en un navegador de verdad porque es la única forma honesta de
comprobar código que vive en el navegador: reimplementar la lógica en Python
probaría la reimplementación, no el panel.

English: these pin the two functions phases 0 and 2 introduced in `web/ops/`,
and they exist because of concrete observed faults. They run in a real browser
because that is the only honest way to test code that lives in one:
reimplementing the logic in Python would test the reimplementation.
"""

from __future__ import annotations

import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = REPO_ROOT / "web"

pytest.importorskip("playwright.sync_api", reason="playwright no instalado")
from playwright.sync_api import sync_playwright  # noqa: E402


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# Sonda de paleta, en una constante y no en linea: black 25 y black 26
# envuelven distinto un argumento de cadena multilinea, y el CI fija la
# primera mientras el proyecto declara la segunda.
# English: the palette probe lives in a constant because black 25 and 26
# wrap a multiline string argument differently.
_PALETTE_PROBE_JS = """() => {
            const bad = [];
            const hue = (r,g,b) => {
                const mx = Math.max(r,g,b), mn = Math.min(r,g,b), d = mx-mn;
                if (!d) return null;
                let h;
                if (mx === r) h = ((g-b)/d) % 6;
                else if (mx === g) h = (b-r)/d + 2;
                else h = (r-g)/d + 4;
                h *= 60; if (h < 0) h += 360;
                const s = mx ? d/mx : 0;
                return s < 0.25 ? null : h;
            };
            for (const el of document.querySelectorAll('body *')) {
                if (!el.offsetParent && el.tagName !== 'BODY') continue;
                const cs = getComputedStyle(el);
                for (const prop of ['color','backgroundColor','borderTopColor']) {
                    const m = cs[prop].match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?/);
                    if (!m) continue;
                    if (m[4] !== undefined && parseFloat(m[4]) < 0.15) continue;
                    const h = hue(+m[1], +m[2], +m[3]);
                    if (h === null) continue;
                    if (h > 20 && h < 340) {
                        bad.push((el.id || el.className || el.tagName) + ' ' + prop + ' ' + cs[prop]);
                    }
                }
            }
            return [...new Set(bad)].slice(0, 12);
        }"""


@pytest.fixture(scope="module")
def site() -> str:
    """Sirve `web/` igual que GitHub Pages: ficheros estáticos y nada más."""

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(WEB_ROOT), **kw)

        def log_message(self, *a):  # silencio
            pass

    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()


# Algunos entornos traen el navegador en una ruta fija y una build distinta de
# la que Playwright espera por su versión. Se usa la del sistema cuando está,
# porque descargar otra en CI sería lento y no aporta nada.
# English: some environments ship the browser at a fixed path and a different
# build from the one Playwright expects by version. Use the system one when
# present rather than downloading another in CI.
_SYSTEM_CHROMIUM = Path("/opt/pw-browsers/chromium")


@pytest.fixture(scope="module")
def browser():
    try:
        with sync_playwright() as pw:
            kwargs = {"args": ["--no-sandbox"]}
            if _SYSTEM_CHROMIUM.exists():
                kwargs["executable_path"] = str(_SYSTEM_CHROMIUM)
            b = pw.chromium.launch(**kwargs)
            try:
                yield b
            finally:
                b.close()
    except Exception as exc:  # pragma: no cover - entorno sin navegador
        pytest.skip(f"no hay navegador utilizable: {exc}")


@pytest.fixture
def page(browser, site):
    p = browser.new_page()
    p.goto(f"{site}/ops/", wait_until="domcontentloaded")
    p.wait_for_function("typeof window.detectMode === 'function'", timeout=10000)
    yield p
    p.close()


# ── detectMode() ─────────────────────────────────────────────────────────────


def test_detect_mode_is_pages_without_an_api_base(page):
    """Sin `VIGIL_API_BASE` no hay servidor que sondear: es `pages`."""
    page.evaluate("() => { window.VIGIL_API_BASE = undefined; window.OPS_MODE = null; }")
    assert page.evaluate("() => detectMode()") == "pages"


def test_detect_mode_falls_back_to_pages_when_the_probe_fails(page):
    """Un servidor declarado que no responde no es un servidor.

    English: a declared server that does not answer is not a server. Failing
    the other way would leave every section waiting on requests that never
    arrive -- which is exactly the "Loading…" that never ended.
    """
    page.evaluate("() => { window.VIGIL_API_BASE = 'http://127.0.0.1:1'; window.OPS_MODE = null; }")
    assert page.evaluate("() => detectMode()") == "pages"


def test_detect_mode_is_resolved_once_and_reused(page):
    """Se resuelve una vez. Cada sección lo consulta, no lo vuelve a medir."""
    page.evaluate("() => { window.OPS_MODE = 'servidor'; }")
    assert page.evaluate("() => detectMode()") == "servidor"


def test_pages_mode_issues_no_api_request(page):
    """En modo `pages` la petición NO sale.

    English: in `pages` mode the request is never issued. This is the point of
    the choke point: before it, each call went out, failed against Pages and
    filled the console with 404s that read as a broken system.
    """
    seen: list[str] = []
    page.on("request", lambda r: seen.append(r.url) if "/api/" in r.url else None)
    page.evaluate("() => { window.VIGIL_API_BASE = undefined; window.OPS_MODE = 'pages'; }")
    rejected = page.evaluate("() => opsApi('/api/pipeline/status').then(() => 'resolvio', e => e.opsOffline === true)")
    assert rejected is True, "opsApi debe rechazar con el error etiquetado"
    assert seen == [], f"no debe salir ninguna peticion: {seen}"


def test_the_offline_error_is_recognisable(page):
    """El error se distingue de un fallo real, o no se puede tratar distinto."""
    page.evaluate("() => { window.OPS_MODE = 'pages'; }")
    assert page.evaluate("() => opsApi('/api/x').catch(e => opsIsOffline(e))") is True
    assert page.evaluate("() => opsIsOffline(new Error('otra cosa'))") is False


# ── computeOverallState() ────────────────────────────────────────────────────


def _state(page, *, mode="servidor", pipeline=None, lang="es"):
    page.evaluate(
        """([mode, pipeline, lang]) => {
            window.OPS_MODE = mode;
            window.OPS_LANG = lang;
            window._opsPipelineState = pipeline || {};
        }""",
        [mode, pipeline, lang],
    )
    return page.evaluate("() => computeOverallState()")


def test_no_node_is_idle_and_not_an_error(page):
    """Sin nodo el semáforo es gris, nunca rojo.

    English: with no node the light is grey, never red. Between elections the
    panel will legitimately sit grey for years; painting that red would teach
    people to ignore reds.
    """
    s = _state(page, mode="pages")
    assert s["level"] == "idle"
    assert "no está encendido" in s["headline"]
    assert s["action"] == "node", "debe ofrecer una salida, no solo informar"


def test_paused_is_idle(page):
    s = _state(page, pipeline={"running": False})
    assert s["level"] == "idle"
    assert s["headline"] == "Pausado"


def test_running_and_fresh_is_ok(page):
    s = _state(page, pipeline={"running": True, "lastMinutes": 4, "source": "cne.hn"})
    assert s["level"] == "ok"
    assert "cne.hn" in s["headline"]
    assert "4 min" in s["detail"]


def test_running_but_stale_is_a_problem(page):
    """Capturando pero sin datos nuevos en horas NO está bien.

    English: capturing but with no new data for hours is NOT fine, even though
    the process is alive. A panel that reports the process instead of the
    result would call this green, which is the exact failure this project
    exists to catch.
    """
    s = _state(page, pipeline={"running": True, "lastMinutes": 240})
    assert s["level"] == "bad"
    assert "240 min" in s["headline"]
    assert s["action"] == "help", "un problema tiene que decir qué hacer"


def test_an_explicit_error_is_a_problem_and_names_itself(page):
    s = _state(page, pipeline={"running": True, "error": "la fuente devolvió 503"})
    assert s["level"] == "bad"
    assert "503" in s["headline"], "el veredicto nombra su causa"


def test_the_state_speaks_the_selected_language(page):
    s = _state(page, mode="pages", lang="en")
    assert s["level"] == "idle"
    assert "not running" in s["headline"]
    assert "está" not in s["headline"], "no se mezclan idiomas en una pantalla"


@pytest.mark.parametrize("minutes,expected", [(0, "ok"), (179, "ok"), (181, "bad")])
def test_the_staleness_threshold_is_where_it_says(page, minutes, expected):
    s = _state(page, pipeline={"running": True, "lastMinutes": minutes})
    assert s["level"] == expected


# ── el semáforo y las pestañas leen de esa única función ─────────────────────


def test_the_rendered_headline_comes_from_the_state_function(page):
    """Lo que se ve y lo que la función dice no pueden discrepar.

    English: what is shown and what the function says cannot disagree. Three
    places used to decide this, and they contradicted each other on screen.
    """
    page.evaluate("() => { try { showAdminShell(); } catch(e) {} }")
    page.wait_for_timeout(500)
    s = _state(page, pipeline={"running": True, "lastMinutes": 2, "source": "cne.hn"})
    page.evaluate("() => renderOverallState()")
    shown = page.eval_on_selector("#hero-headline", "e => e.textContent")
    assert shown == s["headline"]


def test_every_section_belongs_to_exactly_one_tab(page):
    """Ninguna sección queda huérfana ni duplicada entre pestañas."""
    tabs = page.evaluate(
        "() => [...document.querySelectorAll('#main-area > .section')]"
        ".map(e => ({id: e.id, tab: e.getAttribute('data-tab')}))"
    )
    assert tabs, "no se encontraron secciones"
    for s in tabs:
        assert s["tab"] in ("inicio", "evidencia", "red", "avanzado"), s


def test_switching_tabs_shows_one_tab_and_hides_the_rest(page):
    page.evaluate("() => { try { showAdminShell(); } catch(e) {} }")
    page.wait_for_timeout(400)
    for tab in ("inicio", "evidencia", "red", "avanzado"):
        page.evaluate("t => goTab(t)", tab)
        shown = page.evaluate(
            "() => [...document.querySelectorAll('#main-area > [data-tab]')]"
            ".filter(e => !e.hidden).map(e => e.getAttribute('data-tab'))"
        )
        assert set(shown) == {tab}, f"{tab}: se ven {set(shown)}"


def test_the_inicio_section_is_not_nested_inside_another(page):
    """Inicio es hermano de las demás, no hijo.

    English: Inicio is a sibling, not a child. It was briefly nested inside
    the evidence section, so switching tabs hid it along with its parent and
    the main screen came up blank.
    """
    parent = page.evaluate("() => document.getElementById('s0').parentElement.id")
    assert parent == "main-area"


# ── el candado de la paleta, desde el navegador ──────────────────────────────


def test_no_section_renders_with_a_colour_outside_the_palette(page):
    """Nada pintado en azul, amarillo ni morado, medido sobre lo renderizado.

    English: nothing painted blue, yellow or purple, measured on what the
    browser actually computed -- not on the source. A token can resolve to
    something the stylesheet never spells out.
    """
    page.evaluate("() => { try { showAdminShell(); } catch(e) {} }")
    page.wait_for_timeout(800)
    offenders = page.evaluate(_PALETTE_PROBE_JS)
    assert offenders == [], f"colores fuera de paleta en pantalla: {offenders}"
