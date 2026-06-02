# Deteccion Forense de Actas Inconsistentes / Forensic Inconsistent-Acts Detection

Documentacion de los metodos estadisticos y heuristicos del modulo forense
de actas inconsistentes de Centinel.

Documentation for the statistical and heuristic methods in Centinel's forensic
inconsistent-acts module.

**Archivo fuente / Source file:** `src/auditor/inconsistent_acts.py`
(clase `InconsistentActsTracker`)

---

## 1. Inyeccion Progresiva Controlada / Progressive Controlled Injection

### 1.1 Concepto / Concept

Detecta inyecciones sostenidas de bajo volumen de votos mientras la cola de
actas inconsistentes permanece alta. El patron es: mantener un backlog alto de
actas "pendientes" mientras se infiltran votos en lotes pequenos para evitar
deteccion por reglas de salto.

### 1.2 Condiciones de activacion / Trigger Conditions

$$\text{activar} \iff A_{\text{inconsistentes}} > T_{\text{high}} \quad \text{AND} \quad \Delta V < T_{\text{injection}}$$

donde:
- $T_{\text{high}}$ = `high_inconsistent_threshold` (default: 1000)
- $T_{\text{injection}}$ = `progressive_injection_threshold` (default: 800)

Se requieren al menos `min_consecutive_injections` (default: 5) ciclos
consecutivos cumpliendo estas condiciones.

### 1.3 Pruebas estadisticas / Statistical Tests

#### Z-score acumulativo contra linea base dinamica

$$z = \frac{\sum_{i=1}^{k} \delta_i - k \cdot \bar{\delta}_{\text{baseline}}}{\sigma_{\text{baseline}} \cdot \sqrt{k}}$$

$$p\text{-value} = 2 \cdot (1 - \Phi(|z|))$$

donde la baseline se calcula con los eventos historicos previos al periodo
de inyeccion.

#### Runs test (Wald-Wolfowitz) sobre deltas

Se binariza la secuencia de deltas por mediana y se aplica el runs test
(misma formula que en `statistical-tests.md` seccion 1).

- Umbral: `run_test_pvalue_threshold` (default: 0.05)

#### Autocorrelacion lag-1

$$r_1 = \frac{\sum_{i=1}^{n-1}(x_i - \bar{x})(x_{i+1} - \bar{x})}{\sqrt{\sum_{i=1}^{n-1}(x_i - \bar{x})^2 \cdot \sum_{i=2}^{n}(x_i - \bar{x})^2}}$$

Valores $r_1 > 0.5$ indican persistencia no aleatoria en los deltas.

#### Varianza de micro-deltas

Si $k \geq 5$ ciclos consecutivos tienen varianza $< 1.0$, los deltas son
practicamente identicos -- imposible en un proceso estocastico real.

### 1.4 Decision combinada / Combined Decision

$$\text{detectado} \iff z_p < 0.01 \quad \text{OR} \quad p_{\text{runs}} < 0.05 \quad \text{OR} \quad (\text{var} < 1.0 \text{ con } k \geq 5)$$

### 1.5 Hipotesis / Hypotheses

- **H0:** Los deltas de votos entre snapshots son variaciones aleatorias del
  proceso de conteo normal.
- **H1:** Los deltas muestran un patron de inyeccion controlada: baja
  varianza, alta autocorrelacion, y/o no aleatoriedad en rachas.

---

## 2. Velocidad de Resolucion Anomala / Anomalous Resolution Velocity

### 2.1 Formula

$$r = \frac{\Delta A_{\text{inconsistentes}}}{\Delta t_{\text{min}}}$$

### 2.2 Condicion de alerta / Alert Condition

$$\text{alerta} \iff r > r_{\max}$$

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `max_resolution_rate` | 10 actas/min | Un comite de escrutinio especial revisa ~2-3 actas/min por mesa (lectura de votos, verificacion de firmas, cotejo con copias de partidos) |

---

## 3. Beneficio Asimetrico / Asymmetric Benefit

### 3.1 Concepto / Concept

Compara la distribucion de votos en actas de escrutinio especial vs actas
normales. Si un candidato recibe una proporcion significativamente mayor en
escrutinio especial, indica sesgo dirigido.

### 3.2 Formula

Swing en puntos porcentuales:

$$\text{swing}_c = \hat{p}_{c,\text{especial}} - \hat{p}_{c,\text{normal}}$$

Test z de dos proporciones:

$$z = \frac{\hat{p}_{\text{especial}} - \hat{p}_{\text{normal}}}{\sqrt{\hat{p}_{\text{pool}}(1 - \hat{p}_{\text{pool}})\left(\frac{1}{n_{\text{especial}}} + \frac{1}{n_{\text{normal}}}\right)}}$$

donde:

$$\hat{p}_{\text{pool}} = \frac{V_{c,\text{especial}} + V_{c,\text{normal}}}{n_{\text{especial}} + n_{\text{normal}}}$$

Votos extra estimados:

$$V_{\text{extra}} = \lfloor \text{swing}_{\max} \cdot n_{\text{especial}} \rfloor$$

### 3.3 Hipotesis / Hypotheses

- **H0:** La distribucion de votos en escrutinio especial es igual a la
  distribucion en actas normales.
- **H1:** Existe un beneficio desproporcionado para un candidato en las
  actas de escrutinio especial ($p < 0.01$).

### 3.4 Umbral de swing minimo / Minimum Swing Threshold

Se descarta si el swing maximo es < 2pp (0.02 en proporcion), para evitar
alertas por fluctuaciones naturales.

---

## 4. Patron Hold-and-Release / Hold-and-Release Pattern

### 4.1 Concepto / Concept

Se detiene el procesamiento de actas inconsistentes ("hold") durante
multiples ciclos de monitoreo, seguido de una liberacion masiva ("release"),
tipicamente en horarios de baja vigilancia.

### 4.2 Condiciones / Conditions

$$\text{alerta} \iff \begin{cases}
\text{ciclos\_estancamiento} \geq T_{\text{stagnation}} \\
\Delta A > 0 \\
\text{es\_resolucion\_masiva}
\end{cases}$$

| Parametro | Valor |
|-----------|-------|
| `stagnation_cycles_threshold` | 6 ciclos |
| `bulk_resolution_threshold` | 300 actas |

### 4.3 Hipotesis / Hypotheses

- **H0:** Las variaciones en la tasa de resolucion son normales (turnos de
  trabajo, horarios).
- **H1:** El estancamiento prolongado seguido de resolucion masiva indica
  coordinacion para manipular el conteo durante periodos de baja vigilancia.

---

## 5. Benford sobre Escrutinio Especial / Benford on Special Scrutiny

Ver seccion 5 en [benford-analysis.md](benford-analysis.md).

Se aplica chi-cuadrado sobre primeros digitos de deltas de votos provenientes
exclusivamente de resoluciones de actas inconsistentes.

- Minimo: 10 deltas positivos
- Significancia: $p < 0.05$

---

## 6. Ventanas de Apagon Comunicacional / Communication Blackout Windows

### 6.1 Concepto / Concept

Un apagon es un gap temporal inusualmente largo entre snapshots consecutivos.
Si despues del gap la tendencia de un candidato cambia significativamente,
esto indica que durante el apagon se alteraron datos.

### 6.2 Deteccion / Detection

$$\text{gap} = t^{(i)} - t^{(i-1)}$$

$$\text{es\_apagon} \iff \text{gap} \geq T_{\text{blackout}}$$

| Parametro | Valor |
|-----------|-------|
| `blackout_gap_minutes` | 30 minutos |

### 6.3 Cambios de tendencia post-apagon / Post-blackout Trend Shifts

Para cada candidato:

$$\text{shift}_c = \frac{V_c^{(\text{post})}}{V_{\text{total}}^{(\text{post})}} - \frac{V_c^{(\text{pre})}}{V_{\text{total}}^{(\text{pre})}}$$

Se reporta si $|\text{shift}_c| > 0.005$ (0.5pp).

### 6.4 Hipotesis / Hypotheses

- **H0:** Los gaps entre snapshots son pausas normales del sistema de
  transmision.
- **H1:** El gap fue aprovechado para introducir cambios en los datos que
  alteran la tendencia.

---

## 7. Pruebas Estadisticas Consolidadas / Consolidated Statistical Tests

El metodo `run_statistical_tests()` ejecuta un suite completo:

### 7.1 Chi-cuadrado de bondad de ajuste

$$\chi^2 = \sum_c \frac{(V_{c,\text{especial}} - E_c)^2}{E_c}$$

donde $E_c = n_{\text{especial}} \cdot \hat{p}_{c,\text{nacional}}$.

### 7.2 Test binomial exacto por candidato

Para cada candidato $c$:

$$\text{binomtest}(k = V_{c,\text{especial}},\ n = n_{\text{especial}},\ p_0 = \hat{p}_{c,\text{nacional}})$$

Con correccion de Bonferroni:

$$p_{\text{ajustado}} = \min(p_{\text{exacto}} \cdot m,\ 1.0)$$

donde $m$ es el numero de candidatos testeados.

### 7.3 Intervalo de confianza 95% (aproximacion normal)

$$\text{CI}_{95} = \hat{p} \pm 1.96 \cdot \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$$

### 7.4 Potencia aproximada del test de dos proporciones

$$\text{SE} = \sqrt{\frac{p_1(1-p_1)}{n_1} + \frac{p_2(1-p_2)}{n_2}}$$

$$\text{poder} = 1 - \Phi\left(z_{\alpha/2} - \frac{|p_1 - p_2|}{\text{SE}}\right)$$

---

## 8. Deteccion de Anomalias 3-Sigma / 3-Sigma Anomaly Detection

El metodo `detect_anomalies()` incluye outlier detection sobre deltas de votos
de escrutinio especial:

$$\text{umbral} = \bar{\delta} + 3\sigma_{\delta}$$

$$\text{outlier} \iff \delta_i > \text{umbral}$$

donde $\bar{\delta}$ y $\sigma_{\delta}$ son media y desviacion de los deltas
de votos en eventos de resolucion.
