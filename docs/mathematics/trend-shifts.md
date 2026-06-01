# Deteccion de Cambios de Tendencia / Trend Shift Detection

Documentacion matematica de las reglas que detectan cambios abruptos en la
tendencia del voto entre snapshots consecutivos.

Mathematical documentation for rules detecting abrupt voting trend changes
between consecutive snapshots.

**Archivos fuente / Source files:**
- `src/centinel/core/rules/trend_shift_rule.py`
- `src/centinel/core/rules/snapshot_jump_rule.py`
- `src/centinel/core/rules/granular_anomaly_rule.py` (cambio porcentual brusco, reversion de liderazgo)

---

## 1. Desviacion de Tendencia / Trend Deviation

**config_key:** `trend_shift`
**Severidad / Severity:** High

### 1.1 Metodo / Method

Compara el porcentaje de votos nuevos (delta) por candidato contra su
porcentaje historico acumulado.

### 1.2 Formula

Para cada candidato $c$ entre dos snapshots $t-1$ y $t$:

$$\Delta V_c = V_c^{(t)} - V_c^{(t-1)}$$

$$\Delta V_{\text{total}} = \sum_c \Delta V_c$$

Porcentaje del delta:

$$\delta_c = \frac{\Delta V_c}{\Delta V_{\text{total}}} \times 100 \quad (\text{si } \Delta V_c > 0)$$

Porcentaje historico acumulado:

$$h_c = \frac{V_c^{(t)}}{\sum_c V_c^{(t)}} \times 100$$

Diferencia:

$$\text{diff}_c = |\delta_c - h_c|$$

### 1.3 Hipotesis / Hypotheses

- **H0:** Los votos nuevos entre snapshots mantienen la misma distribucion
  porcentual que el acumulado historico.
- **H1:** El porcentaje de votos nuevos de algun candidato se desvia
  significativamente de su tendencia historica.

### 1.4 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `threshold_percent` | 10% | Diferencia minima en puntos porcentuales para alertar |
| `max_hours` | 3 | Ventana temporal maxima entre snapshots (descarta gaps largos) |

### 1.5 Sensibilidad y especificidad / Sensitivity and Specificity

- **Sensibilidad:** Alta para inyecciones de votos concentradas en un candidato.
- **Especificidad:** El filtro temporal (`max_hours`) y el umbral de 10pp
  reducen falsos positivos por conteos rurales de ultimo momento.

### 1.6 Falsos positivos / False Positives

- Conteos parciales tempranos con pocos votos pueden generar deltas porcentuales
  grandes. Mitigacion: la regla requiere `delta_total > 0` y aplica solo en
  ventanas <= 3 horas.
- Departamentos con fuerte preferencia local pueden mostrar deltas legitimamente
  distintos del promedio nacional.

---

## 2. Saltos entre Snapshots / Snapshot Jumps

**config_key:** `snapshot_jump`
**Severidad / Severity:** CRITICAL

### 2.1 Formula

$$\text{change\_pct} = \frac{V_{\text{total}}^{(t)} - V_{\text{total}}^{(t-1)}}{V_{\text{total}}^{(t-1)}}$$

### 2.2 Condicion de alerta / Alert Condition

$$|\text{change\_pct}| > \text{threshold} \quad \text{AND} \quad \Delta t \leq \text{max\_minutes}$$

### 2.3 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `max_change_pct` | 5% | Cambio maximo plausible en una ventana corta |
| `max_minutes` | 10 | Ventana de tiempo (snapshots cercanos a < 10 min) |

Un cambio de >5% del total de votos en 10 minutos es fisicamente implausible
en un proceso manual de conteo.

---

## 3. Cambio Porcentual Brusco por Departamento / Abrupt Percentage Change

**Fuente / Source:** `granular_anomaly_rule.py`
**Severidad / Severity:** High

Misma logica que snapshot jumps pero aplicada por departamento y nivel
electoral, con parametros:

| Parametro | Valor |
|-----------|-------|
| `delta_pct_alert` | 3.0% |
| `delta_pct_time_window_minutes` | 30 min |

---

## 4. Reversion de Liderazgo / Leadership Reversal

**Fuente / Source:** `granular_anomaly_rule.py`
**Severidad / Severity:** High

Detecta cambio de lider en un departamento cuando el lider previo tenia
un margen significativo y perdio votos:

$$\text{alerta} \iff \begin{cases}
\text{lider\_prev} \neq \text{lider\_actual} \\
\text{margen\_prev} \geq 500 \\
\Delta V_{\text{lider\_prev}} \leq -100 \\
\Delta t \leq 30 \text{ min}
\end{cases}$$

Esto combina tres condiciones: cambio de lider, margen previo significativo,
y perdida neta de votos del lider previo en ventana corta.
