# Analisis de Benford / Benford Analysis

Documentacion matematica de las reglas basadas en la Ley de Benford para la
deteccion de anomalias en conteos electorales.

Mathematical documentation for Benford's Law rules used in electoral count
anomaly detection.

**Archivos fuente / Source files:**
- `src/centinel/core/rules/benford_first_digit_rule.py`
- `src/centinel/core/rules/benford_law_rule.py` (stub, logica en el anterior)
- `src/centinel/core/rules/granular_anomaly_rule.py` (Benford por departamento)
- `src/auditor/inconsistent_acts.py` (Benford sobre escrutinio especial)

---

## 1. Ley de Benford -- Primer Digito / Benford's First Digit Law

### 1.1 Fundamento / Foundation

La Ley de Benford (tambien llamada First Digit Law o 1BL) establece que en
conjuntos de datos numericos naturales, el primer digito significativo $d$
($d \in \{1,2,...,9\}$) sigue una distribucion logaritmica:

$$P(d) = \log_{10}\left(1 + \frac{1}{d}\right)$$

| Digito | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|--------|------|------|------|------|------|------|------|------|------|
| P(d) % | 30.1 | 17.6 | 12.5 | 9.7 | 7.9 | 6.7 | 5.8 | 5.1 | 4.6 |

Los conteos electorales por mesa/candidato, al variar en ordenes de magnitud,
deben aproximar esta distribucion. Desviaciones significativas sugieren
fabricacion o manipulacion de cifras.

---

## 2. Regla 1: MAD + Chi-cuadrado Agregado / Aggregate MAD + Chi-square

**config_key:** `benford_first_digit`
**Severidad / Severity:** CRITICAL

### 2.1 Formula MAD (Mean Absolute Deviation) / MAD Formula

$$\text{MAD} = \frac{1}{9} \sum_{d=1}^{9} \left| \hat{p}_d - P(d) \right|$$

donde $\hat{p}_d$ es la proporcion observada del digito $d$ y $P(d)$ es la
proporcion teorica de Benford.

### 2.2 Chi-cuadrado / Chi-square Goodness of Fit

$$\chi^2 = \sum_{d=1}^{9} \frac{(O_d - E_d)^2}{E_d}$$

donde $O_d$ es el conteo observado del digito $d$ y
$E_d = n \cdot P(d)$ es el conteo esperado, con $n$ = total de muestras.

Los grados de libertad son $\text{df} = 8$ (9 categorias - 1).

### 2.3 Hipotesis / Hypotheses

- **H0:** La distribucion del primer digito de los votos sigue la Ley de Benford.
- **H1:** La distribucion se desvia significativamente de Benford (posible manipulacion).

### 2.4 Umbrales por defecto / Default Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `mad_warning` | 0.008 | Conformidad aceptable segun Nigrini (2012): MAD < 0.006 = conformidad cercana, 0.006-0.012 = aceptable |
| `mad_critical` | 0.015 | MAD > 0.015 = no conformidad segun clasificacion de Nigrini |
| `chi_pvalue_critical` | 0.01 | Nivel de significancia 1% para reducir falsos positivos |
| `min_samples` | 15 | Minimo de muestras para validez estadistica |

### 2.5 Logica de decision / Decision Logic

- **CRITICAL:** `MAD > 0.015` OR `p-value < 0.01`
- **WARNING:** `0.008 <= MAD <= 0.015`
- **PASS:** Caso contrario

### 2.6 Sensibilidad y especificidad / Sensitivity and Specificity

- **Sensibilidad:** Alta para fabricacion uniforme o manipulacion burda.
  Limitada para manipulaciones que preservan la estructura Benford.
- **Especificidad:** El umbral de p-value 0.01 y MAD dual reducen falsos
  positivos frente a variaciones naturales con pocas mesas.

### 2.7 Falsos positivos y mitigaciones / False Positives and Mitigations

- Conteos con pocas mesas (n < 15) son excluidos por `min_samples`.
- Departamentos rurales con pocas mesas pueden mostrar desviaciones naturales;
  la regla agrega todos los candidatos para aumentar n.
- El uso dual MAD + chi-cuadrado reduce falsas alarmas: ambas metricas deben
  ser anomalas para CRITICAL.

---

## 3. Regla 2: Chi-cuadrado por Candidato / Per-Candidate Chi-square

**config_key:** `benford_law`
**Severidad / Severity:** Medium (regla de investigacion, deshabilitada por defecto)

### 3.1 Metodo / Method

Para cada candidato individualmente, se calcula chi-cuadrado sobre los primeros
digitos de sus votos por mesa:

$$\chi^2_c = \sum_{d=1}^{9} \frac{(O_{c,d} - E_{c,d})^2}{E_{c,d}}$$

donde $O_{c,d}$ es el conteo observado del digito $d$ para el candidato $c$,
y $E_{c,d} = n_c \cdot P(d)$.

Ademas se calcula la desviacion maxima porcentual:

$$\Delta_{\max} = \max_{d \in \{1..9\}} \left| \hat{p}_{c,d} - P(d) \cdot 100 \right|$$

### 3.2 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `min_samples` | 10 | Minimo por candidato individual |
| `deviation_pct` | 15% | Desviacion maxima aceptable en puntos porcentuales |
| `chi_square_threshold` | 0.05 | p-value del chi-cuadrado |

### 3.3 Alerta / Alert Condition

Se genera alerta cuando `p-value < 0.05` OR `desviacion_max >= 15%`.

---

## 4. Benford por Departamento / Per-Department Benford

**Fuente / Source:** `granular_anomaly_rule.py`

Aplica chi-cuadrado por departamento y nivel electoral, usando votos de
candidatos con `votos >= 10` (configurable via `benford_min_vote`).

- `benford_pvalue_threshold`: 0.05
- `benford_min_samples`: 50

---

## 5. Benford sobre Escrutinio Especial / Benford on Special Scrutiny

**Fuente / Source:** `src/auditor/inconsistent_acts.py`
(metodo `detect_benford_special_scrutiny`)

Aplica la misma formula chi-cuadrado pero exclusivamente sobre los deltas de
votos provenientes de resoluciones de actas de escrutinio especial (actas
inconsistentes resueltas). Requiere al menos 10 deltas positivos.

- Umbral de significancia: $p < 0.05$
- Los datos fabricados tienden a evitar digitos 1 (sub-representacion) y
  sobre-representar 5-9.

---

## Referencias / References

- Nigrini, M. J. (2012). *Benford's Law: Applications for Forensic Accounting,
  Auditing, and Fraud Detection*. Wiley.
- Mebane, W. R. (2008). "Election Forensics: The Second-digit Benford's Law
  Test and Recent American Presidential Elections." *Election Fraud*.
