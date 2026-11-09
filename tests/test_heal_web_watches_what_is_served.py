"""El healer vigila lo que la página carga, no lo que cargaba.

The healer watches what the page loads, not what it used to.

`scripts/heal_web.py` restaura desde git los archivos críticos de `web/` si
alguno falta o se corrompe. Su utilidad depende por entero de que la lista
diga la verdad, y había dejado de decirla: vigilaba cinco archivos que el
panel v4 ya no carga —`ops.css`, `ops-panel.js`, `ops-monitor.js`,
`ops-command.js` y `vigil-log.js`— y **ninguno** de los que sí carga.

Protegía lo muerto y dejaba lo vivo sin red. Si `ops-v4.js` hubiera
desaparecido, el healer habría pasado en verde y nadie se habría enterado
hasta abrir la página.

Una lista escrita a mano se desincroniza en cuanto alguien renombra un
archivo. Esta prueba la ata a lo que el HTML publicado realmente pide: lee
cada `<script src>` y cada `<link rel=stylesheet>` de las páginas de `web/`,
resuelve la ruta y exige que esté vigilada.

Se limita a scripts y hojas de estilo a propósito. Si falta un favicon la
página se ve peor; si falta un script, no funciona. El healer existe para lo
segundo.

English: heal_web.py restores critical web files from git. Its usefulness
depends entirely on the list telling the truth, and it had stopped: it watched
five files the v4 panel no longer loads and none of the ones it does. It
protected the dead and left the live without a net. A hand-written list drifts
the moment someone renames a file, so this ties it to what the published HTML
actually asks for. Scripts and stylesheets only, on purpose: a missing favicon
makes the page uglier, a missing script makes it not work.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urldefrag, urlparse

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB = REPO_ROOT / "web"
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import heal_web  # noqa: E402

ASSET = re.compile(
    r"""<script[^>]*\ssrc=["']([^"']+)["']|<link[^>]*\srel=["']stylesheet["'][^>]*\shref=["']([^"']+)["']""",
    re.IGNORECASE,
)


def _pages() -> list[Path]:
    return sorted(WEB.rglob("index.html"))


def _assets_of(page: Path) -> list[str]:
    """Rutas locales de scripts y hojas que la página pide, ya resueltas."""
    out: list[str] = []
    for script_src, link_href in ASSET.findall(page.read_text(encoding="utf-8")):
        raw = script_src or link_href
        if not raw or urlparse(raw).scheme or raw.startswith("//"):
            continue
        # `ops-v4.css?v=20261108v4` y `#algo` son la misma ruta en disco.
        clean = urldefrag(raw.split("?", 1)[0])[0]
        if not clean:
            continue
        resolved = (page.parent / clean).resolve()
        try:
            out.append(str(resolved.relative_to(REPO_ROOT)))
        except ValueError:
            continue  # fuera del repositorio: no es nuestro
    return sorted(set(out))


@pytest.mark.parametrize("page", _pages(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_every_script_and_stylesheet_a_page_loads_is_watched(page: Path):
    """Lo que la página necesita para funcionar tiene que estar en la lista."""
    watched = set(heal_web.CRITICAL_FILES)
    missing = [asset for asset in _assets_of(page) if asset not in watched]
    assert not missing, (
        f"{page.relative_to(REPO_ROOT)} carga {missing}, que heal_web.py no vigila. "
        f"Si desaparecen, el healer pasa en verde y la pagina no funciona."
    )


@pytest.mark.parametrize("watched", sorted(heal_web.CRITICAL_FILES))
def test_every_watched_file_exists(watched: str):
    """Vigilar un archivo que ya no está es vigilar un hueco.

    English: watching a file that is gone is watching a hole. This is the
    other direction of the same invariant, and it is the one that was broken.
    """
    assert (REPO_ROOT / watched).exists(), (
        f"heal_web.py vigila {watched}, que no existe. Si se borro a proposito, "
        f"quitalo de CRITICAL_FILES en el mismo cambio."
    )


def test_the_panel_the_healer_watches_is_the_one_that_is_served():
    """La comprobación concreta que faltaba: el v4, no el panel anterior."""
    watched = set(heal_web.CRITICAL_FILES)
    assert "web/ops/js/ops-v4.js" in watched
    assert "web/ops/ops-v4.css" in watched
    for gone in (
        "web/ops/ops.css",
        "web/ops/js/ops-panel.js",
        "web/ops/js/ops-monitor.js",
        "web/ops/js/ops-command.js",
        "web/ops/js/vigil-log.js",
    ):
        assert gone not in watched, f"{gone} ya no se carga ni existe; no se vigila"
        assert not (REPO_ROOT / gone).exists(), f"{gone} deberia estar borrado"
