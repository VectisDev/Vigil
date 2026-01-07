import json
from typing import Any, Dict, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright


def _build_url(base_url: str, params: Mapping[str, str]) -> str:
    split = urlsplit(base_url)
    query = dict(parse_qsl(split.query))
    query.update({key: str(value) for key, value in params.items()})
    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query), split.fragment))


def _apply_stealth(page) -> None:
    page.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """
    )


def fetch_payload_with_playwright(
    base_url: str,
    params: Mapping[str, str],
    timeout: float,
    headers: Mapping[str, str],
    *,
    user_agent: str | None = None,
    locale: str | None = None,
    timezone_id: str | None = None,
    viewport: Dict[str, int] | None = None,
    stealth: bool = False,
) -> Dict[str, Any]:
    url = _build_url(base_url, params)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            extra_http_headers=dict(headers),
            user_agent=user_agent,
            locale=locale,
            timezone_id=timezone_id,
            viewport=viewport,
        )
        try:
            page = context.new_page()
            if stealth:
                _apply_stealth(page)
            response = page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
            if response is None:
                raise RuntimeError("Playwright no recibió respuesta al cargar la URL.")
            try:
                payload = response.json()
            except Exception:
                text = response.text()
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError("Respuesta Playwright no es JSON válido.") from exc
        finally:
            context.close()
            browser.close()

    if not isinstance(payload, dict):
        raise ValueError("Respuesta Playwright no es un objeto JSON.")

    return payload
