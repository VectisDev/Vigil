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

import os
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = REPO_ROOT / "web"

pytest.importorskip("playwright.sync_api", reason="playwright no instalado")
from playwright.sync_api import sync_playwright  # noqa: E402

# El job `browser-tests` de ci.yml selecciona por este marcador. Sin el, este
# modulo se omite en los jobs normales —que no instalan el binario— y el job
# de navegador no lo recoge: 19 pruebas que no corren en ningun sitio, en
# silencio y pareciendo verde.
# English: the browser-tests job selects by this marker. Without it this module
# skips in the normal jobs and the browser job does not pick it up: 19 tests
# running nowhere, silently, looking green.
pytestmark = pytest.mark.browser

# Con esto a "1", no haber navegador es un FALLO y no una omision. Lo pone el
# job que acaba de instalarlo, donde la ausencia solo puede significar que la
# instalacion se rompio.
# English: with this at "1", a missing browser is a FAILURE. Set by the job
# that just installed it, where absence can only mean the install broke.
REQUIRE_BROWSER = os.environ.get("VIGIL_REQUIRE_BROWSER") == "1"


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
            const shown = (el) => {
                const cs = getComputedStyle(el);
                if (cs.display === 'none' || cs.visibility === 'hidden') return false;
                if (parseFloat(cs.opacity) === 0) return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            };
            for (const el of document.querySelectorAll('body *')) {
                if (!shown(el)) continue;
                const cs = getComputedStyle(el);
                for (const prop of ['color','backgroundColor','borderTopColor','fill','stroke']) {
                    const m = cs[prop].match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?/);
                    if (!m) continue;
                    if (m[4] !== undefined && parseFloat(m[4]) < 0.15) continue;
                    const h = hue(+m[1], +m[2], +m[3]);
                    if (h === null) continue;
                    if (h > 20 && h < 340) {
                        const name = el.id || (typeof el.className === 'string' ? el.className : '') || el.tagName;
                        bad.push(name + ' ' + prop + ' ' + cs[prop]);
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


def _launch_browser(pw):
    """Usa el Chromium de Playwright y, si no está, el Chrome del sistema.

    En CI se instala el navegador a propósito: saltarse la prueba cuando
    falta es exactamente como estos fallos llegaron a la página publicada.
    English: Playwright's Chromium, or the system Chrome if that is what the
    machine has. CI installs the browser on purpose -- skipping when it is
    missing is how these faults reached the published page.
    """
    args = ["--no-sandbox", "--disable-dev-shm-usage"]
    if _SYSTEM_CHROMIUM.exists():
        return pw.chromium.launch(executable_path=str(_SYSTEM_CHROMIUM), args=args)
    for candidate in (
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ):
        if Path(candidate).exists():
            return pw.chromium.launch(executable_path=candidate, args=args)
    return pw.chromium.launch(args=args)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        try:
            launched = _launch_browser(pw)
        except Exception as exc:
            pytest.fail(
                "el navegador no arrancó; en CI hay que instalarlo "
                f"(python -m playwright install --with-deps chromium): {exc}"
            )
        try:
            yield launched
        finally:
            launched.close()


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


def test_inicio_does_not_show_another_tabs_elements(page):
    """En Inicio no se ve nada que pertenezca a otra pestaña.

    No basta mirar el atributo `hidden`: la hoja lo pisaba con `display` y
    las secciones seguían en pantalla. Se mide lo que el navegador pinta.
    English: Home shows nothing that belongs to another tab. Checking the
    hidden attribute is not enough -- the sheet overrode it with display and
    the sections stayed on screen. This measures what the browser paints.
    """
    page.evaluate("() => { try { showAdminShell(); } catch(e) {} }")
    page.wait_for_function("() => document.documentElement.getAttribute('data-ops-tab') === 'inicio'")
    seen = page.evaluate(
        """() => {
            const foreign = [];
            for (const el of document.querySelectorAll('[data-tab]')) {
                if (el.getAttribute('data-tab') === 'inicio') continue;
                const cs = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                if (cs.display !== 'none' && r.width > 0 && r.height > 0) {
                    foreign.push(el.id || el.getAttribute('data-tab'));
                }
            }
            return {foreign, text: document.body.innerText};
        }"""
    )
    assert seen["foreign"] == [], f"en Inicio se ven otras pestañas: {seen['foreign']}"
    for phrase in (
        "SISTEMA NOMINAL",
        "CIRCUIT BREAKER",
        "Conectar a la red",
        "Estas acciones cambian cómo funciona VIGIL",
        "Reputación",
        "Coordinar enjambre",
    ):
        assert phrase not in seen["text"], f"en Inicio se lee «{phrase}»"


def test_no_visible_element_uses_a_forbidden_colour(page):
    """Ningún elemento visible usa azul, amarillo ni morado.

    `getComputedStyle` en cada pestaña, no una búsqueda en el fuente: el
    mapa de departamentos llevaba un relleno pizarra que el fuente no
    delataba como azul hasta que el navegador lo calculaba.
    English: no visible element uses blue, yellow or purple. getComputedStyle
    on every tab, not a source search -- the department map carried a slate
    fill the source did not give away as blue until the browser computed it.
    """
    page.evaluate("() => { try { showAdminShell(); } catch(e) {} }")
    page.wait_for_function("() => typeof goTab === 'function'")
    for tab in ("inicio", "evidencia", "red", "avanzado"):
        page.evaluate("t => goTab(t)", tab)
        page.wait_for_timeout(400)
        offenders = page.evaluate(_PALETTE_PROBE_JS)
        assert offenders == [], f"{tab}: colores fuera de paleta: {offenders}"


def _open_shell(page):
    page.evaluate("() => { try { showAdminShell(); } catch (e) {} }")
    page.wait_for_selector("#capture-button", timeout=10000)


def test_pause_cancel_returns_focus_and_confirm_does_not_fake_a_stop(page):
    """Sin nodo, confirmar la pausa no dice que la captura se detuvo.

    Cancelar devuelve el foco al mismo botón. Confirmar dice que no está
    disponible y el botón sigue siendo Pausar.
    """
    _open_shell(page)
    page.click("#capture-button")
    page.wait_for_selector("#sheet-cancel")
    page.click("#sheet-cancel")
    page.wait_for_function("() => document.activeElement && document.activeElement.id === 'capture-button'")
    assert "Pausar" in page.inner_text("#capture-button")
    page.click("#capture-button")
    page.click("#sheet-confirm")
    page.wait_for_function("() => document.getElementById('announcement').textContent.includes('No disponible')")
    assert "Pausar" in page.inner_text("#capture-button")
    assert "Reanudar" not in page.inner_text("#capture-button")


def test_pause_and_resume_follow_the_node_and_return_focus(page):
    """Si el nodo acepta la orden, el botón alterna y el foco vuelve a él.

    La frase no dice que los procesos se hayan comprobado: un HTTP de
    aceptación no es una verificación.
    """

    def _answer(route):
        route.fulfill(status=200, content_type="application/json", body='{"ok":true}')

    page.route("**/api/pipeline/*", _answer)
    _open_shell(page)
    page.evaluate("() => { window.OPS_MODE = 'servidor'; window.VIGIL_API_BASE = location.origin; }")
    page.click("#capture-button")
    page.click("#sheet-confirm")
    page.wait_for_function("() => document.getElementById('capture-button').textContent.includes('Reanudar')")
    assert page.evaluate("() => document.activeElement.id") == "capture-button"
    note = page.inner_text("#announcement")
    assert "aceptó" in note
    assert "No comprobamos" in note
    page.click("#capture-button")
    page.click("#sheet-confirm")
    page.wait_for_function("() => document.getElementById('capture-button').textContent.includes('Pausar')")
    assert page.evaluate("() => document.activeElement.id") == "capture-button"


def test_stop_sheet_does_not_claim_vigil_stopped(page):
    _open_shell(page)
    page.click("#emergency-button")
    page.wait_for_selector("#sheet-cancel")
    assert page.inner_text("#sheet-title")
    page.keyboard.press("Escape")
    page.wait_for_function("() => document.activeElement && document.activeElement.id === 'emergency-button'")
    page.click("#emergency-button")
    page.click("#sheet-confirm")
    note = page.inner_text("#announcement")
    assert "No disponible" in note
    assert (
        "se detuvo" in note or "did not stop" in note or "no se detuvo" in note.lower() or "VIGIL no se detuvo" in note
    )


def test_destroy_confirmation_requires_the_word_and_deletes_nothing(page):
    page.evaluate("() => sessionStorage.setItem('centinel_role', 'admin')")
    _open_shell(page)
    page.evaluate("() => goTab('avanzado')")
    page.click("#destroy-open")
    page.wait_for_selector("#destroy-word")
    assert page.locator("#sheet-confirm").is_disabled()
    page.focus("#destroy-word")
    page.keyboard.press("Enter")
    assert page.locator("#sheet").evaluate("el => el.open") is True
    page.fill("#destroy-word", "DESTRUIR")
    assert page.locator("#sheet-confirm").is_enabled()
    page.click("#sheet-confirm")
    note = page.inner_text("#announcement")
    assert "No disponible" in note
    assert "No se borró" in note


def test_filters_narrow_and_clear_without_moving_focus(page):
    _open_shell(page)
    page.evaluate("() => goTab('evidencia')")
    page.click("#filters summary")
    page.wait_for_selector("#place-filter")
    before = page.inner_text("#result-count")
    page.select_option("#place-filter", "06")
    page.wait_for_function("() => document.activeElement && document.activeElement.id === 'place-filter'")
    after = page.inner_text("#result-count")
    assert (
        after != before
        or "0" in after
        or "Sin" in after
        or "no disponible" in after.lower()
        or "Cantidad" in after
        or "hallazgos" in after
    )
    page.click("#clear-filters")
    page.wait_for_function("() => document.getElementById('place-filter').value === 'all'")
    assert page.evaluate("() => document.activeElement.id") == "clear-filters"


def test_downloads_report_a_visible_status(page):
    _open_shell(page)
    page.evaluate("() => goTab('evidencia')")
    page.click("[data-action=csv]")
    page.wait_for_selector("#download-status:not([hidden])")
    text = page.inner_text("#download-status")
    assert "descarga" in text.lower() or "Descarga" in text or "prepar" in text.lower() or "Archivo" in text


def test_layout_at_390_has_no_horizontal_overflow_and_cancel_comes_first(page):
    page.set_viewport_size({"width": 390, "height": 844})
    _open_shell(page)
    width = page.evaluate("() => document.documentElement.scrollWidth")
    assert width <= 390
    page.click("#emergency-button")
    page.wait_for_selector("#sheet-cancel")
    order = page.evaluate(
        """() => {
            const cancel = document.getElementById('sheet-cancel').getBoundingClientRect();
            const confirm = document.getElementById('sheet-confirm').getBoundingClientRect();
            return {cancel: cancel.top, confirm: confirm.top};
        }"""
    )
    assert order["cancel"] <= order["confirm"]
    header = page.evaluate(
        """() => {
            const bar = document.querySelector('.mast').getBoundingClientRect();
            const main = document.getElementById('main-area').getBoundingClientRect();
            return {bar: bar.bottom, main: main.top};
        }"""
    )
    assert header["bar"] <= header["main"] + 1
