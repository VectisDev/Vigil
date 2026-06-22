"""Generate web/data/{country}_{year}_series.json from fixture snapshots.

Defaults to Honduras 2025 (tests/fixtures/hnd_2025/) for backward compatibility.
Override with environment variables: CENTINEL_COUNTRY and CENTINEL_YEAR.
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

_COUNTRY = os.environ.get("CENTINEL_COUNTRY", "HN").lower()
_YEAR = os.environ.get("CENTINEL_YEAR", "2025")
_SLUG = f"{_COUNTRY}_{_YEAR}"

FIXTURE_DIR = Path(f"tests/fixtures/{_SLUG}")
OUT = Path(f"web/data/{_SLUG}_series.json")
CALIB = Path(f"web/data/calibration_{_SLUG}.json")

ABBREV = {
    "PARTIDO LIBERAL DE HONDURAS": "PLH",
    "PARTIDO NACIONAL DE HONDURAS": "PN",
    "PARTIDO LIBERTAD Y REFUNDACION": "LIBRE",
    "PARTIDO INNOVACION Y UNIDAD SOCIAL DEMOCRATA": "PINU",
    "PARTIDO DEMOCRATA CRISTIANO DE HONDURAS": "DC",
}

COLORS = {
    "PLH": "#6ea8fe",
    "PN": "#df6b86",
    "LIBRE": "#b08cf0",
    "PINU": "#57c08d",
    "DC": "#d4b066",
}

PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2}) (\d{2}_\d{2}_\d{2})\.json$")


def parse_num(s):
    try:
        return int(str(s or 0).replace(",", "").replace(".", "").strip() or 0)
    except (ValueError, TypeError):
        return 0


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    snapshots = []
    for f in sorted(FIXTURE_DIR.glob("HN.PRESIDENTE*.json")):
        m = PATTERN.search(f.name)
        if not m:
            continue
        ts_str = m.group(1) + " " + m.group(2).replace("_", ":")
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )

        d = json.loads(f.read_text(encoding="utf-8"))
        stats = d.get("estadisticas", {})
        tot = stats.get("totalizacion_actas", {})
        dist = stats.get("distribucion_votos", {})
        estado = stats.get("estado_actas_divulgadas", {})

        actas_totales = parse_num(tot.get("actas_totales"))
        actas_divulgadas = parse_num(tot.get("actas_divulgadas"))

        raw_partidos = d.get("resultados") or []
        partidos = []
        for r in raw_partidos:
            nombre = r.get("partido", "").strip().upper()
            abbrev = ABBREV.get(nombre, nombre[:6])
            votos = parse_num(r.get("votos"))
            pct = float(r.get("porcentaje") or 0)
            candidato = r.get("candidato", "").strip()
            partidos.append(
                {
                    "nombre": nombre,
                    "abbrev": abbrev,
                    "candidato": candidato,
                    "color": COLORS.get(abbrev, "#8b929c"),
                    "votos": votos,
                    "pct": pct,
                }
            )

        blackout = (
            not any(p["votos"] > 0 for p in partidos) and actas_divulgadas > 0
        ) or actas_totales == 0

        snapshots.append(
            {
                "idx": len(snapshots),
                "ts": ts.isoformat(),
                "actas_totales": actas_totales,
                "actas_divulgadas": actas_divulgadas,
                "pct_escrutinio": (
                    round(actas_divulgadas / max(actas_totales, 1) * 100, 2)
                    if actas_totales > 0
                    else 0.0
                ),
                "validos": parse_num(dist.get("validos")),
                "nulos": parse_num(dist.get("nulos")),
                "blancos": parse_num(dist.get("blancos")),
                "inconsistentes": parse_num(estado.get("actas_inconsistentes")),
                "correctas": parse_num(estado.get("actas_correctas")),
                "blackout": blackout,
                "partidos": partidos,
            }
        )

    alerts = []
    if CALIB.exists():
        calib = json.loads(CALIB.read_text(encoding="utf-8"))
        alerts = calib.get("alerts", [])

    first_ts = snapshots[0]["ts"] if snapshots else ""
    last_ts = snapshots[-1]["ts"] if snapshots else ""

    result = {
        "meta": {
            "election": "Elecciones Generales Honduras 2025 — Presidencia",
            "generated": datetime.now(timezone.utc).isoformat(),
            "snapshots_count": len(snapshots),
            "actas_totales": 19152,
            "first_ts": first_ts,
            "last_ts": last_ts,
            "alerts_count": len(alerts),
        },
        "snapshots": snapshots,
        "alerts": alerts,
    }

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(snapshots)} snapshots → {OUT}")
    print(f"✓ {len(alerts)} alertas incluidas")

    # Quick sanity
    blackouts = sum(1 for s in snapshots if s["blackout"])
    print(f"  blackouts: {blackouts} snapshots")


if __name__ == "__main__":
    main()
