# Dev Diary - 202605 - MonthLongEndurance - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Resistencia bajo conteo hostil de más de un mes / Endurance under a 30+ day hostile count  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuación de `dev-diary-202605-OneCommandBootstrap-01.md`. Premisa operativa real: en Honduras el conteo puede tardar **más de un mes** por inoperancia y corrupción. El sistema debe recopilar, hashear, analizar y publicar en el ambiente más hostil posible **sin flaquear durante semanas**. Esta entrada cierra el punto donde el sistema sí flaquearía con el tiempo.

---

## [ES]

### 1) Qué cambió y por qué ahora
La auditoría honesta del modelo "un mes hostil" encontró un cuello de botella estructural, no de seguridad: **toda lectura pública de auditoría cargaba cada payload completo a RAM**. `collect_snapshot_entries` leía `snapshot.raw` de *cada* snapshot y construía una lista con todos los payloads simultáneamente. En modo `election` (cadencia 5 min) un mes son ~8.640+ snapshots; cada consulta de un observador (OEA/UE/Carter) a `/audit/timeline`, `/audit/snapshots`, `/audit/proof`, `/audit/transparency` o la raíz de Merkle releía miles de payloads completos. Bajo el sondeo sostenido que ocurre exactamente durante el conteo disputado, el proceso se quedaba sin memoria. El sistema flaqueaba justo cuando más importaba.

### 2) Decisiones de implementación
Regla inviolable intacta: lógica de hashing sin tocar, garantías de integridad idénticas, solo optimización.

- **Vista metadata sin payload (`SnapshotMeta` + `collect_snapshot_metadata`).** Lee solo `snapshot.metadata.json` + `hash.txt`, **nunca** `snapshot.raw`. Duck-typea los atributos que usan las rutas de lectura (`snapshot_dir`, `expected_hash`, `previous_hash`, `timestamp`, `metadata`), así que serializadores y llamadores no cambian — solo desaparece `content`, por diseño. Pico de memoria proporcional a metadatos, no al corpus de evidencia de un mes.
- **Repunte de los 5 llamadores de solo-lectura** (timeline, snapshots-por-día, proof, cache de transparencia, raíz de Merkle) a la vista metadata. Ninguno necesitaba el payload jamás.
- **Verificación en streaming.** `verify_hashchain_from_snapshots` ahora ordena los directorios con payload leyendo solo su metadata (kilobytes), y carga **un payload a la vez** dentro del bucle, dejándolo reclamar. Pico de memoria = un snapshot, no el mes entero. El conjunto verificado y su orden son idénticos al comportamiento previo (dirs con payload, ordenados por timestamp): optimización pura.
- **Recomputación de hash exclusiva para verificación.** `collect_snapshot_entries` (con payload) queda reservada solo para recomputar hashes; documentado.

### 3) Impacto operativo
Probado en aislamiento: cadena válida verifica idéntico (count, verified_count, último hash, anomalías de timestamp, campos legados), la manipulación se detecta en el índice exacto, y la vista metadata funciona **incluso con todos los payloads borrados** — prueba estructural de que nunca lee el payload. El resultado: un mes de conteo hostil con observadores internacionales sondeando sin descanso ya no agota la RAM. El sistema aguanta semanas, no horas.

### 4) Aprendizaje de ciclo
"Sin flaquear" no es una afirmación de seguridad sino de resistencia en el tiempo. El adversario más efectivo en un conteo de un mes no es un exploit: es la duración misma multiplicada por carga legítima de auditores. La optimización que no cambia ni un bit del hash fue más decisiva para la misión que cualquier defensa nueva.

---

## [EN]

### 1) What changed and why now
The honest "one hostile month" audit found a structural — not security — bottleneck: **every public audit read loaded every full payload into RAM**. `collect_snapshot_entries` read each `snapshot.raw` and built a list holding all payloads at once. In `election` mode (5-min cadence) a month is ~8,640+ snapshots; each observer (OAS/EU/Carter) hit on `/audit/timeline`, `/audit/snapshots`, `/audit/proof`, `/audit/transparency` or the Merkle root re-read thousands of full payloads. Under the sustained polling that happens exactly during the contested count, the process ran out of memory — failing precisely when it mattered most.

### 2) Implementation choices
Inviolable rule intact: hashing logic untouched, integrity guarantees identical, optimization only.

- **Payload-free metadata view (`SnapshotMeta` + `collect_snapshot_metadata`).** Reads only `snapshot.metadata.json` + `hash.txt`, **never** `snapshot.raw`. Duck-types the attributes the read paths use, so serializers and callers are unchanged — only `content` is gone, by design. Peak memory scales with metadata, not a month's evidence corpus.
- **Repointed the 5 read-only callers** (timeline, snapshots-by-day, proof, transparency cache, Merkle root) to the metadata view. None ever needed the payload.
- **Streaming verification.** `verify_hashchain_from_snapshots` orders payload-bearing dirs via their tiny metadata files, then loads **one payload at a time** in the loop and lets it be reclaimed. Peak memory = one snapshot. Verified set and order are identical to prior behavior: pure optimization.
- **Hash recomputation only.** `collect_snapshot_entries` (with payload) is now reserved solely for hash recomputation; documented.

### 3) Operational impact
Proven in isolation: a valid chain verifies identically (count, verified_count, last hash, timestamp anomalies, legacy fields), tampering is caught at the exact index, and the metadata view works **even with all payloads deleted** — structural proof it never reads the payload. Result: a month-long hostile count with international observers polling relentlessly no longer exhausts RAM. The system endures for weeks, not hours.

### 4) Cycle takeaway
"Without faltering" is not a security claim but a claim about endurance over time. The most effective adversary in a month-long count is not an exploit: it is duration itself multiplied by legitimate auditor load. The optimization that changes not one bit of the hash mattered more to the mission than any new defense.

---

## Cierre / Close
Sin tocar la lógica de hashing, sin retroceso, verificado en aislamiento: el sistema ahora resiste el adversario que no tiene exploit pero sí tiene un mes. La promesa "recopilar, hashear, analizar y publicar sin flaquear" es defendible en el tiempo, no solo en el instante.
