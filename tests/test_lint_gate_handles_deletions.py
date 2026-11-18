"""El gate de lint no puede morir por un archivo que el PR borró.

The lint gate must not die on a file the PR deleted.

`.github/workflows/ci.yml` revisa solo los archivos Python que el PR cambia, y
arma esa lista con `git diff --name-only`. Ese comando incluye también los
**borrados**, de modo que flake8 recibía rutas que ya no existen en el checkout:

    src/vigil/defense/fetcher.py:0:1: E902 FileNotFoundError
    ##[error]Process completed with exit code 1

El resultado es el peor de los dos posibles: el gate no revisa nada y además se
pone en rojo, así que el rojo deja de significar «hay un problema en el código»
y pasa a significar «este PR borró algo». Un gate que se cae ante una operación
normal enseña a ignorar al gate.

Estaba latente desde que el gate se escribió, y solo salta en un PR que elimine
un `.py` — que hasta ahora ninguno había hecho.

Esta prueba **ejecuta** el comando del workflow contra un repositorio git de
verdad, en lugar de comprobar que el YAML contiene la cadena `--diff-filter`.
La diferencia importa: una prueba de texto pasaría con la bandera mal escrita,
con un valor que no excluye los borrados, o si alguien añadiera un segundo
`git diff` sin ella. Lo que se fija aquí es el comportamiento.

English: `ci.yml` lints only the Python files a PR changes, building that list
with `git diff --name-only`, which also lists DELETED files -- so flake8 was
handed paths that no longer exist and the job died with E902 having checked
nothing. A gate that falls over on an ordinary operation teaches people to
ignore the gate. This test runs the workflow's own command against a real git
repository instead of grepping the YAML for a flag: a text check would pass
with the flag misspelled or with a value that does not exclude deletions.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# La invocación real del gate, tal como vive en el workflow. Se extrae en vez de
# copiarse para que prueba y gate no puedan divergir: si alguien cambia el
# comando, esta prueba mide el comando nuevo.
# English: the gate's real invocation, extracted rather than copied so the test
# and the gate cannot drift apart.
INVOCACION = re.compile(r"git diff --name-only(?P<flags>[^<\n]*?)\s+\"\$\{BASE_SHA\}\"")


def _git(*args: str, cwd: Path) -> str:
    hecho = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return hecho.stdout


@pytest.fixture
def banderas_del_gate() -> str:
    """Las banderas que el workflow le pasa hoy a `git diff --name-only`."""
    encontrado = INVOCACION.search(WORKFLOW.read_text(encoding="utf-8"))
    assert encontrado, (
        "no se encontró la invocación de `git diff --name-only` en ci.yml. "
        "Si el gate cambió de forma, esta prueba debe cambiar con él en vez de "
        "quedarse midiendo algo que ya no existe."
    )
    return encontrado.group("flags").strip()


@pytest.fixture
def repo_con_un_borrado(tmp_path: Path) -> tuple[Path, str, str]:
    """Un repositorio con dos commits: el segundo borra un .py y modifica otro."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "prueba@example.invalid", cwd=repo)
    _git("config", "user.name", "Prueba", cwd=repo)

    (repo / "se_queda.py").write_text("valor = 1\n", encoding="utf-8")
    (repo / "se_borra.py").write_text("valor = 2\n", encoding="utf-8")
    (repo / "no_es_python.md").write_text("texto\n", encoding="utf-8")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "primero", cwd=repo)
    base = _git("rev-parse", "HEAD", cwd=repo).strip()

    (repo / "se_queda.py").write_text("valor = 11\n", encoding="utf-8")
    (repo / "se_borra.py").unlink()
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "segundo", cwd=repo)
    cabeza = _git("rev-parse", "HEAD", cwd=repo).strip()

    return repo, base, cabeza


def _lista_del_gate(repo: Path, banderas: str, base: str, cabeza: str) -> list[str]:
    """Lo que el gate le pasaría a flake8 para este rango."""
    argumentos = ["diff", "--name-only", *banderas.split(), base, cabeza, "--", "*.py"]
    salida = _git(*[a for a in argumentos if a], cwd=repo)
    return [linea for linea in salida.splitlines() if linea.strip()]


def test_the_gate_never_hands_the_linter_a_file_that_is_gone(
    banderas_del_gate: str, repo_con_un_borrado: tuple[Path, str, str]
) -> None:
    """Cada ruta que el gate entrega tiene que existir. Es toda la invariante.

    English: every path the gate hands over must exist. That is the whole
    invariant -- flake8 cannot read a file that was deleted.
    """
    repo, base, cabeza = repo_con_un_borrado
    entregadas = _lista_del_gate(repo, banderas_del_gate, base, cabeza)

    ausentes = [ruta for ruta in entregadas if not (repo / ruta).exists()]
    assert not ausentes, (
        f"el gate entregaría rutas que no están en el checkout: {ausentes}. "
        "flake8 responde E902 FileNotFoundError y el job muere sin haber "
        "revisado nada, en rojo por haber borrado un archivo."
    )


def test_the_deleted_file_is_not_in_the_list(
    banderas_del_gate: str, repo_con_un_borrado: tuple[Path, str, str]
) -> None:
    """Dicho al revés, por si la invariante anterior se cumpliera vacía."""
    repo, base, cabeza = repo_con_un_borrado
    entregadas = _lista_del_gate(repo, banderas_del_gate, base, cabeza)
    assert "se_borra.py" not in entregadas


def test_the_modified_file_is_still_checked(banderas_del_gate: str, repo_con_un_borrado: tuple[Path, str, str]) -> None:
    """Excluir los borrados no puede excluir de paso lo que sí hay que revisar.

    Sin esta prueba, un `--diff-filter` demasiado estrecho dejaría el gate en
    verde sin revisar nada, que es la forma silenciosa del mismo fallo.

    English: excluding deletions must not exclude what actually needs checking.
    Without this, an over-narrow filter would leave the gate green having
    checked nothing -- the silent version of the same failure.
    """
    repo, base, cabeza = repo_con_un_borrado
    entregadas = _lista_del_gate(repo, banderas_del_gate, base, cabeza)
    assert "se_queda.py" in entregadas
    assert "no_es_python.md" not in entregadas, "el filtro '*.py' debe seguir aplicando"
