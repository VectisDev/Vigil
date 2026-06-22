# Pruebas Estadisticas Clasicas / Classical Statistical Tests

Documentacion de las pruebas estadisticas clasicas implementadas en las reglas
de deteccion de Centinel.

Documentation for classical statistical tests implemented in Centinel's
detection rules.

**Archivos fuente / Source files:**
- `src/centinel/core/rules/runs_test_rule.py`
- `src/centinel/core/rules/last_digit_uniformity_rule.py`
- `src/centinel/core/rules/large_numbers_rule.py`
- `src/centinel/core/rules/correlation_participation_vote_rule.py`
- `src/centinel/core/rules/inconsistency_rate_rule.py`
- `src/centinel/core/rules/granular_anomaly_rule.py` (z-scores)

---

## 1. Runs Test (Wald-Wolfowitz) / Prueba de Rachas

**config_key:** `runs_test`
**Severidad / Severity:** CRITICAL

### 1.1 Metodo / Method

Se calcula el porcentaje del candidato lider en cada mesa, se binariza
respecto a la mediana, y se aplica el runs test para evaluar aleatoriedad.

$$b_i = \begin{cases} 1 & \text{si } s_i \geq \tilde{s} \\ 0 & \text{si } s_i < \tilde{s} \end{cases}$$

donde $s_i$ es la proporcion del candidato lider en la mesa $i$ y $\tilde{s}$
es la mediana de todas las proporciones.

### 1.2 Formula

Sea $R$ = numero de rachas observadas, $n_1$ = conteo de 1s, $n_0$ = conteo de 0s:

$$\mu_R = \frac{2 n_1 n_0}{n_1 + n_0} + 1$$

$$\sigma_R = \sqrt{\frac{2 n_1 n_0 (2 n_1 n_0 - n_1 - n_0)}{(n_1 + n_0)^2 (n_1 + n_0 - 1)}}$$

$$z = \frac{R - \mu_R}{\sigma_R}$$

$$p\text{-value} = 2 \cdot (1 - \Phi(|z|))$$

donde $\Phi$ es la CDF de la distribucion normal estandar.

### 1.3 Hipotesis / Hypotheses

- **H0:** La secuencia binarizada es aleatoria (sin patron espacial).
- **H1:** Existen rachas no aleatorias, indicando posible fabricacion
  sistematica de votos por mesa (p. ej. mesas cargadas secuencialmente).

### 1.4 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `min_samples` | 30 | Minimo de mesas para validez del test |
| `critical_pvalue` | 0.01 | Nivel de significancia 1% (bilateral) |

### 1.5 Falsos positivos / False Positives

- Mesas ordenadas geograficamente pueden mostrar rachas naturales por
  homogeneidad regional. Mitigacion: la ordenacion es por codigo de mesa,
  no por ubicacion geografica.

---

## 2. Uniformidad del Ultimo Digito / Last Digit Uniformity

**config_key:** `last_digit_uniformity`
**Severidad / Severity:** CRITICAL

### 2.1 Fundamento / Foundation

El ultimo digito de conteos electorales genuinos debe distribuirse
uniformemente entre 0-9 (cada digito con probabilidad 10%).

### 2.2 Formula Chi-cuadrado / Chi-square Formula

$$\chi^2 = \sum_{d=0}^{9} \frac{(O_d - E_d)^2}{E_d}$$

donde $E_d = n / 10$ para todo $d$ (distribucion uniforme).

Grados de libertad: $\text{df} = 9$ (10 categorias - 1).

### 2.3 Hipotesis / Hypotheses

- **H0:** Los ultimos digitos de los votos se distribuyen uniformemente (U[0,9]).
- **H1:** Los ultimos digitos no son uniformes (posible redondeo o fabricacion).

### 2.4 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `min_samples` | 20 | Minimo de muestras para validez |
| `chi_pvalue_critical` | 0.001 | Umbral muy estricto (0.1%) para reducir falsos positivos |

### 2.5 Falsos positivos / False Positives

- El umbral de p=0.001 es intencionalmente estricto porque variaciones
  naturales en ultimos digitos son comunes con pocas mesas.

---

## 3. Convergencia de Grandes Numeros / Law of Large Numbers Convergence

**config_key:** `large_numbers_convergence`
**Severidad / Severity:** Medium

### 3.1 Metodo / Method

Verifica que las proporciones de votos por mesa converjan hacia el promedio
global, segun la Ley de Grandes Numeros.

### 3.2 Formula

Para cada candidato $c$:

$$\bar{p}_c = \frac{1}{m} \sum_{i=1}^{m} p_{c,i}$$

donde $p_{c,i}$ es la proporcion del candidato $c$ en la mesa $i$, y $m$ es
el numero de mesas.

Proporcion global:

$$P_c = \frac{V_c}{\sum_c V_c}$$

Error estandar:

$$\text{SE}_c = \sqrt{\frac{P_c (1 - P_c)}{m}}$$

Z-score:

$$z_c = \frac{|\bar{p}_c - P_c|}{\text{SE}_c}$$

### 3.3 Hipotesis / Hypotheses

- **H0:** La media muestral de proporciones por mesa converge al promedio
  global.
- **H1:** Las proporciones por mesa no convergen, indicando heterogeneidad
  sistematica.

### 3.4 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `min_samples` | 30 | Minimo de mesas por candidato |
| `z_threshold` | 3.0 | Regla 3-sigma |
| `min_total_votes` | 200 | Minimo de votos totales |

---

## 4. Z-Scores por Departamento / Departmental Z-Scores

**Fuente / Source:** `granular_anomaly_rule.py`
**Severidad / Severity:** High

### 4.1 Formula

Para los deltas de votos entre snapshots por departamento dentro de un nivel
electoral:

$$z_i = \frac{\Delta_i - \bar{\Delta}}{\sigma_{\Delta}}$$

donde $\sigma_{\Delta}$ usa $\text{ddof}=0$ (desviacion poblacional).

### 4.2 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `zscore_threshold` | 3.0 | Outlier a 3 sigma |
| `zscore_min_abs_delta` | 100 | Solo alertar si el delta absoluto es significativo |
| `zscore_min_departments` | 5 | Minimo de departamentos para calcular z-score |

---

## 5. Tasa de Actas Inconsistentes / Inconsistency Rate

**config_key:** `inconsistency_rate`
**Severidad / Severity:** CRITICAL

### 5.1 Formula

$$r = \frac{A_{\text{inconsistentes}}}{A_{\text{divulgadas}}}$$

### 5.2 Deteccion de nivel absoluto

$$\text{alerta} \iff r \geq r_{\text{critical}}$$

### 5.3 Deteccion de escalada entre snapshots

$$\Delta r = r^{(t)} - r^{(t-1)}$$

$$\text{alerta} \iff \Delta r \geq \Delta r_{\text{threshold}}$$

### 5.4 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `critical_pct` | 10% | Calibrado con datos Honduras 2025 (baseline observado: 14.3%) |
| `escalation_delta_pct` | 1.0% | Escalada sostenida de 1pp entre snapshots |

### 5.5 Hipotesis / Hypotheses

- **H0:** Las actas inconsistentes son un porcentaje menor y estable del total.
- **H1:** La tasa excede el umbral critico o escala rapidamente, indicando
  retencion deliberada de actas.

### 5.6 Contexto Honduras 2025

La regla fue calibrada con el hallazgo forense de Honduras 2025: 2,773 actas
(14.3%) marcadas como inconsistentes desde el primer snapshot, representando
aproximadamente 450,000 votos inauditables.
