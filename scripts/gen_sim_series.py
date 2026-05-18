#!/usr/bin/env python3
"""
gen_sim_series.py
-----------------
Generates two high-density simulation JSON series from the real HN 2025 data:
  1. sim_eleccion_limpia_5min.json  — clean election, 5-min intervals, Benford-valid
  2. sim_eleccion_anomala_5min.json — same + 10 embedded anomalies at known timestamps

Output: /web/data/
Usage: python3 scripts/gen_sim_series.py
"""

import json
import math
import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "web" / "data"
SOURCE = OUT_DIR / "hnd_2025_series.json"

# ── Simulation configuration ──────────────────────────────────────────────────
INTERVAL_MINUTES = 5
DURATION_HOURS = 48        # 2 full days
N_SNAPSHOTS = (DURATION_HOURS * 60) // INTERVAL_MINUTES  # 576

# Election start: election night Dec 3 2025, 6 PM local (UTC-6) = 00:00 UTC Dec 4
SIM_START_UTC = datetime(2025, 12, 4, 0, 0, 0, tzinfo=timezone.utc)

# Final election results (anchored to real HN 2025 data)
FINAL_ACTAS_TOTALES = 19167
FINAL_VALIDOS = 3204648
FINAL_NULOS = 119889
FINAL_BLANCOS = 68075
FINAL_INCONSISTENTES = 2773
FINAL_CORRECTAS = 16279

# Final party percentages and metadata
PARTIDOS_META = [
    {"nombre": "PARTIDO NACIONAL DE HONDURAS",
     "abbrev": "PN",
     "candidato": "NASRY JUAN ASFURA ZABLAH",
     "color": "#df6b86",
     "final_pct": 38.28},
    {"nombre": "PARTIDO LIBERAL DE HONDURAS",
     "abbrev": "PLH",
     "candidato": "SALVADOR ALEJANDRO CESAR NASRALLA SALUM",
     "color": "#6ea8fe",
     "final_pct": 37.03},
    {"nombre": "PARTIDO LIBERTAD Y REFUNDACION",
     "abbrev": "LIBRE",
     "candidato": "RIXI RAMONA MONCADA GODOY",
     "color": "#b08cf0",
     "final_pct": 18.23},
    {"nombre": "PARTIDO INNOVACION Y UNIDAD SOCIAL DEMOCRATA",
     "abbrev": "PINU",
     "candidato": "JORGE NELSON AVILA GUTIERREZ",
     "color": "#57c08d",
     "final_pct": 0.75},
    {"nombre": "PARTIDO DEMOCRATA CRISTIANO DE HONDURAS",
     "abbrev": "DC",
     "candidato": "MARIO ENRIQUE RIVERA CALLEJAS",
     "color": "#d4b066",
     "final_pct": 0.16},
]

# ── Seeded RNG for reproducibility ───────────────────────────────────────────
RNG = random.Random(20251203)


def s_curve(t: float) -> float:
    """
    S-shaped growth curve: fast initial count, plateau after ~60%, slow tail.
    t in [0,1] → [0,1]
    """
    # Scaled sigmoid centered at 0.3 (most counting happens early)
    k = 7.0
    c = 0.28
    raw = 1.0 / (1.0 + math.exp(-k * (t - c)))
    # Normalize so s_curve(0)≈0 and s_curve(1)=1
    lo = 1.0 / (1.0 + math.exp(-k * (0.0 - c)))
    hi = 1.0 / (1.0 + math.exp(-k * (1.0 - c)))
    return (raw - lo) / (hi - lo)


def gauss_noise(value: float, rel_std: float = 0.008) -> float:
    """Add Gaussian noise scaled to rel_std fraction of value."""
    return value + RNG.gauss(0, value * rel_std)


def build_clean_series() -> list[dict]:
    """Build the clean 576-snapshot series."""
    snapshots = []
    for i in range(N_SNAPSHOTS):
        t = i / (N_SNAPSHOTS - 1)
        frac = s_curve(t)

        ts = SIM_START_UTC + timedelta(minutes=i * INTERVAL_MINUTES)
        actas_divulgadas = max(0, int(FINAL_ACTAS_TOTALES * frac))

        # Derive vote counts proportionally with small noise
        raw_validos = FINAL_VALIDOS * frac
        raw_nulos = FINAL_NULOS * frac
        raw_blancos = FINAL_BLANCOS * frac
        raw_inconsistentes = FINAL_INCONSISTENTES * frac
        raw_correctas = FINAL_CORRECTAS * frac

        # Apply Benford-preserving noise (small, never negative)
        validos = max(0, int(gauss_noise(raw_validos) if frac > 0.01 else raw_validos))
        nulos = max(0, int(gauss_noise(raw_nulos) if frac > 0.01 else raw_nulos))
        blancos = max(0, int(gauss_noise(raw_blancos) if frac > 0.01 else raw_blancos))
        inconsistentes = max(0, int(raw_inconsistentes))
        correctas = max(0, int(raw_correctas))

        pct_escrutinio = round(actas_divulgadas / FINAL_ACTAS_TOTALES * 100, 2)

        # Party votes: grow proportionally with slight variance per party
        partidos = []
        for pm in PARTIDOS_META:
            raw_v = validos * pm["final_pct"] / 100.0
            if frac > 0.01:
                # Small party-specific drift (each party counts at slightly different rate)
                drift = 1.0 + RNG.gauss(0, 0.003)
                raw_v = raw_v * drift
            votos = max(0, int(raw_v))
            pct = round(votos / validos * 100, 2) if validos > 0 else 0.0
            partidos.append({
                "nombre": pm["nombre"],
                "abbrev": pm["abbrev"],
                "candidato": pm["candidato"],
                "color": pm["color"],
                "votos": votos,
                "pct": pct,
            })

        # Simulate nightly blackouts (CNE goes quiet 2 AM - 6 AM local = 8-12 UTC)
        local_hour = (ts.hour - 6) % 24
        blackout = (local_hour >= 2 and local_hour < 6 and i > 30)

        snapshots.append({
            "idx": i,
            "ts": ts.isoformat(),
            "actas_totales": FINAL_ACTAS_TOTALES,
            "actas_divulgadas": actas_divulgadas,
            "pct_escrutinio": pct_escrutinio,
            "validos": validos,
            "nulos": nulos,
            "blancos": blancos,
            "inconsistentes": inconsistentes,
            "correctas": correctas,
            "blackout": blackout,
            "partidos": partidos,
        })

    return snapshots


def embed_anomalies(snapshots: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Embed 10 electoral anomalies into cloned snapshots.
    Returns (modified_snapshots, anomaly_manifest).
    """
    import copy
    snaps = copy.deepcopy(snapshots)
    anomalias = []

    def log_anomaly(idx, tipo, magnitud, descripcion):
        anomalias.append({
            "snapshot_idx": idx,
            "ts": snaps[idx]["ts"],
            "tipo": tipo,
            "magnitud": magnitud,
            "descripcion": descripcion,
        })
        print(f"  [A] idx={idx:>4} tipo={tipo:<35} ts={snaps[idx]['ts']}")

    # ── A1. Hold-and-Release Masivo (idx ~60, ~5h into count) ─────────────────
    hold_start = 60
    hold_end = 72
    release_bonus = 1800  # actas released all at once
    for i in range(hold_start, hold_end):
        snaps[i]["actas_divulgadas"] = snaps[hold_start]["actas_divulgadas"]
        snaps[i]["validos"] = snaps[hold_start]["validos"]
        snaps[i]["nulos"] = snaps[hold_start]["nulos"]
        snaps[i]["blancos"] = snaps[hold_start]["blancos"]
    # Release burst
    snaps[hold_end]["actas_divulgadas"] = min(
        snaps[hold_end]["actas_divulgadas"] + release_bonus, FINAL_ACTAS_TOTALES)
    votes_bonus = release_bonus * 165
    snaps[hold_end]["validos"] += votes_bonus
    for p in snaps[hold_end]["partidos"]:
        pm = next(x for x in PARTIDOS_META if x["abbrev"] == p["abbrev"])
        p["votos"] += int(votes_bonus * pm["final_pct"] / 100)
    log_anomaly(hold_end, "hold_and_release", release_bonus,
                f"Retención de {release_bonus} actas por {hold_end - hold_start} snapshots y liberación masiva")

    # ── A2. Votos Redondeados / Ballot Stuffing (idx ~96, ~8h) ───────────────
    idx = 96
    for p in snaps[idx]["partidos"]:
        p["votos"] = round(p["votos"] / 500) * 500  # round to nearest 500
    log_anomaly(idx, "ballot_stuffing_redondeo", 500,
                "Totales de votos redondeados al múltiplo de 500 → violación de Benford y último dígito")

    # ── A3. Apagón Geográfico simulado (idx 120–132, ~10h) ────────────────────
    for i in range(120, 133):
        snaps[i]["_geo_blackout_dept"] = "Francisco Morazán"
    log_anomaly(120, "apagon_geografico", 12,
                "Apagón de 12 snapshots (60 min) sin actas del departamento Francisco Morazán")

    # ── A4. Inyección Progresiva de Ventaja (idx 150–200, ~12.5h–16.7h) ──────
    bonus_per_snap = 280
    total_injected = 0
    for i in range(150, 200):
        snaps[i]["partidos"][1]["votos"] += (i - 149) * bonus_per_snap  # PLH partido[1]
        snaps[i]["validos"] += (i - 149) * bonus_per_snap
        total_injected += bonus_per_snap
    log_anomaly(150, "inyeccion_progresiva_ventaja", bonus_per_snap,
                f"PLH gana +{bonus_per_snap} votos por snapshot durante 50 snaps (ventaja acumulada: {total_injected * 25:,} votos)")

    # ── A5. Aceleración Nocturna (idx 240–244, ~20h, 2–3 AM local) ───────────
    nocturnal_bonus = 2400
    snaps[240]["actas_divulgadas"] = min(
        snaps[240]["actas_divulgadas"] + nocturnal_bonus, FINAL_ACTAS_TOTALES)
    snaps[240]["validos"] += nocturnal_bonus * 165
    for p in snaps[240]["partidos"]:
        pm = next(x for x in PARTIDOS_META if x["abbrev"] == p["abbrev"])
        p["votos"] += int(nocturnal_bonus * 165 * pm["final_pct"] / 100)
    log_anomaly(240, "aceleracion_nocturna", nocturnal_bonus,
                f"+{nocturnal_bonus} actas en un solo snapshot a las 2 AM → velocidad 48× la normal")

    # ── A6. Campaña de Votos Nulos (idx 276–288, ~23h) ───────────────────────
    for i in range(276, 289):
        snaps[i]["nulos"] = int(snaps[i]["nulos"] * 3.8)
    log_anomaly(276, "campana_votos_nulos", 3.8,
                "Votos nulos ×3.8 durante 12 snapshots (60 min) en zona de oposición simulada")

    # ── A7. Rollback de Datos (idx 312, ~26h) ────────────────────────────────
    rollback_target = 280
    snaps[312]["actas_divulgadas"] = snaps[rollback_target]["actas_divulgadas"]
    snaps[312]["validos"] = snaps[rollback_target]["validos"]
    snaps[312]["nulos"] = snaps[rollback_target]["nulos"]
    snaps[312]["blancos"] = snaps[rollback_target]["blancos"]
    snaps[312]["_rollback"] = True
    log_anomaly(312, "rollback_datos", rollback_target,
                f"Datos revertidos al estado del snapshot {rollback_target} (regresión de ~2h de conteo)")

    # ── A8. Uniformidad Sospechosa de Mesas (idx 360–372, ~30h) ──────────────
    for i in range(360, 373):
        total_v = snaps[i]["validos"]
        # Force exact percentages (too perfect = fabricated)
        for j, p in enumerate(snaps[i]["partidos"]):
            pm = PARTIDOS_META[j]
            p["votos"] = int(total_v * pm["final_pct"] / 100)  # no noise at all
            p["pct"] = round(pm["final_pct"], 2)
        snaps[i]["_uniformidad_sospechosa"] = True
    log_anomaly(360, "uniformidad_sospechosa_mesas", 12,
                "Distribución de votos perfectamente idéntica al porcentaje teórico durante 12 snapshots → datos fabricados")

    # ── A9. Inversión de Resultados post-Apagón (idx 432, ~36h) ─────────────
    # Black out 3 snaps first
    for i in range(429, 432):
        snaps[i]["blackout"] = True
    # Then swap partido[0] and partido[1]
    old0 = snaps[432]["partidos"][0]["votos"]
    old1 = snaps[432]["partidos"][1]["votos"]
    snaps[432]["partidos"][0]["votos"] = old1
    snaps[432]["partidos"][1]["votos"] = old0
    snaps[432]["partidos"][0]["pct"] = snaps[432]["partidos"][1]["pct"]
    snaps[432]["partidos"][1]["pct"] = snaps[432]["partidos"][0]["pct"]
    snaps[432]["_resultado_invertido"] = True
    log_anomaly(432, "inversion_resultados_post_apagon", abs(old0 - old1),
                f"Candidatos [0] y [1] intercambiados después de apagón de 3 snaps → cambio de líder de {abs(old0 - old1):,} votos")

    # ── A10. Mesa Fantasma / Conteo Imposible (idx 504, ~42h) ────────────────
    snaps[504]["actas_divulgadas"] = FINAL_ACTAS_TOTALES + 450
    snaps[504]["_mesa_fantasma"] = True
    log_anomaly(504, "mesa_fantasma_conteo_imposible", 450,
                "actas_divulgadas supera actas_totales en 450 → conteo imposible, mesas fantasma")

    return snaps, anomalias


def build_meta(clean: bool, n: int, anomalias: list | None) -> dict:
    return {
        "election": "Elecciones Generales Honduras 2025 — Presidencia (SIMULACIÓN)",
        "tipo": "limpia" if clean else "anomala",
        "generado": datetime.now(timezone.utc).isoformat(),
        "snapshots_count": n,
        "actas_totales": FINAL_ACTAS_TOTALES,
        "interval_minutes": INTERVAL_MINUTES,
        "duration_hours": DURATION_HOURS,
        "first_ts": SIM_START_UTC.isoformat(),
        "last_ts": (SIM_START_UTC + timedelta(minutes=(n - 1) * INTERVAL_MINUTES)).isoformat(),
        "descripcion": (
            "Serie limpia interpolada desde datos reales HN 2025 con ruido gaussiano Benford-preservante"
            if clean else
            "Serie anómala: misma base limpia + 10 anomalías electorales embebidas en índices conocidos"
        ),
        **({"anomalias_embebidas": anomalias} if anomalias else {}),
    }


def main():
    print("Generando series de simulación electoral...")
    print(f"  Duración: {DURATION_HOURS}h | Intervalo: {INTERVAL_MINUTES}min | Snapshots: {N_SNAPSHOTS}")

    print("\n[1/3] Construyendo serie limpia...")
    clean_snaps = build_clean_series()
    print(f"  Generados {len(clean_snaps)} snapshots limpios")

    print("\n[2/3] Embebiendo anomalías en copia...")
    anomalous_snaps, anomaly_manifest = embed_anomalies(clean_snaps)
    print(f"  {len(anomaly_manifest)} anomalías embebidas")

    print("\n[3/3] Escribiendo archivos JSON...")

    clean_out = OUT_DIR / "sim_eleccion_limpia_5min.json"
    clean_doc = {
        "meta": build_meta(True, len(clean_snaps), None),
        "snapshots": clean_snaps,
    }
    clean_out.write_text(json.dumps(clean_doc, ensure_ascii=False, separators=(',', ':')))
    size_kb = clean_out.stat().st_size / 1024
    print(f"  ✓ {clean_out.name} ({size_kb:.0f} KB)")

    anom_out = OUT_DIR / "sim_eleccion_anomala_5min.json"
    anom_doc = {
        "meta": build_meta(False, len(anomalous_snaps), anomaly_manifest),
        "snapshots": anomalous_snaps,
    }
    anom_out.write_text(json.dumps(anom_doc, ensure_ascii=False, separators=(',', ':')))
    size_kb = anom_out.stat().st_size / 1024
    print(f"  ✓ {anom_out.name} ({size_kb:.0f} KB, {len(anomaly_manifest)} anomalías documentadas)")

    print("\nListo. Archivos disponibles en web/data/")


if __name__ == "__main__":
    main()
