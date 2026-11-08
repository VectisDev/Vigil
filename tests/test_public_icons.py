"""Every public page uses the white, red, and black mark."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
LEGACY = ("#2563EB", "#0EA5E9", "#FBBF24", "#0F172A", "#475569")


def test_pages_point_at_the_mark_and_not_the_old_colors() -> None:
    html_files = list(WEB.rglob("*.html"))
    assert html_files
    problems: list[str] = []
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(WEB).as_posix()
        if 'rel="icon"' not in text or "favicon.svg" not in text:
            problems.append(f"{rel}: missing favicon")
        if "apple-touch-icon" not in text:
            problems.append(f"{rel}: missing apple touch icon")
        if "manifest.webmanifest" not in text:
            problems.append(f"{rel}: missing manifest")
        if "social-preview.png" not in text:
            problems.append(f"{rel}: missing preview image")
        for color in LEGACY:
            if color.lower() in text.lower():
                problems.append(f"{rel}: {color}")
    icon_files = [
        WEB / "assets" / "favicon.svg",
        WEB / "favicon.svg",
        WEB / "assets" / "mark.svg",
        WEB / "assets" / "logo-mark.svg",
        WEB / "assets" / "logo.svg",
        WEB / "assets" / "logo-dark.svg",
        WEB / "assets" / "social-preview.svg",
        WEB / "manifest.webmanifest",
    ]
    for path in icon_files:
        text = path.read_text(encoding="utf-8")
        for color in LEGACY:
            if color.lower() in text.lower():
                problems.append(f"{path.relative_to(ROOT)}: {color}")
    for name in ("apple-touch-icon.png", "favicon.ico", "assets/icon-192.png", "assets/icon-512.png"):
        if not (WEB / name).is_file():
            problems.append(f"missing {name}")
    assert problems == []
