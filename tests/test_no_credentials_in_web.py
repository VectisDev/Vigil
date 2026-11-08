"""Nada de lo que se publica lleva una credencial, y la maquinaria no se extiende.

Nothing published carries a credential, and the machinery does not spread.

Todo `web/` se publica en GitHub Pages, así que cualquier cosa con forma de
token que entre ahí queda a la vista de cualquiera, y además alcanzable por SHA
en cada clon aunque se borre después.

La primera mitad de este archivo es el candado obvio: ningún valor con forma
de token de GitHub, ninguna cabecera de autorización con un valor real, en
ningún archivo publicado.

La segunda mitad es la que hace trabajo de verdad. El panel conserva la
maquinaria que descifra el PAT publicado —`decryptWriterPat`,
`_deriveWrapKey`, `_aesgcmDecrypt` y `window.VigilToken`— y retirarla toca los
mismos archivos que el rediseño del panel, así que no cabe en este cambio.
Mientras siga ahí, lo que sí se puede imponer es que **no se extienda**:
`PAT_READERS` enumera los cinco archivos exactos que la tienen hoy, y la
prueba falla en los dos sentidos. Si un archivo nuevo aprende a descifrar el
token, falla. Si uno de los cinco deja de tenerla y nadie quita su línea de la
lista, falla también.

Una lista que solo puede encogerse es la única forma honesta de poner un
candado sobre algo que todavía existe. Un candado con un agujero sin declarar
no es un candado.

English: everything under `web/` is published to GitHub Pages, so anything
token-shaped in there is visible to anyone and reachable by SHA in every clone
even if deleted later. The first half is the obvious lock: no GitHub
token-shaped value anywhere published.

The second half does the real work. The panel still carries the machinery that
decrypts the published PAT, and removing it touches the same files as the panel
redesign, so it does not fit in this change. While it is there, what can be
enforced is that it does not spread: `PAT_READERS` names the exact five files
that have it today, and the test fails both ways -- a new file that learns to
decrypt the token fails, and a listed file that no longer has it fails too, so
the list cannot rot. A list that can only shrink is the only honest way to lock
something that still exists.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB = REPO_ROOT / "web"

PUBLISHED_SUFFIXES = {".html", ".htm", ".js", ".json", ".css", ".md", ".txt", ".yaml", ".yml", ".svg"}

# Valores con forma de credencial de GitHub. Los prefijos son los que GitHub
# documenta; la longitud mínima evita casar con una explicación en prosa.
# English: GitHub's documented credential prefixes, with a minimum length so
# prose that merely mentions a prefix does not match.
TOKEN_VALUE = re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{16,}|\bgithub_pat_[A-Za-z0-9_]{16,}")

# Una cabecera de autorización con un valor literal detrás. `${...}` y
# `"+token` son codigo que la rellena en ejecucion, no un secreto escrito.
# English: an authorization header with a literal value behind it.
HARDCODED_AUTH = re.compile(
    r"""['"]?Authorization['"]?\s*[:=]\s*['"]\s*(?:Bearer|token)\s+(?!\$\{|'|"|\+)[A-Za-z0-9_\-.]{12,}""",
    re.IGNORECASE,
)

# Los cinco archivos que hoy saben descifrar el PAT publicado. La lista solo
# puede encoger: retirar la maquinaria de uno exige quitarlo de aquí.
# English: the five files that today know how to decrypt the published PAT.
PAT_READERS = {
    "web/index.html",
    "web/ops/index.html",
    "web/ops/js/ops-core.js",
    "web/ops/js/ops-monitor.js",
    "web/ops/js/ops-panel.js",
}

PAT_MACHINERY = ("decryptWriterPat", "_deriveWrapKey", "_aesgcmDecrypt", "writer_pat", "VigilToken")


def _published() -> list[Path]:
    return sorted(p for p in WEB.rglob("*") if p.is_file() and p.suffix.lower() in PUBLISHED_SUFFIXES)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


# ── el candado obvio ──────────────────────────────────────────────────────────


def test_there_are_files_to_check():
    """Un candado sobre un conjunto vacío pasa siempre y no protege nada."""
    assert len(_published()) > 20


@pytest.mark.parametrize("path", _published(), ids=_relative)
def test_no_published_file_carries_a_token_value(path: Path):
    """Un token publicado no se arregla borrándolo: el blob sigue alcanzable."""
    found = sorted(set(TOKEN_VALUE.findall(_text(path))))
    assert not found, f"{_relative(path)} lleva {len(found)} valor(es) con forma de token de GitHub"


@pytest.mark.parametrize("path", _published(), ids=_relative)
def test_no_published_file_hardcodes_an_authorization_header(path: Path):
    matches = HARDCODED_AUTH.findall(_text(path))
    assert not matches, f"{_relative(path)} escribe una cabecera de autorizacion con valor literal"


def test_not_even_a_placeholder_token():
    """`placeholder="ghp_xxxx…"` invita a pegar uno de verdad.

    English: a placeholder token invites pasting a real one.
    """
    offenders = [
        _relative(path) for path in _published() if re.search(r"ghp_x{8,}|github_pat_x{8,}", _text(path), re.IGNORECASE)
    ]
    assert not offenders, f"ejemplo de token en {offenders}"


# ── la lista que solo puede encoger ───────────────────────────────────────────


def test_no_new_file_learns_to_decrypt_the_published_token():
    """Mientras la maquinaria exista, al menos no se extiende."""
    spread = []
    for path in _published():
        relative = _relative(path)
        if relative in PAT_READERS:
            continue
        text = _text(path)
        hits = [needle for needle in PAT_MACHINERY if needle in text]
        if hits:
            spread.append(f"{relative}: {hits}")
    assert not spread, (
        "archivos nuevos con la maquinaria del PAT: " + "; ".join(spread) + ". "
        "No se añade a sitios nuevos: la lista PAT_READERS solo puede encoger."
    )


@pytest.mark.parametrize("relative", sorted(PAT_READERS))
def test_every_listed_reader_still_has_it_so_the_list_cannot_rot(relative: str):
    """Si ya no la tiene, hay que quitarlo de la lista en el mismo cambio.

    English: if it no longer has it, it must leave the list in the same change.
    Otherwise the list keeps granting an exemption nobody needs any more.
    """
    path = REPO_ROOT / relative
    assert path.exists(), f"{relative} esta en PAT_READERS y no existe: quitalo de la lista"
    hits = [needle for needle in PAT_MACHINERY if needle in _text(path)]
    assert hits, (
        f"{relative} ya no lleva la maquinaria del PAT. Quitalo de PAT_READERS "
        f"en este mismo cambio, o la exencion sobrevive a lo que exentaba."
    )


def test_the_assistant_is_not_on_the_list():
    """El asistente de despliegue era quien la ESCRIBÍA. Ya no."""
    assert "web/setup/index.html" not in PAT_READERS
    text = _text(WEB / "setup" / "index.html")
    assert not [needle for needle in PAT_MACHINERY if needle in text]
