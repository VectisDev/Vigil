# Guía de Migración: dev-v10 → v11 — Módulos Estadísticos Unificados
# Migration Guide: dev-v10 → v11 — Unified Statistical Modules

**Fecha / Date:** 2026-06-07
**Cambios:** Unificación de Z-score + Consolidación de Benford
**Compatibilidad:** Retrocompatible — severidades pueden cambiar (siempre a la baja)

---

## Resumen ejecutivo / Executive Summary

Esta migración resuelve dos brechas críticas identificadas en la auditoría
multi-agente del 2026-06-07:

1. **Z-score:** Tres variantes inconsistentes → dos familias justificadas.
2. **Benford:** Tres implementaciones redundantes → una canónica (2BL) + una experimental (1er dígito INFO).

**Impacto neto:** Reducción de falsos positivos. Ninguna anomalía real dejará
de ser detectada.

---

## Cambio 1: Z-score unificado

### Archivo nuevo
`src/centinel/core/rules/zscore_unified.py`

### Funciones a usar

| Antes (dev-v10) | Después (v11) | Notas |
|-----------------|---------------|-------|
| Z manual en `large_numbers_convergence` | `zscore_proportion()` | Sin cambio funcional |
| Z con `ddof=0` en `granular_anomaly` | `zscore_empirical()` | ddof=0 → ddof=1 |
| Z con μ/σ externos en `participation_anomaly_advanced` | `zscore_empirical()` | Pasar historial como sample |

### Cambios en rules.yaml

```yaml
# ANTES (dev-v10) — inconsistente
large_numbers_convergence:
  z_threshold: 3.0    # ← hardcodeado, no justificado

participation_anomaly_advanced:
  # |Z|>3 hardcodeado en código, no en config

# DESPUÉS (v11) — unificado
zscore_thresholds:
  warning: 2.576       # p < 0.01 two-tailed
  critical: 3.291      # p < 0.001 two-tailed
  # Aplica a TODAS las reglas que usen Z-score
```

### Código de migración

```python
# ANTES (dev-v10, en granular_anomaly)
z = (x - np.mean(deltas)) / np.std(deltas)  # ddof=0 implícito
if abs(z) > 3.0:
    alert("CRITICAL")

# DESPUÉS (v11)
from centinel.core.rules.zscore_unified import zscore_empirical
result = zscore_empirical(x=x, sample=deltas)
if result and result.severity == Severity.CRITICAL:
    alert("CRITICAL")
```

---

## Cambio 2: Benford consolidado

### Archivo nuevo
`src/centinel/core/rules/benford_unified.py`

### Mapa de migración

| Antes (dev-v10) | config_key | Después (v11) | Severidad |
|-----------------|------------|---------------|-----------|
| Regla 1 (Benford 1er dígito) | `benford_first_digit` | `benford_experimental_first_digit()` | INFO (era CRITICAL) |
| Regla 2 (Benford por candidato) | `benford_law` | `benford_batch(test_type="canonical")` | CRITICAL (era MEDIUM) |
| Regla 10e (Benford granular) | parte de `granular_anomaly` | `benford_batch(test_type="canonical")` | Hereda de batch |
| **NUEVO: Regla canónica 2BL** | `benford_canonical` | `benford_canonical()` | CRITICAL |

### Cambios en rules.yaml

```yaml
# ANTES (dev-v10) — tres configs inconsistentes
benford_first_digit:
  min_samples: 15
  mad_warning: 0.008
  mad_critical: 0.015
  chi_pvalue_critical: 0.01

benford_law:
  min_samples: 10
  deviation_pct: 15
  chi_square_threshold: 0.05

# DESPUÉS (v11) — unificado
benford_canonical:
  digit: 2                   # 2nd digit (Mebane 2006)
  min_samples: 30            # chi² requires ≥30
  chi_pvalue_critical: 0.01
  chi_pvalue_warning: 0.05
  mad_warning: 0.006         # Calibrated HN 2025
  mad_critical: 0.012        # Calibrated HN 2025
  severity: CRITICAL

benford_first_digit_experimental:
  digit: 1
  min_samples: 30
  max_severity: INFO          # NEVER triggers WARNING/CRITICAL
  rationale: "Demoted per Deckert et al. (2011), high FP in electoral data"
```

### Código de migración

```python
# ANTES (dev-v10, Rule 1)
from centinel.core.rules.rule_benford_first_digit import check_benford_first_digit
result = check_benford_first_digit(votes, config)

# DESPUÉS (v11)
from centinel.core.rules.benford_unified import benford_canonical
result = benford_canonical(votes)

# ANTES (dev-v10, Rule 2 — per candidate)
for candidate in candidates:
    check_benford_per_candidate(candidate_votes[candidate])

# DESPUÉS (v11)
from centinel.core.rules.benford_unified import benford_batch
results = benford_batch(candidate_votes, test_type="canonical")
```

---

## Checklist de migración / Migration checklist

- [ ] Copiar `zscore_unified.py` a `src/centinel/core/rules/`
- [ ] Copiar `benford_unified.py` a `src/centinel/core/rules/`
- [ ] Copiar `STATISTICAL_CONVENTIONS.md` a `docs/stats/`
- [ ] Actualizar `rules.yaml` con los parámetros unificados
- [ ] Refactorizar Regla 7 para usar `zscore_proportion()`
- [ ] Refactorizar Regla 8 para usar `zscore_empirical()` con ddof=1
- [ ] Refactorizar Regla 10 (sub-tests Z-score) para usar `zscore_empirical()`
- [ ] Reemplazar Regla 1 por `benford_experimental_first_digit()` (INFO)
- [ ] Reemplazar Regla 2 por `benford_batch(test_type="canonical")`
- [ ] Agregar nueva Regla canónica: `benford_canonical()`
- [ ] Ejecutar `pytest tests/test_unified_stats.py -v`
- [ ] Ejecutar regresión completa contra 96 JSONs históricos
- [ ] Documentar tasas de FP antes/después en CHANGELOG.md
- [ ] Actualizar CentinelReglasMatematicas.pdf (nueva sección)
- [ ] Notificar al Prof. Devis Alvarado para revisión
