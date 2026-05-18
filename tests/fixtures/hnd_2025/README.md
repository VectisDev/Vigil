# Fixtures — Elecciones Generales Honduras 2025

**Fuente:** Servidor oficial CNE Honduras (datos públicos)
**Cobertura:** 2025-12-03 16:25 UTC → 2025-12-10 17:03 UTC
**Snapshots:** 64 archivos JSON nacionales (nivel agregado — todos los departamentos)
**Candidatura:** Presidencia de la República

---

## Uso

```bash
# Calibrar reglas Centinel contra datos reales
python scripts/calibrate_2025.py --data tests/fixtures/hnd_2025/

# Resultado
# reports/calibration_2025.json  — anomalías por regla (JSON)
# reports/calibration_2025.md   — resumen legible
```

---

## Estructura de cada snapshot

```json
{
  "resultados": [
    { "partido": "PARTIDO LIBERAL DE HONDURAS", "candidato": "...", "votos": "1,027,090", "porcentaje": "38.10" },
    { "partido": "PARTIDO NACIONAL DE HONDURAS", "candidato": "...", "votos": "1,013,050", "porcentaje": "37.58" }
  ],
  "estadisticas": {
    "totalizacion_actas": { "actas_totales": "19,152", "actas_divulgadas": "15,310" },
    "distribucion_votos":  { "validos": "2,552,777", "nulos": "93,520", "blancos": "49,732" },
    "estado_actas_divulgadas": { "actas_correctas": "13,121", "actas_inconsistentes": "2,189" }
  }
}
```

---

## Anomalías detectadas por Centinel (primera calibración — 2026-05-18)

| Regla | Alertas | Severidad | Descripción |
|-------|---------|-----------|-------------|
| `inconsistency_rate` | 55 | CRITICAL | 14.3 % de actas inconsistentes a lo largo de toda la serie (umbral: 10 %) |
| `data_blackout_start/end` | 16 | CRITICAL | Períodos donde resultados se vuelven vacíos mientras las actas siguen contando |
| `snapshot_jump` | 2 | CRITICAL | Saltos del 6.4 % (PN) y 6.5 % (Libre) en 786 minutos — 2025-12-04T11:06 |
| `trend_reversal_at_blackout` | 1 | CRITICAL | Brecha líder-segundo aumentó 69.6 % durante período de opacidad |
| `universe_mutation` | 1 | CRITICAL | `actas_totales` cambió de 19,152 → 0 — 2025-12-04T16:00 |
| `processing_speed` | 1 | HIGH | Aceleración anómala en velocidad de procesamiento |

**Total: 83 alertas — 82 CRITICAL, 1 HIGH**

> Estas alertas son señales de auditoría, no acusaciones. Requieren investigación
> independiente para determinar si representan errores técnicos, problemas operativos
> o irregularidades en el proceso de divulgación.

---

## Cobertura del escrutinio

| Fecha inicio | Actas divulgadas | % Escrutinio |
|-------------|-----------------|--------------|
| 2025-12-03T16:25 | 15,310 / 19,152 | 79.9 % |
| 2025-12-10T17:03 | 19,038 / 19,152 | 99.4 % |

---

## Licencia y reproducibilidad

Datos publicados oficialmente por el CNE Honduras — información pública de libre acceso.
El script `calibrate_2025.py` es determinista: cualquier tercero puede reproducir exactamente
las 83 alertas ejecutando el pipeline sobre estos archivos.

*Generado con C.E.N.T.I.N.E.L. v0.2.0 — AGPL-3.0*
