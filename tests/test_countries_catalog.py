"""El catálogo de países no puede discrepar de los presets.

The country catalogue cannot drift from the presets.

`web/data/countries.json` existía mantenido a mano y **nada lo generaba**. La
desincronización no era cosmética: el asistente de despliegue ofrece países
leyéndolo, así que si el catálogo dice que un país está disponible y su preset
no declara ninguna URL, el asistente invita a desplegar un nodo que el
arranque va a rechazar.

Ya había discrepado: la autoridad de Estados Unidos estaba truncada respecto
al preset.

Estas pruebas hacen del archivo una salida generada y no una copia: si no
coincide con lo que `export_countries_json.py` produce, fallan y dicen cómo
regenerarlo.

English: the file existed, hand-maintained, and nothing generated it. Drift was
not cosmetic: the assistant offers countries by reading it, so a country listed
as available whose preset declares no URL invites a deployment the bootstrap
will refuse. It had already drifted. These make the file a generated output
rather than a copy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / ".github" / "scripts"
for _candidate in (SCRIPTS, REPO_ROOT / "src"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

pytest.importorskip("yaml")

import export_countries_json as exporter  # noqa: E402
from vigil.countries import LATAM_COUNTRIES  # noqa: E402

CATALOG = REPO_ROOT / exporter.OUTPUT


def _catalog() -> list[dict]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def test_the_committed_catalog_matches_the_presets():
    """La prueba sin la cual generarlo una vez no sirve de nada."""
    assert CATALOG.read_text(encoding="utf-8") == exporter.render(exporter.build()), (
        "web/data/countries.json esta desfasado respecto a src/vigil/countries.py. "
        "Regenera con `python .github/scripts/export_countries_json.py`."
    )


def test_the_check_mode_agrees_with_the_file():
    assert exporter.main(["--check", "--root", str(REPO_ROOT)]) == 0


def test_every_preset_appears_exactly_once():
    codes = [entry["code"] for entry in _catalog()]
    assert sorted(codes) == sorted(LATAM_COUNTRIES)
    assert len(codes) == len(set(codes))


def test_a_country_with_no_declared_url_is_marked_unconfigurable():
    """Cuba, Haití y Estados Unidos. El asistente los deshabilita por esto."""
    for entry in _catalog():
        preset = LATAM_COUNTRIES[entry["code"]]
        expected = bool(preset.url_pattern or preset.national_url)
        assert entry["configurable"] is expected, entry["code"]
        if not expected:
            assert entry["reason"], f"{entry['code']}: una negativa sin motivo no se puede actuar"


def test_no_entry_claims_more_requests_than_the_ceiling():
    """El techo de 19 es la premisa ética; el catálogo no puede sugerir más."""
    import wizard_config as wc  # noqa: PLC0415

    for entry in _catalog():
        assert entry["requests_per_cycle"] <= wc.ceiling(), entry["code"]


def test_coverage_is_complete_exactly_when_nothing_is_left_out():
    for entry in _catalog():
        if not entry["configurable"]:
            continue
        assert entry["complete"] is (entry["divisions_covered"] == entry["divisions_total"]), entry["code"]


def test_honduras_fits_exactly():
    """18 departamentos + 1 nacional = 19, que es el techo justo."""
    honduras = next(entry for entry in _catalog() if entry["code"] == "HN")
    assert honduras["divisions_total"] == 18
    assert honduras["divisions_covered"] == 18
    assert honduras["requests_per_cycle"] == 19
    assert honduras["complete"] is True
