"""Regenerating keys is a workflow run, not a key printed on the page."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_the_workflow_uploads_a_one_day_artifact_and_does_not_print_keys() -> None:
    path = ROOT / ".github" / "workflows" / "regenerate-seeds.yml"
    text = path.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    assert doc["name"] == "Regenerate Admin Seeds"
    on = doc.get(True, doc.get("on"))
    assert "workflow_dispatch" in on
    assert "schedule" not in on
    assert doc["permissions"]["contents"] == "read"
    assert "vigil-keys-download-once" in text
    assert "retention-days: 1" in text
    assert "vigil-seeds.txt" in text
    assert "cat " not in text
    assert "echo " not in text
    script = (ROOT / ".github" / "scripts" / "wizard_seeds.py").read_text(encoding="utf-8")
    for line in script.splitlines():
        if line.strip().startswith("print("):
            assert "{key}" not in line
    assert "does not print the keys" in script


def test_the_panel_explains_three_clicks_and_hides_the_keys() -> None:
    page = (ROOT / "web" / "ops" / "index.html").read_text(encoding="utf-8")
    assert "Clave de acceso" in page
    assert "Regenerar claves" in page
    assert "vigil-keys-download-once" in page
    assert "Run workflow" in page
    assert "sessionStorage" not in page
    assert "console.log" not in page
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "vigil-keys-download-once" in readme
