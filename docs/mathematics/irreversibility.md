# Irreversibilidad Estadistica / Statistical Irreversibility

Documentacion matematica de la regla de deteccion de irreversibilidad en
conteos electorales.

Mathematical documentation for vote-count irreversibility detection.

**Archivo fuente / Source file:** `src/centinel/core/rules/irreversibility_rule.py`
**config_key:** `irreversibility`
**Severidad / Severity:** High

---

## 1. Concepto / Concept

Un resultado electoral es "estadisticamente irreversible" cuando la brecha
entre el lider y el segundo lugar supera el maximo de votos que aun pueden
emitirse, dado un nivel de participacion proyectado. Si un resultado
previamente declarado irreversible se revierte en un snapshot posterior,
esto constituye evidencia de manipulacion del universo de actas.

An electoral result is "statistically irreversible" when the gap between
the leader and the runner-up exceeds the maximum votes still available,
given a projected participation rate.

---

## 2. Formula / Formula

### 2.1 Votos faltantes proyectados / Projected remaining votes

$$V_{\text{remaining}} = \max\left( \lfloor R \cdot p_h \rfloor - V_{\text{total}},\ 0 \right)$$

donde:
- $R$ = votantes registrados (padron electoral)
- $p_h$ = tasa de participacion historica (default: 0.60)
- $V_{\text{total}}$ = votos emitidos en el snapshot actual

### 2.2 Brecha y condicion de irreversibilidad / Gap and irreversibility condition

$$\text{gap} = |V_{\text{lider}} - V_{\text{segundo}}|$$

$$\text{irreversible} \iff (\text{gap} + 1) > V_{\text{remaining}}$$

El "+1" es porque el segundo necesitaria alcanzar y superar al lider.

### 2.3 Deteccion de fraude por reversion / Fraud detection by reversal

Si en un snapshot anterior el estado era irreversible (almacenado en SQLite)
y en el snapshot actual:
- El resultado deja de ser irreversible, O
- El lider cambio de identidad

Entonces se genera alerta de **Fraude Confirmado por Manipulacion de Universo
de Actas**.

---

## 3. Hipotesis / Hypotheses

- **H0:** El resultado actual se mantendra con participacion historica normal;
  la tendencia de votos faltantes no alterara el liderazgo.
- **H1:** La brecha se revirtio despues de declararse irreversible, lo cual
  requiere votos no explicados por el padron proyectado.

---

## 4. Umbrales por defecto / Default Thresholds

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `historical_participation_rate` | 0.60 | Tasa de participacion tipica en Honduras (ultimas 3 elecciones) |
| `sqlite_path` | `reports/irreversibility_state.db` | Persistencia de estado entre ejecuciones |

### 4.1 Nota sobre la tasa de participacion

El valor 0.60 es conservador: asume que el 60% del padron votara. Si la
participacion real es mayor, los votos faltantes reales son mayores, haciendo
la irreversibilidad mas dificil de alcanzar (umbral mas exigente). Esto
reduce falsos positivos de irreversibilidad prematura.

---

## 5. Sensibilidad y especificidad / Sensitivity and Specificity

- **Sensibilidad:** Alta para detectar reversiones de resultados previamente
  irreversibles. La persistencia en SQLite permite deteccion entre ejecuciones.
- **Especificidad:** La tasa de participacion conservadora (60%) evita
  declarar irreversibilidad prematuramente.

---

## 6. Falsos positivos y mitigaciones / False Positives and Mitigations

| Escenario | Mitigacion |
|-----------|------------|
| Participacion real muy superior a 60% | La irreversibilidad solo se declara con la tasa configurada; ajustar `historical_participation_rate` |
| Errores de transmision que bajan votos temporalmente | La alerta de reversion requiere que el estado previo haya sido guardado como irreversible |
| Cambios de lider por correccion de datos | La alerta diferencia entre cambio de lider y cambio de estado; ambos generan alerta separada |

---

## 7. Persistencia de estado / State Persistence

La regla usa SQLite para almacenar el estado por scope (departamento):
- `leader`: ID del lider actual
- `irreversible`: flag booleano
- `timestamp`: marca temporal del ultimo calculo

Esto permite comparar entre snapshots no contiguos y sobrevivir reinicios
del proceso.
