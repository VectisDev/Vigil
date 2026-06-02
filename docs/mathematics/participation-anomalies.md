# Anomalias de Participacion / Participation Anomalies

Documentacion matematica de las reglas que detectan participacion electoral
anomala, turnout imposible, y votos nulos/blancos elevados.

Mathematical documentation for rules detecting anomalous voter turnout,
impossible turnout, and elevated null/blank votes.

**Archivos fuente / Source files:**
- `src/centinel/core/rules/participation_anomaly_rule.py`
- `src/centinel/core/rules/participation_anomaly_advanced_rule.py`
- `src/centinel/core/rules/turnout_impossible_rule.py`
- `src/centinel/core/rules/null_blank_rule.py`

---

## 1. Anomalia de Participacion Basica / Basic Participation Anomaly

**config_key:** `participation_anomaly`
**Severidad / Severity:** High / Medium

### 1.1 Deteccion 1: Actas procesadas exceden totales

$$\text{alerta} \iff A_{\text{procesadas}} > A_{\text{totales}}$$

donde $A$ son conteos de actas (tally sheets).

- **H0:** El conteo de actas procesadas nunca excede el total registrado.
- **H1:** El sistema reporta mas actas procesadas que existentes (error o manipulacion).
- **Severidad:** High. Sin umbral configurable; es una imposibilidad logica.

### 1.2 Deteccion 2: Salto abrupto de escrutinio

$$\Delta_{\text{pct}} = \%_{\text{escrutado}}^{(t)} - \%_{\text{escrutado}}^{(t-1)}$$

$$\text{alerta} \iff \Delta_{\text{pct}} \geq \text{threshold}$$

Porcentaje escrutado se calcula como:

$$\%_{\text{escrutado}} = \frac{A_{\text{procesadas}}}{A_{\text{totales}}} \times 100$$

o se usa el valor directo del payload (`porcentaje_escrutado`).

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `scrutiny_jump_pct` | 5% | Un salto de 5pp en escrutinio entre snapshots es anomalo |

### 1.3 Falsos positivos / False Positives

- Consolidaciones reales al final del conteo pueden saltar porcentajes.
  Mitigacion: la severidad es Medium, no CRITICAL.

---

## 2. Participacion Anomala Avanzada / Advanced Anomalous Participation

**config_key:** `participation_anomaly_advanced`
**Severidad / Severity:** CRITICAL / WARNING

### 2.1 Deteccion 1: Participacion fuera de rango

$$\text{turnout} = \frac{V_{\text{total}}}{R}$$

donde $R$ = votantes registrados (padron).

$$\text{alerta CRITICAL} \iff \text{turnout} < p_{\min} \quad \text{OR} \quad \text{turnout} > p_{\max}$$

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `min_turnout_pct` | 40% | Participacion minima historica en Honduras |
| `max_turnout_pct` | 90% | Participacion maxima plausible |

### 2.2 Deteccion 2: Desviacion historica >3 sigma

$$z = \frac{\text{turnout} - \mu_h}{\sigma_h}$$

donde $\mu_h$ y $\sigma_h$ son media y desviacion estandar historicas del
departamento (o globales si no hay datos departamentales).

$$\text{alerta WARNING} \iff |z| > 3$$

### 2.3 Hipotesis / Hypotheses

- **H0:** La participacion del departamento esta dentro de 3 desviaciones
  estandar de su media historica.
- **H1:** La participacion se desvia mas de 3 sigma, indicando condiciones
  anormales.

### 2.4 Normalizacion / Normalization

Los valores historicos pueden venir como porcentaje (0-100) o proporcion (0-1).
La funcion `_normalize_ratio` convierte automaticamente:

$$\hat{v} = \begin{cases} v / 100 & \text{si } v > 1 \\ v & \text{si } v \leq 1 \end{cases}$$

### 2.5 Falsos positivos / False Positives

- Departamentos con datos historicos insuficientes ($\sigma = 0$) son
  descartados automaticamente.
- La regla 3-sigma es conservadora: solo 0.27% de datos normales caen fuera.

---

## 3. Turnout Imposible / Impossible Turnout

**config_key:** `turnout_impossible`
**Severidad / Severity:** CRITICAL

### 3.1 Formula

$$\text{turnout} = \frac{V_{\text{total}}}{R}$$

$$\text{alerta} \iff \text{turnout} < 0\% \quad \text{OR} \quad \text{turnout} > 100\%$$

### 3.2 Hipotesis / Hypotheses

- **H0:** Los votos emitidos estan entre 0% y 100% del padron.
- **H1:** Los votos exceden los votantes registrados o son negativos.

No es un test estadistico sino una imposibilidad logica. Cero falsos positivos
si el padron es correcto.

---

## 4. Votos Nulos y Blancos Elevados / Elevated Null and Blank Votes

**config_key:** `null_blank_votes`
**Severidad / Severity:** CRITICAL / WARNING

### 4.1 Formula

$$r = \frac{V_{\text{nulos}} + V_{\text{blancos}}}{V_{\text{total}}}$$

### 4.2 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `warning_pct` | 8% | Promedio historico en Honduras es ~2-4%; 8% es anomalo |
| `critical_pct` | 12% | Nivel de alerta maxima; indica posible sabotaje o error sistematico |

### 4.3 Hipotesis / Hypotheses

- **H0:** Los votos nulos+blancos estan dentro de la proporcion historica normal.
- **H1:** La proporcion es anomalamente alta, sugiriendo anulacion masiva de
  votos o error de conteo.

### 4.4 Falsos positivos / False Positives

- Elecciones con muchos candidatos pueden tener tasas naturales de nulos/blancos
  mas altas. Los umbrales son ajustables por configuracion.
