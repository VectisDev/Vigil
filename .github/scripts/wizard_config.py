#!/usr/bin/env python3
"""
======================== ÍNDICE / INDEX ========================
1. Propósito / Purpose
2. Los cuatro fallos que corrige / The four bugs it fixes
3. El techo, y qué pasa cuando el país no cabe
4. Lo que no puede saber / What it cannot know
5. ENGLISH

======================== ESPAÑOL ========================
Archivo: `.github/scripts/wizard_config.py`.

Genera la configuración de un nodo a partir del preset de su país: la lista de
divisiones que el panel dibuja, los endpoints que se van a consultar y las
fuentes declaradas.

Es el primer paso del arranque de un nodo, así que es también el primer sitio
donde el techo ético de 19 endpoints se puede respetar o romper. Lo rompía.

======================== LOS CUATRO FALLOS ========================
Medidos sobre los 21 presets de `src/vigil/countries.py`, no deducidos:

1. **Fusionaba en vez de sustituir.** Escribía `cne.main_url` solo `if
   preset.national_url`, y **de los 21 presets solo Honduras declara uno**.
   Para los otros 20 países el valor de Honduras sobrevivía intacto: un nodo
   de Guatemala quedaba configurado para consultar al CNE hondureño. Igual con
   `base_url` y `cne_domains` en `command_center/config.yaml`.

2. **Sustituía un único marcador.** Hacía `pattern.replace("{cne_code}", …)`
   y **17 de los 21 presets usan `{division}`**. Sus URLs se escribían con el
   marcador literal dentro: `https://…/api/actas/{division}`.

3. **No había techo.** Escribía una línea por división: 23 para Guatemala, 33
   para México, 51 para Estados Unidos. **Once de los 21 presets pasan de 19.**
   `assert_source_budget.py` las rechaza después, así que el arranque no
   llegaba a terminar — y sin ese aserto, el nodo habría consultado 51
   endpoints por ciclo.

4. **Sin preset seguía adelante.** Devolvía una lista de una entrada y escribía
   una configuración de aspecto válido que conservaba la de Honduras. Un nodo
   que no se puede configurar tiene que decirlo y parar, no arrancar apuntando
   al país de otro.

Los cuatro tienen el mismo efecto compuesto: el despliegue de un clic
funcionaba exactamente para un país, el del autor, y para los demás producía
un nodo que parecía configurado.

======================== EL TECHO ========================
19 endpoints por ciclo: 1 nacional y 18 divisiones. No es un límite técnico,
es la premisa ética del proyecto — un sistema que vigila la integridad de una
elección no puede ser, él mismo, un problema de carga para la autoridad que
audita.

El número se lee de `assert_source_budget.py` en vez de escribirse otra vez
aquí. Un segundo 19 escrito a mano se desincroniza del primero, y al
desincronizarse falla abierto.

Cuando el país tiene más divisiones de las que caben, el nodo cubre 18 y **lo
declara**. `web/data/departments.json` lleva un bloque `coverage` con las
cubiertas, las que quedan fuera y `complete: false`, para que el panel pueda
decir «18 de 22» en vez de insinuar cobertura total. `VIGIL_DIVISIONS` elige
otro subconjunto, que es lo que hacen falta dos nodos para cubrir un país
entero sin que ninguno de los dos pase del techo.

Subir el techo para que el país quepa no está disponible, y eso es
deliberado.

======================== LO QUE NO PUEDE SABER ========================
De los 21 presets, **solo el de Honduras tiene URLs en producción**. Los otros
20 llevan patrones plausibles pero no confirmados; `wizard_discovery.py` existe
precisamente para descubrir los de verdad, probándolos. Por eso esta
configuración se escribe siempre con `urls_confirmed: false`: es discovery
quien puede ponerlo a true, porque es quien pregunta. Nadie debe confundir
«configurado» con «comprobado».

Tampoco puede saber la zona horaria ni el idioma: el preset no los lleva. Por
eso `playwright_locale` y `playwright_timezone` se quedan como están y siguen
diciendo Honduras para cualquier otro país. Queda escrito aquí porque es un
dato que identifica al nodo, no un error de cálculo, y se corrige cuando
`CountryPreset` tenga esos campos.

======================== ENGLISH ========================
File: `.github/scripts/wizard_config.py`.

Generates a node's configuration from its country preset: the divisions the
panel draws, the endpoints to be queried, and the declared sources. It is the
first step of a node's bootstrap, so it is also the first place where the
19-endpoint ethical ceiling can be honoured or broken. It broke it.

Four bugs, measured against the 21 presets rather than assumed:

1. It merged instead of replacing. `cne.main_url` was written only if the
   preset declared a `national_url`, and only Honduras does -- so for the other
   20 countries Honduras' value survived and a Guatemalan node was configured
   to query Honduras' authority.
2. It substituted one placeholder. 17 of 21 presets use `{division}`, so their
   URLs were written with the placeholder still in them.
3. There was no ceiling. One endpoint per division means 23 for Guatemala, 33
   for Mexico, 51 for the United States; 11 of 21 presets exceed 19.
4. With no preset it carried on, writing a valid-looking config that kept
   Honduras'.

The ceiling is read from `assert_source_budget.py` rather than written again
here: a second hand-written 19 drifts from the first, and drifting it fails
open. When a country has more divisions than fit, the node covers 18 and says
so in a `coverage` block, so the panel can state "18 of 22" instead of
implying full coverage. `VIGIL_DIVISIONS` picks a different subset, which is
what two nodes need to cover a whole country without either exceeding the
ceiling. Raising the ceiling is not on offer, deliberately.

Only Honduras' preset carries production URLs, so the config is always written
`urls_confirmed: false`; `wizard_discovery.py`, which probes, is what can set
it true. Locale and timezone are left as they are because the preset does not
carry them -- recorded here because it is a detail that identifies the node,
not a miscalculation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
for _candidate in (SCRIPT_DIR, REPO_ROOT, REPO_ROOT / "src"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

# Marcadores con nombre: {division}, {cne_code}. No casa con {2}, que aparece
# en `national_filename_pattern` como cuantificador de una expresion regular y
# no es un marcador que haya que sustituir.
# English: named placeholders only, so the `{2}` of a regex quantifier in
# `national_filename_pattern` is not mistaken for one.
PLACEHOLDER = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")

DEPARTMENTS_JSON = Path("web/data/departments.json")
COMMAND_CENTER = Path("command_center/config.yaml")
ENDPOINTS_YAML = Path("config/prod/endpoints.yaml")

# Las claves de `command_center/config.yaml` que pertenecen a un pais. Se
# sustituyen enteras en cada generacion; el resto del archivo se conserva.
# English: the keys of command_center/config.yaml that belong to a country.
# They are replaced wholesale on every generation; the rest is preserved.
COUNTRY_SCOPED = ("cne_domains", "base_url", "endpoints", "sources", "scope")


class Unconfigurable(RuntimeError):
    """El pais no se puede configurar, y seguir seria peor que parar.

    English: the country cannot be configured, and carrying on would be worse
    than stopping -- it would leave a node pointing at someone else's
    electoral authority.
    """


def ceiling() -> int:
    """El techo, leido de donde se assertan las violaciones.

    English: the ceiling, read from where violations are asserted, so the two
    cannot drift apart.
    """
    from assert_source_budget import MAX_SOURCES  # noqa: PLC0415

    return int(MAX_SOURCES)


def load_preset(code: str):
    """El preset del pais, o `Unconfigurable` si no hay ninguno."""
    from vigil.countries import LATAM_COUNTRIES  # noqa: PLC0415

    preset = LATAM_COUNTRIES.get(code)
    if preset is None:
        raise Unconfigurable(
            f"no hay preset para el pais '{code}' en src/vigil/countries.py. "
            f"Paises disponibles: {', '.join(sorted(LATAM_COUNTRIES))}"
        )
    if not preset.url_pattern and not preset.national_url:
        raise Unconfigurable(
            f"el preset de '{code}' ({preset.name}) no declara ninguna URL. "
            "Sin URL no hay nada que configurar, y escribir la configuracion "
            "de todas formas dejaria al nodo apuntando al pais anterior. "
            "Declara `url_pattern` o `national_url` en src/vigil/countries.py, "
            "o descubre el patron real con wizard_discovery.py"
        )
    return preset


def _slugify(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


def _abbr(name: str, iso: str | None) -> str:
    """Abreviatura de 2-3 caracteres: sufijo ISO si lo hay, si no iniciales."""
    if iso and "-" in iso:
        return iso.split("-", 1)[1].upper()
    skip = {"de", "la", "las", "los", "el", "a", "y", "del"}
    words = [w for w in name.split() if w.lower() not in skip]
    if len(words) >= 2:
        return "".join(w[0] for w in words[:3]).upper()
    return name[:2].upper()


def fill(template: str | None, *, code: str, iso: str | None, slug: str) -> str:
    """Sustituye todos los marcadores conocidos, y falla si queda alguno.

    English: substitutes every known placeholder and fails if any survives. A
    URL with `{division}` still inside it is not a URL, and the fetcher would
    request it verbatim.
    """
    if not template:
        return ""
    url = (
        template.replace("{cne_code}", code)
        .replace("{division}", code)
        .replace("{division_code}", code)
        .replace("{iso}", (iso or "").replace("-", ""))
        .replace("{slug}", slug)
    )
    leftover = sorted(set(PLACEHOLDER.findall(url)))
    if leftover:
        raise Unconfigurable(
            f"la plantilla deja marcadores sin sustituir {leftover}: {template!r}. "
            "Una URL con un marcador dentro se pediria tal cual. Anade el "
            "marcador a wizard_config.fill() o corrige el preset"
        )
    return url


def build_entries(preset) -> tuple[dict, list[dict]]:
    """Devuelve (nacional, divisiones) con las URLs ya sustituidas.

    English: returns (national, divisions) with placeholders already filled.
    Divisions come ordered by code, which is stable: ordering by name made the
    subset chosen under the ceiling depend on the alphabet of the language the
    preset happens to be written in.
    """
    cne_map = preset.build_cne_map()
    isos = list(preset.division_iso_codes or [])
    national_code = preset.national_cne_code

    def iso_for(name: str) -> str | None:
        try:
            idx = preset.divisions.index(name)
        except ValueError:
            return None
        return isos[idx] if idx < len(isos) else None

    national = {
        "code": national_code,
        "name": "TODOS",
        "abbr": "NAC",
        "iso": None,
        "url": fill(preset.national_url, code=national_code, iso=None, slug="nacional"),
        "label": preset.divisions_label,
    }

    divisions: list[dict] = []
    for code, name in sorted((c, n) for c, n in cne_map.items() if c != national_code):
        iso = iso_for(name)
        divisions.append(
            {
                "code": code,
                "name": name,
                "abbr": _abbr(name, iso),
                "iso": iso,
                "url": fill(preset.url_pattern, code=code, iso=iso, slug=_slugify(name)),
            }
        )
    return national, divisions


def select(national: dict, divisions: list[dict], max_total: int, chosen: list[str] | None = None) -> dict:
    """Reparte las divisiones entre cubiertas y fuera, sin pasar del techo.

    English: splits divisions into covered and left out without exceeding the
    ceiling. The national endpoint counts against it, because it is a request
    like any other.
    """
    budget = max_total - (1 if national["url"] else 0)
    if budget < 0:
        raise Unconfigurable(f"el techo de {max_total} no deja sitio ni para el endpoint nacional")

    if chosen:
        wanted = [c.strip() for c in chosen if c.strip()]
        unknown = sorted(set(wanted) - {d["code"] for d in divisions})
        if unknown:
            raise Unconfigurable(
                f"VIGIL_DIVISIONS nombra divisiones que el pais no tiene: {unknown}. "
                f"Codigos validos: {', '.join(d['code'] for d in divisions)}"
            )
        if len(wanted) > budget:
            raise Unconfigurable(
                f"VIGIL_DIVISIONS pide {len(wanted)} divisiones y el techo de {max_total} "
                f"deja sitio para {budget}. El techo es deliberado: no se sube."
            )
        order = {code: i for i, code in enumerate(wanted)}
        covered = sorted((d for d in divisions if d["code"] in order), key=lambda d: order[d["code"]])
    else:
        covered = divisions[:budget]

    covered_codes = {d["code"] for d in covered}
    left_out = [d for d in divisions if d["code"] not in covered_codes]
    return {
        "national": national,
        "covered": covered,
        "left_out": left_out,
        "ceiling": max_total,
        "requests_per_cycle": len(covered) + (1 if national["url"] else 0),
    }


def coverage_block(plan: dict) -> dict:
    """Lo que el panel necesita para no insinuar una cobertura que no tiene."""
    total = len(plan["covered"]) + len(plan["left_out"])
    return {
        "ceiling": plan["ceiling"],
        "requests_per_cycle": plan["requests_per_cycle"],
        "divisions_total": total,
        "divisions_covered": len(plan["covered"]),
        "complete": not plan["left_out"],
        "left_out": [{"code": d["code"], "name": d["name"]} for d in plan["left_out"]],
        "note": (
            "Cobertura completa."
            if not plan["left_out"]
            else (
                f"Este nodo cubre {len(plan['covered'])} de {total} "
                f"{'divisiones' if total != 1 else 'division'}. El techo de "
                f"{plan['ceiling']} endpoints por ciclo es deliberado; cubrir el resto "
                "requiere otro nodo con VIGIL_DIVISIONS distinto."
            )
        ),
    }


def departments_document(preset, country: str, year: str, plan: dict) -> dict:
    """El documento que leen el panel OPS y el monitor.

    La clave `departments` conserva su forma: los dos paneles la recorren y
    romperla no era necesario para arreglar nada.
    """
    entries = [plan["national"]] + plan["covered"]
    return {
        "country": country,
        "country_name": preset.name,
        "flag": preset.flag,
        "authority": preset.authority,
        "divisions_label": preset.divisions_label,
        "year": year,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_of_truth": "country-preset",
        "urls_confirmed": False,
        "coverage": coverage_block(plan),
        "departments": entries,
    }


def endpoints_document(existing: dict, preset, plan: dict) -> dict:
    """Sustituye el bloque `cne` entero y conserva el resto del archivo.

    English: replaces the whole `cne` block and preserves the rest. Merging is
    what let Honduras' `main_url` survive into every other country's config.
    """
    doc = dict(existing or {})
    cne = dict(doc.get("cne") or {})
    for key in ("main_url", "presidential_endpoints"):
        cne.pop(key, None)

    if plan["national"]["url"]:
        cne["main_url"] = plan["national"]["url"]
    cne["presidential_endpoints"] = [
        {"department_code": _code_as_declared(d["code"]), "url": d["url"]} for d in plan["covered"]
    ]
    cne["max_sources_per_cycle"] = plan["ceiling"]
    doc["cne"] = cne
    return doc


def command_center_document(existing: dict, preset, country: str, year: str, plan: dict) -> dict:
    """Igual: las claves de pais se sustituyen, las demas se quedan."""
    doc = dict(existing or {})
    for key in COUNTRY_SCOPED:
        doc.pop(key, None)

    hosts: list[str] = []
    for url in [plan["national"]["url"]] + [d["url"] for d in plan["covered"]]:
        m = re.match(r"https?://([^/]+)", url or "")
        if m and m.group(1) not in hosts:
            hosts.append(m.group(1))
    if hosts:
        doc["cne_domains"] = hosts
    if plan["national"]["url"]:
        doc["base_url"] = plan["national"]["url"]

    endpoints: dict[str, str] = {}
    if plan["national"]["url"]:
        endpoints["nacional"] = plan["national"]["url"]
    for d in plan["covered"]:
        endpoints[d["code"]] = d["url"]
    doc["endpoints"] = endpoints

    sources: list[dict] = []
    if plan["national"]["url"]:
        sources.append({"name": "Nacional", "source_id": "NACIONAL", "level": "PRES", "scope": "NATIONAL"})
    for d in plan["covered"]:
        sources.append(
            {
                "name": d["name"],
                "source_id": f"{d['code']}_{_slugify(d['name'])}",
                "department_code": d["code"],
                "level": "PRES",
                "scope": "DEPARTMENT",
            }
        )
    doc["sources"] = sources

    meta = dict(doc.get("centinel") or {})
    meta.update(
        {
            "country": country,
            "year": year,
            "setup_at": datetime.now(timezone.utc).isoformat(),
            "setup_source": "wizard_config",
            "max_sources_per_cycle": plan["ceiling"],
            "divisions_covered": len(plan["covered"]),
            "divisions_total": len(plan["covered"]) + len(plan["left_out"]),
        }
    )
    doc["centinel"] = meta
    return doc


def _code_as_declared(code: str) -> int | str:
    """Entero donde el codigo es numerico, cadena donde no lo es.

    `download_and_hash.py` y el panel comparan `department_code` con enteros
    para los paises cuyos codigos lo son, asi que convertirlos todos en cadena
    habria roto esas comparaciones en silencio. Estados Unidos usa `AK`, `AL`:
    ahi la cadena es el dato, no una conversion perdida.

    English: int where the code is numeric, string where it is not. Honduras'
    config carried ints and the consumers compare against ints; turning them
    all into strings would have broken those comparisons silently. The United
    States uses `AK`, `AL`, where the string is the datum.
    """
    return int(code) if code.isdigit() else code


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def generate(country: str, year: str, chosen: list[str] | None, root: Path) -> dict:
    """Escribe los tres archivos y devuelve el plan. Lanza `Unconfigurable`."""
    preset = load_preset(country)
    national, divisions = build_entries(preset)
    plan = select(national, divisions, ceiling(), chosen)

    dept_path = root / DEPARTMENTS_JSON
    dept_path.parent.mkdir(parents=True, exist_ok=True)
    dept_path.write_text(
        json.dumps(departments_document(preset, country, year, plan), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    ep_path = root / ENDPOINTS_YAML
    ep_path.parent.mkdir(parents=True, exist_ok=True)
    ep_path.write_text(
        yaml.safe_dump(endpoints_document(_read_yaml(ep_path), preset, plan), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    cc_path = root / COMMAND_CENTER
    cc_path.parent.mkdir(parents=True, exist_ok=True)
    cc_path.write_text(
        yaml.safe_dump(
            command_center_document(_read_yaml(cc_path), preset, country, year, plan),
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera la configuracion de un nodo desde el preset de su pais.")
    parser.add_argument("--country", default="", help="Codigo de pais; por defecto $VIGIL_COUNTRY o HN.")
    parser.add_argument("--year", default="", help="Ano electoral; por defecto $VIGIL_YEAR.")
    parser.add_argument("--divisions", default="", help="Codigos separados por comas; por defecto $VIGIL_DIVISIONS.")
    parser.add_argument("--root", default=".", help="Raiz del repositorio sobre la que escribir.")
    args = parser.parse_args(argv)

    country = (args.country or os.environ.get("VIGIL_COUNTRY") or os.environ.get("CENTINEL_COUNTRY") or "HN").upper()
    year = args.year or os.environ.get("VIGIL_YEAR") or os.environ.get("CENTINEL_YEAR") or "2029"
    raw = args.divisions or os.environ.get("VIGIL_DIVISIONS") or ""
    chosen = [c for c in raw.replace(";", ",").split(",") if c.strip()] or None

    try:
        plan = generate(country, year, chosen, Path(args.root))
    except Unconfigurable as exc:
        print(f"wizard_config=FAIL {exc}", file=sys.stderr)
        return 1

    cov = coverage_block(plan)
    print(
        f"wizard_config=PASS {country} {year} — "
        f"{cov['requests_per_cycle']}/{cov['ceiling']} peticiones por ciclo, "
        f"{cov['divisions_covered']}/{cov['divisions_total']} divisiones"
    )
    if not cov["complete"]:
        print(f"  {cov['note']}")
        print(f"  Fuera: {', '.join(d['code'] for d in cov['left_out'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
