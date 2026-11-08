"""Una prueba de navegador sin marcador no corre en ninguna parte.

A browser test without the marker runs nowhere.

Las pruebas que necesitan un navegador se omiten solas en los jobs que no
instalan el binario, lo cual es correcto: sin esa guarda el job saldría en rojo
por una dependencia ausente y no por un fallo del código. Pero la omisión tiene
un precio — **una prueba omitida en todas partes se ve igual que un verde**— y
ese precio solo se paga una vez: el job `browser-tests` de `ci.yml` instala
Chromium y las selecciona con `-m browser`.

El mecanismo tiene un agujero evidente: un archivo nuevo de pruebas de
navegador que se olvide el marcador se omite en los jobs normales, no lo
selecciona el job de navegador, y **no corre en ningún sitio**, en silencio y
pareciendo verde. Esta prueba cierra ese agujero: recorre `tests/` y exige que
todo módulo que use Playwright lleve `pytest.mark.browser`.

Es la misma disciplina que `PAT_READERS` en
`tests/test_no_credentials_in_web.py`: donde hay una exención, la exención se
enumera y la enumeración se comprueba, en vez de confiar en que alguien se
acuerde.

English: browser tests skip themselves in jobs that do not install the binary,
which is correct — without that guard the job would go red for a missing
dependency rather than a code failure. But a skip has a cost, since a test
skipped everywhere looks exactly like a pass, and that cost is paid once: the
`browser-tests` job installs Chromium and selects them with `-m browser`.

The mechanism has an obvious hole: a new browser-test file that forgets the
marker skips in the normal jobs, is not selected by the browser job, and runs
nowhere at all -- silently, looking green. This closes it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS = REPO_ROOT / "tests"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
SELF = Path(__file__).name

USES_PLAYWRIGHT = re.compile(r"playwright\.sync_api")
MARKED = re.compile(r"pytestmark\s*=\s*pytest\.mark\.browser|@pytest\.mark\.browser")


def _browser_modules() -> list[Path]:
    """Los módulos de prueba que usan Playwright, sin contar este."""
    found = []
    for path in sorted(TESTS.glob("test_*.py")):
        if path.name == SELF:
            continue
        if USES_PLAYWRIGHT.search(path.read_text(encoding="utf-8")):
            found.append(path)
    return found


def test_there_is_at_least_one_browser_module():
    """Si no hay ninguno, el job de navegador sale con «no tests ran».

    English: with none, the browser job exits "no tests ran" and goes red,
    which is the correct outcome rather than a quiet green.
    """
    assert _browser_modules(), "no hay modulos de prueba con Playwright; el job de navegador no tendria que existir"


@pytest.mark.parametrize("path", _browser_modules(), ids=lambda p: p.name)
def test_every_browser_module_carries_the_marker(path: Path):
    """Sin marcador, el módulo se omite en todos los jobs y nadie lo nota."""
    assert MARKED.search(path.read_text(encoding="utf-8")), (
        f"{path.name} usa Playwright y no lleva `pytestmark = pytest.mark.browser`, "
        f"asi que se omite en los jobs normales y el job `browser-tests` no lo "
        f"selecciona: no corre en ningun sitio y parece verde."
    )


# ── el job que las hace valer ─────────────────────────────────────────────────


def test_ci_has_a_job_that_installs_the_browser():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "browser-tests:" in text, "sin este job, las pruebas de navegador no corren en ninguna parte"
    assert "playwright install --with-deps chromium" in text
    assert "-m browser" in text, "el job debe seleccionar por marcador, no por lista de archivos"


def test_the_job_sets_the_variable_that_turns_a_skip_into_a_failure():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "VIGIL_REQUIRE_BROWSER" in text


@pytest.mark.parametrize("path", _browser_modules(), ids=lambda p: p.name)
def test_every_browser_module_honours_that_variable(path: Path):
    """Un módulo que la ignora se omite en silencio en el job que la pone.

    Y eso es un verde falso: el job habría instalado el navegador, habría
    fallado al hacerlo, y las pruebas de ese módulo se habrían saltado sin que
    nada lo dijera. Comprobarlo en UN módulo no bastaba — el agujero reaparece
    con el siguiente que se añada.

    English: a module that ignores it skips silently in the job that sets it,
    and that is a false green. Checking one module was not enough: the hole
    reappears with the next one added.
    """
    source = path.read_text(encoding="utf-8")
    assert 'os.environ.get("VIGIL_REQUIRE_BROWSER") == "1"' in source, (
        f"{path.name} no lee VIGIL_REQUIRE_BROWSER, asi que en el job de navegador "
        f"una instalacion rota lo omitiria en silencio"
    )
    assert "raise AssertionError" in source, (
        f"{path.name} lee la variable pero no falla con ella puesta: la omision "
        f"tiene que convertirse en FALLO, no quedarse en omision"
    )


def test_the_marker_is_registered():
    """Un marcador sin registrar es una advertencia hoy y un error mañana."""
    assert "browser: necesita un navegador" in (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
