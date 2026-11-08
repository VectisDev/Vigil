"""La portada usa la marca nueva y se puede leer entera.

Favicon, logo, los dos idiomas, el desplazamiento y la consola.
"""

from __future__ import annotations

import os
import re
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = REPO_ROOT / "web"

pytest.importorskip("playwright.sync_api", reason="playwright no instalado")
from playwright.sync_api import sync_playwright  # noqa: E402

pytestmark = pytest.mark.browser

REQUIRE_BROWSER = os.environ.get("VIGIL_REQUIRE_BROWSER") == "1"

PAGES = ("/", "/ops/", "/lab/", "/monitor/")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def site() -> str:
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

        def log_message(self, *args):
            pass

    port = _free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()


def _launch_browser(playwright):
    args = ["--no-sandbox", "--disable-dev-shm-usage"]
    for candidate in (
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ):
        if Path(candidate).exists():
            return playwright.chromium.launch(executable_path=candidate, args=args)
    return playwright.chromium.launch(args=args)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        try:
            launched = _launch_browser(playwright)
        except Exception as exc:
            if os.environ.get("VIGIL_REQUIRE_BROWSER") == "1":
                raise AssertionError(
                    "VIGIL_REQUIRE_BROWSER=1 pero el navegador no arranca, asi que "
                    f"la instalacion de Chromium fallo en este job: {exc}"
                ) from exc
            pytest.skip(f"no hay navegador utilizable: {exc}")
        try:
            yield launched
        finally:
            launched.close()


def _open(browser, site, path, width, height):
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    errors = []
    missing = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on(
        "console",
        lambda msg: errors.append(msg.text) if msg.type == "error" else None,
    )

    def _note(response):
        if response.status < 400:
            return
        url = response.url
        if any(part in url for part in ("favicon", "/brand/", "tokens.css", "brand-header.css")):
            missing.append(f"{response.status} {url}")

    page.on("response", _note)
    page.goto(site + path, wait_until="domcontentloaded")
    return context, page, errors, missing


@pytest.mark.parametrize("path", PAGES)
def test_every_named_page_has_a_favicon_and_a_logo(browser, site, path):
    context, page, errors, missing = _open(browser, site, path, 1440, 900)
    try:
        icons = page.evaluate(
            "() => [...document.querySelectorAll('link[rel=icon]')]"
            ".map(el => el.getAttribute('href') + ' ' + (el.getAttribute('data-icon-light') || ''))"
            ".join(' ')"
        )
        assert "mark-light.svg" in icons
        assert "favicon.svg" in icons
        page.wait_for_function(
            """() => {
                const imgs = [...document.querySelectorAll('.vigil-lockup img')];
                return imgs.some(img => {
                    const r = img.getBoundingClientRect();
                    return img.complete && img.naturalWidth > 0 && r.width > 0
                        && getComputedStyle(img).display !== 'none';
                });
            }"""
        )
        box = page.locator(".vigil-lockup img:visible").first.bounding_box()
        assert box is not None and box["width"] >= 24 and box["height"] >= 16
        assert missing == []
        assert errors == [] or path != "/"
    finally:
        context.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_the_landing_scrolls_and_switches_language(browser, site, width, height):
    context, page, errors, missing = _open(browser, site, "/", width, height)
    try:
        page.evaluate("localStorage.removeItem('vigil-lang')")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function(
            """() => {
                const es = document.querySelector('h1 [data-lang="es"]');
                return es && getComputedStyle(es).display !== 'none'
                    && es.innerText.includes('alterados');
            }"""
        )
        page.locator("#btn-lang").click()
        page.wait_for_function(
            """() => {
                const en = document.querySelector('h1 [data-lang="en"]');
                const es = document.querySelector('h1 [data-lang="es"]');
                return getComputedStyle(en).display !== 'none'
                    && en.innerText.includes('altered')
                    && getComputedStyle(es).display === 'none'
                    && localStorage.getItem('vigil-lang') === 'en';
            }"""
        )
        page.locator("#btn-lang").click()
        page.wait_for_function("() => localStorage.getItem('vigil-lang') === 'es'")
        hrefs = page.evaluate(
            """() => [...document.querySelectorAll('a[href]')]
                .map(a => a.getAttribute('href'))"""
        )
        for needed in (
            "monitor/",
            "lab/",
            "ops/",
            "reports/hnd_2025.html",
            "setup/",
            "verifier/",
        ):
            assert needed in hrefs
        assert all(href != "#" for href in hrefs)
        metrics = page.evaluate(
            """() => {
                const sc = document.scrollingElement;
                sc.scrollTop = sc.scrollHeight;
                const last = document.querySelector('footer');
                return {
                    top: sc.scrollTop,
                    max: sc.scrollHeight - sc.clientHeight,
                    bottom: last.getBoundingClientRect().bottom,
                    inner: window.innerHeight,
                    wide: document.documentElement.scrollWidth - window.innerWidth,
                };
            }"""
        )
        assert metrics["wide"] <= 1
        assert metrics["bottom"] <= metrics["inner"] + 2
        assert metrics["max"] <= 1 or metrics["top"] > 0
        assert missing == []
        assert errors == []
    finally:
        context.close()


def _channel(value: float) -> float:
    value = value / 255
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _contrast(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        parts = [int(n) for n in re.findall(r"\d+", color)[:3]]
        red, green, blue = (_channel(c) for c in parts)
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    lighter = max(luminance(foreground), luminance(background))
    darker = min(luminance(foreground), luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


_LOOK_JS = """() => {
    const body = getComputedStyle(document.body).backgroundColor;
    const em = document.querySelector('h1 em');
    const red = em ? getComputedStyle(em).color : '';
    const logo = [...document.querySelectorAll('.vigil-lockup img')].find(img => {
        const r = img.getBoundingClientRect();
        return r.width > 0 && getComputedStyle(img).display !== 'none';
    });
    const bands = [];
    const sel = 'section, header, footer, nav, .band, .why, .card, .hero';
    for (const el of document.querySelectorAll(sel)) {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) continue;
        const bg = cs.backgroundColor;
        if (bg !== 'rgba(0, 0, 0, 0)' && bg !== body) {
            bands.push((el.id || el.className || el.tagName) + ' ' + bg);
        }
    }
    return {body, red, logo: logo ? logo.getAttribute('src') : '', bands: bands.slice(0, 8)};
}"""


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize(
    "scheme,theme,bg",
    [("light", "light", "rgb(255, 255, 255)"), ("dark", "dark", "rgb(0, 0, 0)")],
)
def test_the_toggle_keeps_contrast_and_one_background(browser, site, width, height, scheme, theme, bg):
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme)
    page = context.new_page()
    try:
        page.add_init_script("localStorage.removeItem('vigil-theme')")
        page.goto(site + "/", wait_until="domcontentloaded")
        page.locator("#theme-toggle").wait_for(state="visible")
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == theme
        look = page.evaluate(_LOOK_JS)
        assert look["body"] == bg
        assert look["bands"] == []
        assert _contrast(look["red"], look["body"]) >= 4.5
        if theme == "dark":
            assert "oscuro" in look["logo"]
        else:
            assert "oscuro" not in look["logo"]
        box = page.locator("#theme-toggle").bounding_box()
        assert box is not None and box["width"] >= 44 and box["height"] >= 44
    finally:
        context.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_the_choice_survives_reload_at_both_widths(browser, site, width, height):
    context = browser.new_context(viewport={"width": width, "height": height}, color_scheme="light")
    page = context.new_page()
    try:
        page.goto(site + "/", wait_until="domcontentloaded")
        page.locator("#theme-toggle").click()
        page.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'")
        assert page.evaluate("localStorage.getItem('vigil-theme')") == "dark"
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(0, 0, 0)"
        page.reload(wait_until="domcontentloaded")
        page.locator("#theme-toggle").wait_for(state="visible")
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"
        assert page.evaluate("localStorage.getItem('vigil-theme')") == "dark"
        logo = page.evaluate(
            """() => {
                const img = [...document.querySelectorAll('.vigil-lockup img')]
                    .find(el => el.getBoundingClientRect().width > 0);
                return img ? img.getAttribute('src') : '';
            }"""
        )
        assert "oscuro" in logo
    finally:
        context.close()
