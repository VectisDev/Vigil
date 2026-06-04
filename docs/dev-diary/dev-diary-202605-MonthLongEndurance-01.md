# Dev Diary - 202605 - MonthLongEndurance - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Resistencia bajo conteo hostil de mas de un mes / Endurance under a 30+ day hostile count  
**Version interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuacion de `dev-diary-202605-OneCommandBootstrap-01.md`. Premisa operativa real: en Honduras el conteo puede tardar **mas de un mes** por inoperancia y corrupcion. El sistema debe recopilar, hashear, analizar y publicar en el ambiente mas hostil posible **sin flaquear durante semanas**. Esta entrada cierra el punto donde el sistema si flaquearia con el tiempo.

---

## [ES]

### 1) Que cambio y por que ahora
Mi auditoria honesta del modelo "un mes hostil" me llevo a encontrar un cuello de botella estructural, no de seguridad: **toda lectura publica de auditoria cargaba cada payload completo a RAM**. `collect_snapshot_entries` leia `snapshot.raw` de *cada* snapshot y construia una lista con todos los payloads simultaneamente. En modo `election` (cadencia 5 min) un mes son ~8.640+ snapshots; cada consulta de un observador (OEA/UE/Carter) a `/audit/timeline`, `/audit/snapshots`, `/audit/proof`, `/audit/transparency` o la raiz de Merkle releia miles de payloads completos. Bajo el sondeo sostenido que ocurre exactamente durante el conteo disputado, el proceso se quedaba sin memoria. El sistema flaqueaba justo cuando mas importaba.

### 2) Decisiones de implementacion
Regla inviolable intacta: logica de hashing sin tocar, garantias de integridad identicas, solo optimizacion.

- **Vista metadata sin payload (`SnapshotMeta` + `collect_snapshot_metadata`).** Disene esta vista para que lea solo `snapshot.metadata.json` + `hash.txt`, **nunca** `snapshot.raw`. Duck-typea los atributos que usan las rutas de lectura (`snapshot_dir`, `expected_hash`, `previous_hash`, `timestamp`, `metadata`), asi que serializadores y llamadores no cambian -- solo desaparece `content`, por diseno. Pico de memoria proporcional a metadatos, no al corpus de evidencia de un mes.
- **Reconecte los 5 llamadores de solo-lectura** (timeline, snapshots-por-dia, proof, cache de transparencia, raiz de Merkle) a la vista metadata. Ninguno necesitaba el payload jamas.
- **Verificacion en streaming.** Modifique `verify_hashchain_from_snapshots` para que ahora ordene los directorios con payload leyendo solo su metadata (kilobytes), y cargue **un payload a la vez** dentro del bucle, dejandolo reclamar. Pico de memoria = un snapshot, no el mes entero. El conjunto verificado y su orden son identicos al comportamiento previo (dirs con payload, ordenados por timestamp): optimizacion pura.
- **Recomputacion de hash exclusiva para verificacion.** `collect_snapshot_entries` (con payload) queda reservada solo para recomputar hashes; lo documente asi.

### 3) Impacto operativo
Probe en aislamiento: cadena valida verifica identico (count, verified_count, ultimo hash, anomalias de timestamp, campos legados), la manipulacion se detecta en el indice exacto, y la vista metadata funciona **incluso con todos los payloads borrados** -- prueba estructural de que nunca lee el payload. El resultado: un mes de conteo hostil con observadores internacionales sondeando sin descanso ya no agota la RAM. El sistema aguanta semanas, no horas.

### 4) Aprendizaje de ciclo
"Sin flaquear" no es una afirmacion de seguridad sino de resistencia en el tiempo. El adversario mas efectivo en un conteo de un mes no es un exploit: es la duracion misma multiplicada por carga legitima de auditores. La optimizacion que no cambia ni un bit del hash fue mas decisiva para la mision que cualquier defensa nueva. Me di cuenta de que habia estado pensando en ataques cuando el verdadero enemigo era el tiempo.

---

## [EN]

### 1) What changed and why now
My honest "one hostile month" audit led me to find a structural -- not security -- bottleneck: **every public audit read loaded every full payload into RAM**. `collect_snapshot_entries` read each `snapshot.raw` and built a list holding all payloads at once. In `election` mode (5-min cadence) a month is ~8,640+ snapshots; each observer (OAS/EU/Carter) hit on `/audit/timeline`, `/audit/snapshots`, `/audit/proof`, `/audit/transparency` or the Merkle root re-read thousands of full payloads. Under the sustained polling that happens exactly during the contested count, the process ran out of memory -- failing precisely when it mattered most.

### 2) Implementation choices
Inviolable rule intact: hashing logic untouched, integrity guarantees identical, optimization only.

- **Payload-free metadata view (`SnapshotMeta` + `collect_snapshot_metadata`).** I designed this view to read only `snapshot.metadata.json` + `hash.txt`, **never** `snapshot.raw`. Duck-types the attributes the read paths use, so serializers and callers are unchanged -- only `content` is gone, by design. Peak memory scales with metadata, not a month's evidence corpus.
- **I repointed the 5 read-only callers** (timeline, snapshots-by-day, proof, transparency cache, Merkle root) to the metadata view. None ever needed the payload.
- **Streaming verification.** I modified `verify_hashchain_from_snapshots` to order payload-bearing dirs via their tiny metadata files, then load **one payload at a time** in the loop and let it be reclaimed. Peak memory = one snapshot. Verified set and order are identical to prior behavior: pure optimization.
- **Hash recomputation only.** `collect_snapshot_entries` (with payload) is now reserved solely for hash recomputation; I documented it that way.

### 3) Operational impact
I proved in isolation: a valid chain verifies identically (count, verified_count, last hash, timestamp anomalies, legacy fields), tampering is caught at the exact index, and the metadata view works **even with all payloads deleted** -- structural proof it never reads the payload. Result: a month-long hostile count with international observers polling relentlessly no longer exhausts RAM. The system endures for weeks, not hours.

### 4) Cycle takeaway
"Without faltering" is not a security claim but a claim about endurance over time. The most effective adversary in a month-long count is not an exploit: it is duration itself multiplied by legitimate auditor load. The optimization that changes not one bit of the hash mattered more to the mission than any new defense. I realized I had been thinking about attacks when the real enemy was time.

---

## Cierre / Close
Sin tocar la logica de hashing, sin retroceso, verificado en aislamiento: el sistema ahora resiste el adversario que no tiene exploit pero si tiene un mes. La promesa "recopilar, hashear, analizar y publicar sin flaquear" es defendible en el tiempo, no solo en el instante.
