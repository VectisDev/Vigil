#!/usr/bin/env python3
"""
======================== ÍNDICE / INDEX ========================
1. Propósito / Purpose
2. Qué revisa / What it checks
3. Cómo añadir una excepción / How to add an exception

======================== ESPAÑOL ========================
Archivo: `.github/scripts/assert_no_ai_references.py`.

Falla si el repositorio introduce una referencia a un asistente de IA en rutas,
en el contenido de archivos rastreados o en mensajes de commit.

La autoría pública de este proyecto es un asunto de seguridad del operador, no
una preferencia de estilo: debe existir una sola firma, la de la cuenta. Una
referencia a una herramienta de IA en un mensaje de commit es permanente y
pública, y no se puede retirar sin reescribir la historia.

Este candado existe porque la limpieza manual se deshace sola. Sin él, el
primer merge desde una rama con nombre generado vuelve a introducir el
problema, y nadie lo nota hasta que ya está en la rama por defecto.

Uso:
    python .github/scripts/assert_no_ai_references.py              # solo el árbol
    python .github/scripts/assert_no_ai_references.py BASE..HEAD   # + mensajes

======================== ENGLISH ========================
File: `.github/scripts/assert_no_ai_references.py`.

Fails if the repository introduces a reference to an AI assistant in paths, in
tracked file contents, or in commit messages.

Public authorship here is an operator-safety matter, not a style preference:
there must be exactly one signature, the account's. A reference to an AI tool
in a commit message is permanent and public, and cannot be retracted without
rewriting history.

This gate exists because manual cleanup undoes itself. Without it, the first
merge from a generated branch name reintroduces the problem, and nobody notices
until it is already on the default branch.

Usage:
    python .github/scripts/assert_no_ai_references.py              # tree only
    python .github/scripts/assert_no_ai_references.py BASE..HEAD   # + messages
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Se construyen por partes para que este archivo no se delate a sí mismo.
# Built piecewise so this file does not match its own pattern.
_VENDORS = ["cla" + "ude", "anthro" + "pic", "copi" + "lot", "chat" + "gpt", "open" + "ai"]
PATTERN = re.compile("|".join(_VENDORS), re.IGNORECASE)

# Rutas que legítimamente pueden nombrar a un proveedor: este candado y su
# lista de excepciones. Cualquier otra adición debe justificarse en la revisión.
# Paths that may legitimately name a vendor: this gate and its allowlist.
SELF = "assert_no_ai_references.py"
ALLOWLIST_FILE = Path(".github/ai-reference-allowlist.txt")

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".svg",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".zip",
    ".gz",
    ".ots",
    ".parquet",
}


def _run(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=False).stdout


def _allowlist() -> set[str]:
    """Rutas exentas, una por línea. / Exempt paths, one per line."""
    if not ALLOWLIST_FILE.exists():
        return set()
    out = set()
    for raw in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def check_tree(allow: set[str]) -> list[str]:
    """Rutas y contenido de archivos rastreados."""
    problems: list[str] = []
    files = [f for f in _run(["git", "ls-files"]).splitlines() if f]

    for path in files:
        if path in allow or path.endswith(SELF) or path == str(ALLOWLIST_FILE):
            continue
        if PATTERN.search(path):
            problems.append(f"ruta / path: {path}")

    for path in files:
        if path in allow or path.endswith(SELF) or path == str(ALLOWLIST_FILE):
            continue
        if Path(path).suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = Path(path).read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            # Binario o ilegible: la comprobación de ruta ya lo cubrió.
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            match = PATTERN.search(line)
            if match:
                problems.append(f"contenido / content: {path}:{number} -> {match.group(0)!r}")
                break
    return problems


def check_messages(rev_range: str) -> list[str]:
    """Mensajes de commit del rango dado.

    Es la vía por la que el problema entró de verdad: un merge desde una rama
    con nombre generado deja el nombre del proveedor en el asunto, para siempre.

    English: this is how the problem actually got in -- a merge from a
    generated branch name leaves the vendor name in the subject, permanently.
    """
    problems: list[str] = []
    raw = _run(["git", "log", "--format=%H%x1f%B%x1e", rev_range])
    for entry in raw.split("\x1e"):
        entry = entry.strip()
        if not entry or "\x1f" not in entry:
            continue
        sha, body = entry.split("\x1f", 1)
        match = PATTERN.search(body)
        if match:
            subject = body.strip().splitlines()[0] if body.strip() else ""
            problems.append(f"mensaje / message: {sha[:9]} -> {match.group(0)!r} :: {subject[:70]}")
    return problems


def main() -> int:
    allow = _allowlist()
    problems = check_tree(allow)

    if len(sys.argv) > 1 and sys.argv[1]:
        problems += check_messages(sys.argv[1])

    if not problems:
        print("assert_no_ai_references=PASS")
        return 0

    print("assert_no_ai_references=FAIL", file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "La autoria publica de este proyecto debe ser unica y sin referencias a\n"
        "herramientas de IA. Un mensaje de commit es permanente: corrigelo ANTES\n"
        "de mergear, porque despues solo se quita reescribiendo la historia.\n"
        "\n"
        "Public authorship must be single and free of AI-tool references. A commit\n"
        "message is permanent: fix it BEFORE merging, because afterwards it can\n"
        "only be removed by rewriting history.\n",
        file=sys.stderr,
    )
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    print(
        f"\n{len(problems)} hallazgo(s). Para una excepcion legitima, anade la ruta a\n"
        f"{ALLOWLIST_FILE} y justificala en la revision.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
