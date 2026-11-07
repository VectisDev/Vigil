"""Un repositorio recién creado desde la plantilla no consulta a nadie.

A freshly created repository does not query anyone.

Un despliegue de VIGIL es un repositorio creado en la cuenta de otra persona.
En el instante en que se crea hereda los workflows programados de la plantilla,
y GitHub los activa: a diferencia de un fork, una plantilla arranca con Actions
y con los `schedule` vivos. Sin nada que lo impida, alguien que pulsa «Use this
template» por curiosidad empieza a consultar el portal del CNE sin saberlo, y
con N despliegues la carga se multiplica por N.

El techo de 19 endpoints es la premisa ética del proyecto. Un sistema que
vigila la integridad de una elección no puede ser, él mismo, un problema de
carga para la autoridad que audita.

Estas pruebas son una red sobre la configuración, no sobre el código: lo que
protegen es que nadie añada mañana un workflow programado sin guarda, que es
exactamente lo que había pasado con `audit.yml` — los otros cuatro colectores
recibieron su comprobación de modo y él se quedó fuera, corriendo cada tres
horas sin nada que lo parase.

English: these guard the configuration rather than the code. What they protect
against is someone adding a scheduled workflow with no guard tomorrow -- which
is exactly what had happened to `audit.yml`: the other four collectors got
their mode check and it was left out, running every three hours with nothing
stopping it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
GATE = WORKFLOWS / "_gate.yml"

# CodeQL analiza el código del propio repositorio y no emite ninguna petición
# a la fuente auditada. Que corra en un despliegue ajeno es inofensivo, y de
# hecho útil para quien lo despliega. Es la única excepción, y está aquí por
# escrito para que sea una decisión y no un olvido.
# English: CodeQL analyses the repository's own code and issues no requests to
# the audited source. Running in someone else's deployment is harmless and in
# fact useful to them. It is the one exception, written down so that it is a
# decision rather than an oversight.
EXEMPT = {"codeql.yml"}

# Los que consultan la fuente auditada. Estos necesitan el gate completo, no
# solo una guarda de fork: también el modo y el techo de fuentes.
COLLECTORS = {"audit.yml", "poller-A.yml", "poller-B.yml", "scheduler.yml", "pipeline.yml"}


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _triggers(doc: dict) -> dict:
    # PyYAML interpreta la clave `on:` como el booleano True.
    # English: PyYAML reads the key `on:` as the boolean True.
    raw = doc.get(True, doc.get("on"))
    return raw if isinstance(raw, dict) else {}


def _workflows() -> list[Path]:
    return sorted(WORKFLOWS.glob("*.yml"))


def _scheduled() -> list[Path]:
    return [p for p in _workflows() if "schedule" in _triggers(_load(p))]


def _is_covered(name: str, job: dict) -> bool:
    condition = str(job.get("if", ""))
    needs = job.get("needs")
    needs = [needs] if isinstance(needs, str) else list(needs or [])
    return (
        name == "gate"
        or str(job.get("uses", "")).endswith("_gate.yml")
        or "gate.outputs.go" in condition
        or "fork" in condition
        or any("gate" in n for n in needs)
    )


# ── la invariante ─────────────────────────────────────────────────────────────


def test_every_workflow_parses():
    """Un YAML roto se salta en silencio, y un gate que no corre no gatea."""
    for path in _workflows():
        assert isinstance(_load(path), dict), path.name


@pytest.mark.parametrize("path", _scheduled(), ids=lambda p: p.name)
def test_every_scheduled_job_is_guarded(path: Path):
    """Ningún job programado corre sin guarda en un repositorio ajeno.

    English: no scheduled job runs unguarded in someone else's repository.
    """
    if path.name in EXEMPT:
        pytest.skip(f"{path.name} no consulta la fuente auditada")

    doc = _load(path)
    unguarded = [
        name for name, job in doc.get("jobs", {}).items() if isinstance(job, dict) and not _is_covered(name, job)
    ]
    assert not unguarded, (
        f"{path.name}: {unguarded} corre por horario sin guarda. "
        f"Añade una guarda de fork, o el gate completo si consulta la fuente."
    )


def test_the_collectors_use_the_full_gate_not_just_a_fork_guard():
    """Una guarda de fork no basta donde se emiten peticiones.

    English: a fork guard is not enough where requests are issued. The gate
    also checks the declared mode and the 19-endpoint ceiling; a fork guard
    alone would let a legitimate node scrape a dead portal forever, which is
    what the old ELECTION_CLOSED marker allowed.
    """
    for name in sorted(COLLECTORS):
        doc = _load(WORKFLOWS / name)
        jobs = doc.get("jobs", {})
        assert "gate" in jobs, f"{name} no llama a _gate.yml"
        assert str(jobs["gate"].get("uses", "")).endswith("_gate.yml"), name

        consumers = [j for n, j in jobs.items() if n != "gate" and "gate" in str(j.get("needs", ""))]
        assert consumers, f"{name}: nadie depende del gate, asi que no gatea nada"
        assert any("gate.outputs.go == 'true'" in str(j.get("if", "")) for j in consumers), (
            f"{name}: alguien depende del gate pero nadie comprueba su salida. "
            f"`needs` solo ordena; sin el `if` el job corre igual."
        )


def test_no_capture_workflow_keeps_a_cancelling_shared_group():
    """Dos workflows en un grupo que cancela se matan mutuamente.

    English: two workflows in a cancelling group kill each other. scheduler and
    pipeline both sat in `centinel-pipeline` with cancel-in-progress, so
    whichever fired second killed the other mid-flight. Measured over the
    repo's history, observed cadence had a median of 283 minutes against the
    30 declared.
    """
    cancelling: dict[str, list[str]] = {}
    for path in _workflows():
        concurrency = _load(path).get("concurrency")
        if isinstance(concurrency, dict) and concurrency.get("cancel-in-progress") is True:
            cancelling.setdefault(str(concurrency.get("group")), []).append(path.name)

    shared = {group: names for group, names in cancelling.items() if len(names) > 1}
    assert not shared, f"grupos de concurrencia compartidos CON cancelacion: {shared}"


def test_the_capture_group_never_cancels():
    """Una captura encolada espera; una cancelada pierde el ciclo."""
    doc = _load(WORKFLOWS / "audit.yml")
    concurrency = doc.get("concurrency") or {}
    assert concurrency.get("cancel-in-progress") is False
    assert "${{ github.repository }}" in str(
        concurrency.get("group")
    ), "el grupo debe llevar el repositorio: sin eso, dos nodos distintos competirian entre si"


# ── el gate mismo ─────────────────────────────────────────────────────────────


def test_the_gate_is_callable_and_declares_what_callers_read():
    doc = _load(GATE)
    call = _triggers(doc).get("workflow_call") or {}
    assert set(call.get("outputs", {})) >= {"go", "mode", "reason"}
    assert doc.get("permissions") == {"contents": "read"}, "el gate solo decide; no debe poder escribir"


def test_the_gate_writes_go_exactly_once():
    """`go` tiene un único autor, y esto no es cosmético.

    English: `go` has exactly one author, and this is not cosmetic.

    `resolve_mode.py` también escribe `go=` en $GITHUB_OUTPUT cuando esa
    variable existe, porque los workflows que lo invocan directamente leen esa
    salida. Dentro del gate eso duplicaba la clave, y de las dos ganaba la
    última por orden de escritura: el resultado era correcto por accidente, y
    reordenar dos líneas habría invertido el gate a dejar pasar, en silencio.
    """
    body = str(next(s for s in _load(GATE)["jobs"]["decide"]["steps"] if s.get("id") == "verdict")["run"])
    assert "env -u GITHUB_OUTPUT python .github/scripts/resolve_mode.py" in body, (
        "resolve_mode.py debe correr sin GITHUB_OUTPUT dentro del gate, "
        "o duplicara la clave `go` y el resultado dependera del orden"
    )


def test_the_gate_checks_fork_mode_and_budget():
    """Las tres comprobaciones están, y el aserto del techo es una de ellas."""
    body = str(next(s for s in _load(GATE)["jobs"]["decide"]["steps"] if s.get("id") == "verdict")["run"])
    assert "IS_FORK" in body
    assert ".vigil/UPSTREAM" in body
    assert "resolve_mode.py" in body
    assert "assert_source_budget.py" in body


def test_the_upstream_marker_is_tracked_in_this_repository():
    """El original lo lleva; el arranque lo borra en cada nodo."""
    assert (
        REPO_ROOT / ".vigil" / "UPSTREAM"
    ).exists(), "sin este archivo la plantilla original captura por horario como si fuera un nodo"
