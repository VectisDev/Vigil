# Dev Diary - 202605 - MediumGapsHardening - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Cierre de brechas MEDIA tras TIER 4/5 / Closing MEDIUM gaps after TIER 4/5  
**Version interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto de esta entrada / Entry context:**  
Continuacion de `dev-diary-202605-OperatorUxOneDial-01.md`. TIER 4 cerro las criticas y TIER 5 las hizo operables. Quedaban cuatro brechas MEDIA que un adversario competente usaria como escalones. Sin features nuevas: solo cerrar las cuatro, con la misma regla inviolable (nada de hashing destruido, sin retrocesos).

---

## [ES] Diario narrativo desde la ultima publicacion

### 1) Que cambio y por que ahora
Identifique cuatro debilidades MEDIA, cada una explotable por separado:

- **M1 -- fuga de rutas en `/audit/*`.** Los endpoints publicos sin auth devolvian rutas de sistema (`str(snapshot_dir)`), regalando el mapa del despliegue a cualquier atacante. Cuando me di cuenta de lo que estaba exponiendo, fue obvio que habia que cerrarlo de inmediato.
- **M2 -- contador de fallback no persistente.** `_next_fallback_sequence` vivia solo en memoria; tras un reinicio en noche electoral, las secuencias se repetian (1,2,3,...,1,2,3). Los auditores dependen de `(timestamp, secuencia)` como orden TOTAL; en ambiente hostil el atacante puede ademas mover el reloj hacia atras, dejando la secuencia como unico desempate.
- **M3 -- sin validacion de monotonicidad de timestamps.** El hash cubre contenido+metadatos+prev_hash pero no el orden temporal: un snapshot con fecha retrocedida o futura hashea valido y nada lo senalaba. El problema que vi fue que la verificacion pasaba sin quejarse de algo que un auditor si notaria.
- **M4 -- DoS de memoria del honeypot.** El disco ya rotaba, pero la cola de eventos era `queue.Queue()` *sin limite* y los dicts por-IP crecian sin tope. Un flood (o IPs rotadas con XFF falsificado) agotaba la RAM y mataba todo el pipeline -- la propia contabilidad defensiva convertida en el ataque.

### 2) Decisiones de implementacion
- **M1:** Decidi redactar en el borde de la API (`_redact_path` -> solo el nombre de hoja). El auditor cruza por hash via `/audit/proof`, asi que no pierde nada; el esquema de respuesta se mantiene (sin retroceso de contrato).
- **M2:** Implemente persistencia con el mismo `write_atomic` fsync-durable de TIER 4. Carga perezosa, `max()` para nunca retroceder, archivo ausente/corrupto degrada al comportamiento legado (mejora, nunca regresion). Fallo de escritura se registra, nunca lanza.
- **M3:** Agregue un campo **aditivo** `timestamp_anomalies` en `verify_hashchain_from_snapshots`. No-fatal: nunca cambia `valid` (un problema de reloj no es ruptura de cadena). Detecta `future_timestamp` (tolerancia 300s) y `non_monotonic_vs_chain_predecessor`. Campos legados intactos.
- **M4:** Implemente cola acotada con `put_nowait` (descarta+cuenta bajo flood, jamas bloquea el hilo del honeypot -- el bloqueo seria un DoS de hilos). Cardinalidad por-IP acotada con eviccion LRU sobre las tres estructuras a la vez. `cap<=0` preserva el comportamiento ilimitado legado (opt-out explicito, sin sorpresa). Apagado robusto aunque el centinela se descarte por cola llena.

### 3) Impacto operativo
La superficie publica ya no dibuja el mapa del servidor; el orden forense de fallbacks sobrevive reinicios y manipulacion de reloj; una linea de tiempo retrocedida es visible para el auditor sin romper la verificacion; y un flood al honeypot degrada con gracia en vez de tumbar la captura electoral. Cada arreglo es interruptor simple o degradacion elegante, a costo cero.

### 4) Aprendizaje de ciclo
Me di cuenta de que lo MEDIO es donde se gana o se pierde de verdad: lo CRITICO ya lo mira todo el mundo. El patron repetido que encontre fue "la herramienta defensiva sin limite es el vector" -- colas, contadores, dicts por-IP. La leccion: acotar y degradar con gracia, nunca bloquear ni reventar.

---

## [EN] Narrative diary since the previous publication

### 1) What changed and why now
I identified four separately-exploitable MEDIUM weaknesses:

- **M1 -- path disclosure in `/audit/*`.** Unauthenticated public endpoints returned server paths, handing an attacker the deployment map. When I realized what I was exposing, it was obvious this had to be closed immediately.
- **M2 -- non-persistent fallback counter.** In-memory only; after an election-night restart fallback sequences repeated. Auditors rely on `(timestamp, sequence)` as a TOTAL order, and a hostile actor can push the clock backwards, leaving the sequence as the only tiebreaker.
- **M3 -- no timestamp monotonicity check.** The hash does not cover wall-clock ordering, so a back/forward-dated snapshot still hash-verifies, unflagged. The problem I saw was that verification passed without complaining about something an auditor would definitely notice.
- **M4 -- honeypot memory DoS.** Disk already rotated, but the event queue was unbounded and per-IP dicts grew without cap. A flood (or rotated/spoofed IPs) exhausted RAM and killed the whole pipeline.

### 2) Implementation choices
- **M1:** I decided to redact at the API boundary (`_redact_path` -> leaf name only). Auditors cross-reference by hash via `/audit/proof`, so nothing is lost; response schema preserved (no contract regression).
- **M2:** I implemented persistence via the same fsync-durable `write_atomic` from TIER 4. Lazy load, `max()` so it never moves backwards, missing/corrupt degrades to legacy (improvement, never regression). Write failure logged, never raised.
- **M3:** I added an **additive** `timestamp_anomalies` field. Non-fatal: never flips `valid`. Detects `future_timestamp` (300s tolerance) and `non_monotonic_vs_chain_predecessor`. Legacy fields untouched.
- **M4:** I implemented a bounded queue with `put_nowait` (drop+count under flood, never blocks the honeypot thread -- blocking would be a thread-exhaustion DoS). Bounded per-IP cardinality with LRU eviction across all three structures. `cap<=0` preserves legacy unbounded behavior (explicit opt-out). Shutdown robust even if the shutdown signal is dropped.

### 3) Operational impact
The public surface no longer draws the server map; forensic fallback order survives restarts and clock tampering; a rewound timeline is visible to auditors without breaking verification; a honeypot flood degrades gracefully instead of taking down election capture. Every fix is a simple switch or graceful degradation, at zero cost.

### 4) Cycle takeaway
I learned that MEDIUM is where it is actually won or lost -- everyone already watches CRITICAL. The recurring pattern I found was "the unbounded defensive tool is the vector": queues, counters, per-IP dicts. The lesson: bound and degrade gracefully; never block, never burst.

---

## Cierre de entrada / Entry close
Cerre cuatro brechas MEDIA sin features nuevas, sin romper esquemas ni logica de hashing, verificadas en aislamiento con pruebas de no-regresion. La promesa sigue siendo defendible ante un esceptico hostil.
