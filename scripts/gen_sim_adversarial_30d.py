#!/usr/bin/env python3
"""
gen_sim_adversarial_30d.py
--------------------------
Generates two month-scale adversarial simulation JSON series:
  1. sim_mes_adversarial_15min.json  — clean baseline, 30 days, 15-min intervals (2880 snaps)
  2. sim_mes_adversarial_anomala_15min.json — same + 10 adversarial anomalies at known indices

Models the HN adversarial scenario: CNE deliberately delays the final count for 30+ days
as a political attrition strategy. Front-loaded S-curve (70% counted by day 5, last 30%
drags across the remaining 25 days).

Output: /web/data/
Usage: python3 scripts/gen_sim_adversarial_30d.py
"""

import json
import math
import random
import copy
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "web" / "data"

# ── Simulation configuration ──────────────────────────────────────────────────
INTERVAL_MINUTES = 15
DURATION_HOURS   = 720           # 30 days
N_SNAPSHOTS      = (DURATION_HOURS * 60) // INTERVAL_MINUTES  # 2880
SNAPS_PER_DAY    = (24 * 60) // INTERVAL_MINUTES              # 96

# Election night start: Dec 3 2025, 6 PM local (UTC-6) = 00:00 UTC Dec 4
SIM_START_UTC = datetime(2025, 12, 4, 0, 0, 0, tzinfo=timezone.utc)

# Final election results (anchored to real HN 2025 data)
FINAL_ACTAS_TOTALES  = 19167
FINAL_VALIDOS        = 3204648
FINAL_NULOS          = 119889
FINAL_BLANCOS        = 68075
FINAL_INCONSISTENTES = 2773
FINAL_CORRECTAS      = 16279

PARTIDOS_META = [
    {"nombre": "PARTIDO NACIONAL DE HONDURAS",
     "abbrev": "PN",  "candidato": "NASRY JUAN ASFURA ZABLAH",
     "color": "#df6b86", "final_pct": 38.28},
    {"nombre": "PARTIDO LIBERAL DE HONDURAS",
     "abbrev": "PLH", "candidato": "SALVADOR ALEJANDRO CESAR NASRALLA SALUM",
     "color": "#6ea8fe", "final_pct": 37.03},
    {"nombre": "PARTIDO LIBERTAD Y REFUNDACION",
     "abbrev": "LIBRE", "candidato": "RIXI RAMONA MONCADA GODOY",
     "color": "#b08cf0", "final_pct": 18.23},
    {"nombre": "PARTIDO INNOVACION Y UNIDAD SOCIAL DEMOCRATA",
     "abbrev": "PINU",  "candidato": "JORGE NELSON AVILA GUTIERREZ",
     "color": "#57c08d", "final_pct": 0.75},
    {"nombre": "PARTIDO DEMOCRATA CRISTIANO DE HONDURAS",
     "abbrev": "DC",   "candidato": "MARIO ENRIQUE RIVERA CALLEJAS",
     "color": "#d4b066", "final_pct": 0.16},
]

RNG = random.Random(20260101)


def s_curve(t: float) -> float:
    """
    Front-loaded adversarial S-curve: ~70% counted in first 15% of the time window
    (days 1-4), then a long tail drags across the remaining 25 days.
    c=0.12 pushes the midpoint to ~day 3.6; k=9 makes the rise very steep.
    """
    k = 9.0
    c = 0.12
    raw = 1.0 / (1.0 + math.exp(-k * (t - c)))
    lo  = 1.0 / (1.0 + math.exp(-k * (0.0 - c)))
    hi  = 1.0 / (1.0 + math.exp(-k * (1.0 - c)))
    return (raw - lo) / (hi - lo)


def gauss_noise(value: float, rel_std: float = 0.008) -> float:
    return value + RNG.gauss(0, value * rel_std)


def build_clean_series() -> list[dict]:
    snapshots = []
    for i in range(N_SNAPSHOTS):
        t    = i / (N_SNAPSHOTS - 1)
        frac = s_curve(t)
        ts   = SIM_START_UTC + timedelta(minutes=i * INTERVAL_MINUTES)

        actas_divulgadas = max(0, int(FINAL_ACTAS_TOTALES * frac))
        raw_validos      = FINAL_VALIDOS        * frac
        raw_nulos        = FINAL_NULOS          * frac
        raw_blancos      = FINAL_BLANCOS        * frac

        validos        = max(0, int(gauss_noise(raw_validos)  if frac > 0.01 else raw_validos))
        nulos          = max(0, int(gauss_noise(raw_nulos)    if frac > 0.01 else raw_nulos))
        blancos        = max(0, int(gauss_noise(raw_blancos)  if frac > 0.01 else raw_blancos))
        inconsistentes = max(0, int(FINAL_INCONSISTENTES * frac))
        correctas      = max(0, int(FINAL_CORRECTAS      * frac))
        pct_escrutinio = round(actas_divulgadas / FINAL_ACTAS_TOTALES * 100, 2)

        partidos = []
        for pm in PARTIDOS_META:
            raw_v = validos * pm["final_pct"] / 100.0
            if frac > 0.01:
                raw_v *= (1.0 + RNG.gauss(0, 0.003))
            votos = max(0, int(raw_v))
            pct   = round(votos / validos * 100, 2) if validos > 0 else 0.0
            partidos.append({
                "nombre":    pm["nombre"],
                "abbrev":    pm["abbrev"],
                "candidato": pm["candidato"],
                "color":     pm["color"],
                "votos":     votos,
                "pct":       pct,
            })

        # Nightly blackout: 2–6 AM local (UTC-6) → 8–12 UTC
        local_hour = (ts.hour - 6) % 24
        blackout   = (local_hour >= 2 and local_hour < 6 and i > 30)

        snapshots.append({
            "idx":              i,
            "ts":               ts.isoformat(),
            "actas_totales":    FINAL_ACTAS_TOTALES,
            "actas_divulgadas": actas_divulgadas,
            "pct_escrutinio":   pct_escrutinio,
            "validos":          validos,
            "nulos":            nulos,
            "blancos":          blancos,
            "inconsistentes":   inconsistentes,
            "correctas":        correctas,
            "blackout":         blackout,
            "partidos":         partidos,
        })

    return snapshots


def embed_anomalies(snapshots: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Embed 10 adversarial anomalies scaled across 30 days.
    At 96 snaps/day the key days are: 3→288, 5→480, 7→672, 9→864 ...
    """
    snaps    = copy.deepcopy(snapshots)
    anomalias = []

    def log_anomaly(idx, tipo, magnitud, descripcion):
        anomalias.append({
            "snapshot_idx": idx,
            "ts":           snaps[idx]["ts"],
            "tipo":         tipo,
            "magnitud":     magnitud,
            "descripcion":  descripcion,
        })
        day = idx // SNAPS_PER_DAY + 1
        print(f"  [M] idx={idx:>5}  día={day:>2}  tipo={tipo}")

    # ── M1. Hold-and-Release Masivo — día 3→4 (snaps 192→287, libera en 288) ──
    hold_start   = 192
    hold_end     = 288
    release_bonus = 3600   # 1 día de actas retenidas, liberadas de golpe
    for i in range(hold_start, hold_end):
        snaps[i]["actas_divulgadas"] = snaps[hold_start]["actas_divulgadas"]
        snaps[i]["validos"]          = snaps[hold_start]["validos"]
        snaps[i]["nulos"]            = snaps[hold_start]["nulos"]
        snaps[i]["blancos"]          = snaps[hold_start]["blancos"]
    snaps[hold_end]["actas_divulgadas"] = min(
        snaps[hold_end]["actas_divulgadas"] + release_bonus, FINAL_ACTAS_TOTALES)
    votes_bonus = release_bonus * 165
    snaps[hold_end]["validos"] += votes_bonus
    for p in snaps[hold_end]["partidos"]:
        pm = next(x for x in PARTIDOS_META if x["abbrev"] == p["abbrev"])
        p["votos"] += int(votes_bonus * pm["final_pct"] / 100)
    log_anomaly(hold_end, "hold_and_release",
                release_bonus,
                f"Retención de {hold_end - hold_start} snaps (1 día) y liberación masiva de {release_bonus} actas")

    # ── M2. Ballot Stuffing / Votos Redondeados — día 5 (snap 400) ───────────
    idx = 400
    for p in snaps[idx]["partidos"]:
        p["votos"] = round(p["votos"] / 1000) * 1000   # redondear al millar
    log_anomaly(idx, "ballot_stuffing_redondeo", 1000,
                "Todos los votos redondeados al millar → viola Benford y uniformidad de último dígito")

    # ── M3. Apagón Geográfico — día 6 completo (snaps 480–575, 96 snaps) ─────
    for i in range(480, 576):
        snaps[i]["_geo_blackout_dept"] = "Francisco Morazán"
    log_anomaly(480, "apagon_geografico", 96,
                "Apagón de 1 día completo (96 snaps / 24h) sin datos del depto Francisco Morazán")

    # ── M4. Aceleración Nocturna — día 8, 2 AM local (snap 700) ─────────────
    nocturnal_bonus = 4800   # 2× el de 48h, para escalar a contexto mensual
    snaps[700]["actas_divulgadas"] = min(
        snaps[700]["actas_divulgadas"] + nocturnal_bonus, FINAL_ACTAS_TOTALES)
    snaps[700]["validos"] += nocturnal_bonus * 165
    for p in snaps[700]["partidos"]:
        pm = next(x for x in PARTIDOS_META if x["abbrev"] == p["abbrev"])
        p["votos"] += int(nocturnal_bonus * 165 * pm["final_pct"] / 100)
    log_anomaly(700, "aceleracion_nocturna", nocturnal_bonus,
                f"+{nocturnal_bonus} actas en 1 snap a las 2 AM → velocidad 96× la normal (48 snaps/día esperados)")

    # ── M5. Inyección Progresiva de Ventaja — días 9–12 (snaps 768–1151) ─────
    bonus_per_snap = 120   # más suave que 48h pero durante 384 snaps (4 días)
    total_injected = 0
    for i in range(768, 1152):
        delta = (i - 767) * bonus_per_snap
        snaps[i]["partidos"][1]["votos"] += delta   # PLH = partido[1]
        snaps[i]["validos"]              += delta
        total_injected += bonus_per_snap
    log_anomaly(768, "inyeccion_progresiva_ventaja",
                bonus_per_snap,
                f"PLH +{bonus_per_snap} votos/snap durante 384 snaps (4 días) → ventaja acumulada de {total_injected * 192:,}")

    # ── M6. Campaña de Votos Nulos — días 13–14 (snaps 1152–1247) ────────────
    for i in range(1152, 1248):
        snaps[i]["nulos"] = int(snaps[i]["nulos"] * 3.8)
    log_anomaly(1152, "campana_votos_nulos", 3.8,
                "Votos nulos ×3.8 durante 96 snaps (24h) — zona de oposición simulada")

    # ── M7. Rollback de Datos — día 15 (snap 1344, revierte a día 12 / snap 1056) ──
    rollback_target = 1056
    for field in ("actas_divulgadas", "validos", "nulos", "blancos"):
        snaps[1344][field] = snaps[rollback_target][field]
    snaps[1344]["partidos"]  = copy.deepcopy(snaps[rollback_target]["partidos"])
    snaps[1344]["_rollback"] = True
    log_anomaly(1344, "rollback_datos", rollback_target,
                f"Datos revertidos al estado del snapshot {rollback_target} (día 12) → regresión de 3 días de conteo")

    # ── M8. Uniformidad Sospechosa de Mesas — días 16–17 (snaps 1440–1535) ───
    for i in range(1440, 1536):
        total_v = snaps[i]["validos"]
        for j, p in enumerate(snaps[i]["partidos"]):
            pm = PARTIDOS_META[j]
            p["votos"] = int(total_v * pm["final_pct"] / 100)
            p["pct"]   = round(pm["final_pct"], 2)
        snaps[i]["_uniformidad_sospechosa"] = True
    log_anomaly(1440, "uniformidad_sospechosa_mesas", 96,
                "Distribución perfectamente idéntica al % teórico durante 96 snaps (24h) → datos fabricados")

    # ── M9. Inversión de Resultados post-Apagón — día 21 (snap 2016) ─────────
    # Blackout de 3 días (días 18–20, snaps 1632–1919)
    for i in range(1632, 1920):
        snaps[i]["blackout"] = True
    # Inversión en el snap post-apagón
    old0 = snaps[2016]["partidos"][0]["votos"]
    old1 = snaps[2016]["partidos"][1]["votos"]
    snaps[2016]["partidos"][0]["votos"] = old1
    snaps[2016]["partidos"][1]["votos"] = old0
    pct0 = snaps[2016]["partidos"][0]["pct"]
    pct1 = snaps[2016]["partidos"][1]["pct"]
    snaps[2016]["partidos"][0]["pct"] = pct1
    snaps[2016]["partidos"][1]["pct"] = pct0
    snaps[2016]["_resultado_invertido"] = True
    log_anomaly(2016, "inversion_resultados_post_apagon", abs(old0 - old1),
                f"Apagón de 3 días (snaps 1632–1919) seguido de inversión de candidatos [0]↔[1] en snap 2016")

    # ── M10. Mesa Fantasma / Conteo Imposible — día 29 (snap 2688) ───────────
    snaps[2688]["actas_divulgadas"] = FINAL_ACTAS_TOTALES + 850
    snaps[2688]["_mesa_fantasma"]   = True
    log_anomaly(2688, "mesa_fantasma_conteo_imposible", 850,
                "actas_divulgadas supera actas_totales en 850 → mesas fantasma, conteo imposible")

    return snaps, anomalias


def build_meta(clean: bool, n: int, anomalias: list | None) -> dict:
    return {
        "election":         "Elecciones Generales Honduras 2025 — Presidencia (SIMULACIÓN ADVERSARIAL 30 DÍAS)",
        "tipo":             "adversarial_limpia" if clean else "adversarial_anomala",
        "generado":         datetime.now(timezone.utc).isoformat(),
        "snapshots_count":  n,
        "actas_totales":    FINAL_ACTAS_TOTALES,
        "interval_minutes": INTERVAL_MINUTES,
        "duration_hours":   DURATION_HOURS,
        "duration_days":    DURATION_HOURS // 24,
        "snaps_per_day":    SNAPS_PER_DAY,
        "first_ts":         SIM_START_UTC.isoformat(),
        "last_ts":          (SIM_START_UTC + timedelta(minutes=(n - 1) * INTERVAL_MINUTES)).isoformat(),
        "descripcion": (
            "Simulación adversarial de 30 días: CNE demora deliberadamente el conteo final. "
            "S-curve front-loaded: ~70% de actas en los primeros 4 días, cola larga hasta día 30. "
            "Apagones nocturnos recurrentes. Línea base limpia (sin anomalías inyectadas)."
            if clean else
            "Simulación adversarial de 30 días con 10 anomalías embebidas en índices conocidos. "
            "Hold-and-release (día 3-4), ballot stuffing (día 5), apagón geográfico (día 6), "
            "aceleración nocturna (día 8), inyección progresiva (días 9-12), campaña nulos (días 13-14), "
            "rollback (día 15), uniformidad sospechosa (días 16-17), inversión post-apagón 3días (día 21), "
            "mesa fantasma (día 29)."
        ),
        **({"anomalias_embebidas": anomalias} if anomalias else {}),
    }


def main():
    print("Generando simulación adversarial de 30 días...")
    print(f"  Duración: {DURATION_HOURS}h ({DURATION_HOURS//24} días) | Intervalo: {INTERVAL_MINUTES}min | Snapshots: {N_SNAPSHOTS}")
    print(f"  Snaps por día: {SNAPS_PER_DAY}")

    print("\n[1/3] Construyendo serie base limpia (30 días)...")
    clean_snaps = build_clean_series()
    print(f"  Generados {len(clean_snaps)} snapshots")

    print("\n[2/3] Embebiendo 10 anomalías adversariales...")
    anomalous_snaps, anomaly_manifest = embed_anomalies(clean_snaps)
    print(f"  {len(anomaly_manifest)} anomalías embebidas")

    print("\n[3/3] Escribiendo archivos JSON...")

    clean_out = OUT_DIR / "sim_mes_adversarial_15min.json"
    clean_doc = {"meta": build_meta(True, len(clean_snaps), None), "snapshots": clean_snaps}
    clean_out.write_text(json.dumps(clean_doc, ensure_ascii=False, separators=(',', ':')))
    size_kb = clean_out.stat().st_size / 1024
    print(f"  ✓ {clean_out.name} ({size_kb:.0f} KB)")

    anom_out = OUT_DIR / "sim_mes_adversarial_anomala_15min.json"
    anom_doc = {"meta": build_meta(False, len(anomalous_snaps), anomaly_manifest), "snapshots": anomalous_snaps}
    anom_out.write_text(json.dumps(anom_doc, ensure_ascii=False, separators=(',', ':')))
    size_kb = anom_out.stat().st_size / 1024
    print(f"  ✓ {anom_out.name} ({size_kb:.0f} KB, {len(anomaly_manifest)} anomalías)")

    print("\nListo. Archivos disponibles en web/data/")


if __name__ == "__main__":
    main()
