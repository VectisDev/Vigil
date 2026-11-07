"""Ningún paso que contacte la fuente corre sin que el modo lo autorice.

No step that contacts the source runs unless the mode authorises it.

Esta prueba existe por un fallo concreto: el marcador `ELECTION_CLOSED` se
comprobaba con `exit 0` dentro de su propio paso. En GitHub Actions cada `run:`
es un shell distinto, así que ese `exit 0` terminaba ESE paso y no el job, y el
colector del paso siguiente se ejecutaba igualmente. Los workflows de captura
tenían el mismo patrón: el único freno a la captura era decorativo, y nadie lo
notó porque el workflow salía en verde.

Un `if:` sí salta el paso. Esta prueba fija esa diferencia.

**La guarda subió de paso a job.** Antes cada paso que tocaba la fuente llevaba
su propio `if: steps.mode.outputs.go == 'true'`. Eso dependía de que alguien se
acordara de anotar cada paso nuevo, y falló dos veces: `audit.yml` no tenía
ninguna comprobación pese a correr cada tres horas, y dentro de los demás los
pasos sin anotar corrían igual.

Ahora la condición vive en el job (`needs: gate` más
`if: needs.gate.outputs.go == 'true'`), así que **todos** los pasos del job se
saltan a la vez, incluidos los que nadie anotó. La invariante es la misma; la
cobertura pasa de enumerada a completa.

English: the guard moved from step level to job level. Before, each step
touching the source carried its own `if:`, which depended on someone
remembering to annotate every new step -- and that failed twice: `audit.yml`
had no check at all despite running every three hours, and unannotated steps
elsewhere ran anyway. The condition now lives on the job, so every step is
skipped together. Same invariant; coverage goes from enumerated to complete.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"

# Los workflows que pueden contactar la fuente electoral. `audit.yml` entra
# aquí ahora: era el único de los cinco sin ninguna comprobación de modo.
# English: audit.yml joins the list now -- it was the one of the five with no
# mode check at all.
CAPTURE_WORKFLOWS = [
    "audit.yml",
    "pipeline.yml",
    "poller-A.yml",
    "poller-B.yml",
    "scheduler.yml",
]

# Workflow -> jobs que contactan la fuente y por tanto deben depender del gate.
CAPTURE_JOBS = {
    "audit.yml": ["audit"],
    "pipeline.yml": ["collector"],
    "poller-A.yml": ["continuous-poll-A"],
    "poller-B.yml": ["continuous-poll-B"],
    "scheduler.yml": ["build"],
}


def _doc(workflow: str) -> dict:
    return yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8")) or {}


def _steps(workflow: str) -> list[dict]:
    out: list[dict] = []
    for job in (_doc(workflow).get("jobs") or {}).values():
        if isinstance(job, dict):
            out.extend(job.get("steps") or [])
    return out


@pytest.mark.parametrize("workflow", CAPTURE_WORKFLOWS)
def test_workflow_resolves_the_mode(workflow: str):
    """El modo se resuelve, y en un único sitio para todo el workflow."""
    jobs = _doc(workflow).get("jobs") or {}
    assert "gate" in jobs, f"{workflow} no resuelve el modo"
    assert str(jobs["gate"].get("uses", "")).endswith(
        "_gate.yml"
    ), f"{workflow}: el job `gate` debe delegar en _gate.yml y no reimplementar la decision"


@pytest.mark.parametrize(
    "workflow,job",
    [(w, j) for w, jobs in sorted(CAPTURE_JOBS.items()) for j in jobs],
)
def test_collection_job_is_gated_on_the_resolved_mode(workflow: str, job: str):
    """`needs` solo ordena; hace falta el `if:` para que no corra.

    English: `needs` only orders; the `if:` is what stops it running. A job
    with `needs: gate` and no condition runs regardless of what the gate
    decided -- it merely waits for it first.
    """
    jobs = _doc(workflow).get("jobs") or {}
    assert job in jobs, f"{workflow}: no existe el job {job!r}"
    spec = jobs[job]

    needs = spec.get("needs")
    needs = [needs] if isinstance(needs, str) else list(needs or [])
    assert "gate" in needs, f"{workflow}/{job} no depende del gate"

    condition = str(spec.get("if", ""))
    assert "needs.gate.outputs.go == 'true'" in condition, (
        f"{workflow}: el job {job!r} contacta la fuente sin comprobar la salida del gate. "
        f"Condicion actual: {condition!r}"
    )


@pytest.mark.parametrize("workflow", CAPTURE_WORKFLOWS)
def test_no_step_relies_on_exit_zero_to_stop_the_job(workflow: str):
    """`exit 0` en un paso de guarda no detiene el job: solo ese paso.

    English: `exit 0` in a guard step does not stop the job, only that step.
    """
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    assert (
        "ELECTION_CLOSED marker found" not in text
    ), f"{workflow} conserva el patron del marcador, que no detenia nada"


@pytest.mark.parametrize("workflow", CAPTURE_WORKFLOWS)
def test_no_leftover_step_level_mode_checks(workflow: str):
    """Dos guardas son peor que una: pueden discrepar.

    English: two guards are worse than one -- they can disagree. A step-level
    `steps.mode.outputs.go` left behind after the job-level gate means the
    mode is resolved twice, and the two can differ if the election window is
    crossed between the gate job and the capture job.
    """
    for step in _steps(workflow):
        condition = str(step.get("if", ""))
        assert "steps.mode.outputs.go" not in condition, (
            f"{workflow}: el paso {step.get('name')!r} conserva una guarda de modo por paso, "
            f"redundante con el gate del job y capaz de discrepar de el"
        )


def test_the_node_explains_itself_when_it_does_not_collect():
    """Un nodo que no captura debe decir por qué.

    Si no lo dice, un nodo detenido a propósito y uno roto se ven igual desde
    fuera, que es el problema que este sistema entero existe para resolver.

    El motivo lo publica ahora el gate en el resumen de la ejecución, donde se
    ve sin abrir los registros, en vez de en un `echo` repetido en cada
    workflow. Un solo sitio que lo diga, igual que un solo sitio que lo decida.

    English: a node that does not collect must say why. Otherwise a
    deliberately idle node and a broken one look identical from outside, which
    is the very problem this system exists to solve. The reason is now
    published by the gate into the run summary, visible without opening logs.
    """
    gate = _doc("_gate.yml")
    verdict = next(s for s in gate["jobs"]["decide"]["steps"] if s.get("id") == "verdict")
    body = str(verdict["run"])

    assert "GITHUB_STEP_SUMMARY" in body, "el gate no publica el motivo donde se ve"
    assert "Motivo:" in body, "el gate no nombra el motivo de no capturar"
    assert "reason=" in body, "el gate no expone el motivo a quien lo llama"

    call = gate.get(True, gate.get("on")) or {}
    assert "reason" in (
        call.get("workflow_call", {}).get("outputs") or {}
    ), "el motivo debe ser una salida del gate, para que el llamador pueda repetirlo"
