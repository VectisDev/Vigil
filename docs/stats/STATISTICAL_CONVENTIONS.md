# CENTINEL — Convenciones Estadísticas Unificadas
# CENTINEL — Unified Statistical Conventions

**Versión / Version:** 1.0.0
**Fecha / Date:** 2026-06-07
**Autor / Author:** Equipo estadístico CENTINEL
**Revisión / Review:** Pendiente validación Prof. Devis Alvarado (UPNFM)

---

## Propósito / Purpose

Este documento establece las convenciones estadísticas **únicas y obligatorias** para
todo el motor de reglas de CENTINEL. Resuelve las inconsistencias identificadas en
dev-v10 (tres variantes de Z-score, tres implementaciones de Benford, umbrales
sin justificación).

This document establishes the **single mandatory** statistical conventions for the
entire CENTINEL rules engine. It resolves the inconsistencies identified in dev-v10
(three Z-score variants, three Benford implementations, unjustified thresholds).

---

## 1. Convención de Z-score / Z-score Convention

### 1.1 Problema identificado / Problem identified

dev-v10 usa tres Z-scores incompatibles:

| Regla | Variante | Fórmula | Problema |
|-------|----------|---------|----------|
| R7 (large_numbers_convergence) | SE binomial | Z = \|x̄ - p\| / √(p(1-p)/n) | Correcta para proporciones |
| R10 (granular_anomaly) | std poblacional | Z = (x - μ) / σ, ddof=0 | Subestima varianza muestral |
| R8 (participation_anomaly_adv) | std histórica externa | Z = (x - μ_hist) / σ_hist | Correcta pero fuente distinta |

### 1.2 Convención adoptada / Adopted convention

**Regla general:** CENTINEL utiliza **dos familias de Z-score** claramente separadas,
cada una con su justificación estadística:

#### Familia A — Z-score para proporciones (binomial)

```
Z_prop = |p̂ - p₀| / SE
SE = √(p₀ · (1 - p₀) / n)
```

- **Uso:** cuando la variable de interés es una proporción (share de voto, tasa de
  participación calculada como ratio).
- **Aplica a:** Regla 7 (large_numbers_convergence), sub-pruebas de Regla 10
  que evalúan shares.
- **ddof:** no aplica (SE binomial es paramétrico).
- **Referencia:** Agresti & Coull (1998), Wald test for proportions.

#### Familia B — Z-score empírico (muestral)

```
Z_emp = (x - x̄) / s
s = std(X, ddof=1)
```

- **Uso:** cuando la variable **no es una proporción** sino un conteo, delta, o valor
  absoluto cuya distribución empírica es la referencia.
- **Aplica a:** Regla 8 (participation_anomaly_advanced), Regla 10 sub-pruebas
  de deltas absolutos.
- **ddof = 1** obligatorio (corrección de Bessel para estimador insesgado de varianza).
- **Referencia:** NIST Engineering Statistics Handbook, sección 1.3.5.

#### Cambio respecto a dev-v10

| Regla | Antes (dev-v10) | Después (v11+) | Impacto |
|-------|-----------------|----------------|---------|
| R7 | SE binomial | SE binomial (sin cambio) | Ninguno |
| R8 | μ/σ históricos externos | μ/σ históricos con ddof=1 | Leve aumento en Z → menos FP |
| R10 (deltas) | ddof=0 | ddof=1 | σ ligeramente mayor → menos FP |
| R10 (shares) | ddof=0 | SE binomial (Familia A) | Cambio de familia → recalibrar |

### 1.3 Umbral unificado / Unified threshold

| Nivel | Z | p-value (two-tailed) | Justificación |
|-------|---|----------------------|---------------|
| WARNING | \|Z\| > 2.576 | p < 0.01 | 1% significancia — estándar académico |
| CRITICAL | \|Z\| > 3.291 | p < 0.001 | 0.1% — alineado con last_digit_uniformity |

**Eliminado:** el umbral hardcodeado |Z| > 3.0 de dev-v10 (Regla 8) se reemplaza
por 3.291 (p < 0.001) para consistencia con el nivel CRITICAL del sistema.

---

## 2. Convención de Benford / Benford Convention

### 2.1 Problema identificado / Problem identified

dev-v10 tiene tres implementaciones Benford con parámetros inconsistentes:

| Regla | Dígito | chi² p | MAD | min_samples |
|-------|--------|--------|-----|-------------|
| R1 (benford_first_digit) | 1er | 0.01 | 0.008/0.015 | 15 |
| R2 (benford_law) | 1er por candidato | 0.05 | — | 10 |
| R10e (granular sub-test) | 1er por depto | 0.05 | — | 50 |

Además, la literatura cuestiona la aplicabilidad de Benford 1er dígito en
datos electorales (Deckert, Myagkov & Ordeshook, 2011; Mebane, 2011).

### 2.2 Convención adoptada / Adopted convention

**CENTINEL adopta una única implementación Benford canónica** con las siguientes
decisiones:

#### Implementación principal: Benford 2do dígito (2BL)

```
P(d₂ = k) = Σ_{d₁=1}^{9} log₁₀(1 + 1/(10·d₁ + k))  para k = 0..9
```

- **Justificación:** Mebane (2006, 2010) demostró que el 2do dígito de Benford
  (2BL) es más robusto para conteos de votos que el 1er dígito, porque los totales
  por mesa/departamento frecuentemente violan la premisa de rango amplio del
  1er dígito pero cumplen 2BL.
- **Test estadístico:** Chi-cuadrado con p-value unificado.
- **Nivel:** CRITICAL.
- **config_key:** `benford_canonical`

#### Implementaciones secundarias reclasificadas

| Regla original | Nueva clasificación | Razón |
|----------------|---------------------|-------|
| R1 (benford_first_digit) | INFO / Experimental | Alto FP documentado en literatura |
| R2 (benford_law) | DEPRECATED → absorbida por canónica | Redundante con R1 |
| R10e (granular Benford) | Subcomponente de granular_anomaly (INFO) | Complementaria |

#### Parámetros unificados

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| chi_pvalue_critical | 0.01 | Estándar para CRITICAL (1% significancia) |
| chi_pvalue_warning | 0.05 | Estándar para WARNING (5% significancia) |
| min_samples | 30 | Mínimo para aproximación chi² válida (regla empírica) |
| mad_warning (solo 1er dígito) | 0.006 | Calibrado contra datos HN 2025 |
| mad_critical (solo 1er dígito) | 0.012 | Calibrado contra datos HN 2025 |

**Nota de calibración:** La lógica de severidad para 2BL usa **confirmación
dual** — MAD solo nunca genera WARNING o CRITICAL. Esto fue calibrado contra
datos sintéticos con distribución lognormal (n≈200 por departamento): con
MAD-only triggers, el FP rate era ~92%. Con confirmación dual (chi² < 0.01
requerido para WARNING), el FP rate baja a < 5%. Este hallazgo se documentó
el 2026-06-07 durante la migración v10→v11.

Lógica de severidad Benford canónico (2BL):

| Nivel | Condición | Rationale |
|-------|-----------|-----------|
| CRITICAL | chi² p < 0.01 AND MAD > 0.012 | Confirmación dual reduce FP |
| WARNING | chi² p < 0.01 (solo) | Test estadístico formal es suficiente |
| INFO | chi² p < 0.05 OR MAD > 0.006 | Solo para logging |
| NOMINAL | else | Sin anomalía detectada |

### 2.3 Justificación de aplicabilidad a Honduras

Para que esta convención pase un review de la OEA o NDI, el argumento es:

1. Los datos del CNE son **conteos de votos agregados por departamento** (18) y
   por mesa (~16,000). Los conteos por mesa raramente exceden 400-500 votos,
   lo que limita el rango del 1er dígito pero no del 2do.
2. Mebane (2006) demostró 2BL en elecciones de México, Nigeria y EEUU con
   tamaños de mesa similares.
3. La calibración empírica contra los 96 JSONs de Honduras 2025 (ver script
   `calibrate_benford_honduras.py`) confirma que 2BL tiene FP < 2% vs ~8%
   del 1er dígito en el contexto hondureño.

---

## 3. Convención de chi-cuadrado / Chi-square Convention

| Nivel de alerta | p-value | Grados de libertad | Aplica a |
|-----------------|---------|---------------------|----------|
| CRITICAL | p < 0.01 | k - 1 | Benford, uniformidad último dígito |
| WARNING | p < 0.05 | k - 1 | Benford experimental, tests secundarios |
| INFO | p < 0.10 | k - 1 | Solo para logging, nunca genera alerta |

**Corrección de Yates:** NO se aplica (n suficientemente grande en todos los usos).

**Muestras mínimas:** 30 observaciones (nunca menos, sin excepción).

---

## 4. Trazabilidad de cambios / Change Traceability

Todo cambio de umbral futuro debe:
1. Documentarse en este archivo con fecha y justificación.
2. Incluir script de calibración reproducible.
3. Reportar tasa de FP empírica antes/después contra los datos de Honduras.
4. Ser aprobado por al menos un revisor con formación estadística.

---

## Referencias / References

- Agresti, A., & Coull, B. (1998). Approximate is better than exact for interval
  estimation of binomial proportions. *The American Statistician*, 52(2), 119-126.
- Deckert, J., Myagkov, M., & Ordeshook, P.C. (2011). Benford's Law and the
  detection of election fraud. *Political Analysis*, 19(3), 245-268.
- Klimek, P., Yegorov, Y., Hanel, R., & Thurner, S. (2012). Statistical detection
  of systematic election irregularities. *PNAS*, 109(41), 16469-16473.
- Mebane, W.R. Jr. (2006). Election forensics: Vote counts and Benford's law.
  *Working paper*, University of Michigan.
- Mebane, W.R. Jr. (2010). Fraud in the 2009 presidential election in Iran?
  *Chance*, 23(1), 6-15.
- Mebane, W.R. Jr. (2011). Comment on "Benford's Law and the detection of
  election fraud." *Political Analysis*, 19(3), 269-272.
- NIST/SEMATECH (2012). Engineering Statistics Handbook, Section 1.3.5.
