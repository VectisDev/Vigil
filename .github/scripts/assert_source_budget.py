#!/usr/bin/env python3
"""
======================== ÍNDICE / INDEX ========================
1. Propósito / Purpose
2. Lo que comprueba / What it checks
3. Lo que no puede impedir / What it cannot prevent

======================== ESPAÑOL ========================
Archivo: `.github/scripts/assert_source_budget.py`.

El techo ético del proyecto, convertido en un aserto que falla.

VIGIL consulta como mucho 19 endpoints por ciclo: 1 nacional y 18
departamentales. No es una limitación técnica; es una decisión deliberada para
no constituir un problema de carga para la autoridad electoral que se audita.
Un sistema que vigila la integridad de una elección no puede ser, él mismo, un
ataque de denegación de servicio.

Hasta ahora la única defensa era `scripts/download_and_hash.py`, que lee
`max_sources_per_cycle` con un defecto de 19. Un defecto por proceso que
cualquier archivo de configuración puede subir, en un repositorio que está
pensado para que cualquiera lo despliegue en su propia cuenta.

Este script asserta sobre la configuración *resuelta*, no sobre el defecto:

  - el número total de fuentes no pasa de 19;
  - `max_sources_per_cycle`, si está declarado, no pasa de 19;
  - todo host al que se apunta pertenece al preset del país declarado.

La tercera es la que importa más y la que no existía de ninguna forma. Sin
ella, el presupuesto se respeta pero nada impide apuntar esas 19 peticiones a
un host cualquiera. El preset de país de `src/vigil/countries.py` ya declara
las URLs legítimas de cada autoridad electoral; la allowlist se deriva de ahí
en vez de mantenerse por separado, para que no puedan separarse.

======================== LO QUE NO PUEDE IMPEDIR ========================
Hay que decirlo con claridad, porque un gate del que se exagera el alcance es
peor que ninguno.

Este script vive en el repositorio del propio nodo. Quien despliegue VIGIL
tiene permiso de escritura sobre su copia y puede editarlo, saltárselo o
borrar el paso que lo invoca. **No impone nada a un operador hostil.**

Lo que sí hace: convierte el techo en algo explícito, versionado y
comprobable, de modo que una desviación exige un cambio deliberado y visible
en el diff en lugar de poder ocurrir por descuido, por copiar una config de
otro sitio o por un valor que alguien subió «para probar» y no volvió a bajar.
Esa es toda la garantía que un sistema distribuido sin autoridad central puede
dar, y vale la pena precisamente porque es honesta sobre su propio límite.

======================== ENGLISH ========================
File: `.github/scripts/assert_source_budget.py`.

The project's ethical ceiling, turned into an assert that fails.

VIGIL queries at most 19 endpoints per cycle: 1 national and 18 departmental.
This is not a technical limit but a deliberate decision not to become a load
problem for the very electoral authority being audited. A system that watches
an election's integrity cannot itself be a denial-of-service attack.

Until now the only defence was a per-process default of 19 in
`scripts/download_and_hash.py`, which any config file can raise -- in a
repository meant to be deployed by anyone into their own account.

This asserts against the *resolved* config: the source count stays within 19,
a declared `max_sources_per_cycle` stays within 19, and every host targeted
belongs to the declared country's preset. The last one is the one that
mattered most and did not exist in any form: without it the budget holds but
nothing stops those 19 requests from pointing anywhere.

What it cannot do: this lives in the node's own repository, so whoever deploys
it can edit or skip it. It binds no hostile operator. What it does is make the
ceiling explicit, versioned and checkable, so that exceeding it takes a
deliberate, visible change to the diff rather than happening by accident. That
is the whole guarantee a distributed system with no central authority can
offer, and it is worth having precisely because it is honest about its limit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _candidate in (REPO_ROOT, REPO_ROOT / "src"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

# El techo. No es configurable a propósito: si pudiera subirse desde un
# archivo, no sería un techo.
# English: the ceiling. Deliberately not configurable -- a ceiling that a file
# can raise is not a ceiling.
MAX_SOURCES = 19

DEFAULT_CONFIG = Path("config/prod/endpoints.yaml")
DEFAULT_MODE = Path(".vigil/mode.yaml")


def allowed_hosts_for(country: str) -> set[str]:
    """Los hosts que el preset del país declara, y ninguno más.

    English: the hosts the country preset declares, and no others.

    Se derivan de `url_pattern` y `national_url` en vez de mantenerse en una
    lista aparte: una allowlist separada del sitio donde se definen las URLs
    legítimas acaba desincronizada, y cuando se desincroniza falla abierta.
    """
    from vigil.countries import get_country  # noqa: PLC0415

    try:
        preset = get_country(country)
    except KeyError:
        return set()

    hosts: set[str] = set()
    for template in (preset.url_pattern, preset.national_url):
        if not template:
            continue
        # Las plantillas llevan marcadores como {cne_code}; el host está
        # siempre antes del primero, así que urlparse lo extrae sin sustituir.
        host = urlparse(template).hostname
        if host:
            hosts.add(host.lower())
    return hosts


def collect_urls(config: dict) -> list[str]:
    """Toda URL a la que la configuración apunta, venga de donde venga.

    English: every URL the config points at, wherever it comes from.

    Recorre las dos formas que usa el repositorio (`cne.main_url` y
    `cne.presidential_endpoints`) y también las genéricas, para que añadir una
    sección nueva no deje fuentes fuera del recuento en silencio.
    """
    urls: list[str] = []

    cne = config.get("cne") or {}
    if isinstance(cne, dict):
        if isinstance(cne.get("main_url"), str):
            urls.append(cne["main_url"])
        for entry in cne.get("presidential_endpoints") or []:
            if isinstance(entry, dict) and isinstance(entry.get("url"), str):
                urls.append(entry["url"])

    for key in ("endpoints", "sources"):
        for entry in config.get(key) or []:
            if isinstance(entry, str):
                urls.append(entry)
            elif isinstance(entry, dict) and isinstance(entry.get("url"), str):
                urls.append(entry["url"])

    return urls


def declared_country(mode_path: Path) -> str:
    """El país declarado en `.vigil/mode.yaml`, o HN por defecto."""
    try:
        data = yaml.safe_load(mode_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return "HN"
    country = data.get("country")
    return country.upper() if isinstance(country, str) and country.strip() else "HN"


def check(config: dict, country: str) -> list[str]:
    """Devuelve la lista de violaciones. Vacía significa que pasa."""
    problems: list[str] = []

    urls = collect_urls(config)
    if len(urls) > MAX_SOURCES:
        problems.append(
            f"{len(urls)} fuentes configuradas; el techo es {MAX_SOURCES} " f"(1 nacional + 18 departamentales)"
        )

    declared_max = config.get("max_sources_per_cycle")
    if declared_max is None:
        declared_max = (config.get("cne") or {}).get("max_sources_per_cycle")
    if declared_max is not None:
        try:
            if int(declared_max) > MAX_SOURCES:
                problems.append(f"max_sources_per_cycle={declared_max} supera el techo de {MAX_SOURCES}")
        except (TypeError, ValueError):
            problems.append(f"max_sources_per_cycle no es un entero: {declared_max!r}")

    allowed = allowed_hosts_for(country)
    if not allowed:
        # Sin preset no hay con qué comparar. Es un fallo, no un permiso: la
        # alternativa seria aceptar cualquier host para un pais desconocido.
        # English: no preset means nothing to compare against. That is a
        # failure, not a pass -- the alternative accepts any host.
        problems.append(f"el pais '{country}' no tiene preset en src/vigil/countries.py; no hay allowlist")
    else:
        for url in urls:
            host = (urlparse(url).hostname or "").lower()
            if not host:
                problems.append(f"URL sin host: {url!r}")
            elif host not in allowed:
                problems.append(f"host fuera del preset de {country}: {host} ({url})")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Asserta el techo de 19 fuentes por ciclo.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Config de endpoints resuelta.")
    parser.add_argument("--mode", default=str(DEFAULT_MODE), help="Archivo de modo, de donde sale el pais.")
    parser.add_argument("--country", default="", help="Forzar el pais en vez de leerlo del modo.")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        # Sin configuracion no hay nada que capturar, y eso no es una
        # violacion del techo. Un nodo en REPLAY es exactamente este caso.
        # English: no config means nothing to collect, which does not breach
        # the ceiling. A node in REPLAY is exactly this case.
        print(f"assert_source_budget=SKIP sin configuracion en {config_path}")
        return 0

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        print(f"assert_source_budget=FAIL configuracion ilegible: {exc}", file=sys.stderr)
        return 1
    if not isinstance(config, dict):
        print("assert_source_budget=FAIL la configuracion no es un mapa", file=sys.stderr)
        return 1

    country = args.country.strip().upper() or declared_country(Path(args.mode))
    problems = check(config, country)

    if problems:
        print(f"assert_source_budget=FAIL ({len(problems)} violacion(es), pais {country})", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nEl techo de 19 endpoints es deliberado: VIGIL audita a una autoridad\n"
            "electoral sin convertirse en un problema de carga para ella.",
            file=sys.stderr,
        )
        return 1

    print(f"assert_source_budget=PASS {len(collect_urls(config))}/{MAX_SOURCES} fuentes, pais {country}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
