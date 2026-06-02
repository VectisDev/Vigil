# Velocidad de Procesamiento / Processing Speed Anomalies

Documentacion matematica de la regla de deteccion de velocidades de
procesamiento anomalas en actas electorales.

Mathematical documentation for the processing speed anomaly detection rule.

**Archivo fuente / Source file:** `src/centinel/core/rules/processing_speed_rule.py`
**config_key:** `processing_speed`
**Severidad / Severity:** High

---

## 1. Concepto / Concept

El procesamiento de actas electorales es un proceso fisico: apertura de
sobres, lectura de votos, verificacion de firmas, digitacion. Existe un
limite superior plausible de actas que un centro puede procesar por unidad
de tiempo. Si la tasa observada excede este limite, el procesamiento
probablemente es automatizado o los datos son inyectados.

The processing of tally sheets is a physical process. There is an upper
plausible limit of sheets a center can process per time unit. If the
observed rate exceeds this limit, the processing is likely automated or
the data is being injected.

---

## 2. Formula / Formula

### 2.1 Tasa de procesamiento normalizada / Normalized processing rate

$$\Delta A = A_{\text{procesadas}}^{(t)} - A_{\text{procesadas}}^{(t-1)}$$

$$\Delta t_{\text{min}} = \frac{(t_{\text{actual}} - t_{\text{previo}})}{60} \quad \text{(en minutos)}$$

$$r_{15} = \frac{\Delta A}{\Delta t_{\text{min}}} \times 15$$

donde $r_{15}$ es la tasa normalizada a una ventana de 15 minutos.

### 2.2 Condicion de alerta / Alert Condition

$$\text{alerta} \iff r_{15} > r_{\max}$$

---

## 3. Hipotesis / Hypotheses

- **H0:** La velocidad de procesamiento es compatible con un proceso humano
  de conteo y digitacion.
- **H1:** La velocidad excede la capacidad fisica humana, indicando carga
  automatizada o inyeccion de datos.

---

## 4. Umbrales por defecto / Default Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `max_actas_per_15min` | 500 | Equivale a ~33 actas/minuto. Un operador procesa 1-2 actas/min; 500/15min implica ~16 operadores simultaneos procesando sin pausa, lo cual es el limite superior plausible |

### 4.1 Calculo de referencia / Reference Calculation

- Velocidad humana individual: 1-2 actas/minuto
- 500 actas en 15 minutos = 33.3 actas/minuto
- Esto requiere ~17-33 operadores simultaneos trabajando sin pausa
- Un centro de escrutinio tipico tiene 3-8 mesas de trabajo

---

## 5. Sensibilidad y especificidad / Sensitivity and Specificity

- **Sensibilidad:** Alta para inyeccion masiva de datos. Baja para
  inyecciones graduales que se mantienen bajo el umbral.
- **Especificidad:** El umbral de 500/15min es conservador; centros grandes
  con muchas mesas pueden alcanzarlo legitimamente. Ajustar segun contexto.

---

## 6. Falsos positivos y mitigaciones / False Positives and Mitigations

| Escenario | Mitigacion |
|-----------|------------|
| Consolidacion de datos retrasados que llegan en lote | Combinar con `snapshot_jump_rule` para confirmar patron |
| Centro de conteo muy grande con muchas mesas | Ajustar `max_actas_per_15min` por centro si se tiene informacion de capacidad |
| Errores de timestamp (snapshots con timestamps incorrectos) | La regla requiere `delta_minutes > 0` para evitar division por cero |

---

## 7. Relacion con velocidad forense / Relationship with Forensic Velocity

El modulo forense `inconsistent_acts.py` implementa una deteccion similar pero
para resoluciones de actas inconsistentes (no para procesamiento general):

$$r_{\text{resolucion}} = \frac{\Delta A_{\text{inconsistentes}}}{\Delta t_{\text{min}}}$$

con umbral default de 10 actas/minuto (mas estricto porque la resolucion
de actas inconsistentes es un proceso mas lento que requiere revision manual
completa).
