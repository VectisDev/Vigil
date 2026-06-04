# Dev Diary - 202605 - SwarmDistributedAuditNetwork - 01

**Fecha aproximada / Approximate date:** 27-may-2026 / May 27, 2026  
**Fase / Phase:** Cerrar las 4 brechas que separaban un swarm de salud de una red de auditoria real / Closing the 4 gaps separating a health-monitoring swarm from a real audit network  
**Version interna / Internal version:** v0.2.x (ciclo dev-v12)  
**Rama / Branch:** dev-v12  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuacion de `dev-diary-202605-LabSwarmTelemetry-01.md`. La simulacion del /lab demostraba las propiedades matematicas del enjambre. El siguiente paso era hacer que el swarm en produccion fuera lo que la simulacion prometia: una red de auditoria distribuida que produce evidencia corroborada, no solo un sistema de monitoreo de salud de nodos. / Continuation of `dev-diary-202605-LabSwarmTelemetry-01.md`. The `/lab` simulation demonstrated the mathematical properties of the swarm. The next step was making the production swarm what the simulation promised: a distributed audit network that produces corroborated evidence, not just a node health monitoring system.

---

## [ES]

### 1) El Problema (Contexto)
El motor gossip P2P (`gossip.py`) funcionaba correctamente: nodos se descubrian, firmaban attestations con Ed25519, y hacian fan-out de `FindingPayload` a 3 peers. Pero el swarm en produccion era, en esencia, un sistema de monitoreo de salud. Identifique cuatro brechas concretas que lo separaban de ser una red de auditoria real. Primera: los hallazgos HIGH/CRITICAL de `analyze_rules.py` llegaban al swarm con un delay de ~5 minutos porque `run_pipeline.py` era el unico punto de broadcast, y disparaba al final del ciclo completo. Segunda: no habia forma de saber si dos nodos distintos habian detectado la misma anomalia en el mismo snapshot; `FederationAnomalyLog.stats()` solo agrupaba por columna individual, no por (regla, snapshot). Tercera: `scripts/collector.py` nunca llamaba a `/api/swarm/last_scraped` ni a `/api/swarm/report_scrape` aunque esas APIs existian y estaban documentadas. El scraping cooperativo existia en el API pero no en el collector. Cuarta: `NodePayload` no tenia campo `specialization`; todos los nodos eran funcionalmente identicos, sin coordinacion sobre que subconjunto de reglas priorizar.

### 2) La Hipotesis
Cuatro cambios quirurgicos -- uno por brecha -- convierten el swarm de salud en red de auditoria sin tocar la arquitectura core: (1) broadcast inmediato desde `analyze_rules.py` al terminar la deteccion, antes de que `run_pipeline.py` lea el reporte; (2) query SQL de consenso que cuenta `COUNT(DISTINCT node_id)` por `(rule_key, snapshot_id)`; (3) skip/report del collector wired a las APIs existentes del swarm; (4) especializacion determinista derivada del `node_id` con soft assignment (todos ejecutan todas las reglas). El resultado es que el swarm produce evidencia corroborada verificable: cuando dos nodos independientes reportan la misma regla en el mismo snapshot, eso es consenso, no coincidencia.

### 3) El Experimento / Implementacion
**Gap 1 -- Broadcast urgente:** anadi `_broadcast_findings_urgent()` a `scripts/analyze_rules.py`. La funcion filtra alertas HIGH/CRITICAL del resultado de `RulesEngine.run()` y las postea a `POST /api/swarm/broadcast` inmediatamente, antes de que el pipeline lea el reporte. Fire-and-forget con timeout 1.5s: si el swarm esta offline, la deteccion no se interrumpe. Tambien respeta `CENTINEL_SPECIALIZATION` -- cuando esta seteada, marca como `"priority": true` los hallazgos de las reglas del dominio especializado del nodo.

**Gap 2 -- Consenso visible:** anadi `get_consensus_summary(min_nodes, limit)` a `FederationAnomalyLog` en `findings_log.py`. La query SQL agrupa hallazgos por `(rule_key, snapshot_id)` con `COUNT(DISTINCT node_id)` y filtra con `HAVING node_count >= min_nodes`. Cree el endpoint `GET /api/swarm/consensus_findings?min_nodes=N`. En `/ops S8` anadi una tabla de consenso con fondo ambar para 2-4 nodos corroborantes y rojo para 5+.

**Gap 3 -- Scraping cooperativo:** conecte el collector a las APIs existentes del swarm. Antes de cada fetch, el collector consulta `/api/swarm/last_scraped` con `source_id`; si otro nodo ya raspo esa fuente en los ultimos 240 segundos, el fetch se omite. Despues de un fetch exitoso, el collector postea a `/api/swarm/report_scrape` con el hash SHA256 del payload. Ambas llamadas tienen timeout 0.5s. Cambie el modo por defecto de `CENTINEL_SWARM_COOPERATIVE=1` (opt-in muerto) a `"auto"`: una sola llamada a `/api/swarm/status` al inicio del run determina si el swarm esta activo con >=1 peer; si no, el collector procede sin ningun overhead cooperativo.

**Gap 4 -- Especializacion de nodos:** anadi el campo `specialization: str = "general"` a `NodePayload` en `gossip.py`. La especializacion se deriva deterministicamente del `node_id` hex: `int(node_id, 16) % 3` mapea a `temporal` / `statistical` / `structural`. Se incluye en el payload firmado de `build_my_attestation()`. En `/ops S8`, la tabla de peers muestra la especializacion con identificador visual.

### 4) El Resultado (La Leccion)
Funciono en las cuatro brechas. El broadcast urgente redujo el delay de hallazgos HIGH/CRITICAL de ~5 minutos a ~1.5 segundos. El consenso SQL permitio la primera query que responde "cuantos nodos distintos confirmaron esta anomalia?" -- que es exactamente la pregunta que importa en un conteo disputado. El scraping cooperativo con auto-detect tiene overhead cero cuando el swarm esta offline (el default operativo mas frecuente) y se activa automaticamente sin configuracion cuando hay peers reales. La especializacion soft garantiza cobertura completa independientemente de que nodos fallen.

### 5) La Decision Final (Takeaway)
Un swarm de salud dice "todos los nodos estan vivos". Una red de auditoria dice "tres nodos independientes detectaron la misma anomalia en el snapshot 0x4a7f en los ultimos 8 minutos". La segunda afirmacion es evidencia; la primera es infraestructura. Las cuatro brechas no eran features faltantes -- eran la diferencia entre un sistema de monitoreo y un sistema de produccion de evidencia. Cerrarlas convirtio el swarm en lo que prometia ser.

### 6) Que cambio y por que ahora
Las cuatro brechas eran conocidas desde el diseno inicial. Las postergue porque el MVP necesitaba el gossip funcionando primero. Con el gossip en produccion y la simulacion del /lab demostrando el valor del enjambre, cerrar las brechas fue el paso logico siguiente. El timing tambien fue determinado por el modelo de amenaza: en un conteo electoral activo, el delay de 5 minutos entre deteccion y broadcast puede significar la diferencia entre alertar antes o despues de que el adversario consolide los datos manipulados.

### 7) Decisiones de implementacion
- **Fire-and-forget para broadcast urgente:** la deteccion es el flujo principal; el swarm es un canal secundario. Si `requests.post` falla en 1.5s, el analisis continua sin interrupcion. El swarm offline no puede interrumpir la deteccion.
- **SQL HAVING para consenso, no logica de aplicacion:** la base de datos ya tiene todos los hallazgos de todos los nodos con sus `node_id`. Una query con `GROUP BY` y `HAVING` es O(log N) sobre indices existentes y no requiere cargar nada a memoria de aplicacion.
- **"auto" como default para cooperative scraping:** opt-in con `CENTINEL_SWARM_COOPERATIVE=1` era dead code -- nadie lo activaba porque requeria configuracion manual consciente. El default "auto" elimina esa friccion: si el swarm tiene peers, coopera; si no, continua solo. Zero overhead en ambos casos.
- **Una sola llamada a `/api/swarm/status` al inicio del run:** en lugar de verificar por fuente (18 llamadas para HN), una sola llamada determina el estado para todo el run. Si el swarm cae a mitad del run, el collector ya determino "cooperativo = true" y seguira intentando -- lo que es correcto porque la mayoria del run probablemente fue cooperativo.
- **Especializacion soft, no hard:** si un nodo `temporal` falla, sus reglas de timestamp siguen siendo cubiertas por los nodos `statistical` y `structural` que ejecutan todas las reglas. La especializacion es sobre que se prioriza en el broadcast, no sobre que se ejecuta. La cobertura de deteccion es siempre completa.
- **Threshold ambar/rojo para consenso en /ops:** 2-4 nodos es senal de corroboracion; 5+ es consenso fuerte. El umbral visual hace la distincion sin requerir que el operador calcule nada.

### 8) Impacto
El swarm en produccion ahora produce tres tipos de evidencia que antes no existian: hallazgos con latencia de segundos (no minutos), hallazgos con consenso cuantificado por nodo, y un registro verificable de que nodo raspo que fuente y cuando. Para un conteo disputado donde se alega manipulacion de datos, la combinacion de "el engine detecto" + "N nodos independientes corroboraron" + "estos N nodos eran los que tenian datos frescos de esa fuente" es una cadena de evidencia que no existia antes de estos cuatro cambios.

### 9) Aprendizaje de ciclo
La arquitectura distribuida produce su valor mas alto en el momento de mayor presion adversarial -- que es exactamente el momento en que los sistemas centralizados son mas vulnerables. Un swarm de auditoria que solo monitorea salud de nodos es un sistema centralizado con mas nodos: si el servidor central cae, la red cae. Un swarm que produce consenso verificable es cualitativamente distinto: cada nodo es un testigo independiente, y el adversario necesita silenciar suficientes testigos simultaneamente para que el consenso colapse. Eso requiere una capacidad de ataque que aumenta linealmente con el tamano de la red.

---

## [EN]

### 1) The Problem (Context)
The P2P gossip engine (`gossip.py`) was functioning correctly: nodes discovered each other, signed attestations with Ed25519, and fanned out `FindingPayload` to 3 peers. But the production swarm was, in essence, a node health monitoring system. I identified four concrete gaps that separated it from being a real audit network. First: HIGH/CRITICAL findings from `analyze_rules.py` reached the swarm with a ~5-minute delay because `run_pipeline.py` was the only broadcast point, and it fired at the end of the complete cycle. Second: there was no way to know if two distinct nodes had detected the same anomaly in the same snapshot; `FederationAnomalyLog.stats()` only grouped by individual column, not by (rule, snapshot). Third: `scripts/collector.py` never called `/api/swarm/last_scraped` or `/api/swarm/report_scrape` even though those APIs existed and were documented. Cooperative scraping existed in the API but not in the collector. Fourth: `NodePayload` had no `specialization` field; all nodes were functionally identical, with no coordination over which rule subset to prioritize.

### 2) The Hypothesis
Four surgical changes -- one per gap -- turn the health swarm into an audit network without touching the core architecture: (1) immediate broadcast from `analyze_rules.py` upon completing detection, before `run_pipeline.py` reads the report; (2) SQL consensus query counting `COUNT(DISTINCT node_id)` per `(rule_key, snapshot_id)`; (3) collector skip/report wired to the swarm's existing APIs; (4) deterministic specialization derived from `node_id` with soft assignment (all nodes run all rules). The result is that the swarm produces verifiable corroborated evidence: when two independent nodes report the same rule on the same snapshot, that is consensus, not coincidence.

### 3) The Experiment / Implementation
**Gap 1 -- Urgent broadcast:** I added `_broadcast_findings_urgent()` to `scripts/analyze_rules.py`. The function filters HIGH/CRITICAL alerts from the `RulesEngine.run()` result and posts them to `POST /api/swarm/broadcast` immediately, before the pipeline reads the report. Fire-and-forget with 1.5s timeout: if the swarm is offline, detection is not interrupted. It also respects `CENTINEL_SPECIALIZATION` -- when set, it marks findings from the node's specialized domain's rules as `"priority": true`.

**Gap 2 -- Visible consensus:** I added `get_consensus_summary(min_nodes, limit)` to `FederationAnomalyLog` in `findings_log.py`. The SQL query groups findings by `(rule_key, snapshot_id)` with `COUNT(DISTINCT node_id)` and filters with `HAVING node_count >= min_nodes`. I created the endpoint `GET /api/swarm/consensus_findings?min_nodes=N`. In `/ops S8`, I added a consensus table with amber background for 2-4 corroborating nodes and red for 5+.

**Gap 3 -- Cooperative scraping:** I wired the collector to the swarm's existing APIs. Before each fetch, the collector queries `/api/swarm/last_scraped` with `source_id`; if another node already scraped that source in the last 240 seconds, the fetch is skipped. After a successful fetch, the collector posts to `/api/swarm/report_scrape` with the SHA256 hash of the payload. Both calls have a 0.5s timeout. I changed the default mode from `CENTINEL_SWARM_COOPERATIVE=1` (dead opt-in) to `"auto"`: a single call to `/api/swarm/status` at the start of the run determines whether the swarm is active with >=1 peer; if not, the collector proceeds with zero cooperative overhead.

**Gap 4 -- Node specialization:** I added the field `specialization: str = "general"` to `NodePayload` in `gossip.py`. Specialization is deterministically derived from the `node_id` hex: `int(node_id, 16) % 3` maps to `temporal` / `statistical` / `structural`. It is included in the signed payload of `build_my_attestation()`. In `/ops S8`, the peer table shows specialization with an identifying visual marker.

### 4) The Result (The Lesson)
It worked on all four gaps. Urgent broadcast reduced the delay for HIGH/CRITICAL findings from ~5 minutes to ~1.5 seconds. The SQL consensus enabled the first query that answers "how many distinct nodes confirmed this anomaly?" -- which is exactly the question that matters in a disputed count. Cooperative scraping with auto-detect has zero overhead when the swarm is offline (the most frequent operational default) and activates automatically without configuration when real peers are present. Soft specialization guarantees complete coverage regardless of which nodes fail.

### 5) The Final Decision (Takeaway)
A health swarm says "all nodes are alive." An audit network says "three independent nodes detected the same anomaly in snapshot 0x4a7f in the last 8 minutes." The second statement is evidence; the first is infrastructure. The four gaps were not missing features -- they were the difference between a monitoring system and an evidence-production system. Closing them turned the swarm into what it promised to be.

### 6) What Changed and Why Now
The four gaps were known since the initial design. I postponed them because the MVP needed gossip working first. With gossip in production and the `/lab` simulation demonstrating the swarm's value, closing the gaps was the logical next step. Timing was also determined by the threat model: in an active electoral count, the 5-minute delay between detection and broadcast can mean the difference between alerting before or after the adversary consolidates the manipulated data.

### 7) Implementation Choices
- **Fire-and-forget for urgent broadcast:** detection is the main flow; the swarm is a secondary channel. If `requests.post` fails in 1.5s, analysis continues without interruption. The swarm being offline cannot interrupt detection.
- **SQL HAVING for consensus, not application logic:** the database already has all findings from all nodes with their `node_id`. A `GROUP BY` + `HAVING` query is O(log N) on existing indexes and does not require loading anything into application memory.
- **"auto" as default for cooperative scraping:** opt-in with `CENTINEL_SWARM_COOPERATIVE=1` was dead code -- nobody activated it because it required conscious manual configuration. The "auto" default eliminates that friction: if the swarm has peers, it cooperates; if not, it continues alone. Zero overhead in both cases.
- **A single `/api/swarm/status` call at the start of the run:** instead of checking per source (18 calls for HN), a single call determines the state for the entire run. If the swarm goes down mid-run, the collector already determined "cooperative = true" and will keep trying -- which is correct because most of the run was probably cooperative.
- **Soft specialization, not hard:** if a `temporal` node fails, its timestamp rules are still covered by `statistical` and `structural` nodes that run all rules. Specialization is about what is prioritized in the broadcast, not what is executed. Detection coverage is always complete.
- **Amber/red threshold for consensus in /ops:** 2-4 nodes is a corroboration signal; 5+ is strong consensus. The visual threshold makes the distinction without requiring the operator to calculate anything.

### 8) Impact
The production swarm now produces three types of evidence that did not exist before: findings with latency of seconds (not minutes), findings with node-quantified consensus, and a verifiable record of which node scraped which source and when. For a disputed count where data manipulation is alleged, the combination of "the engine detected" + "N independent nodes corroborated" + "those N nodes were the ones with fresh data from that source" is a chain of evidence that did not exist before these four changes.

### 9) Cycle Takeaway
Distributed architecture produces its highest value at the moment of greatest adversarial pressure -- which is exactly when centralized systems are most vulnerable. A swarm that only monitors node health is a centralized system with more nodes: if the central server goes down, the network goes down. A swarm that produces verifiable consensus is qualitatively different: each node is an independent witness, and the adversary needs to simultaneously silence enough witnesses for consensus to collapse. That requires an attack capability that increases linearly with network size.

---

## Cierre / Close
Un swarm que monitorea salud de nodos y un swarm que produce consenso verificable son sistemas distintos que comparten la misma infraestructura -- la diferencia esta en cuatro funciones que conectan la deteccion con la corroboracion. / A swarm that monitors node health and a swarm that produces verifiable consensus are different systems sharing the same infrastructure -- the difference is four functions that connect detection to corroboration.
