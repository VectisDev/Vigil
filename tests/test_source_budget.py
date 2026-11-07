"""El techo de 19 fuentes es un aserto, no un comentario.

The 19-source ceiling is an assert, not a comment.

VIGIL consulta como mucho 1 endpoint nacional y 18 departamentales por ciclo.
No es una limitación técnica: es la decisión de no convertirse en un problema
de carga para la autoridad electoral que se audita.

Hasta ahora la única defensa era un defecto por proceso en
`download_and_hash.py` que cualquier archivo de configuración podía subir. Estas
pruebas fijan que el techo falle de verdad, y sobre todo que falle también
cuando el número es correcto pero las peticiones apuntan a otra parte: un
presupuesto sin allowlist deja 19 peticiones libres de destino.

English: these pin that the ceiling actually fails -- and above all that it
fails when the count is right but the requests point somewhere else. A budget
with no allowlist leaves 19 requests free to go anywhere.
"""

from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".github" / "scripts" / "assert_source_budget.py"
for _candidate in (REPO_ROOT, REPO_ROOT / "src", REPO_ROOT / ".github" / "scripts"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from assert_source_budget import (  # noqa: E402
    MAX_SOURCES,
    allowed_hosts_for,
    check,
    collect_urls,
    declared_country,
)

REAL_CONFIG = REPO_ROOT / "config" / "prod" / "endpoints.yaml"


@pytest.fixture
def config() -> dict:
    return copy.deepcopy(yaml.safe_load(REAL_CONFIG.read_text(encoding="utf-8")))


# ── el techo, sobre la configuración que se envía ─────────────────────────────


def test_the_shipped_config_sits_exactly_at_the_ceiling(config: dict):
    """19 fuentes: 1 nacional + 18 departamentales, sin margen.

    English: 19 sources exactly, with no headroom. If this ever reads 18, an
    endpoint was lost; if it reads 20, the ceiling was breached.
    """
    assert len(collect_urls(config)) == MAX_SOURCES
    assert check(config, "HN") == []


def test_one_source_over_the_ceiling_fails(config: dict):
    config["cne"]["presidential_endpoints"].append(
        {"department_code": 19, "url": "https://resultadosgenerales2025.cne.hn/api/presidencial/departamento/19"}
    )
    problems = check(config, "HN")
    assert problems
    assert "20 fuentes" in problems[0]


def test_a_raised_max_sources_per_cycle_fails(config: dict):
    """Subir el límite declarado no sirve de nada: el techo no es configurable.

    English: raising the declared limit buys nothing -- the ceiling is not
    configurable. A ceiling a file can raise is not a ceiling.
    """
    config["max_sources_per_cycle"] = 50
    problems = check(config, "HN")
    assert any("max_sources_per_cycle" in p for p in problems)


def test_a_lowered_max_sources_per_cycle_is_fine(config: dict):
    """Un operador puede ser más conservador que el techo, nunca menos."""
    config["max_sources_per_cycle"] = 5
    assert check(config, "HN") == []


def test_a_non_integer_limit_is_rejected_not_ignored(config: dict):
    config["max_sources_per_cycle"] = "muchas"
    assert any("no es un entero" in p for p in check(config, "HN"))


# ── el destino, que es lo que faltaba por completo ────────────────────────────


def test_the_right_count_pointed_elsewhere_still_fails(config: dict):
    """19 peticiones a un host ajeno siguen siendo 19 peticiones a un host ajeno.

    English: 19 requests aimed at someone else's host are still 19 requests
    aimed at someone else's host. Counting alone never caught this.
    """
    for entry in config["cne"]["presidential_endpoints"]:
        entry["url"] = entry["url"].replace("resultadosgenerales2025.cne.hn", "evil.example.org")
    problems = check(config, "HN")
    assert len(collect_urls(config)) == MAX_SOURCES, "el recuento sigue dentro del techo"
    assert problems, "y aun asi debe fallar"
    assert all("evil.example.org" in p for p in problems)


def test_a_single_redirected_endpoint_is_caught(config: dict):
    config["cne"]["presidential_endpoints"][7]["url"] = "https://attacker.test/api/x"
    assert any("attacker.test" in p for p in check(config, "HN"))


def test_the_national_url_is_checked_too(config: dict):
    config["cne"]["main_url"] = "https://attacker.test/api/nacional"
    assert any("attacker.test" in p for p in check(config, "HN"))


def test_the_allowlist_comes_from_the_country_preset():
    """La allowlist se deriva del preset; no se mantiene por separado.

    English: the allowlist is derived from the preset rather than kept
    separately. A list maintained apart from where the legitimate URLs are
    defined drifts, and when it drifts it fails open.
    """
    assert allowed_hosts_for("HN") == {"resultadosgenerales2025.cne.hn"}
    assert allowed_hosts_for("hn") == {"resultadosgenerales2025.cne.hn"}
    assert allowed_hosts_for("GT") == {"resultados.tse.org.gt"}


def test_an_unknown_country_fails_closed(config: dict):
    """Sin preset no hay allowlist, y eso es un fallo, no un permiso.

    English: no preset means no allowlist, and that is a failure rather than a
    pass. Failing open here would make an unrecognised country code the way
    around the whole check.
    """
    problems = check(config, "ZZ")
    assert problems
    assert "no tiene preset" in problems[0]


def test_a_url_without_a_host_is_rejected(config: dict):
    config["cne"]["presidential_endpoints"][0]["url"] = "no-es-una-url"
    assert any("sin host" in p for p in check(config, "HN"))


# ── el país sale del modo declarado ───────────────────────────────────────────


def test_country_comes_from_the_mode_file(tmp_path: Path):
    mode = tmp_path / "mode.yaml"
    mode.write_text("mode: REPLAY\ncountry: GT\n", encoding="utf-8")
    assert declared_country(mode) == "GT"


@pytest.mark.parametrize("content", ["", "mode: REPLAY\n", "country: ''\n", ": no es yaml válido : ["])
def test_an_absent_or_broken_mode_falls_back_to_hn(tmp_path: Path, content: str):
    mode = tmp_path / "mode.yaml"
    mode.write_text(content, encoding="utf-8")
    assert declared_country(mode) == "HN"


def test_a_missing_mode_file_falls_back_to_hn(tmp_path: Path):
    assert declared_country(tmp_path / "no-existe.yaml") == "HN"


# ── el script como lo invoca el workflow ──────────────────────────────────────


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env={"PYTHONPATH": f"{REPO_ROOT}:{REPO_ROOT / 'src'}", "PATH": "/usr/bin:/bin"},
    )


def test_the_script_passes_on_the_real_tree():
    result = _run()
    assert result.returncode == 0, result.stderr
    assert "assert_source_budget=PASS" in result.stdout


def test_the_script_exits_nonzero_on_a_breach(tmp_path: Path, config: dict):
    config["cne"]["main_url"] = "https://evil.example.org/api"
    bad = tmp_path / "endpoints.yaml"
    bad.write_text(yaml.safe_dump(config), encoding="utf-8")
    result = _run("--config", str(bad))
    assert result.returncode == 1
    assert "assert_source_budget=FAIL" in result.stderr


def test_no_config_is_not_a_breach(tmp_path: Path):
    """Un nodo en REPLAY no tiene config de captura, y eso no viola nada.

    English: a node in REPLAY has no collection config, and that breaches
    nothing. Failing here would paint every idle node red, and a permanent red
    teaches people to ignore reds.
    """
    result = _run("--config", str(tmp_path / "no-existe.yaml"))
    assert result.returncode == 0
    assert "SKIP" in result.stdout


def test_an_unreadable_config_is_a_failure(tmp_path: Path):
    bad = tmp_path / "endpoints.yaml"
    bad.write_text("{{{ no es yaml", encoding="utf-8")
    result = _run("--config", str(bad))
    assert result.returncode == 1
