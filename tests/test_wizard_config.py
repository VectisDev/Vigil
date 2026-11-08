"""El generador de configuración respeta el país y el techo, o para.

The config generator honours the country and the ceiling, or stops.

`wizard_config.py` es el primer paso del arranque de un nodo, así que es el
primer sitio donde el techo ético de 19 endpoints se puede respetar o romper.
Estas pruebas fijan los cuatro fallos que lo rompían, medidos sobre los 21
presets reales y no supuestos:

1. Solo Honduras declara `national_url`, así que para los otros 20 países el
   `cne.main_url` hondureño sobrevivía a la generación. Un nodo de Guatemala
   quedaba configurado para consultar al CNE de Honduras.
2. 17 de los 21 presets usan `{division}` y el script sustituía `{cne_code}`,
   así que sus URLs llevaban el marcador literal dentro.
3. Once de los 21 presets tienen más divisiones de las que caben en 19.
4. Sin preset seguía adelante, dejando la configuración del país anterior.

La prueba que más vale es `test_every_preset_either_configures_within_budget_or_refuses`:
recorre los 21 presets y exige que cada uno acabe en una configuración que
`assert_source_budget.py` acepta, o en una negativa explícita. No hay tercera
salida, y la tercera salida era justo lo que había.

English: these pin the four bugs that broke the generator, measured against
the 21 real presets. The one that matters most walks all 21 and requires each
to end either in a config the budget assert accepts or in an explicit refusal.
There is no third outcome, and the third outcome was exactly what existed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / ".github" / "scripts"
for _candidate in (SCRIPTS, REPO_ROOT / "src"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

import assert_source_budget as budget  # noqa: E402
import wizard_config as wc  # noqa: E402
from vigil.countries import LATAM_COUNTRIES  # noqa: E402

ALL_COUNTRIES = sorted(LATAM_COUNTRIES)
HN_HOST = "resultadosgenerales2025.cne.hn"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """Una raíz sembrada con la configuración REAL de Honduras.

    Sembrarla es el punto: el fallo de la fusión solo aparece cuando ya hay
    una configuración de otro país donde escribir. Una raíz vacía lo habría
    escondido.

    English: seeded with Honduras' real config on purpose -- the merge bug
    only shows when there is another country's config already in place.
    """
    for relative in (wc.ENDPOINTS_YAML, wc.COMMAND_CENTER):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((REPO_ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "web" / "data").mkdir(parents=True, exist_ok=True)
    return tmp_path


def _urls(root: Path) -> list[str]:
    document = yaml.safe_load((root / wc.ENDPOINTS_YAML).read_text(encoding="utf-8")) or {}
    return budget.collect_urls(document)


def _departments(root: Path) -> dict:
    return json.loads((root / wc.DEPARTMENTS_JSON).read_text(encoding="utf-8"))


# ── la invariante, sobre los 21 presets ───────────────────────────────────────


@pytest.mark.parametrize("country", ALL_COUNTRIES)
def test_every_preset_either_configures_within_budget_or_refuses(country: str, root: Path):
    """Configuración que el aserto acepta, o negativa. No hay tercera salida."""
    try:
        wc.generate(country, "2029", None, root)
    except wc.Unconfigurable:
        return

    document = yaml.safe_load((root / wc.ENDPOINTS_YAML).read_text(encoding="utf-8")) or {}
    problems = budget.check(document, country)
    assert not problems, f"{country}: la configuracion generada viola el techo: {problems}"


@pytest.mark.parametrize("country", ALL_COUNTRIES)
def test_no_generated_url_keeps_a_placeholder(country: str, root: Path):
    """Una URL con `{division}` dentro se pediría tal cual."""
    try:
        wc.generate(country, "2029", None, root)
    except wc.Unconfigurable:
        pytest.skip(f"{country} no es configurable, que es la otra salida valida")

    offenders = [url for url in _urls(root) if wc.PLACEHOLDER.search(url)]
    assert not offenders, f"{country}: marcadores sin sustituir en {offenders}"


@pytest.mark.parametrize("country", ALL_COUNTRIES)
def test_no_configuration_inherits_another_countrys_host(country: str, root: Path):
    """El fallo número uno: el host de Honduras sobrevivía a la generación."""
    try:
        wc.generate(country, "2029", None, root)
    except wc.Unconfigurable:
        pytest.skip(f"{country} no es configurable")

    allowed = budget.allowed_hosts_for(country)
    for url in _urls(root):
        from urllib.parse import urlparse

        host = (urlparse(url).hostname or "").lower()
        assert host in allowed, f"{country}: {host} no pertenece al preset ({url})"

    command_center = yaml.safe_load((root / wc.COMMAND_CENTER).read_text(encoding="utf-8")) or {}
    if country != "HN":
        assert HN_HOST not in str(command_center.get("cne_domains")), country
        assert HN_HOST not in str(command_center.get("base_url")), country
        assert HN_HOST not in str(command_center.get("endpoints")), country


# ── Honduras: lo que ya funcionaba sigue igual ────────────────────────────────


def test_honduras_is_unchanged_apart_from_the_declared_ceiling(root: Path):
    """El único país que funcionaba no debe moverse.

    English: the one country that worked must not move. The only addition is
    `max_sources_per_cycle`, which makes the ceiling explicit in the resolved
    config instead of living only in a per-process default.
    """
    committed = yaml.safe_load((REPO_ROOT / wc.ENDPOINTS_YAML).read_text(encoding="utf-8"))
    wc.generate("HN", "2029", None, root)
    produced = yaml.safe_load((root / wc.ENDPOINTS_YAML).read_text(encoding="utf-8"))

    assert produced["cne"]["max_sources_per_cycle"] == budget.MAX_SOURCES
    shared = {key: value for key, value in produced["cne"].items() if key in committed["cne"]}
    assert shared == committed["cne"]
    assert produced.get("healing") == committed.get("healing"), "una clave ajena al pais no debe tocarse"


def test_department_code_stays_an_integer_where_it_was_one(root: Path):
    """Los consumidores comparan con enteros; convertirlos a cadena rompe.

    English: consumers compare against ints, so turning them all into strings
    breaks those comparisons silently.
    """
    wc.generate("HN", "2029", None, root)
    document = yaml.safe_load((root / wc.ENDPOINTS_YAML).read_text(encoding="utf-8"))
    codes = [entry["department_code"] for entry in document["cne"]["presidential_endpoints"]]
    assert codes == list(range(1, 19))


def test_honduras_spends_exactly_the_whole_budget(root: Path):
    """1 nacional + 18 departamentales = 19, que es el techo justo."""
    plan = wc.generate("HN", "2029", None, root)
    coverage = wc.coverage_block(plan)
    assert coverage["requests_per_cycle"] == budget.MAX_SOURCES
    assert coverage["complete"] is True
    assert coverage["left_out"] == []


# ── el techo, donde el país no cabe ───────────────────────────────────────────


def test_a_country_that_does_not_fit_is_capped_and_says_so(root: Path):
    """Guatemala tiene 22 divisiones. Se cubren las que caben y se declara.

    English: Guatemala has 22 divisions. The node covers what fits and
    declares it, so the panel can state the real coverage instead of implying
    a complete one.
    """
    plan = wc.generate("GT", "2029", None, root)
    coverage = wc.coverage_block(plan)

    assert coverage["requests_per_cycle"] <= budget.MAX_SOURCES
    assert coverage["divisions_total"] == 22
    assert coverage["complete"] is False
    assert coverage["left_out"], "si queda alguna fuera, debe nombrarse"
    assert str(coverage["divisions_covered"]) in coverage["note"]
    assert _departments(root)["coverage"] == coverage


def test_the_ceiling_is_read_from_where_it_is_asserted(root: Path):
    """Un segundo 19 escrito a mano se desincroniza y falla abierto."""
    assert wc.ceiling() == budget.MAX_SOURCES
    source = (SCRIPTS / "wizard_config.py").read_text(encoding="utf-8")
    assert "from assert_source_budget import MAX_SOURCES" in source
    assert "MAX_SOURCES = 19" not in source, "el techo no se vuelve a escribir aqui"


def test_chosen_divisions_are_honoured(root: Path):
    """Dos nodos cubren un país entero sin que ninguno pase del techo."""
    plan = wc.generate("GT", "2029", ["20", "21", "22"], root)
    assert [entry["code"] for entry in plan["covered"]] == ["20", "21", "22"]
    assert wc.coverage_block(plan)["requests_per_cycle"] == 3


def test_an_unknown_division_is_refused_not_ignored(root: Path):
    """Un código mal escrito que se ignora deja al nodo cubriendo menos."""
    with pytest.raises(wc.Unconfigurable, match="no tiene"):
        wc.generate("GT", "2029", ["01", "99"], root)


def test_asking_for_more_than_the_ceiling_is_refused(root: Path):
    """El techo no se sube pidiéndolo por variable de entorno."""
    with pytest.raises(wc.Unconfigurable, match="no se sube"):
        wc.generate("GT", "2029", [f"{n:02d}" for n in range(1, 22)], root)


# ── negativas ─────────────────────────────────────────────────────────────────


def test_a_country_with_no_preset_is_refused(root: Path):
    with pytest.raises(wc.Unconfigurable, match="no hay preset"):
        wc.generate("ZZ", "2029", None, root)


@pytest.mark.parametrize("country", ["CU", "HT", "US"])
def test_a_preset_with_no_urls_is_refused_rather_than_left_pointing_elsewhere(country: str, root: Path):
    """Tres presets no declaran URL. Antes conservaban la de Honduras.

    English: three presets declare no URL. Before, they kept Honduras'.
    """
    with pytest.raises(wc.Unconfigurable, match="no declara ninguna URL"):
        wc.generate(country, "2029", None, root)

    untouched = yaml.safe_load((root / wc.ENDPOINTS_YAML).read_text(encoding="utf-8"))
    committed = yaml.safe_load((REPO_ROOT / wc.ENDPOINTS_YAML).read_text(encoding="utf-8"))
    assert untouched == committed, "una negativa no debe dejar la configuracion a medio escribir"


def test_a_template_that_leaves_a_placeholder_is_refused():
    """`fill()` falla en vez de devolver una URL con un marcador dentro."""
    with pytest.raises(wc.Unconfigurable, match="sin sustituir"):
        wc.fill("https://example.test/{desconocido}", code="01", iso=None, slug="x")


# ── forma del documento que leen los paneles ──────────────────────────────────


def test_departments_json_keeps_the_shape_both_panels_read(root: Path):
    """El panel OPS y el monitor recorren `departments`; la forma no cambia."""
    wc.generate("HN", "2029", None, root)
    document = _departments(root)

    assert isinstance(document["departments"], list)
    assert document["departments"][0]["abbr"] == "NAC", "el nacional va primero"
    for entry in document["departments"]:
        assert {"code", "name", "abbr", "iso", "url"} <= set(entry)
    assert document["urls_confirmed"] is False, "configurado no es comprobado"
    assert document["country"] == "HN"


def test_the_config_never_claims_urls_it_has_not_probed(root: Path):
    """Solo `wizard_discovery.py` pregunta, así que solo él puede afirmar."""
    for country in ("HN", "GT"):
        wc.generate(country, "2029", None, root)
        assert _departments(root)["urls_confirmed"] is False
        assert _departments(root)["source_of_truth"] == "country-preset"
