#!/usr/bin/env python3
"""
gen_sim_adversarial_30d.py
--------------------------
Generates two 28-day adversarial simulation JSON series calibrated to the
real Honduras 2025 presidential election (Nov 30 – Dec 24 2025):

  1. sim_mes_adversarial_5min.json      — clean baseline, 28 days, 5-min intervals (8064 snaps)
  2. sim_mes_adversarial_anomala_5min.json — same + 10 adversarial anomalies

Counting curve follows the real CNE 6-phase pattern:
  Phase 1 (day 1):     0% → 57%   TREP rápido (noche elección)
  Phase 2 (days 2-7):  57% → 60%  Sistema bloqueado, CNE web cae 2 veces
  Phase 3 (days 8-13): 60% → 99.8% Reanudación lenta
  Phase 4 (days 14-17): 99.8% flat  Boicot PLH/LIBRE
  Phase 5 (days 18-22): 99.8% → 100% Escrutinio especial
  Phase 6 (days 23-28): 100%        Declaración pendiente (Asfura ganador 24 dic)

Final results: PN/Asfura 40.27%, PLH/Nasralla 39.53%, LIBRE/Moncada 18.96%

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
INTERVAL_MINUTES = 5
DURATION_HOURS   = 672           # 28 days
N_SNAPSHOTS      = (DURATION_HOURS * 60) // INTERVAL_MINUTES  # 8064
SNAPS_PER_DAY    = (24 * 60) // INTERVAL_MINUTES              # 288

# Election night start: Nov 30 2025, 6 PM local (UTC-6) = Dec 1 00:00 UTC
SIM_START_UTC = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)

# Final election results (real HN 2025 data, declared Dec 24 2025)
FINAL_ACTAS_TOTALES  = 19167
FINAL_VALIDOS        = 3_674_945   # derived: 1,479,822 / 0.4027
FINAL_NULOS          = 137_284
FINAL_BLANCOS        = 78_219
FINAL_INCONSISTENTES = 2_773
FINAL_CORRECTAS      = 16_279

PARTIDOS_META = [
    {"nombre": "PARTIDO NACIONAL DE HONDURAS",
     "abbrev": "PN",  "candidato": "NASRY JUAN ASFURA ZABLAH",
     "color": "#df6b86", "final_pct": 40.27},   # 1,479,822 votos reales
    {"nombre": "PARTIDO LIBERAL DE HONDURAS",
     "abbrev": "PLH", "candidato": "SALVADOR ALEJANDRO CESAR NASRALLA SALUM",
     "color": "#6ea8fe", "final_pct": 39.53},   # 1,452,796 votos reales
    {"nombre": "PARTIDO LIBERTAD Y REFUNDACION",
     "abbrev": "LIBRE", "candidato": "RIXI RAMONA MONCADA GODOY",
     "color": "#b08cf0", "final_pct": 18.96},   # 705,428 votos reales (ajustado)
    {"nombre": "PARTIDO INNOVACION Y UNIDAD SOCIAL DEMOCRATA",
     "abbrev": "PINU",  "candidato": "JORGE NELSON AVILA GUTIERREZ",
     "color": "#57c08d", "final_pct": 0.75},
    {"nombre": "PARTIDO DEMOCRATA CRISTIANO DE HONDURAS",
     "abbrev": "DC",   "candidato": "MARIO ENRIQUE RIVERA CALLEJAS",
     "color": "#d4b066", "final_pct": 0.49},
]

RNG = random.Random(20260101)


def hn2025_count_curve(t: float) -> float:
    """
    Piecewise counting curve calibrated to the real HN 2025 CNE pattern.
    t = fraction of the 28-day window [0.0, 1.0].

    Phase 1 t∈[0,    1/28]: 0%  → 57%   TREP rápido noche elección
    Phase 2 t∈[1/28, 7/28]: 57% → 60%   Sistema CNE bloqueado (6 días)
    Phase 3 t∈[7/28,13/28]: 60% → 99.8% Reanudación lenta
    Phase 4 t∈[13/28,17/28]: 99.8% flat  Boicot PLH y LIBRE
    Phase 5 t∈[17/28,22/28]: 99.8% → 100% Escrutinio especial
    Phase 6 t∈[22/28, 1.0]: 100%          Declaración pendiente
    """
    P = [
        (0.0,    0.000),
        (1/28,   0.570),
        (7/28,   0.600),
        (13/28,  0.998),
        (17/28,  0.998),
        (22/28,  1.000),
        (1.0,    1.000),
    ]
    for i in range(len(P) - 1):
        t0, v0 = P[i]
        t1, v1 = P[i + 1]
        if t0 <= t <= t1:
            if t1 == t0:
                return v0
            frac = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * frac
    return 1.0


def gauss_noise(value: float, rel_std: float = 0.008) -> float:
    return value + RNG.gauss(0, value * rel_std)


def build_clean_series() -> list[dict]:
    """
    Build the 8,064-snapshot clean baseline series.

    Includes two real documented events (not anomalies):
      - CNE website crashes: snaps 110-120 (Dec 1, ~3:24 AM) and 180-190 (~6h later)
      - Nasralla brief lead: snaps 400-430 (Dec 2 afternoon, PLH +~2,000 votes over PN)
        Asfura reclaims lead by snap 576 (Dec 4).
    """
    snapshots = []
    for i in range(N_SNAPSHOTS):
        t    = i / (N_SNAPSHOTS - 1) if N_SNAPSHOTS > 1 else 0.0
        frac = hn2025_count_curve(t)
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

        # CNE website crash 1: Dec 1 ~3:24 AM local (UTC-6) = snap ~113
        # CNE website crash 2: ~6h later = snap ~185
        blackout_cne = (110 <= i <= 120) or (180 <= i <= 190)

        # Nightly maintenance blackout: 2–6 AM local (UTC-6) → 8–12 UTC
        # Only applies after the first 2 days
        local_hour = (ts.hour - 6) % 24
        blackout_nightly = (local_hour >= 2 and local_hour < 6 and i > SNAPS_PER_DAY * 2)

        blackout = blackout_cne or blackout_nightly

        snap: dict = {
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
        }

        # Real event: Nasralla brief lead (Dec 2 afternoon, ~+2,000 votes over PN)
        # Transfer enough votes from PN to PLH so PLH actually leads by ~2,000
        if 400 <= i <= 430:
            pn_v  = snap["partidos"][0]["votos"]
            plh_v = snap["partidos"][1]["votos"]
            gap   = pn_v - plh_v          # current PN advantage (>0)
            shift = gap // 2 + 1000       # enough to make PLH lead by ~2,000
            snap["partidos"][0]["votos"] = pn_v  - shift
            snap["partidos"][1]["votos"] = plh_v + shift
            if snap["validos"] > 0:
                snap["partidos"][0]["pct"] = round(snap["partidos"][0]["votos"] / snap["validos"] * 100, 2)
                snap["partidos"][1]["pct"] = round(snap["partidos"][1]["votos"] / snap["validos"] * 100, 2)
            snap["_nasralla_brief_lead"] = True

        snapshots.append(snap)

    return snapshots


def embed_anomalies(snapshots: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Embed 10 adversarial anomalies scaled to 288 snaps/day (×3 vs the old 96 snaps/day).
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

    # ── M1. Hold-and-Release Masivo — día 3→4 (snaps 576→864) ─────────────────
    hold_start   = 576
    hold_end     = 864
    release_bonus = 3600
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

    # ── M2. Ballot Stuffing / Votos Redondeados — día ~5 (snap 1200) ──────────
    idx = 1200
    for p in snaps[idx]["partidos"]:
        p["votos"] = round(p["votos"] / 1000) * 1000
    log_anomaly(idx, "ballot_stuffing_redondeo", 1000,
                "Todos los votos redondeados al millar → viola Benford y uniformidad de último dígito")

    # ── M3. Apagón Geográfico — día 6 completo (snaps 1440–1727, 288 snaps) ───
    for i in range(1440, 1728):
        snaps[i]["_geo_blackout_dept"] = "Francisco Morazán"
    log_anomaly(1440, "apagon_geografico", 288,
                "Apagón de 1 día completo (288 snaps / 24h) sin datos del depto Francisco Morazán")

    # ── M4. Aceleración Nocturna — día ~8, 2 AM local (snap 2100) ────────────
    nocturnal_bonus = 4800
    snaps[2100]["actas_divulgadas"] = min(
        snaps[2100]["actas_divulgadas"] + nocturnal_bonus, FINAL_ACTAS_TOTALES)
    snaps[2100]["validos"] += nocturnal_bonus * 165
    for p in snaps[2100]["partidos"]:
        pm = next(x for x in PARTIDOS_META if x["abbrev"] == p["abbrev"])
        p["votos"] += int(nocturnal_bonus * 165 * pm["final_pct"] / 100)
    log_anomaly(2100, "aceleracion_nocturna", nocturnal_bonus,
                f"+{nocturnal_bonus} actas en 1 snap a las 2 AM → velocidad 288× la normal")

    # ── M5. Inyección Progresiva de Ventaja — días 9–12 (snaps 2304–3455) ─────
    bonus_per_snap = 120
    total_injected = 0
    for i in range(2304, 3456):
        delta = (i - 2303) * bonus_per_snap
        snaps[i]["partidos"][1]["votos"] += delta   # PLH = partido[1]
        snaps[i]["validos"]              += delta
        total_injected += bonus_per_snap
    log_anomaly(2304, "inyeccion_progresiva_ventaja",
                bonus_per_snap,
                f"PLH +{bonus_per_snap} votos/snap durante 1152 snaps (4 días) → ventaja acumulada")

    # ── M6. Campaña de Votos Nulos — días 13–14 (snaps 3456–3743) ────────────
    for i in range(3456, 3744):
        snaps[i]["nulos"] = int(snaps[i]["nulos"] * 3.8)
    log_anomaly(3456, "campana_votos_nulos", 3.8,
                "Votos nulos ×3.8 durante 288 snaps (24h) — zona de oposición simulada")

    # ── M7. Rollback de Datos — día 15 (snap 4032, revierte a día 12 / snap 3456) ──
    rollback_target = 3456
    for field in ("actas_divulgadas", "validos", "nulos", "blancos"):
        snaps[4032][field] = snaps[rollback_target][field]
    snaps[4032]["partidos"]  = copy.deepcopy(snaps[rollback_target]["partidos"])
    snaps[4032]["_rollback"] = True
    log_anomaly(4032, "rollback_datos", rollback_target,
                f"Datos revertidos al estado del snapshot {rollback_target} (día 12) → regresión de 3 días de conteo")

    # ── M8. Uniformidad Sospechosa de Mesas — días 16–17 (snaps 4320–4607) ───
    for i in range(4320, 4608):
        total_v = snaps[i]["validos"]
        for j, p in enumerate(snaps[i]["partidos"]):
            pm = PARTIDOS_META[j]
            p["votos"] = int(total_v * pm["final_pct"] / 100)
            p["pct"]   = round(pm["final_pct"], 2)
        snaps[i]["_uniformidad_sospechosa"] = True
    log_anomaly(4320, "uniformidad_sospechosa_mesas", 288,
                "Distribución perfectamente idéntica al % teórico durante 288 snaps (24h) → datos fabricados")

    # ── M9. Inversión de Resultados post-Apagón — días 18–21 ─────────────────
    # Blackout de 3 días (días 18–20, snaps 4896–5759)
    for i in range(4896, 5760):
        snaps[i]["blackout"] = True
    # Inversión en el snap inmediatamente post-apagón (snap 5760, día 21)
    tgt = min(5760, len(snaps) - 1)
    old0 = snaps[tgt]["partidos"][0]["votos"]
    old1 = snaps[tgt]["partidos"][1]["votos"]
    snaps[tgt]["partidos"][0]["votos"] = old1
    snaps[tgt]["partidos"][1]["votos"] = old0
    pct0 = snaps[tgt]["partidos"][0]["pct"]
    pct1 = snaps[tgt]["partidos"][1]["pct"]
    snaps[tgt]["partidos"][0]["pct"] = pct1
    snaps[tgt]["partidos"][1]["pct"] = pct0
    snaps[tgt]["_resultado_invertido"] = True
    log_anomaly(tgt, "inversion_resultados_post_apagon", abs(old0 - old1),
                f"Apagón de 3 días (snaps 4896–5759) seguido de inversión de candidatos [0]↔[1] en snap {tgt}")

    # ── M10. Mesa Fantasma / Conteo Imposible — día ~28 (snap 8000) ──────────
    tgt10 = min(8000, len(snaps) - 1)
    snaps[tgt10]["actas_divulgadas"] = FINAL_ACTAS_TOTALES + 850
    snaps[tgt10]["_mesa_fantasma"]   = True
    log_anomaly(tgt10, "mesa_fantasma_conteo_imposible", 850,
                "actas_divulgadas supera actas_totales en 850 → mesas fantasma, conteo imposible")

    return snaps, anomalias


def build_meta(clean: bool, n: int, anomalias: list | None) -> dict:
    return {
        "election":         "Elecciones Generales Honduras 2025 — Presidencia (SIMULACIÓN ADVERSARIAL 28 DÍAS)",
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
        "calibracion":      "Datos reales HN 2025: Asfura (PN) 40.27%, Nasralla (PLH) 39.53%, Moncada (LIBRE) 18.96%. CNE tardó 24 días en declarar ganador.",
        "descripcion": (
            "Simulación adversarial 28 días calibrada a elecciones HN 30/11/2025. "
            "Curva de conteo en 6 fases reales del CNE: TREP rápido (día 1, 0%→57%), "
            "sistema bloqueado (días 2-7, 57%→60%), reanudación lenta (días 8-13, 60%→99.8%), "
            "boicot PLH/LIBRE (días 14-17, flat), escrutinio especial (días 18-22, 99.8%→100%), "
            "declaración pendiente (días 23-28, flat). "
            "Incluye eventos reales: 2 caídas del sistema CNE (día 1) y ventaja breve de Nasralla (día 2, +2,000 votos). "
            "Línea base limpia sin anomalías inyectadas."
            if clean else
            "Simulación adversarial 28 días con 10 anomalías embebidas calibradas a cronología real HN 2025. "
            "M1: hold-and-release (día 3-4), M2: ballot stuffing (día ~5), M3: apagón Francisco Morazán (día 6), "
            "M4: aceleración nocturna (día ~8), M5: inyección progresiva PLH (días 9-12), "
            "M6: campaña votos nulos (días 13-14), M7: rollback datos (día 15), "
            "M8: uniformidad sospechosa (días 16-17), M9: apagón 3 días + inversión (días 18-21), "
            "M10: mesa fantasma al cierre (día ~28)."
        ),
        **({"anomalias_embebidas": anomalias} if anomalias else {}),
    }


def main():
    print("Generando simulación adversarial 28 días / 5 min calibrada a HN 2025...")
    print(f"  Duración: {DURATION_HOURS}h ({DURATION_HOURS//24} días) | Intervalo: {INTERVAL_MINUTES}min | Snapshots: {N_SNAPSHOTS}")
    print(f"  Snaps por día: {SNAPS_PER_DAY}")
    print(f"  Resultados reales: PN 40.27%, PLH 39.53%, LIBRE 18.96%")

    print("\n[1/3] Construyendo serie base limpia (28 días)...")
    clean_snaps = build_clean_series()
    print(f"  Generados {len(clean_snaps)} snapshots")

    print("\n[2/3] Embebiendo 10 anomalías adversariales...")
    anomalous_snaps, anomaly_manifest = embed_anomalies(clean_snaps)
    print(f"  {len(anomaly_manifest)} anomalías embebidas")

    print("\n[3/3] Escribiendo archivos JSON...")

    clean_out = OUT_DIR / "sim_mes_adversarial_5min.json"
    clean_doc = {"meta": build_meta(True, len(clean_snaps), None), "snapshots": clean_snaps}
    clean_out.write_text(json.dumps(clean_doc, ensure_ascii=False, separators=(',', ':')))
    size_kb = clean_out.stat().st_size / 1024
    print(f"  ✓ {clean_out.name} ({size_kb:.0f} KB)")

    anom_out = OUT_DIR / "sim_mes_adversarial_anomala_5min.json"
    anom_doc = {"meta": build_meta(False, len(anomalous_snaps), anomaly_manifest), "snapshots": anomalous_snaps}
    anom_out.write_text(json.dumps(anom_doc, ensure_ascii=False, separators=(',', ':')))
    size_kb = anom_out.stat().st_size / 1024
    print(f"  ✓ {anom_out.name} ({size_kb:.0f} KB, {len(anomaly_manifest)} anomalías)")

    print("\nListo. Archivos disponibles en web/data/")


if __name__ == "__main__":
    main()
