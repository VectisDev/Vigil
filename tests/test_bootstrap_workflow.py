"""Crear un repositorio desde la plantilla no manda una sola petición al CNE.

Creating a repository from the template sends no request to the authority.

Ésta es la prueba que más importa de este archivo. Una plantilla arranca con
Actions vivos —a diferencia de un fork— así que alguien que pulsa «Use this
template» por curiosidad ejecuta código inmediatamente. Si ese código
consultara la fuente auditada, el proyecto sería un ataque de denegación de
servicio distribuido por diseño, multiplicado por el número de curiosos.

`bootstrap.yml` no toca la fuente: ni descubre endpoints, ni descarga, ni
corre el pipeline. Solo retira datos heredados, genera configuración local,
acuña claves y publica un panel en modo `REPLAY`. Las pruebas de abajo lo
fijan por nombre de script, para que añadir mañana un paso que sí consulte
tenga que pasar por aquí.

Lo demás son las lecciones que ya costaron dinero en este repositorio:
`needs` solo ordena y hace falta el `if:`; cada job declara sus permisos
porque CodeQL lo exige y porque un job sin declararlos hereda los del
workflow; y los datos que vienen del evento no se interpolan dentro de `run:`.

English: this is the test that matters most here. A template starts with
Actions live, unlike a fork, so anyone who clicks "Use this template" out of
curiosity runs code immediately -- and if that code queried the audited source,
the project would be a distributed denial of service by design. `bootstrap.yml`
does not touch the source. The rest are lessons this repository already paid
for: `needs` only orders, every job declares its permissions, and event data is
not interpolated inside `run:`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "bootstrap.yml"
SEEDS_SCRIPT = REPO_ROOT / ".github" / "scripts" / "wizard_seeds.py"

# Todo lo que emite una peticion a la fuente auditada. Si alguno aparece en el
# arranque, la prueba falla y con razon.
# English: everything that issues a request to the audited source.
TOUCHES_THE_SOURCE = (
    "wizard_discovery.py",
    "download_and_hash.py",
    "run_pipeline.py",
    "poller",
    "audit.yml",
)


def _doc() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8")) or {}


def _triggers(doc: dict) -> dict:
    # PyYAML lee la clave `on:` como el booleano True.
    raw = doc.get(True, doc.get("on"))
    return raw if isinstance(raw, dict) else {}


def _run_bodies(doc: dict) -> list[str]:
    bodies: list[str] = []
    for job in (doc.get("jobs") or {}).values():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps") or []:
            if isinstance(step, dict) and isinstance(step.get("run"), str):
                bodies.append(step["run"])
    return bodies


# ── la invariante ética ───────────────────────────────────────────────────────


def test_the_bootstrap_never_contacts_the_audited_source():
    """Pulsar «Use this template» no debe generar ni una petición al CNE."""
    text = WORKFLOW.read_text(encoding="utf-8")
    found = [name for name in TOUCHES_THE_SOURCE if re.search(rf"(?<![\w-]){re.escape(name)}", text)]
    assert not found, (
        f"bootstrap.yml invoca {found}, que contacta la fuente auditada. Una "
        f"plantilla arranca con Actions vivos: eso consultaria al CNE por cada "
        f"repositorio creado por curiosidad."
    )


def test_the_bootstrap_declares_replay_and_not_live():
    """El modo por defecto de un nodo nuevo es el que no pide nada."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--mode REPLAY" in text
    assert "--mode LIVE" not in text
    assert "--mode ARMED" not in text


def test_the_ceiling_is_asserted_during_the_bootstrap():
    assert "assert_source_budget.py" in WORKFLOW.read_text(encoding="utf-8")


# ── las guardas ───────────────────────────────────────────────────────────────


def test_the_template_itself_does_not_bootstrap():
    """`.vigil/UPSTREAM` presente significa plantilla, y la plantilla no arranca."""
    verdict = next(s for s in _doc()["jobs"]["decide"]["steps"] if s.get("id") == "verdict")
    body = str(verdict["run"])
    assert ".vigil/UPSTREAM" in body
    assert ".vigil/node.json" in body
    assert "go=true" in body and "go=false" in body


def test_the_bootstrap_job_checks_the_verdict_and_does_not_merely_wait_for_it():
    """`needs` solo ordena; sin el `if:` el job corre igual.

    English: `needs` only orders; without the `if:` the job runs anyway.
    """
    job = _doc()["jobs"]["bootstrap"]
    needs = job.get("needs")
    needs = [needs] if isinstance(needs, str) else list(needs or [])
    assert "decide" in needs
    assert "needs.decide.outputs.go == 'true'" in str(job.get("if", ""))


def test_a_fork_does_not_bootstrap():
    assert "github.event.repository.fork" in str(_doc()["jobs"]["decide"].get("if", ""))


def test_it_cannot_re_trigger_itself():
    """El commit final lo empuja GITHUB_TOKEN, que no dispara workflows.

    Además el propio `.vigil/node.json` que escribe hace que el veredicto
    siguiente diga que no. Dos frenos, y el segundo no depende de una
    propiedad de la plataforma que podria cambiar.
    """
    doc = _doc()
    triggers = _triggers(doc)
    assert "push" in triggers
    verdict = next(s for s in doc["jobs"]["decide"]["steps"] if s.get("id") == "verdict")
    assert ".vigil/node.json" in str(verdict["run"]), "sin marcador de idempotencia el arranque se repetiria"


def test_there_is_no_issues_trigger():
    """Se dejó fuera a propósito, y la prueba lo fija.

    Cualquiera puede abrir un Issue, así que un disparador `issues` obliga a
    validar texto ajeno. `workflow_dispatch` lleva los mismos datos y exige
    permiso de escritura. Una entrada menos que validar es una superficie
    menos que defender.

    English: anyone can open an Issue, so an `issues` trigger means validating
    someone else's text. `workflow_dispatch` carries the same data and
    requires write access.
    """
    assert "issues" not in _triggers(_doc())


def test_queued_bootstraps_wait_instead_of_cancelling_each_other():
    concurrency = _doc().get("concurrency") or {}
    assert concurrency.get("cancel-in-progress") is False
    assert "${{ github.repository }}" in str(concurrency.get("group"))


# ── las lecciones que ya costaron ─────────────────────────────────────────────


def test_every_job_declares_its_own_permissions():
    """Un job sin declararlos hereda los del workflow. CodeQL lo marca."""
    for name, job in (_doc().get("jobs") or {}).items():
        assert isinstance(job.get("permissions"), dict), f"el job {name!r} no declara permissions"


def test_the_bootstrap_job_asks_for_no_more_than_it_uses():
    job = _doc()["jobs"]["bootstrap"]
    assert job["permissions"] == {"contents": "write", "issues": "write"}, (
        "escribe el commit del nodo y abre el Issue de arranque, y nada mas; "
        "si se quita alguna de las dos cosas, el permiso sobra y debe irse con ella"
    )
    assert _doc()["jobs"]["decide"]["permissions"] == {"contents": "read"}


def test_no_run_block_interpolates_event_controlled_data():
    """Los datos del evento llegan por `env:`, nunca dentro de `run:`."""
    dangerous = re.compile(r"\$\{\{\s*github\.event\.(?!inputs\.)")
    for body in _run_bodies(_doc()):
        assert not dangerous.search(body), f"interpolacion de datos del evento dentro de un run:\n{body[:200]}"


def test_every_action_is_pinned_by_sha():
    text = WORKFLOW.read_text(encoding="utf-8")
    for uses in re.findall(r"uses:\s*(\S+)", text):
        if uses.startswith("./"):
            continue
        reference = uses.split("@", 1)[1] if "@" in uses else ""
        assert re.fullmatch(r"[0-9a-f]{40}", reference), f"{uses} no esta fijado por SHA"


# ── el Issue de arranque ──────────────────────────────────────────────────────


def test_the_setup_issue_cites_the_platform_limit_verbatim():
    """Un evaluador que ve un paso manual quiere saber que no es pereza."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "This option requires a token other than" in text
    assert "don't trigger a Pages build" in text
    assert "Administration: write" in text
    assert "Settings → Pages" in text


def test_the_setup_issue_states_the_consent_and_what_is_not_running():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "tu cuenta de GitHub queda públicamente asociada" in text
    assert "No captura nada" in text


# ── claves traídas de fuera ───────────────────────────────────────────────────


def _run_seeds(tmp_path: Path, hashes: str) -> subprocess.CompletedProcess:
    environment = dict(os.environ)
    environment.update({"VIGIL_SEED_HASHES": hashes, "VIGIL_COUNTRY": "HN", "FORCE_REGENERATE": "true"})
    (tmp_path / "web").mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [sys.executable, str(SEEDS_SCRIPT)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_externally_supplied_hashes_are_used_and_no_plaintext_is_written(tmp_path: Path):
    """Las claves se quedan en el navegador; aquí solo llegan sus hashes."""
    hashes = [f"{index:064x}" for index in range(1, 13)]
    result = _run_seeds(tmp_path, ",".join(hashes))

    assert result.returncode == 0, result.stderr
    document = json.loads((tmp_path / "web" / "access.json").read_text(encoding="utf-8"))
    assert document["seeds"] == hashes
    assert document["origin"] == "external-hashes"
    assert document["method"] == "SHA-256"


@pytest.mark.parametrize(
    "hashes,expected",
    [
        (",".join(f"{index:064x}" for index in range(1, 12)), "hacen falta 12"),
        (",".join([f"{1:064x}"] * 12), "repetidos"),
        (",".join(["zz" + "0" * 62] + [f"{index:064x}" for index in range(2, 13)]), "no son hashes"),
        (",".join(["abc"] * 12), "no son hashes"),
    ],
)
def test_bad_hashes_are_refused(tmp_path: Path, hashes: str, expected: str):
    """Once hashes, o doce con repetidos, son menos de doce claves."""
    result = _run_seeds(tmp_path, hashes)
    assert result.returncode == 1
    assert expected in result.stderr
    assert not (tmp_path / "web" / "access.json").exists()


def test_the_bootstrap_passes_the_hashes_through():
    assert "VIGIL_SEED_HASHES" in WORKFLOW.read_text(encoding="utf-8")
