# Análisis de Tasa de Falsos Positivos — CENTINEL Engine dev-v12
# False Positive Rate Analysis — CENTINEL Engine dev-v12

**Working Paper WP-CENTINEL-2026-01**  
**Fecha / Date:** 2026-06-07  
**Versión / Version:** 1.0 — Borrador para revisión académica  
**Estado / Status:** Pendiente revisión y firma — Prof. Devis Alvarado (UPNFM)

---

## Resumen ejecutivo / Executive Summary

Este documento reporta los resultados de un análisis de tasa de falsos positivos
(FP) sobre las reglas estadísticas del motor CENTINEL dev-v12, realizado mediante
simulación Monte Carlo de 500 ensayos sobre datos sintéticos limpios calibrados
para representar conteos de votos por departamento en Honduras.

**Hallazgo crítico:** La implementación de Benford de primer dígito de dev-v10
presentó una tasa de falsos positivos del **100%** sobre datos limpios simulados
(500/500 ensayos), mientras que la implementación canónica de segundo dígito
(2BL, Mebane 2006) presentó una tasa del **1.2%** (6/500), por debajo del
umbral de diseño del 5%.

This document reports false positive rate analysis for the CENTINEL dev-v12
statistical rules engine via 500-trial Monte Carlo simulation on clean synthetic
data calibrated to Honduran per-department vote count distributions.

**Critical finding:** The dev-v10 first-digit Benford implementation exhibited a
**100% false positive rate** on clean simulated data (500/500 trials), while the
canonical second-digit implementation (2BL, Mebane 2006) exhibited **1.2%**
(6/500), below the 5% design threshold.

---

## 1. Introducción / Introduction

### 1.1 Contexto / Context

CENTINEL aplica 23 reglas forenses sobre datos JSON del CNE de Honduras.
Un requisito fundamental es mantener FP < 5% sobre datos electorales limpios.

La versión dev-v10 presentaba tres inconsistencias metodológicas identificadas:

1. Tres implementaciones de Ley de Benford con parámetros inconsistentes.
2. Tres variantes de Z-score sin unificación (SE binomial, ddof=0, std histórico).
3. Umbral hardcodeado |Z|>3 sin justificación estadística formal.

### 1.2 Declaración de neutralidad / Neutrality statement

Análisis metodológico y técnico exclusivamente. No evalúa datos electorales
reales ni emite juicios sobre integridad de procesos electorales específicos.
CENTINEL no afirma fraude; detecta anomalías para evaluación humana independiente.

---

## 2. Metodología / Methodology

### 2.1 Generador de datos limpios / Clean data generator

Los conteos por mesa/departamento en Honduras siguen distribución aproximadamente
lognormal, estimada visualmente de los 64 archivos JSON CNE 2025 disponibles:

$$\text{votos}_{mesa} \sim \text{Lognormal}(\mu=5.5,\ \sigma=1.8)$$

Produce valores típicos entre 50 y 2,000 votos, consistente con el rango
observado en Honduras (200–500 votos/mesa típico).

**Parámetros de simulación:**
- N = 500 ensayos independientes
- Semilla aleatoria: `np.random.default_rng(seed=2025)` (reproducible)
- Filtros: valores ≥ 10 (necesario para extraer 2do dígito), mínimo 30 obs.

### 2.2 Reglas evaluadas / Rules evaluated

| Regla | Config key | Cambio dev-v10 → dev-v12 |
|-------|------------|--------------------------|
| R1 | benford_first_digit | CRITICAL → INFO (demotion, experimental) |
| R2 | benford_law | 1er dígito/candidato → 2BL canónica (Mebane 2006) |
| R7 | large_numbers_convergence | Z manual hardcoded → `zscore_proportion()` |
| R8 | participation_anomaly_advanced | |Z|>3 hardcoded → `zscore_empirical()` ddof=1 |
| R10 | granular_anomaly | ddof=0 → ddof=1 (corrección Bessel) |

### 2.3 Criterio de falso positivo / False positive criterion

$$\text{FP rate} = \frac{\text{ensayos con alerta WARNING o CRITICAL}}{N=500}$$

Las alertas INFO no se cuentan como FP en producción (solo logging).

---

## 3. Resultados / Results

| Componente | FP rate dev-v10 | FP rate dev-v12 | Reducción |
|------------|-----------------|-----------------|-----------|
| Benford 1er dígito (WARNING+CRITICAL) | **100.0%** (500/500) | 0.0% (capped INFO) | ↓ 100 pp |
| Benford 2BL CRITICAL (chi² AND MAD) | — | **1.2%** (6/500) | — |
| Benford 2BL WARNING (chi² solo) | — | **1.2%** (6/500) | — |
| Z-score proporciones CRITICAL | ~0.1% (teórico) | 0.0% | ↓ ~0.1 pp |
| Z-score empírico WARNING (ddof=1) | ~3.5%* | **2.4%** (12/500) | ↓ ~1.1 pp |
| Z-score empírico CRITICAL (ddof=1) | ~0.8%* | **0.6%** (3/500) | ↓ ~0.2 pp |

*Estimado teórico para dev-v10; ddof=0 produce Z artificialmente mayor.

### 3.1 Hallazgo principal: Benford 1er dígito / Key finding

La tasa de FP del 100% en Benford de primer dígito es consistente con la
literatura internacional:

> *"The first-digit distribution of vote counts does not in general follow
> Benford's Law because the underlying counts are not scale-invariant random
> variables spanning several orders of magnitude."*
> — Deckert, Myagkov & Ordeshook (2011, p. 248)

> *"I strongly recommend against using the first-significant-digit version
> of Benford's Law for election forensics."*
> — Mebane (2011, p. 270)

**Justificación para Honduras:** Conteos por mesa oscilan entre ~200 y ~500
votos — menos de una orden de magnitud. La premisa de escala de Benford de
primer dígito no se cumple en este contexto.

### 3.2 Validación Benford 2BL / 2BL validation

La fórmula del segundo dígito de Benford:

$$P(d_2 = k) = \sum_{d_1=1}^{9} \log_{10}\!\left(1 + \frac{1}{10 \cdot d_1 + k}\right), \quad k = 0..9$$

Con confirmación dual (chi² p<0.01 **AND** MAD>0.012) para nivel CRITICAL,
la tasa de FP fue 1.2% (IC 95%: 0.4%–2.6%), dentro del umbral del 5%.

### 3.3 Corrección Bessel / Bessel correction

La corrección ddof=0 → ddof=1 aplica el estimador insesgado de varianza:

$$s^2 = \frac{1}{n-1} \sum_{i=1}^{n} (x_i - \bar{x})^2$$

Para n < 50 (típico en Honduras: 18 departamentos), ddof=0 subestima σ y
produce Z-scores artificialmente elevados. La corrección es estadísticamente
obligatoria (NIST Engineering Statistics Handbook, §1.3.5).

---

## 4. Limitaciones / Limitations

1. **Datos sintéticos** — validación con los 96 JSONs reales del CNE pendiente.
2. **Sin correlación espacial** — no modela dependencia entre departamentos.
3. **Parámetros lognormal estimados visualmente** — ajuste MLE formal pendiente.
4. **N=500** — para FP~1%, IC 95% es [0.4%, 2.6%]. N=2000 daría IC más estrecho.

---

## 5. Reproducibilidad / Reproducibility

```bash
git clone https://github.com/VectisDev/centinel.git
cd centinel && git checkout dev-v12
pip install numpy scipy pandas pytest
PYTHONPATH=src python docs/research/run_fp_analysis.py
# Resultados esperados:
# benford_2bl_critical:           6/500  (1.2%)
# benford_1st_would_be_critical: 500/500 (100.0%)
# zscore_emp_warning:            12/500  (2.4%)
# zscore_emp_critical:            3/500  (0.6%)
```

**Semilla fija:** `np.random.default_rng(seed=2025)`

---

## 6. Conclusiones / Conclusions

1. Benford 1er dígito en dev-v10 → FP 100% → estadísticamente inútil.
   **Decisión correcta:** demotion a INFO en dev-v12.
2. Benford 2BL en dev-v12 → FP 1.2% → dentro del umbral del 5%.
   **Decisión correcta:** adopción como test canónico.
3. Corrección Bessel (ddof=1) es estadísticamente necesaria para n<50.
4. Umbrales Z unificados (2.576 = p<0.01; 3.291 = p<0.001) son estándar.

---

## Referencias / References

- Deckert, J., Myagkov, M. & Ordeshook, P.C. (2011). Benford's Law and the
  detection of election fraud. *Political Analysis*, 19(3), 245–268.
  https://doi.org/10.1093/pan/mpr014
- Klimek, P. et al. (2012). Statistical detection of systematic election
  irregularities. *PNAS*, 109(41), 16469–16473.
- Mebane, W.R. Jr. (2006). Election forensics: Vote counts and Benford's law.
  *Working paper*, University of Michigan.
- Mebane, W.R. Jr. (2011). Comment on "Benford's Law and the detection of
  election fraud." *Political Analysis*, 19(3), 269–272.
- NIST/SEMATECH (2012). Engineering Statistics Handbook, §1.3.5.

---

## Aprobación / Approval

Pendiente revisión técnica y firma:

**Prof. Devis Alvarado**  
Departamento de Matemáticas y Estadística  
Universidad Pedagógica Nacional Francisco Morazán (UPNFM)  
Tegucigalpa, Honduras

_Firma: _________________________ Fecha: _____________

---
*CENTINEL — AGPL-3.0 — WP-CENTINEL-2026-01 v1.0*
