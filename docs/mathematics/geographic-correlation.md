# Dispersion Geografica y Correlacion / Geographic Dispersion and Correlation

Documentacion de las reglas que analizan patrones geograficos y correlaciones
estadisticas entre participacion y voto.

Documentation for rules analyzing geographic patterns and statistical
correlations between turnout and vote share.

**Archivos fuente / Source files:**
- `src/centinel/core/rules/geographic_dispersion_rule.py`
- `src/centinel/core/rules/correlation_participation_vote_rule.py`

---

## 1. Dispersion Geografica / Geographic Dispersion

**config_key:** `geographic_dispersion`
**Severidad / Severity:** CRITICAL

### 1.1 Concepto / Concept

Calcula el coeficiente de variacion (CV) del porcentaje de votos de cada
candidato entre departamentos. Un CV excesivamente bajo indicaria resultados
sospechosamente uniformes (posible fabricacion); un CV excesivamente alto
puede indicar manipulacion focalizada.

### 1.2 Formula

Para cada candidato $c$, sea $s_{c,j}$ su proporcion de votos en el
departamento $j$ ($j = 1, \ldots, D$):

$$\bar{s}_c = \frac{1}{D} \sum_{j=1}^{D} s_{c,j}$$

$$\sigma_c = \sqrt{\frac{1}{D-1} \sum_{j=1}^{D} (s_{c,j} - \bar{s}_c)^2}$$

$$\text{CV}_c = \frac{\sigma_c}{\bar{s}_c}$$

Se usa $\text{ddof}=1$ (desviacion muestral).

### 1.3 Hipotesis / Hypotheses

- **H0:** La variacion del porcentaje de voto entre departamentos es normal
  para el contexto electoral.
- **H1:** La variacion es excesivamente alta ($\text{CV} > \text{threshold}$),
  indicando concentracion o fabricacion regional anomala.

### 1.4 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `critical_cv` | 0.45 | CV > 0.45 indica alta dispersion en preferencia regional; calibrado empiricamente |
| `min_departments` | 5 | Minimo de departamentos para que el CV sea significativo |

### 1.5 Sensibilidad y especificidad / Sensitivity and Specificity

- **Sensibilidad:** Alta para fabricacion concentrada en pocos departamentos.
- **Especificidad:** Moderada. Paises con fuerte polarizacion regional
  (urbano/rural) pueden tener CV naturalmente alto. El umbral de 0.45 es
  conservador para Honduras (18 departamentos).

### 1.6 Falsos positivos / False Positives

| Escenario | Mitigacion |
|-----------|------------|
| Candidatos regionales con base local fuerte | Combinar con otras reglas (Benford, runs test) antes de confirmar anomalia |
| Partidos minoritarios con voto concentrado | Candidatos con menos de 5 departamentos con datos son excluidos |

---

## 2. Correlacion Participacion-Voto / Turnout-Vote Correlation

**config_key:** `participation_vote_correlation`
**Severidad / Severity:** CRITICAL

### 2.1 Concepto / Concept

En una eleccion limpia, la participacion (turnout) en una mesa no deberia
correlacionar fuertemente con el porcentaje del candidato lider. Una
correlacion positiva alta ($r > 0.85$) sugiere ballot stuffing: mas votos
fabricados en una mesa aumentan tanto la participacion como la proporcion del
candidato beneficiado.

### 2.2 Formula: Correlacion de Pearson / Pearson Correlation

Para cada mesa $i$ con participacion $x_i$ y proporcion del lider $y_i$:

$$r = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i - \bar{x})^2 \cdot \sum_{i=1}^{n}(y_i - \bar{y})^2}}$$

donde:

$$x_i = \frac{V_{\text{total},i}}{R_i} \quad \text{(turnout por mesa)}$$

$$y_i = \frac{V_{\text{lider},i}}{V_{\text{validos},i}} \quad \text{(proporcion del lider por mesa)}$$

Se usa `scipy.stats.pearsonr` que retorna $(r, p\text{-value})$.

### 2.3 Hipotesis / Hypotheses

- **H0:** No existe correlacion significativa entre participacion y proporcion
  del candidato lider ($\rho = 0$).
- **H1:** Existe correlacion espuria positiva ($|r| > 0.85$), indicando
  posible inyeccion coordinada de votos (ballot stuffing).

### 2.4 Umbrales / Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `critical_r` | 0.85 | Correlacion fuerte; r=0.85 explica ~72% de la varianza. En elecciones limpias, r tipicamente esta entre -0.2 y 0.3 |
| `min_samples` | 30 | Minimo de mesas con datos completos (turnout + votos lider) |

### 2.5 Interpretacion / Interpretation

| Rango de \|r\| | Interpretacion |
|----------------|----------------|
| 0.0 - 0.3 | Correlacion debil -- normal |
| 0.3 - 0.5 | Correlacion moderada -- investigar contexto |
| 0.5 - 0.7 | Correlacion fuerte -- sospechosa |
| 0.7 - 0.85 | Correlacion muy fuerte -- requiere explicacion |
| > 0.85 | Correlacion anomala -- alerta CRITICAL |

### 2.6 Sensibilidad y especificidad / Sensitivity and Specificity

- **Sensibilidad:** Alta para ballot stuffing clasico (votos fabricados
  uniformemente en mesas afectadas).
- **Especificidad:** El umbral de 0.85 es alto para reducir falsos positivos.
  Correlaciones naturales por factores sociodemograficos raramente exceden 0.5.

### 2.7 Falsos positivos / False Positives

| Escenario | Mitigacion |
|-----------|------------|
| Zonas con alta participacion que naturalmente favorecen al lider | El umbral de 0.85 es muy alto; correlaciones naturales son < 0.5 |
| Mesas con pocos votantes registrados (alta varianza) | `min_samples=30` filtra datasets insuficientes |
| Correlacion negativa (lider pierde con mas participacion) | La regla usa `abs(r)` |

---

## 3. Referencia bibliografica / Bibliographic Reference

- Klimek, P., Yegorov, Y., Hanel, R., & Thurner, S. (2012). "Statistical
  detection of systematic election irregularities." *PNAS*, 109(41),
  16469-16473. (Scatter plots participacion-voto como diagnostico.)
- Myagkov, M., Ordeshook, P. C., & Shakin, D. (2009). *The Forensics of
  Election Fraud: Russia and Ukraine*. Cambridge University Press.
