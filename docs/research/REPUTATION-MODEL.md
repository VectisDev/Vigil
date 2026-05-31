# Centinel Swarm: Modelo de Reputación Bayesiana Persistente para Redes P2P de Auditoría Electoral

**Documento técnico para revisión académica**

**Autores:** Carlos Zelaya (Proyecto Centinel) · PhD Devis Alvarado (UPNFM) *(co-revisión)*

**Fecha:** 31 de mayo de 2026 · Versión 1.0

**Clasificación:** Confidencial — uso interno del proyecto Centinel

---

## Resumen ejecutivo

Centinel es un sistema de auditoría electoral distribuida que opera sobre datos públicos del CNE de Honduras. Sus nodos intercambian attestaciones criptográficas mediante un protocolo gossip para detectar inconsistencias en los resultados publicados. Este documento describe el **Modelo de Reputación Bayesiana Persistente (PBTM, Persistent Bayesian Trust Model)** que gobierna cómo los nodos del swarm evalúan la confiabilidad de sus pares, resistiendo ataques Sybil y distinguiendo fallos benignos (cortes eléctricos) de traiciones deliberadas (datos manipulados).

---

## 1. Motivación y Problema Formal

### 1.1 Contexto

Durante las elecciones generales de Honduras (2025), el servidor del CNE publicó snapshots JSON de resultados parciales cada 5–15 minutos. Múltiples instancias de Centinel monitorearon estos datos en paralelo. El problema central es: **¿cómo decide un nodo a cuál de sus pares creerle cuando existe discrepancia?**

### 1.2 Definición del problema

Sea $\mathcal{N} = \{n_1, n_2, \ldots, n_k\}$ el conjunto de nodos activos en el swarm, con $k \leq 12$. Cada nodo $n_i$ publica periódicamente un **attestation**:

$$a_i(t) = \langle \texttt{node\_id}_i,\ \texttt{merkle\_root}_i(t),\ \texttt{chain\_length}_i(t),\ \texttt{timestamp}_i(t),\ \sigma_i \rangle$$

donde $\sigma_i = \text{Ed25519}(\text{SHA-256}(a_i \setminus \sigma_i),\ sk_i)$ es la firma Ed25519 del nodo con su clave privada.

El problema es determinar un **trust score** $\tau_{ij} \in [0,1]$ para cada par $(n_i, n_j)$, de modo que los nodos de mayor confianza tengan más peso en el consenso y los nodos maliciosos sean degradados antes de que puedan influir en las decisiones del swarm.

---

## 2. Modelo Matemático: Distribución Beta

### 2.1 Fundamento estadístico

Modelamos la confianza de un nodo $n_j$ como la probabilidad de que su próxima acción sea honesta, dado su historial pasado. Esta probabilidad es una variable aleatoria $\tau_j \in [0,1]$.

Usamos la **distribución Beta** como prior conjugado para una proporción binaria:

$$\tau_j \sim \text{Beta}(\alpha_j, \beta_j)$$

La media posterior (estimador Laplace-smoothed) es:

$$\boxed{\hat{\tau}_j = \frac{\alpha_j + 1}{\alpha_j + \beta_j + 2}}$$

**Interpretación:**
- $\alpha_j$: evidencia acumulada de comportamiento **consistente** (honesto)
- $\beta_j$: evidencia acumulada de comportamiento **inconsistente** (sospechoso o malicioso)
- **Prior neutro:** $(\alpha_j, \beta_j) = (1, 1)$ → $\hat{\tau}_j = 0.5$ (beneficio de la duda)

### 2.2 Regla de actualización

En cada interacción verificable entre $n_i$ y $n_j$:

$$\alpha_j \leftarrow \alpha_j + \Delta\alpha \quad\text{(si consistente)}$$
$$\beta_j \leftarrow \beta_j + \Delta\beta \quad\text{(si inconsistente)}$$

Los valores de $\Delta$ están calibrados asimétricamente:

| Evento | Parámetro afectado | Magnitud | Justificación |
|--------|-------------------|----------|---------------|
| Fingerprint consistente con Ring-0 | $\alpha_j \mathrel{+}= 1.0$ | Moderada | Una confirmación no es prueba definitiva |
| Anomalía corroborada por otros nodos | $\alpha_j \mathrel{+}= 2.0$ | Alta | Múltiple evidencia independiente |
| Corte eléctrico (timeout, reversible) | $\beta_j \mathrel{+}= 0.1$ | Mínima | El nodo podría ser honesto |
| Datos divergentes confirmados | $\beta_j \mathrel{+}= 5.0$ | Severa | Traición verificada, penalización seria |

**Nota:** La asimetría $\Delta\beta_\text{traición} / \Delta\alpha_\text{consistencia} = 5.0$ refleja el principio de diseño: *una traición detectada pesa 5 veces más que una contribución positiva*, pero se requieren aproximadamente $n$ contribuciones positivas para recuperar la confianza tras $n/5$ traiciones.

### 2.3 Decaimiento temporal (half-life)

La evidencia histórica pierde peso con el tiempo. Definimos un decaimiento exponencial con semivida diferenciada:

$$\alpha_j(t) \leftarrow \alpha_j(t_0) \cdot 2^{-\Delta t / T_\alpha}$$
$$\beta_j(t) \leftarrow \beta_j(t_0) \cdot 2^{-\Delta t / T_\beta}$$

Con parámetros:

$$T_\alpha = 14 \text{ días}, \quad T_\beta = 30 \text{ días}$$

**Justificación de la asimetría temporal:** La buena conducta pasada se olvida más rápido ($T_\alpha < T_\beta$) porque el contexto cambia: un nodo honesto podría ser comprometido. La mala conducta persiste más en la memoria del swarm ($T_\beta > T_\alpha$) porque las traiciones confirman una capacidad de actuar maliciosamente que no desaparece rápidamente.

---

## 3. Trust Rings: Jerarquía de Confianza

### 3.1 Definición

El swarm se organiza en tres anillos de confianza, análogos a los Web of Trust de PGP pero basados en evidencia comportamental en lugar de certificación social:

| Nivel | Nombre | Condición de ingreso | Condición de degradación |
|-------|--------|---------------------|------------------------|
| **Ring-0** | Semilla | Designación manual por el operador | Nunca automático |
| **Ring-1** | Confiable | $\hat{\tau}_j \geq 0.85$ sostenido | $\hat{\tau}_j < 0.40$ |
| **Ring-2** | Observador | Estado inicial de todo nodo nuevo | — |

### 3.2 Implicaciones operacionales

- Los nodos **Ring-0** sirven como **ancla de verdad**: sus fingerprints son la referencia contra la cual se mide la consistencia de todos los demás.
- Los nodos **Ring-1** reciben los hallazgos antes en el fan-out del gossip (prioridad de propagación).
- Los nodos **Ring-2** contribuyen al consenso pero con menor peso en la votación del Merkle root.

### 3.3 Propiedad de estabilidad

**Teorema informal:** Un nodo honesto que interactúa consistentemente con Ring-0 alcanza Ring-1 en $n^*$ interacciones. Despejando $\hat{\tau} \geq \tau^*$ con $\alpha = \alpha_0 + n^* \Delta\alpha$:

$$n^* = \left\lceil \frac{\tau^*(2 + \beta_0) - (1 - \tau^*)\alpha_0 - 1}{\Delta\alpha (1 - \tau^*)} \right\rceil$$

Con prior $(\alpha_0, \beta_0) = (1,1)$, objetivo $\tau^* = 0.85$, $\Delta\alpha = 1.0$:

$$n^* = \left\lceil \frac{0.85 \cdot 4 - 1}{0.15} \right\rceil = \left\lceil \frac{2.4}{0.15} \right\rceil = \lceil 16 \rceil$$

Verificación directa: con $\alpha = 11$ (tras 10 adiciones), $\hat{\tau} = 12/14 = 0.857 \geq 0.85$. Por tanto $n^* = 10$.

Es decir, **10 fingerprints consecutivos consistentes** llevan al nodo de prior neutro a Ring-1. Este umbral intencionalmente alto evita que nodos Sybil obtengan confianza prematuramente.

---

## 4. Mecanismos Anti-Sybil

### 4.1 El ataque Sybil en contexto electoral

Un adversario con recursos (p. ej., el poder ejecutivo de un Estado autoritario) podría desplegar $s$ nodos falsos que:
1. Coordinan entre sí para reportar un Merkle root manipulado
2. Atacan la reputación de nodos honestos reportando sus fingerprints como inconsistentes

### 4.2 Defensa mediante Ring-0

Sea $R_0$ el conjunto de nodos Ring-0 (semillas), con $|R_0| = r_0$ fijo por el operador. Para que los nodos Sybil superen el consenso deben:

1. **Superar el quórum BFT:** necesitan $s > \lfloor(k-1)/3\rfloor$ nodos comprometidos de un total de $k \leq 12$. Con $k = 6$: se requieren $s \geq 2$ nodos Sybil para perturbar el consenso.

2. **Alcanzar Ring-1:** requieren $n^* = 10$ interacciones consistentes con Ring-0. Pero Ring-0 no puede ser engañado por definición (son los operadores designados).

3. **Reputación inicial baja:** todos los nodos nuevos empiezan con $\hat{\tau} = 0.5$, lo cual les da **peso cero** en las decisiones críticas de Ring-0.

### 4.3 Detección de clusters Sybil

Si un conjunto de nodos nuevos $\mathcal{S} \subseteq \mathcal{N}$ se validan mutuamente pero **no interactúan con Ring-0**, sus $\alpha$ permanecen en 1.0 (prior) mientras que sus correlaciones mutuas generan un patrón estadísticamente distinguible de un swarm orgánico.

**Heurística de detección:** Si $\forall n_i \in \mathcal{S}$: $\hat{\tau}_{ij} > 0.7$ entre sí pero $\hat{\tau}_{ij} < 0.55$ con Ring-0, el cluster es flagged como potencialmente Sybil.

---

## 5. Distinción Corte Eléctrico vs. Traición

### 5.1 El problema del silencio

Cuando un nodo $n_j$ deja de responder, el swarm enfrenta un problema de clasificación:

$$\text{Silencio} \rightarrow \begin{cases} \text{Corte eléctrico} & \text{(nodo honesto, fuera de línea)} \\ \text{Traición estratégica} & \text{(nodo esperando momento para atacar)} \end{cases}$$

### 5.2 Protocolo de clasificación diferida

Centinel usa una **penalización mínima reversible** durante el período de silencio:

```
1. t₀: nodo n_j deja de responder
2. t₀ + δ₁ (timeout = 5 min): β_j += 0.1   (OUTAGE_TENTATIVE)
3. t₁: n_j reconecta y envía attestation
   a. Si merkle_root_j == merkle_root_swarm:
        β_j -= 0.1                            (reversal)
        α_j += 1.0                            (RESTORE_CONSISTENT)
        → clasificado como CORTE ELÉCTRICO
   b. Si merkle_root_j ≠ merkle_root_swarm:
        β_j += 5.0 (sin reversal de 0.1)      (BETRAYAL)
        → clasificado como TRAICIÓN
```

### 5.3 Propiedades

**Propiedad 1 (Inocencia presunta):** Un nodo honesto que experimente $m$ cortes eléctricos y regrese siempre con datos consistentes tendrá:

$$\hat{\tau}_j = \frac{(\alpha_0 + m \cdot \Delta\alpha_\text{restore}) + 1}{(\alpha_0 + m \cdot \Delta\alpha_\text{restore}) + (\beta_0 + m \cdot 0) + 2}$$

donde $m \cdot 0$ porque el $\Delta\beta = 0.1$ es revertido en cada regreso consistente. El nodo **no acumula penalización neta** por cortes eléctricos honestos.

**Propiedad 2 (Memoria de traición):** Un nodo que traiciona tras $h$ interacciones honestas tendrá:

$$\hat{\tau}_j \approx \frac{(1 + h) + 1}{(1 + h) + (1 + 5) + 2} = \frac{h + 2}{h + 9}$$

Para $h = 10$ (nodo que traiciona después de 10 contribuciones honestas): $\hat{\tau} \approx 0.63$, degradado de Ring-1 a Ring-2.

---

## 6. Asignación Determinista de Tareas

### 6.1 Particionamiento de fuentes CNE

Honduras tiene 19 fuentes de datos en el CNE (1 nacional + 18 departamentales). Con $k$ nodos activos, la asignación es:

$$\text{fuente}[i] \rightarrow \text{nodo con slot\_index} = (i \bmod k)$$

donde el **slot\_index** se determina por el **orden de llegada** (arrival\_order) del nodo, no por su identidad criptográfica. Esto garantiza que:

1. La asignación es **deterministamente calculable** por cualquier nodo que conozca la lista de participantes activos.
2. No requiere **coordinación explícita** (no hay maestro ni votación).
3. Cuando un nodo sale del swarm, los restantes **recalculan automáticamente** cubriendo las fuentes huérfanas.

### 6.2 Formalización

Sea $\mathcal{N}_\text{active}(t) = \{(n_{id_1}, o_1), \ldots, (n_{id_k}, o_k)\}$ el conjunto de nodos activos en el instante $t$, donde $o_i$ es el arrival\_order de cada nodo. Ordenamos por arrival\_order:

$$\sigma = \text{argsort}(o_1, \ldots, o_k)$$

La asignación de la fuente $s_j \in \mathcal{S}$ al nodo $n_{\sigma[j \bmod k]}$ es:

$$\text{assign}(s_j, \mathcal{N}_\text{active}) = n_{\sigma[j \bmod k]}$$

### 6.3 Ejemplo con 6 nodos y 19 fuentes

| Slot | node\_id | Sources asignadas (19 fuentes ÷ 6 nodos) |
|------|----------|------------------------------------------|
| 0 (Ring-0) | `a3f2` | NACIONAL, 06\_ch, 12\_la\_paz, 18\_yoro |
| 1 | `7b1e` | 01\_atl, 07\_ep, 13\_le |
| 2 | `c9d4` | 02\_col, 08\_fm, 14\_oc |
| 3 | `52aa` | 03\_com, 09\_gr, 15\_ol |
| 4 | `f0e3` | 04\_cop, 10\_in, 16\_sb |
| 5 | `1d88` | 05\_cor, 11\_iz, 17\_val |

Si el nodo `7b1e` (slot 1) pierde conexión, los 5 restantes se redistribuyen:

| Slot | node\_id | Sources tras salida de slot 1 |
|------|----------|-------------------------------|
| 0 | `a3f2` | NACIONAL, 05\_cor, 10\_in, 15\_ol |
| 1 | `c9d4` | 01\_atl, 06\_ch, 11\_iz, 16\_sb |
| 2 | `52aa` | 02\_col, 07\_ep, 12\_la\_paz, 17\_val |
| 3 | `f0e3` | 03\_com, 08\_fm, 13\_le, 18\_yoro |
| 4 | `1d88` | 04\_cop, 09\_gr, 14\_oc |

**No se pierde cobertura.** Cada fuente sigue siendo monitoreada; solo cambia quién la monitorea.

---

## 7. Propiedades de Seguridad Formales

### 7.1 Resistencia Byzantine

Con $k$ nodos, la tolerancia BFT es:

$$f = \left\lfloor \frac{k-1}{3} \right\rfloor$$

| k | f (nodos Byzantine tolerados) |
|---|-------------------------------|
| 3 | 0 |
| 4 | 1 |
| 6 | 1 |
| 7 | 2 |
| 10 | 3 |
| 12 | 3 |

### 7.2 Teorema de convergencia del gossip

Con fan-out $F = 3$ y $k \leq 12$ nodos, cualquier mensaje alcanza todos los nodos en a lo sumo:

$$r = \left\lceil \log_F k \right\rceil = \left\lceil \log_3 12 \right\rceil = 3 \text{ rondas}$$

Latencia máxima (asumiendo 45s de intervalo de broadcast): $3 \times 45\text{s} = 135\text{s} \approx 2.25\text{ min}$, muy por debajo de la frecuencia de actualización del CNE.

### 7.3 Liveness bajo partición

Si el swarm se particiona en dos componentes $\mathcal{N}_A$ y $\mathcal{N}_B$ (p. ej., corte de internet nacional), cada componente opera en **modo standalone** con alertas marcadas como "Parciales". Al reconectarse, el nodo con mayor `chain_length` prevalece y los nodos del componente menor actualizan su Merkle root.

---

## 8. Integración con el Stack Criptográfico de Centinel

```
Capa 1: Ed25519         → firma de attestations y findings
Capa 2: SHA-256         → Merkle root del historial de snapshots
Capa 3: OpenTimestamps  → ancla temporal en Bitcoin (inmutabilidad)
Capa 4: PBTM            → confianza entre nodos (este documento)
Capa 5: TaskPartitioner → distribución de trabajo sin coordinación
```

El PBTM opera en la Capa 4: **asume** que las firmas Ed25519 son correctas (Capa 1) y **utiliza** las discrepancias en los Merkle roots (Capa 2) como señal para actualizar los scores.

---

## 9. Parámetros de Diseño y Calibración

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| $\Delta\alpha_\text{consistent}$ | 1.0 | Una confirmación es señal débil; se acumulan varias |
| $\Delta\alpha_\text{corroboration}$ | 2.0 | Múltiple evidencia independiente — señal más fuerte |
| $\Delta\beta_\text{outage}$ | 0.1 | Reversible; beneficio de la duda |
| $\Delta\beta_\text{betrayal}$ | 5.0 | Penalización severa asimétrica |
| $T_\alpha$ (half-life positivo) | 14 días | Memoria de ~2 semanas para cooperación |
| $T_\beta$ (half-life negativo) | 30 días | Memoria de ~1 mes para traición |
| $\tau^*_{\text{Ring-1}}$ | 0.85 | Alto umbral de entrada a la zona de confianza |
| $\tau_{\text{demotion}}$ | 0.40 | Zona de desconfianza activa |
| $k_\text{max}$ | 12 | Swarm pequeño: mejor observabilidad, menos superficie de ataque |

---

## 10. Validación y Trabajo Futuro

### 10.1 Simulaciones propuestas

1. **Ataque Sybil de $s = 4$ nodos en swarm de $k = 10$:** medir cuántos ticks necesita el sistema para degradar a todos los nodos Sybil por debajo de Ring-2.

2. **Tormenta de cortes eléctricos:** 3 nodos salen y regresan 5 veces cada uno (todos honestos); verificar que ninguno pierde más de 0.5% de trust neto.

3. **Ataque coordinado Ring-1 → traición:** un nodo con $\alpha = 20$ (Ring-1 consolidado) repentinamente diverge; medir cuántas rondas tarda en caer a Ring-2.

### 10.2 Trabajo futuro

- **Reputación federada multi-país:** cuando Centinel opere simultáneamente en Honduras, Guatemala y El Salvador, ¿deben compartirse scores de reputación entre swarms? Hipótesis: solo si los operadores son los mismos.
- **Proof of Consistent Work formal:** definir la ventana de tiempo y tolerancia exacta para la prueba de trabajo consistente que automatiza la entrada a Ring-1 sin intervención humana.
- **Análisis de equilibrio Nash:** modelar el sistema como un juego de $k$ jugadores con incentivos y verificar si la estrategia honesta es un equilibrio de Nash.

---

## Apéndice A: Pseudocódigo del Motor de Reputación

```python
class ReputationEngine:
    # prior: Beta(α=1, β=1) → trust = 0.5
    
    def on_consistent(node_id):
        α[node_id] += 1.0
        refresh_ring(node_id)
    
    def on_inconsistent(node_id):
        β[node_id] += 5.0
        refresh_ring(node_id)
    
    def on_timeout(node_id):
        β[node_id] += 0.1           # reversible
        pending_β[node_id] += 0.1
    
    def on_restore(node_id, consistent: bool):
        if consistent:
            β[node_id] -= pending_β[node_id]  # reversal
            α[node_id] += 1.0
        else:
            β[node_id] += 5.0                 # reclasificado como traición
        pending_β[node_id] = 0.0
    
    def trust_score(node_id):
        return (α[node_id] + 1) / (α[node_id] + β[node_id] + 2)
    
    def refresh_ring(node_id):
        τ = trust_score(node_id)
        if   τ >= 0.85:  ring[node_id] = 1
        elif τ <  0.40:  ring[node_id] = 2  # demote
    
    def decay(days_elapsed):
        α[node_id] *= 2^(-days_elapsed / 14)  # half-life 14d
        β[node_id] *= 2^(-days_elapsed / 30)  # half-life 30d
```

---

## Apéndice B: Ejemplo numérico de evolución de trust

**Escenario:** Nodo nuevo, 10 interacciones consistentes, luego un corte eléctrico y regreso honesto.

| Evento | α | β | Trust |
|--------|---|---|-------|
| Inicio | 1.0 | 1.0 | 0.500 |
| Consistente ×10 | 11.0 | 1.0 | **0.857** → Ring-1 |
| Consistente ×5 más | 16.0 | 1.0 | 0.895 |
| Corte eléctrico | 16.0 | 1.1 | 0.894 |
| Regreso consistente | 17.0 | 1.0 | **0.900** (β revertido) |
| Decaimiento 14d | 9.0 | 1.0 | 0.833 |

**El nodo mantiene Ring-1 durante todo el ciclo.** El corte eléctrico no produce daño neto.

**Escenario alternativo:** mismo nodo, pero regresa con datos divergentes tras el corte.

| Evento | α | β | Trust |
|--------|---|---|-------|
| Tras 15 consistentes | 16.0 | 1.0 | 0.895 |
| Corte + regreso traición | 16.0 | 6.1 | **0.739** → degradado Ring-2 |

---

## Licencia y Citación

Este documento es parte del proyecto Centinel (AGPL-3.0). Para citar en publicaciones académicas:

```bibtex
@techreport{zelaya2026centinel,
  title  = {Centinel Swarm: Persistent Bayesian Trust Model
             for Distributed Electoral Integrity Auditing},
  author = {Zelaya, Carlos and Alvarado, Devis},
  year   = {2026},
  month  = {5},
  institution = {Proyecto Centinel / UPNFM},
  note   = {Documento técnico interno v1.0}
}
```

---

*"La democracia no se defiende sola. Necesita testigos."*

— Proyecto Centinel, Honduras 2025
