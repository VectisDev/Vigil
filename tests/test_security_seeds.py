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
    assert job["if"] == "github.actor == github.repository_owner"
    assert job["permissions"] == {"contents": "write"}
    assert 'FORCE_REGENERATE: "true"' in text or "FORCE_REGENERATE: 'true'" in text
    assert "python3 .github/scripts/wizard_seeds.py" in text
    assert "git add -- web/access.json" in text
    assert "path: /tmp/centinel-seeds.txt" in text
    assert "retention-days: 1" in text
    assert "echo " not in text
    assert "cat " not in text
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
