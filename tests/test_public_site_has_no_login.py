"""The public site does not ask for a key and does not load a tracker."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

BANNED = (
    'type="password"',
    "type='password'",
    "googletagmanager",
    "google-analytics",
    "google" + "tagmanager",
    "fonts.googleapis.com",
    "cdn.jsdelivr.net",
    "cdnjs.cloudflare.com",
    "document.cookie",
    "gtag(",
    "plausible.io",
    "hotjar",
)


def test_public_files_have_no_tracker_or_password_prompt() -> None:
    problems: list[str] = []
    for path in WEB.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".js", ".css", ".svg"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for needle in BANNED:
            if needle.lower() in text:
                problems.append(f"{path.relative_to(ROOT)}: {needle}")
    assert problems == []


def test_privacy_page_says_the_site_collects_nothing() -> None:
    text = (WEB / "privacy" / "index.html").read_text(encoding="utf-8")
    assert "collects no user data" in text
    assert "Content-Security-Policy" in text
    ops = (WEB / "ops" / "index.html").read_text(encoding="utf-8")
    assert "Content-Security-Policy" in ops
    assert 'type="password"' not in ops
