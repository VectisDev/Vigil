"""Cada página tiene un solo fondo, y el interruptor recuerda la elección.

Light is white. Dark is black. The first visit follows prefers-color-scheme.
A later visit follows the choice stored in localStorage.
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

pytestmark = pytest.mark.browser

REQUIRE_BROWSER = os.environ.get("VIGIL_REQUIRE_BROWSER") == "1"

PAGES = ("/", "/ops/", "/lab/", "/monitor/")

_ONE_BACKGROUND_JS = """() => {
    const body = getComputedStyle(document.body).backgroundColor;
    const bad = [];
    const sel = 'section, header, footer, nav, main, .evidence, .audiences, .audience-card, .card, .sim, .mast, .hero';
    for (const el of document.querySelectorAll(sel)) {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) continue;
        const bg = cs.backgroundColor;
        if (bg === 'rgba(0, 0, 0, 0)' || bg === body) continue;
        bad.push((el.id || el.className || el.tagName) + ' ' + bg);
    }
    return bad.slice(0, 8);
}"""


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


def _launch_browser(pw):
    args = ["--no-sandbox", "--disable-dev-shm-usage"]
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
            if os.environ.get("VIGIL_REQUIRE_BROWSER") == "1":
                raise AssertionError(
                    "VIGIL_REQUIRE_BROWSER=1 pero el navegador no arranca: " + str(exc)
                ) from exc
            pytest.skip(f"no hay navegador utilizable: {exc}")
        try:
            yield launched
        finally:
            launched.close()


def _open(browser, site, path, scheme):
    context = browser.new_context(color_scheme=scheme)
    page = context.new_page()
    page.add_init_script("localStorage.removeItem('vigil-theme')")
    page.goto(site + path, wait_until="domcontentloaded")
    page.locator("#theme-toggle, .theme-toggle").first.wait_for(state="visible")
    return context, page


@pytest.mark.parametrize("path", PAGES)
@pytest.mark.parametrize("scheme,theme,red,bg", [
    ("light", "light", "#D7262E", "rgb(255, 255, 255)"),
    ("dark", "dark", "#FF4D55", "rgb(0, 0, 0)"),
])
def test_each_page_follows_the_system_and_uses_one_background(browser, site, path, scheme, theme, red, bg):
    context, page = _open(browser, site, path, scheme)
    try:
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == theme
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == bg
        assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--red').trim().toUpperCase()") == red
        icon = page.evaluate("document.querySelector('link[rel=icon]').getAttribute('href')")
        assert ("mark-dark.svg" if theme == "dark" else "mark-light.svg") in icon
        bands = page.evaluate(_ONE_BACKGROUND_JS)
        assert bands == []
        box = page.locator("#theme-toggle, .theme-toggle").locator("visible=true").first.bounding_box()
        assert box is not None and box["width"] >= 44 and box["height"] >= 44
    finally:
        context.close()


def test_the_toggle_is_remembered_against_the_system(browser, site):
    context = browser.new_context(color_scheme="light")
    page = context.new_page()
    try:
        page.goto(site + "/", wait_until="domcontentloaded")
        toggle = page.locator("#theme-toggle")
        toggle.wait_for(state="visible")
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
        toggle.click()
        page.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'")
        assert page.evaluate("localStorage.getItem('vigil-theme')") == "dark"
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(0, 0, 0)"
        assert "mark-dark.svg" in page.evaluate("document.querySelector('link[rel=icon]').getAttribute('href')")
        page.reload(wait_until="domcontentloaded")
        page.locator("#theme-toggle").wait_for(state="visible")
        assert page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"
        assert page.evaluate("localStorage.getItem('vigil-theme')") == "dark"
    finally:
        context.close()
