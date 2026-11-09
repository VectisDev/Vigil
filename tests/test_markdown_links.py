"""Relative Markdown links must point at a file in this tree.

Los enlaces relativos de Markdown tienen que apuntar a un archivo de este árbol.

docs/wiki usa títulos de la wiki de GitHub. wiki-sync los publica; no son rutas
de este árbol. tests/fixtures es la muestra atestada de Honduras 2025: esos
bytes no se editan aquí, así que un enlace roto dentro de la muestra se deja.

docs/brand/README-banner-snippet.md se pega en el README de la raíz. Sus rutas
están escritas desde la raíz del repositorio, no desde docs/brand/.

English: docs/wiki holds GitHub wiki titles, published by wiki-sync, not paths
in this tree. tests/fixtures is the attested Honduras 2025 sample and is not
edited here. The banner snippet is pasted into the root README, so its paths
are written from the repository root.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Prefijos que no se revisan. / Prefixes that are not checked.
#
# `.venv`, `venv` y `node_modules` son dependencias instaladas, no archivos de
# este arbol: estan en .gitignore y sus README traen enlaces a sus propios
# repositorios. Sin esta exclusion la prueba sale ROJA en cuanto alguien crea
# un entorno virtual en la raiz, que es el flujo normal de trabajo, y un rojo
# que no significa nada ensena a ignorar los rojos.
#
# English: these are installed dependencies, not files of this tree. They are
# in .gitignore and their own READMEs link to their own repositories. Without
# this the test goes red as soon as anyone creates a virtualenv at the root --
# the normal workflow -- and a red that means nothing teaches people to ignore
# reds.
SKIP_PARTS = (
    ("docs", "wiki"),
    ("tests", "fixtures"),
    (".venv",),
    ("venv",),
    ("node_modules",),
)

# Rutas escritas como si el archivo viviera en la raíz. / Paths written as if
# the file lived at the repository root.
ROOT_RELATIVE = {ROOT / "docs" / "brand" / "README-banner-snippet.md"}

FENCE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)")
DEFINE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s+(\S+)", re.MULTILINE)
HTML = re.compile(r"""(?:href|src|srcset)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)


def _skip(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    return any(parts[: len(prefix)] == prefix for prefix in SKIP_PARTS)


def _destinations(text: str) -> list[str]:
    body = FENCE.sub("", text)
    found: list[str] = []
    for match in INLINE.finditer(body):
        found.append(match.group(1) or match.group(2))
    found.extend(DEFINE.findall(body))
    for raw in HTML.findall(body):
        for piece in raw.split(","):
            token = piece.strip().split()[0] if piece.strip() else ""
            if token:
                found.append(token)
    return found


def _clean(raw: str) -> str | None:
    dest = raw.strip().strip("<>")
    if not dest or dest.startswith(("#", "mailto:", "data:")):
        return None
    if "://" in dest or dest.startswith("//"):
        return None
    path = dest.split("#", 1)[0].split("?", 1)[0].strip()
    if not path:
        return None
    return path


def _resolves(base: Path, rel: str) -> bool:
    target = (base / rel).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return False
    if target.exists():
        return True
    if target.suffix == "" and (target.with_suffix(".md")).is_file():
        return True
    return False


def test_relative_markdown_links_resolve() -> None:
    problems: list[str] = []
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts or not path.is_file() or _skip(path):
            continue
        base = ROOT if path in ROOT_RELATIVE else path.parent
        text = path.read_text(encoding="utf-8", errors="replace")
        for raw in _destinations(text):
            rel = _clean(raw)
            if rel is None:
                continue
            if not _resolves(base, rel):
                problems.append(f"{path.relative_to(ROOT)} -> {rel}")
    assert problems == []
