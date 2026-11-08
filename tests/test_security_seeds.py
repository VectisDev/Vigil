"""Seed regeneration is an owner-only workflow, and auto-heal does not take a PR head."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_regenerate_seeds_matches_the_documented_steps() -> None:
    path = ROOT / ".github" / "workflows" / "regenerate-seeds.yml"
    text = path.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    assert doc["name"] == "Regenerate Admin Seeds"
    on = doc.get(True, doc.get("on"))
    assert list(on) == ["workflow_dispatch"]
    assert doc["permissions"] == {"contents": "read"}
    job = doc["jobs"]["regenerate"]
    assert "if" not in job
    assert "github.actor == github.repository_owner" not in text
    assert "repos/${GITHUB_REPOSITORY}/collaborators/${GITHUB_ACTOR}/permission" in text
    assert "orgs/${GITHUB_REPOSITORY_OWNER}/memberships/${GITHUB_ACTOR}" in text
    # El perímetro de permisos se fija exacto, no por contención: este
    # workflow escribe en el repositorio y lo puede lanzar cualquier admin, y
    # la forma en que un workflow así se vuelve peligroso es ganando un
    # permiso que nadie revisó.
    #
    # `actions: write` entró a propósito y hace falta: el paso que publica la
    # página dispara `pages.yml`. Sin él, el push de los hashes nuevos se hace
    # con GITHUB_TOKEN, que por diseño no dispara workflows, y la página
    # seguía sirviendo los hashes viejos: la clave recién generada daba
    # «Clave incorrecta» y había que disparar Pages a mano.
    #
    # English: the permission surface is pinned exactly, not by containment.
    # `actions: write` is deliberate and necessary -- the publish step
    # dispatches `pages.yml`, because a GITHUB_TOKEN push does not trigger
    # workflows and the site kept serving the old hashes.
    assert job["permissions"] == {"contents": "write", "actions": "write"}
    assert (
        "gh workflow run pages.yml" in text
    ), "si se quita el disparo de Pages, `actions: write` sobra y debe irse con el"
    assert "repository admins" in (ROOT / "web" / "ACCESO_ADMIN.md").read_text(encoding="utf-8")
    assert 'FORCE_REGENERATE: "true"' in text or "FORCE_REGENERATE: 'true'" in text
    assert "python3 .github/scripts/wizard_seeds.py" in text
    assert "git add -- web/access.json" in text
    assert "path: /tmp/centinel-seeds.txt" in text
    assert "retention-days: 1" in text
    assert "cat " not in text
    assert "echo /tmp/centinel-seeds.txt" not in text
    script = (ROOT / ".github" / "scripts" / "wizard_seeds.py").read_text(encoding="utf-8")
    assert 'SEEDS_PATH = Path("/tmp/centinel-seeds.txt")' in script
    for line in script.splitlines():
        if line.strip().startswith("print("):
            assert "Clave" not in line
    page = (ROOT / "web" / "ops" / "index.html").read_text(encoding="utf-8")
    assert "Regenerar claves" in page
    assert "actions/workflows/regenerate-seeds.yml" in page
    guide = (ROOT / "web" / "ACCESO_ADMIN.md").read_text(encoding="utf-8")
    assert "Actions → Regenerate Admin Seeds" in guide
    assert "Run workflow" in guide
    assert "centinel-seeds-DESCARGAR-Y-GUARDAR-FUERA-DE-LINEA" in guide
    assert "1 día" in guide


def test_no_workflow_treats_the_actor_as_the_repository_owner() -> None:
    needle = "github.actor == github.repository_owner"
    problems: list[str] = []
    for folder in (ROOT / ".github", ROOT / "scripts"):
        for path in folder.rglob("*"):
            if path.suffix.lower() not in {".yml", ".yaml", ".py", ".sh"}:
                continue
            if needle in path.read_text(encoding="utf-8"):
                problems.append(str(path.relative_to(ROOT)))
    assert problems == []


def test_autoheal_does_not_checkout_a_pull_request_head() -> None:
    text = (ROOT / ".github" / "workflows" / "ci-autoheal.yml").read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    on = doc.get(True, doc.get("on"))
    assert "pull_request" not in on
    assert "pull_request_target" not in on
    assert "workflow_run" not in on
    assert "head_ref" not in text
    assert "cache:" not in text
    assert doc["permissions"]["contents"] == "read"
