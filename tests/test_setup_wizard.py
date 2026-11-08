"""El asistente de despliegue no pide ningún token y no llama a GitHub.

The deployment assistant asks for no token and calls no GitHub API.

Antes pedía un Personal Access Token con permisos `repo` y `workflow`, creaba
el repositorio por la API, empujaba archivos y cifraba el token dentro de
`web/access.json` para que el panel lo usara después. Eso estaba del revés en
dos sentidos: un sistema cuya premisa es que no tengas que confiar en nadie no
puede abrir pidiendo una credencial con permiso de escritura sobre toda tu
cuenta, y cifrar el token bajo doce claves derivadas de los seeds no es
mitigación sino una distribución 12-de-12 del mismo secreto.

Estas pruebas corren en un navegador de verdad porque lo que fijan es
comportamiento, no texto: cuántas peticiones salen y a dónde, que el
consentimiento bloquee el botón, y —la que más vale— que los hashes que
calcula el navegador sean **byte a byte** los que calcula `hashlib` en Python.
Si esos dos discreparan, las claves generadas aquí no serían las que el panel
acepta, y no habría forma de notarlo leyendo el código de un lado solo.

English: these run in a real browser because what they pin is behaviour, not
text: how many requests leave and where to, that consent gates the button, and
-- the one that matters most -- that the hashes the browser computes are
byte-for-byte the ones `hashlib` computes in Python. If those disagreed, the
keys generated here would not be the ones the panel accepts, and there would be
no way to notice by reading either side alone.
"""

from __future__ import annotations

import functools
import hashlib
import http.server
import json
import os
import re
import socket
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB = REPO_ROOT / "web"
PAGE = WEB / "setup" / "index.html"
CHROMIUM = Path("/opt/pw-browsers/chromium")

# Mide el color RESUELTO de cada elemento visible y devuelve los que llevan un
# tono fuera de la paleta. Vive en una constante porque black 25 —la de CI— y
# black 26 —la de requirements/dev.txt— discrepan en si un unico argumento
# multilinea se abraza al parentesis, y una llamada de una sola linea no les da
# nada sobre lo que discrepar.
# English: measures each visible element's resolved colour. It lives in a
# constant because black 25 (CI) and black 26 (dev.txt) disagree on hugging a
# sole multiline argument, and a one-line call gives them nothing to disagree on.
_PALETTE_PROBE_JS = """
        () => {
          const bad = [];
          const parse = (value) => {
            const m = /rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/.exec(value || '');
            if (!m) return null;
            if (m[4] !== undefined && parseFloat(m[4]) === 0) return null;
            return [ +m[1], +m[2], +m[3] ];
          };
          const hue = ([r, g, b]) => {
            const max = Math.max(r, g, b), min = Math.min(r, g, b);
            if (max - min < 24) return null;           // gris: sin tono
            const d = max - min;
            let h;
            if (max === r) h = ((g - b) / d) % 6;
            else if (max === g) h = (b - r) / d + 2;
            else h = (r - g) / d + 4;
            h = Math.round(h * 60);
            return h < 0 ? h + 360 : h;
          };
          document.querySelectorAll('*').forEach((el) => {
            if (!el.getClientRects().length) return;
            const style = getComputedStyle(el);
            ['color', 'backgroundColor', 'borderTopColor', 'outlineColor'].forEach((prop) => {
              const rgb = parse(style[prop]);
              if (!rgb) return;
              const h = hue(rgb);
              if (h === null) return;
              // Rojo: 0-25 o 340-360. Todo lo demas es azul, amarillo o morado.
              if (!(h <= 25 || h >= 340)) {
                bad.push(el.tagName.toLowerCase() + '#' + (el.id || '') + ' ' + prop + '=' + style[prop] + ' hue=' + h);
              }
            });
          });
          return bad.slice(0, 12);
        }
"""

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright

# El job `browser-tests` de ci.yml selecciona por este marcador. Marcarlo a
# nivel de modulo incluye tambien las pruebas estaticas de aqui, que no
# necesitan navegador: correrlas dos veces cuesta milisegundos y elegirlas una
# por una se desincronizaria del archivo.
# English: the browser-tests job selects by this marker. Marking at module
# level also takes the static tests here, which need no browser: running those
# twice costs milliseconds, and picking them one by one would drift.
pytestmark = pytest.mark.browser

# Con esto a "1", no haber navegador es un FALLO y no una omision. Lo pone el
# job que acaba de instalarlo: alli la ausencia solo puede significar que la
# instalacion se rompio, y una omision silenciosa en ese job seria un verde
# que no prueba nada — exactamente el fallo que #788 encontro en el lint.
# English: with this set to "1", a missing browser is a FAILURE, not a skip.
# The job that just installed it sets it: there, absence can only mean the
# install broke, and a silent skip would be a green that proves nothing.
REQUIRE_BROWSER = os.environ.get("VIGIL_REQUIRE_BROWSER") == "1"


# ── servidor y navegador ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def site() -> str:
    """Sirve `web/` por HTTP. `file://` bloquea `fetch`, así que no sirve."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB))
    handler.log_message = lambda *args, **kwargs: None  # type: ignore[assignment]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="module")
def browser():
    """El navegador, u omitir si no hay uno utilizable.

    `playwright` esta en requirements.txt, asi que el import existe en CI; el
    BINARIO del navegador no, porque CI no corre `playwright install`. Sin esta
    guarda el arranque lanzaria una excepcion y el job de pruebas saldria en
    ROJO por una dependencia ausente, no por un fallo del codigo.

    Se caza solo el fallo de arranque y no lo que ocurra dentro de la prueba:
    una guarda mas ancha convertiria un fallo real en una omision, que es la
    peor de las dos salidas porque se ve igual que un verde.

    Consecuencia honesta: estas pruebas corren en local y se OMITEN en CI.
    Hacerlas valer alli pide un job propio que instale el navegador una vez.

    English: playwright is in requirements.txt so the import exists in CI, but
    the browser binary does not, because CI does not run `playwright install`.
    Without this guard the launch would raise and the test job would go RED for
    a missing dependency rather than a code failure. Only the launch is caught,
    never what happens inside a test: a wider guard would turn a real failure
    into a skip, which is the worse of the two because it looks like a pass.
    These therefore run locally and SKIP in CI.
    """
    options = {"args": ["--no-sandbox"]}
    if CHROMIUM.exists():
        options["executable_path"] = str(CHROMIUM)
    with sync_playwright() as play:
        try:
            instance = play.chromium.launch(**options)
        except Exception as exc:  # pragma: no cover - entorno sin navegador
            if REQUIRE_BROWSER:
                raise AssertionError(
                    "VIGIL_REQUIRE_BROWSER=1 pero el navegador no arranca, asi que "
                    f"la instalacion de Chromium fallo en este job: {exc}"
                ) from exc
            pytest.skip(f"no hay navegador utilizable: {exc}")
        try:
            yield instance
        finally:
            instance.close()


@pytest.fixture
def wizard(browser, site: str):
    """La página cargada, con todas sus peticiones registradas."""
    context = browser.new_context()
    page = context.new_page()
    requests: list[str] = []
    errors: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{site}/setup/", wait_until="networkidle")
    page.requests = requests  # type: ignore[attr-defined]
    page.errors = errors  # type: ignore[attr-defined]
    try:
        yield page
    finally:
        context.close()


def _reach_keys(page) -> None:
    """Avanza hasta el paso de las claves."""
    page.check("#consent")
    page.click("#to2")
    page.fill("#repo", "alguien/vigil-hn")
    page.click("#to3")
    page.wait_for_function("document.querySelectorAll('#keys .key').length === 12")


# ── lo que importa: ninguna credencial, ninguna llamada ───────────────────────


def test_no_request_leaves_this_origin(wizard, site: str):
    """La única petición es a un archivo estático del mismo despliegue."""
    _reach_keys(wizard)
    outside = [url for url in wizard.requests if not url.startswith(site)]
    assert not outside, f"peticiones fuera de este origen: {outside}"


def test_no_request_reaches_github_or_a_cdn(wizard):
    _reach_keys(wizard)
    forbidden = re.compile(r"github\.com|githubusercontent|cdnjs|jsdelivr|unpkg|googleapis|gstatic")
    offenders = [url for url in wizard.requests if forbidden.search(url)]
    assert not offenders, f"la pagina contacta terceros: {offenders}"


def test_the_page_raises_no_exceptions(wizard):
    _reach_keys(wizard)
    assert wizard.errors == []


def test_there_is_nowhere_to_type_a_token(wizard):
    """Sin campo de token no hay token que filtrar."""
    assert wizard.locator("input[type=password]").count() == 0
    source = PAGE.read_text(encoding="utf-8")
    assert "ghp_" not in source, "ni como placeholder: un ejemplo de token invita a pegar uno"
    assert "settings/tokens" not in source


@pytest.mark.parametrize(
    "needle",
    [
        "verifyToken",
        "createRepo",
        "pushFile",
        "pushCollectWorkflow",
        "pushPagesWorkflow",
        "pushDashboard",
        "enablePages(",
        "encryptPatForSeeds",
        "deriveWrapKey",
        "aesgcmEncrypt",
        "writerPat",
        "writer_pat",
        "DATA_REPO_TOKEN",
    ],
)
def test_the_pat_machinery_is_gone(needle: str):
    """Trece nombres que ya no deben existir en esta página."""
    assert needle not in PAGE.read_text(encoding="utf-8"), f"{needle} sigue en web/setup/index.html"


def test_the_requirements_path_bug_left_with_its_function():
    """`pushCollectWorkflow()` escribía `_engine/requirements-prod.txt`.

    La ruta real es `requirements/prod.txt`, y esa diferencia es la fábrica del
    error que llevaba al colector compañero 66 ejecuciones fallando. Se retira
    con la función; no hacía falta repararla.

    English: the real path is `requirements/prod.txt`, and that difference is
    the factory of the error behind 66 failing runs. It leaves with the
    function; there was nothing to repair.
    """
    assert "_engine/requirements-prod.txt" not in PAGE.read_text(encoding="utf-8")


def test_no_third_party_script_or_stylesheet():
    source = PAGE.read_text(encoding="utf-8")
    for tag in re.findall(r'<(?:script|link)[^>]*(?:src|href)="(https?://[^"]+)"', source):
        pytest.fail(f"recurso de tercero: {tag}")


# ── el consentimiento, antes del botón ────────────────────────────────────────


def test_consent_gates_the_first_button(wizard):
    """2.8: decirlo en pantalla antes del botón, no en una página de docs."""
    assert wizard.is_disabled("#to2")
    wizard.check("#consent")
    assert wizard.is_enabled("#to2")
    wizard.uncheck("#consent")
    assert wizard.is_disabled("#to2")


def test_the_consent_names_what_becomes_public(wizard):
    text = wizard.inner_text("#s1")
    assert "públicamente asociada" in text
    assert "registros de Actions son públicos" in text


def test_the_page_says_the_node_does_not_collect(wizard):
    """Un nodo nuevo está en REPLAY. Prometer captura en vivo era falso."""
    text = wizard.inner_text("#s1")
    assert "REPLAY" in text
    assert "cero peticiones" in text.lower()
    source = PAGE.read_text(encoding="utf-8")
    assert "cada 15 minutos" not in source, "la version anterior prometia captura cada 15 minutos"


# ── el catálogo ───────────────────────────────────────────────────────────────


def _catalog() -> list[dict]:
    return json.loads((WEB / "data" / "countries.json").read_text(encoding="utf-8"))


def test_every_country_in_the_catalog_is_offered(wizard):
    wizard.wait_for_function("document.querySelectorAll('#countries .country').length > 0")
    assert wizard.locator("#countries .country").count() == len(_catalog())


def test_a_country_with_no_url_cannot_be_chosen(wizard):
    """Ofrecerlo sería invitar a desplegar un nodo que el arranque rechaza."""
    wizard.wait_for_function("document.querySelectorAll('#countries .country').length > 0")
    for country in _catalog():
        button = wizard.locator(f"#c-{country['code']}")
        assert button.is_disabled() is (not country["configurable"]), country["code"]


def test_a_partial_country_says_how_much_it_covers(wizard):
    """«Cubre 19 de 22» antes del botón, no después."""
    partial = [c for c in _catalog() if c["configurable"] and not c["complete"]]
    if not partial:
        pytest.skip("ningun pais queda parcial bajo el techo actual")

    country = partial[0]
    wizard.wait_for_function("document.querySelectorAll('#countries .country').length > 0")
    wizard.click(f"#c-{country['code']}")
    note = wizard.inner_text("#country-note")
    assert str(country["divisions_covered"]) in note
    assert str(country["divisions_total"]) in note
    assert "techo" in note


# ── las doce claves ───────────────────────────────────────────────────────────


def test_twelve_distinct_keys_of_the_shape_the_panel_expects(wizard):
    _reach_keys(wizard)
    keys = wizard.eval_on_selector_all("#keys .key .v", "els => els.map(e => e.textContent)")
    assert len(keys) == 12
    assert len(set(keys)) == 12, "una repetida serian menos de doce claves"
    for key in keys:
        assert len(key) == 24, key
        assert re.fullmatch(r"[A-Za-z0-9_-]{24}", key), key


def test_the_browser_and_python_agree_on_every_hash(wizard):
    """La prueba que no se puede hacer leyendo un solo lado.

    English: the test that cannot be done by reading either side alone.
    """
    _reach_keys(wizard)
    keys = wizard.eval_on_selector_all("#keys .key .v", "els => els.map(e => e.textContent)")
    hashes = wizard.input_value("#hashes").split(",")

    assert len(hashes) == 12
    for key, produced in zip(keys, hashes):
        expected = hashlib.sha256(key.encode()).hexdigest()
        assert produced == expected, f"la clave {key!r} se hashea distinto en el navegador"


def test_regenerating_replaces_all_twelve(wizard):
    _reach_keys(wizard)
    before = wizard.eval_on_selector_all("#keys .key .v", "els => els.map(e => e.textContent)")
    wizard.click("#regen")
    wizard.wait_for_function(
        "first => document.querySelector('#keys .key .v').textContent !== first",
        arg=before[0],
    )
    after = wizard.eval_on_selector_all("#keys .key .v", "els => els.map(e => e.textContent)")
    assert len(after) == 12
    assert not set(before) & set(after), "regenerar debe sustituir las doce"
    assert "ya no sirven" in wizard.inner_text("#said-keys")


def test_the_download_hands_over_a_file_with_the_keys(wizard):
    _reach_keys(wizard)
    keys = wizard.eval_on_selector_all("#keys .key .v", "els => els.map(e => e.textContent)")
    with wizard.expect_download() as info:
        wizard.click("#download")
    download = info.value
    assert download.suggested_filename.endswith(".txt")

    body = Path(download.path()).read_text(encoding="utf-8")
    for key in keys:
        assert key in body
    assert "FUERA DE LINEA" in body
    assert "no se enviaron a ninguna parte" in body


# ── los enlaces ───────────────────────────────────────────────────────────────


def test_the_template_link_is_derived_and_not_hardcoded(wizard):
    """Una constante deja de ser cierta al renombrar el repositorio."""
    wizard.check("#consent")
    wizard.click("#to2")
    href = wizard.get_attribute("#generate", "href")
    assert "/generate?" in href
    assert "name=vigil-" in href
    assert "visibility=public" in href

    source = PAGE.read_text(encoding="utf-8")
    assert "location.hostname" in source, "el dueno y el repo se derivan del sitio que sirve la pagina"


@pytest.mark.parametrize(
    "typed,expected",
    [
        ("alguien/vigil-hn", "alguien/vigil-hn"),
        ("  alguien/vigil-hn  ", "alguien/vigil-hn"),
        ("https://github.com/alguien/vigil-hn", "alguien/vigil-hn"),
        ("https://github.com/alguien/vigil-hn.git", "alguien/vigil-hn"),
    ],
)
def test_the_repository_is_read_in_the_forms_people_paste(wizard, typed: str, expected: str):
    wizard.check("#consent")
    wizard.click("#to2")
    wizard.fill("#repo", typed)
    assert wizard.is_enabled("#to3")
    wizard.click("#to3")
    assert wizard.get_attribute("#dispatch", "href").endswith(f"/{expected}/actions/workflows/bootstrap.yml")


@pytest.mark.parametrize("typed", ["", "alguien", "/vigil", "alguien/", "a b/c d", "alguien/vigil/extra"])
def test_a_repository_that_is_not_one_does_not_let_you_through(wizard, typed: str):
    wizard.check("#consent")
    wizard.click("#to2")
    wizard.fill("#repo", typed)
    assert wizard.is_disabled("#to3")


def test_the_links_point_at_the_operators_repository(wizard):
    _reach_keys(wizard)
    wizard.click("#to4")
    assert wizard.get_attribute("#pages-link", "href") == "https://github.com/alguien/vigil-hn/settings/pages"
    assert wizard.get_attribute("#panel-link", "href") == "https://alguien.github.io/vigil-hn/"
    assert wizard.get_attribute("#ops-link", "href") == "https://alguien.github.io/vigil-hn/ops/"


# ── el paso manual, dicho en voz alta ─────────────────────────────────────────


def test_the_manual_step_cites_the_platform_limit(wizard):
    _reach_keys(wizard)
    wizard.click("#to4")
    text = wizard.inner_text("#s4")
    assert "Settings → Pages" in text
    assert "This option requires a token other than" in text
    assert "don't trigger a Pages build" in text
    assert "Administration: write" in text


def test_the_page_explains_why_the_hashes_need_pasting(wizard):
    """GitHub no acepta parámetros por URL en `Run workflow`.

    Decirlo es mejor que dar un enlace que parezca llevarlos y no los lleve.
    """
    _reach_keys(wizard)
    text = wizard.inner_text("#s3")
    assert "no acepta parámetros por URL" in text


# ── una sola pantalla a la vez, y la paleta ───────────────────────────────────


@pytest.mark.parametrize("step", [1, 2, 3, 4])
def test_exactly_one_screen_is_visible(wizard, step: int):
    _reach_keys(wizard)
    if step == 4:
        wizard.click("#to4")
    else:
        wizard.evaluate(f"go({step})")
    visible = [n for n in (1, 2, 3, 4) if wizard.locator(f"#s{n}").is_visible()]
    assert visible == [step]


def test_no_blue_yellow_or_purple_in_the_source():
    """Blanco, rojo, negro y grises. El mismo acuerdo que el panel OPS."""
    source = PAGE.read_text(encoding="utf-8")
    forbidden = {"#6ea8fe", "#57c08d", "#d4b066", "#df6b86", "--accent", "--purple"}
    present = sorted(token for token in forbidden if token in source)
    assert not present, f"tonos de la paleta anterior: {present}"


@pytest.mark.parametrize(
    "css,caught",
    [
        ("color:#2563eb", True),  # azul
        ("color:#eab308", True),  # amarillo
        ("color:#7c3aed", True),  # morado
        ("color:#16a34a", True),  # verde
        ("color:#c40500", False),  # el rojo de la paleta
        ("color:#525252", False),  # gris
        ("color:#0a0a0a", False),  # negro
    ],
)
def test_the_palette_probe_can_actually_fail(wizard, css: str, caught: bool):
    """Un medidor que no puede fallar no mide nada.

    Se le inyecta un elemento de cada tono y se comprueba que lo caza o lo
    deja pasar según corresponda. Sin esto, la prueba de la paleta pasaría
    igual con el JavaScript roto.

    English: a probe that cannot fail measures nothing. One element of each
    hue is injected to check it is caught or let through as appropriate;
    without this, the palette test would pass just the same with the
    JavaScript broken.
    """
    wizard.evaluate(
        "css => { const el = document.createElement('p');"
        " el.id = 'palette-probe-fixture'; el.style.cssText = css;"
        " el.textContent = 'x'; document.body.appendChild(el); }",
        css,
    )
    offenders = wizard.evaluate(_PALETTE_PROBE_JS)
    hit = any("palette-probe-fixture" in entry for entry in offenders)
    assert hit is caught, f"{css}: cazado={hit}, esperado={caught} (salida: {offenders})"


def test_the_rendered_colours_carry_no_hue_outside_the_palette(wizard):
    """Medido sobre lo pintado, no sobre la hoja de estilos.

    Un valor puede entrar por una regla heredada que una búsqueda estática no
    ve, así que se mide el color resuelto de cada elemento.

    English: measured on what is painted rather than on the stylesheet, since a
    value can arrive through an inherited rule a static search cannot see.
    """
    _reach_keys(wizard)
    offenders = wizard.evaluate(_PALETTE_PROBE_JS)
    assert offenders == [], f"tonos fuera de la paleta: {offenders}"
