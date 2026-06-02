# Deteccion de Outliers con ML / ML-Based Outlier Detection

Documentacion del metodo de deteccion de outliers basado en Isolation Forest
para cambios relativos de votos entre snapshots.

Documentation for the Isolation Forest-based outlier detection method for
relative vote changes between snapshots.

**Archivo fuente / Source file:** `src/centinel/core/rules/ml_outliers_rule.py`
**config_key:** `ml_outliers`
**Severidad / Severity:** Medium

---

## 1. Concepto / Concept

La regla calcula el cambio porcentual de votos totales entre snapshots
consecutivos y lo incorpora a una serie historica por departamento. Con
suficientes puntos, se entrena un modelo Isolation Forest para identificar
cambios atipicos.

The rule computes the percentage change in total votes between consecutive
snapshots and stores it in a per-department history. With enough data points,
an Isolation Forest model flags abnormal jumps.

---

## 2. Preparacion de datos / Data Preparation

### 2.1 Cambio relativo porcentual

$$\delta_{\%} = \frac{V_{\text{total}}^{(t)} - V_{\text{total}}^{(t-1)}}{V_{\text{total}}^{(t-1)}} \times 100$$

### 2.2 Serie historica

Los valores $\delta_{\%}$ se almacenan en SQLite por departamento,
manteniendo las ultimas `max_history` observaciones (default: 200).

---

## 3. Isolation Forest / Isolation Forest

### 3.1 Principio / Principle

Isolation Forest (Liu et al., 2008) aisla anomalias en vez de perfilar datos
normales. La intuicion es que los outliers son pocos y diferentes, por lo que
se aislan con menos particiones aleatorias.

### 3.2 Algoritmo simplificado / Simplified Algorithm

1. Construir un ensemble de arboles de aislamiento (iTree).
2. En cada nodo, seleccionar aleatoriamente un atributo y un punto de corte.
3. Repetir recursivamente hasta que cada observacion quede aislada.
4. La longitud promedio del camino $E(h(x))$ para cada observacion determina
   su anomaly score:

$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$

donde $c(n)$ es la longitud promedio de camino en un BST no exitoso
(Binary Search Tree) con $n$ nodos:

$$c(n) = 2H(n-1) - \frac{2(n-1)}{n}$$

y $H(i)$ es el $i$-esimo numero armonico.

- $s \approx 1$: anomalia (camino corto)
- $s \approx 0.5$: punto normal (camino promedio)
- $s < 0.5$: punto seguro

### 3.3 Parametros de implementacion / Implementation Parameters

El modelo se entrena con `sklearn.ensemble.IsolationForest`:

| Parametro | Valor | Justificacion |
|-----------|-------|---------------|
| `contamination` | 0.1 | Proporcion esperada de anomalias (10%); conservador para datos electorales |
| `random_state` | 42 | Reproducibilidad entre ejecuciones |
| `min_samples` | 5 | Minimo de observaciones historicas antes de entrenar |
| `max_history` | 200 | Ventana historica maxima por departamento |

### 3.4 Decision

La prediccion del modelo para el punto mas reciente determina la alerta:

$$\text{alerta} \iff \text{predict}(\delta_{\%}^{(t)}) = -1$$

El valor -1 indica outlier segun el modelo.

---

## 4. Hipotesis / Hypotheses

- **H0:** El cambio porcentual actual es consistente con el patron historico
  de cambios del departamento.
- **H1:** El cambio porcentual es un outlier estadistico, indicando un
  evento anomalo (inyeccion, error, o manipulacion).

---

## 5. Sensibilidad y especificidad / Sensitivity and Specificity

- **Sensibilidad:** Mejora con mas datos historicos. Con `min_samples=5`,
  la deteccion temprana es limitada pero se activa rapido.
- **Especificidad:** `contamination=0.1` espera 10% de outliers, lo cual
  puede generar falsos positivos si los datos son todos normales. Esto es
  intencional: la regla tiene severidad Medium para review humano.

---

## 6. Falsos positivos y mitigaciones / False Positives and Mitigations

| Escenario | Mitigacion |
|-----------|------------|
| Pocos datos historicos (< 5 puntos) | La regla no se activa |
| Todos los cambios son similares (baja varianza) | Isolation Forest detecta correctamente cualquier desviacion |
| Cambios legitimamente grandes al inicio del conteo | La serie historica se adapta; cambios iniciales amplios se incorporan como baseline |
| sklearn no disponible | La regla retorna lista vacia con log warning |

---

## 7. Persistencia / Persistence

La historia se persiste en SQLite (`reports/ml_outliers_history.db` por
defecto) con esquema:

```
CREATE TABLE ml_history (
    department TEXT NOT NULL,
    seq INTEGER NOT NULL,
    value REAL NOT NULL,
    PRIMARY KEY (department, seq)
)
```

Las entradas mas antiguas se eliminan automaticamente al superar `max_history`.

---

## 8. Limitaciones / Limitations

- Unidimensional: solo usa el cambio porcentual total, no patrones
  multivariados (por candidato, por tipo de voto).
- No adaptativo: el modelo se reentrena en cada invocacion con toda la
  historia. Para series muy largas, considerar sliding window.
- Dependencia de sklearn: si no esta instalado, la regla se desactiva
  silenciosamente.

---

## 9. Referencias / References

- Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). "Isolation Forest."
  *Proc. ICDM 2008*, pp. 413-422.
- scikit-learn documentation: `sklearn.ensemble.IsolationForest`.
