"""Un nodo nuevo no hereda las claves de acceso de otro.

A new node does not inherit anyone else's access keys.

`web/access.json` está rastreado en la plantilla con doce hashes SHA-256 de las
claves del operador anterior. Un repositorio creado desde la plantilla los
hereda, así que esas doce claves abrirían el panel OPS del nodo nuevo y su
operador no tendría forma de saberlo.

Y no se arreglaba solo. `wizard_seeds.py` se salta la generación cuando ya
existen doce seeds válidos, de modo que el arranque habría pasado por encima
dejándolas en su sitio. Hay una prueba aquí que fija esa condición —
`test_wizard_seeds_would_have_walked_past_the_inherited_keys`— para que quede
escrito por qué el borrado tiene que correr ANTES de generar.

La otra invariante es la red: `keep` declara lo que el borrado no puede
llevarse —el replay, que es lo único que un nodo nuevo muestra el día uno— y
el script falla si falta al terminar. Un borrado mal escrito que se lo llevara
lo haría en silencio, porque el panel se vería igual de vacío que un nodo
recién creado.

English: `web/access.json` is tracked in the template with twelve SHA-256
hashes of the previous operator's keys, and `wizard_seeds.py` would have walked
past them because it skips generation when twelve valid seeds exist. The other
invariant is the net: `keep` declares what the scrub cannot take, and the
script fails if any of it is missing when it finishes.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / ".github" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import bootstrap_scrub as scrub  # noqa: E402

MANIFEST_PATH = REPO_ROOT / scrub.MANIFEST
ACCESS = Path("web/access.json")


def _manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}


@pytest.fixture
def node(tmp_path: Path) -> Path:
    """Un nodo recién creado: copia de la plantilla, con sus datos dentro."""
    root = tmp_path / "node"
    (root / "web" / "data").mkdir(parents=True)
    (root / "web" / "peers").mkdir(parents=True)
    (root / "tests" / "fixtures" / "hnd_2025").mkdir(parents=True)
    (root / ".vigil").mkdir(parents=True)

    shutil.copy(MANIFEST_PATH, root / scrub.MANIFEST)
    shutil.copy(REPO_ROOT / ".vigil" / "mode.yaml", root / ".vigil" / "mode.yaml")
    shutil.copy(REPO_ROOT / ACCESS, root / ACCESS)
    for relative in ("web/data/snapshot.json", "web/data/replay_manifest.json", "web/data/replay_snapshots.json"):
        shutil.copy(REPO_ROOT / relative, root / relative)
    shutil.copy(REPO_ROOT / "web" / "peers" / "HN.json", root / "web" / "peers" / "HN.json")
    shutil.copytree(REPO_ROOT / "web" / "data" / "departments", root / "web" / "data" / "departments")
    (root / "tests" / "fixtures" / "hnd_2025" / "MERKLE_ROOT_HN2025.ots").write_bytes(b"ots")
    return root


# ── lo que importa: las claves heredadas ──────────────────────────────────────


def test_the_manifest_resets_the_inherited_access_keys(node: Path):
    """Nombrado explícitamente: es acceso, no peso."""
    reset_paths = {entry["path"] for entry in _manifest()["reset"]}
    assert str(ACCESS) in reset_paths, (
        "web/access.json tiene que estar en `reset`: lleva doce hashes de las "
        "claves del operador anterior y sin retirarlo abren el panel del nodo nuevo"
    )

    scrub.scrub(node, node / scrub.MANIFEST)
    assert not (node / ACCESS).exists()


def test_wizard_seeds_would_have_walked_past_the_inherited_keys():
    """Por esto el borrado corre ANTES de generar, y no después.

    English: this is why the scrub runs before generation, not after.
    """
    source = (SCRIPTS / "wizard_seeds.py").read_text(encoding="utf-8")
    assert 'if existing.get("seeds") and len(existing["seeds"]) >= 12:' in source
    assert "Seeds already exist" in source

    inherited = json.loads((REPO_ROOT / ACCESS).read_text(encoding="utf-8"))
    assert len(inherited["seeds"]) >= 12, (
        "la plantilla lleva doce seeds validos, asi que la guarda de arriba se "
        "dispara y la generacion se salta: el arranque habria dejado las ajenas"
    )


def test_the_scrub_runs_before_generation_in_the_bootstrap():
    """El orden no es una convención: invertirlo deja las claves ajenas."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "bootstrap.yml").read_text(encoding="utf-8")
    assert workflow.index("bootstrap_scrub.py") < workflow.index("wizard_seeds.py"), (
        "bootstrap_scrub.py debe invocarse antes que wizard_seeds.py, o la guarda "
        "de «ya hay doce seeds» conserva las del operador anterior"
    )
    assert "FORCE_REGENERATE" in workflow, "el segundo cierre sobre la misma puerta"


# ── la red ────────────────────────────────────────────────────────────────────


def test_the_net_fails_when_the_replay_is_gone(node: Path):
    """Si el borrado se lleva el replay, tiene que decirlo y fallar."""
    (node / "web" / "data" / "replay_manifest.json").unlink()
    with pytest.raises(scrub.ScrubError, match="intocables"):
        scrub.scrub(node, node / scrub.MANIFEST)


@pytest.mark.parametrize("pattern", sorted(_manifest().get("keep") or []))
def test_every_kept_path_exists_in_the_template(pattern: str):
    """Un manifiesto que nombra rutas que ya no existen se pudre."""
    assert (REPO_ROOT / pattern).exists(), f"`keep` nombra {pattern}, que no esta en la plantilla"


@pytest.mark.parametrize(
    "pattern",
    sorted(entry["path"] for entry in (_manifest().get("declare_reference") or [])),
)
def test_every_declared_reference_exists_in_the_template(pattern: str):
    assert (REPO_ROOT / pattern).exists(), f"`declare_reference` nombra {pattern}, que no esta"


@pytest.mark.parametrize(
    "pattern",
    sorted(p for entry in (_manifest().get("deferred") or []) for p in (entry.get("paths") or [])),
)
def test_every_deferred_path_exists_in_the_template(pattern: str):
    """Lo aplazado tiene que seguir ahí, o ya no es aplazado sino inventado."""
    assert (REPO_ROOT / pattern).exists(), f"`deferred` nombra {pattern}, que no esta"


# ── el resto del borrado ──────────────────────────────────────────────────────


def test_peers_is_emptied_and_not_deleted(node: Path):
    """El panel lo lee por ruta fija: borrarlo da 404, vaciarlo dice la verdad."""
    scrub.scrub(node, node / scrub.MANIFEST)
    target = node / "web" / "peers" / "HN.json"
    assert target.exists(), "borrarlo daria un 404 donde una lista vacia es correcta"
    assert json.loads(target.read_text(encoding="utf-8")) == {"peers": []}


def test_the_snapshot_is_deleted_rather_than_replaced_by_a_skeleton(node: Path):
    """Un esqueleto escrito a mano se desincroniza del esquema real."""
    scrub.scrub(node, node / scrub.MANIFEST)
    assert not (node / "web" / "data" / "snapshot.json").exists()

    entry = next(e for e in _manifest()["reset"] if e["path"] == "web/data/snapshot.json")
    assert entry["regenerated_by"] == "scripts/export_static_snapshot.py"


def test_the_reference_index_says_it_is_not_a_live_capture(node: Path):
    scrub.scrub(node, node / scrub.MANIFEST)
    document = json.loads((node / scrub.REFERENCE_INDEX).read_text(encoding="utf-8"))

    assert document["schema"] == 1
    assert "no es captura en vivo" in document["label_es"].lower()
    assert "not a live capture" in document["label_en"].lower()
    assert [d["path"] for d in document["datasets"]] == [entry["path"] for entry in _manifest()["declare_reference"]]
    for dataset in document["datasets"]:
        assert dataset["why"], "cada conjunto declarado dice por que se conserva"


def test_a_dry_run_touches_nothing(node: Path):
    before = sorted(p.relative_to(node) for p in node.rglob("*") if p.is_file())
    access_before = (node / ACCESS).read_bytes()

    scrub.scrub(node, node / scrub.MANIFEST, dry_run=True)

    assert sorted(p.relative_to(node) for p in node.rglob("*") if p.is_file()) == before
    assert (node / ACCESS).read_bytes() == access_before


def test_running_it_twice_is_the_same_as_running_it_once(node: Path):
    scrub.scrub(node, node / scrub.MANIFEST)
    first = sorted(p.relative_to(node) for p in node.rglob("*") if p.is_file())
    scrub.scrub(node, node / scrub.MANIFEST)
    assert sorted(p.relative_to(node) for p in node.rglob("*") if p.is_file()) == first


# ── el manifiesto mismo ───────────────────────────────────────────────────────


def test_the_manifest_declares_a_schema_this_script_understands():
    assert _manifest()["schema"] == 1


def test_every_reset_entry_names_an_action_that_exists():
    for entry in _manifest()["reset"]:
        assert entry.get("action") in scrub.ACTIONS, f"{entry.get('path')}: accion {entry.get('action')!r}"


def test_every_entry_says_why():
    """Un manifiesto sin motivos es una lista que nadie puede revisar."""
    manifest = _manifest()
    groups = [manifest.get("reset") or [], manifest.get("declare_reference") or [], manifest.get("deferred") or []]
    for group in groups:
        for entry in group:
            assert str(entry.get("why", "")).strip(), f"entrada sin motivo: {entry}"


def test_an_unknown_action_is_refused(node: Path):
    manifest_path = node / scrub.MANIFEST
    document = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    document["reset"] = [{"path": "web/access.json", "action": "incinerar", "why": "x"}]
    manifest_path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")

    with pytest.raises(scrub.ScrubError, match="accion desconocida"):
        scrub.scrub(node, manifest_path)


def test_a_missing_manifest_is_refused(tmp_path: Path):
    with pytest.raises(scrub.ScrubError, match="no hay manifiesto"):
        scrub.scrub(tmp_path, tmp_path / "no-existe.yaml")
