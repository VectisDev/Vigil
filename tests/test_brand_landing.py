"""La portada usa la marca nueva y se puede leer entera.

Favicon, logo, los dos idiomas, el desplazamiento y la consola.
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
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on(
        "console",
        lambda msg: errors.append(msg.text) if msg.type == "error" else None,
    )
    page.goto(site + path, wait_until="domcontentloaded")
    return context, page, errors


@pytest.mark.parametrize("path", PAGES)
def test_every_named_page_has_a_favicon_and_a_logo(browser, site, path):
    context, page, errors = _open(browser, site, path, 1440, 900)
    try:
        icon = page.evaluate(
            "() => { const el = document.querySelector('link[rel=icon]');"
            " return el ? el.getAttribute('href') : ''; }"
        )
        assert "favicon.svg" in icon
        page.wait_for_function("""() => {
                const imgs = [...document.querySelectorAll('.vigil-lockup img')];
                return imgs.some(img => {
                    const r = img.getBoundingClientRect();
                    return img.complete && img.naturalWidth > 0 && r.width > 0
                        && getComputedStyle(img).display !== 'none';
                });
            }""")
        box = page.locator(".vigil-lockup img:visible").first.bounding_box()
        assert box is not None and box["width"] >= 24 and box["height"] >= 16
        assert errors == []
    finally:
        context.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_the_landing_scrolls_and_switches_language(browser, site, width, height):
    context, page, errors = _open(browser, site, "/", width, height)
    try:
        page.evaluate("localStorage.removeItem('vigil-lang')")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function("""() => {
                const es = document.querySelector('h1 [data-lang="es"]');
                return es && getComputedStyle(es).display !== 'none'
                    && es.innerText.includes('alterados');
            }""")
        page.locator("#btn-lang").click()
        page.wait_for_function("""() => {
                const en = document.querySelector('h1 [data-lang="en"]');
                const es = document.querySelector('h1 [data-lang="es"]');
                return getComputedStyle(en).display !== 'none'
                    && en.innerText.includes('altered')
                    && getComputedStyle(es).display === 'none'
                    && localStorage.getItem('vigil-lang') === 'en';
            }""")
        page.locator("#btn-lang").click()
        page.wait_for_function("() => localStorage.getItem('vigil-lang') === 'es'")
        hrefs = page.evaluate("""() => [...document.querySelectorAll('a[href]')]
                .map(a => a.getAttribute('href'))""")
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
        metrics = page.evaluate("""() => {
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
            }""")
        assert metrics["wide"] <= 1
        assert metrics["bottom"] <= metrics["inner"] + 2
        assert metrics["max"] <= 1 or metrics["top"] > 0
        assert errors == []
    finally:
        context.close()
