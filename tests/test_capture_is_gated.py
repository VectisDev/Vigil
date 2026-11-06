"""Ningún paso que contacte la fuente corre sin que el modo lo autorice.

No step that contacts the source runs unless the mode authorises it.

Esta prueba existe por un fallo concreto: el marcador `ELECTION_CLOSED` se
comprobaba con `exit 0` dentro de su propio paso. En GitHub Actions cada `run:`
es un shell distinto, así que ese `exit 0` terminaba ESE paso y no el job, y el
colector del paso siguiente se ejecutaba igualmente. Los cuatro workflows de
captura tenían el mismo patrón: el único freno a la captura era decorativo, y
nadie lo notó porque el workflow salía en verde.

Un `if:` sí salta el paso. Esta prueba fija esa diferencia.

This test exists because of a concrete bug: the `ELECTION_CLOSED` marker was
checked with `exit 0` inside its own step. In GitHub Actions each `run:` is a
separate shell, so that `exit 0` ended THAT step and not the job, and the
collector in the next step ran anyway. All four capture workflows shared the
pattern: the only brake on collection was decorative, and nobody noticed
because the workflow went green.

An `if:` does skip the step. This test pins that difference.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"

# Workflow -> pasos que contactan la fuente electoral y por tanto deben estar
# condicionados al modo resuelto.
GATED_STEPS = {
    "pipeline.yml": ["Run collector"],
    "scheduler.yml": ["Run collector", "Commit data", "Push data to centinel-data"],
    "poller-A.yml": ["Setup data branch", "Run continuous poller A"],
    "poller-B.yml": ["Setup data branch", "Run continuous poller B"],
}


def _steps(workflow: str) -> list[dict]:
    data = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))
    out: list[dict] = []
    for job in (data.get("jobs") or {}).values():
        out.extend(job.get("steps") or [])
    return out


@pytest.mark.parametrize("workflow", sorted(GATED_STEPS))
def test_workflow_resolves_the_mode(workflow: str):
    names = [s.get("name") for s in _steps(workflow)]
    assert "Resolve node mode" in names, f"{workflow} no resuelve el modo"


@pytest.mark.parametrize(
    "workflow,step",
    [(w, s) for w, steps in sorted(GATED_STEPS.items()) for s in steps],
)
def test_collection_step_is_gated_on_the_resolved_mode(workflow: str, step: str):
    matches = [s for s in _steps(workflow) if s.get("name") == step]
    assert len(matches) == 1, f"{workflow}: {step!r} aparece {len(matches)} veces"
    condition = matches[0].get("if", "")
    assert "steps.mode.outputs.go" in condition, (
        f"{workflow}: el paso {step!r} contacta la fuente sin comprobar el modo. " f"Condicion actual: {condition!r}"
    )


@pytest.mark.parametrize("workflow", sorted(GATED_STEPS))
def test_no_step_relies_on_exit_zero_to_stop_the_job(workflow: str):
    """`exit 0` en un paso de guarda no detiene el job: solo ese paso.

    English: `exit 0` in a guard step does not stop the job, only that step.
    """
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    assert (
        "ELECTION_CLOSED marker found" not in text
    ), f"{workflow} conserva el patron del marcador, que no detenia nada"


@pytest.mark.parametrize("workflow", sorted(GATED_STEPS))
def test_the_node_explains_itself_when_it_does_not_collect(workflow: str):
    """Un nodo que no captura debe decir por qué.

    Si no lo dice, un nodo detenido a propósito y uno roto se ven igual desde
    fuera, que es el problema que este sistema entero existe para resolver.

    English: a node that does not collect must say why. Otherwise a
    deliberately idle node and a broken one look identical from outside, which
    is the very problem this system exists to solve.
    """
    names = [s.get("name") for s in _steps(workflow)]
    assert "Explain why nothing was collected" in names
