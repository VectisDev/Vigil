#!/usr/bin/env python3
"""
======================== ÍNDICE / INDEX ========================
1. Propósito / Purpose
2. Por qué generarlo y no mantenerlo a mano
3. ENGLISH

======================== ESPAÑOL ========================
Archivo: `.github/scripts/export_countries_json.py`.

Genera `web/data/countries.json` a partir de `src/vigil/countries.py`.

======================== POR QUÉ ========================
El archivo existía ya, mantenido a mano, y **nada lo generaba**. Un catálogo
copiado a mano de su fuente se desincroniza, y aquí la desincronización no es
cosmética: el asistente de despliegue ofrece países leyéndolo, así que si el
catálogo dice que un país está disponible y el preset no declara ninguna URL,
el asistente invita a desplegar un nodo que el arranque va a rechazar.

Además el catálogo no llevaba la información que hace falta para no mentir:

  - `configurable` — si el preset declara alguna URL. Cuba, Haití y Estados
    Unidos no, así que el asistente no debe ofrecerlos como si sí.
  - `divisions_total`, `divisions_covered`, `complete` — el techo de 19
    endpoints por ciclo no da para los 22 departamentos de Guatemala ni los 33
    de México. El asistente tiene que poder decir «este nodo cubriría 19 de
    22» antes del botón, no después.

Los tres últimos se calculan con las mismas funciones que usa el arranque
(`wizard_config.build_entries` y `.select`), no con una copia de su lógica: una
segunda implementación del techo acabaría discrepando de la primera.

`tests/test_countries_catalog.py` falla si el archivo commiteado no coincide
con lo que este script produce. Sin esa prueba, generar el archivo una vez no
sirve de nada.

======================== ENGLISH ========================
Generates `web/data/countries.json` from `src/vigil/countries.py`.

The file already existed, maintained by hand, and nothing generated it. A
catalogue hand-copied from its source drifts, and here drift is not cosmetic:
the deployment assistant offers countries by reading it, so if the catalogue
says a country is available and the preset declares no URL, the assistant
invites someone to deploy a node the bootstrap will refuse.

It also lacked what is needed in order not to mislead: whether the preset is
configurable at all (Cuba, Haiti and the United States are not), and how many
divisions a single node could cover, since the 19-endpoint ceiling does not
stretch to Guatemala's 22 or Mexico's 33. The assistant has to be able to say
"this node would cover 19 of 22" before the button, not after.

Those are computed with the same functions the bootstrap uses, not with a copy
of its logic: a second implementation of the ceiling would end up disagreeing
with the first. `tests/test_countries_catalog.py` fails if the committed file
does not match what this produces.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
for _candidate in (SCRIPT_DIR, REPO_ROOT, REPO_ROOT / "src"):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

OUTPUT = Path("web/data/countries.json")


def build() -> list[dict]:
    import wizard_config as wc  # noqa: PLC0415
    from vigil.countries import LATAM_COUNTRIES  # noqa: PLC0415

    ceiling = wc.ceiling()
    catalog: list[dict] = []

    for code, preset in sorted(LATAM_COUNTRIES.items()):
        entry: dict = {
            "code": code,
            "name": preset.name,
            "flag": preset.flag,
            "authority": preset.authority,
            "divisions_label": preset.divisions_label,
            "divisions_total": len(preset.divisions),
        }
        try:
            wc.load_preset(code)
            national, divisions = wc.build_entries(preset)
            plan = wc.select(national, divisions, ceiling)
        except wc.Unconfigurable as exc:
            entry.update(
                {
                    "configurable": False,
                    "reason": " ".join(str(exc).split()),
                    "divisions_covered": 0,
                    "requests_per_cycle": 0,
                    "complete": False,
                }
            )
        else:
            coverage = wc.coverage_block(plan)
            entry.update(
                {
                    "configurable": True,
                    "divisions_covered": coverage["divisions_covered"],
                    "requests_per_cycle": coverage["requests_per_cycle"],
                    "complete": coverage["complete"],
                }
            )
        catalog.append(entry)

    return catalog


def render(catalog: list[dict]) -> str:
    return json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera web/data/countries.json desde los presets.")
    parser.add_argument("--root", default=".", help="Raiz del repositorio.")
    parser.add_argument("--check", action="store_true", help="No escribe; falla si el archivo esta desfasado.")
    args = parser.parse_args(argv)

    target = Path(args.root) / OUTPUT
    produced = render(build())

    if args.check:
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        if current != produced:
            print(
                f"export_countries_json=FAIL {OUTPUT} no coincide con src/vigil/countries.py; "
                "regenera con `python .github/scripts/export_countries_json.py`",
                file=sys.stderr,
            )
            return 1
        print(f"export_countries_json=PASS {OUTPUT} al dia")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(produced, encoding="utf-8")
    catalog = json.loads(produced)
    configurable = sum(1 for entry in catalog if entry["configurable"])
    partial = sum(1 for entry in catalog if entry["configurable"] and not entry["complete"])
    print(
        f"export_countries_json=PASS {len(catalog)} paises, "
        f"{configurable} configurables, {partial} con cobertura parcial bajo el techo"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
