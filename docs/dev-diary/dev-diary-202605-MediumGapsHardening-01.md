# Dev Diary - 202605 - MediumGapsHardening - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Cierre de brechas MEDIA tras TIER 4/5 / Closing MEDIUM gaps after TIER 4/5  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto de esta entrada / Entry context:**  
Continuación de `dev-diary-202605-OperatorUxOneDial-01.md`. TIER 4 cerró las críticas y TIER 5 las hizo operables. Quedaban cuatro brechas MEDIA que un adversario competente usaría como escalones. Sin features nuevas: solo cerrar las cuatro, con la misma regla inviolable (nada de hashing destruido, sin retrocesos).

---

## [ES] Diario narrativo desde la última publicación

### 1) Qué cambió y por qué ahora
Cuatro debilidades MEDIA, cada una explotable por separado:

- **M1 — fuga de rutas en `/audit/*`.** Endpoints públicos sin auth devolvían rutas de sistema (`str(snapshot_dir)`), regalando el mapa del despliegue a cualquier atacante.
- **M2 — contador de fallback no persistente.** `_next_fallback_sequence` vivía solo en memoria; tras un reinicio en noche electoral, las secuencias se repetían (1,2,3,…,1,2,3). Auditores dependen de `(timestamp, secuencia)` como orden TOTAL; en ambiente hostil el atacante puede además mover el reloj hacia atrás, dejando la secuencia como único desempate.
- **M3 — sin validación de monotonicidad de timestamps.** El hash cubre contenido+metadatos+prev_hash pero no el orden temporal: un snapshot con fecha retrocedida o futura hashea válido y nada lo señalaba.
- **M4 — DoS de memoria del honeypot.** El disco ya rotaba, pero la cola de eventos era `queue.Queue()` *sin límite* y los dicts por-IP crecían sin tope. Un flood (o IPs rotadas con XFF falsificado) agotaba la RAM y mataba todo el pipeline — la propia contabilidad defensiva convertida en el ataque.

### 2) Decisiones de implementación
- **M1:** redacción en el borde de la API (`_redact_path` → solo el nombre de hoja). El auditor cruza por hash vía `/audit/proof`, así que no pierde nada; el esquema de respuesta se mantiene (sin retroceso de contrato).
- **M2:** persistencia con el mismo `write_atomic` fsync-durable de TIER 4. Carga perezosa, `max()` para nunca retroceder, archivo ausente/corrupto degrada al comportamiento legado (mejora, nunca regresión). Fallo de escritura se registra, nunca lanza.
- **M3:** campo **aditivo** `timestamp_anomalies` en `verify_hashchain_from_snapshots`. No-fatal: nunca cambia `valid` (un problema de reloj no es ruptura de cadena). Detecta `future_timestamp` (tolerancia 300s) y `non_monotonic_vs_chain_predecessor`. Campos legados intactos.
- **M4:** cola acotada con `put_nowait` (descarta+cuenta bajo flood, jamás bloquea el hilo del honeypot — el bloqueo sería un DoS de hilos). Cardinalidad por-IP acotada con evicción LRU sobre las tres estructuras a la vez. `cap<=0` preserva el comportamiento ilimitado legado (opt-out explícito, sin sorpresa). Apagado robusto aunque el centinela se descarte por cola llena.

### 3) Impacto operativo
La superficie pública ya no dibuja el mapa del servidor; el orden forense de fallbacks sobrevive reinicios y manipulación de reloj; una línea de tiempo retrocedida es visible para el auditor sin romper la verificación; y un flood al honeypot degrada con gracia en vez de tumbar la captura electoral. Cada arreglo es interruptor simple o degradación elegante, a costo cero.

### 4) Aprendizaje de ciclo
Lo MEDIO es donde se gana o se pierde de verdad: lo CRÍTICO ya lo mira todo el mundo. El patrón repetido fue "la herramienta defensiva sin límite es el vector" — colas, contadores, dicts por-IP. Acotar y degradar con gracia, nunca bloquear ni reventar.

---

## [EN] Narrative diary since the previous publication

### 1) What changed and why now
Four separately-exploitable MEDIUM weaknesses:

- **M1 — path disclosure in `/audit/*`.** Unauthenticated public endpoints returned server paths, handing an attacker the deployment map.
- **M2 — non-persistent fallback counter.** In-memory only; after an election-night restart fallback sequences repeated. Auditors rely on `(timestamp, sequence)` as a TOTAL order, and a hostile actor can push the clock backwards, leaving the sequence as the only tiebreaker.
- **M3 — no timestamp monotonicity check.** The hash does not cover wall-clock ordering, so a back/forward-dated snapshot still hash-verifies, unflagged.
- **M4 — honeypot memory DoS.** Disk already rotated, but the event queue was unbounded and per-IP dicts grew without cap. A flood (or rotated/spoofed IPs) exhausted RAM and killed the whole pipeline.

### 2) Implementation choices
- **M1:** redact at the API boundary (`_redact_path` → leaf name only). Auditors cross-reference by hash via `/audit/proof`, so nothing is lost; response schema preserved (no contract regression).
- **M2:** persist via the same fsync-durable `write_atomic` from TIER 4. Lazy load, `max()` so it never moves backwards, missing/corrupt degrades to legacy (improvement, never regression). Write failure logged, never raised.
- **M3:** **additive** `timestamp_anomalies` field. Non-fatal: never flips `valid`. Detects `future_timestamp` (300s tolerance) and `non_monotonic_vs_chain_predecessor`. Legacy fields untouched.
- **M4:** bounded queue with `put_nowait` (drop+count under flood, never blocks the honeypot thread — blocking would be a thread-exhaustion DoS). Bounded per-IP cardinality with LRU eviction across all three structures. `cap<=0` preserves legacy unbounded behavior (explicit opt-out). Shutdown robust even if the sentinel is dropped.

### 3) Operational impact
The public surface no longer draws the server map; forensic fallback order survives restarts and clock tampering; a rewound timeline is visible to auditors without breaking verification; a honeypot flood degrades gracefully instead of taking down election capture. Every fix is a simple switch or graceful degradation, at zero cost.

### 4) Cycle takeaway
MEDIUM is where it is actually won or lost — everyone already watches CRITICAL. The recurring pattern was "the unbounded defensive tool is the vector": queues, counters, per-IP dicts. Bound and degrade gracefully; never block, never burst.

---

## Cierre de entrada / Entry close
Cuatro brechas MEDIA cerradas sin features nuevas, sin romper esquemas ni lógica de hashing, verificadas en aislamiento con pruebas de no-regresión. La promesa sigue siendo defendible ante un escéptico hostil.
