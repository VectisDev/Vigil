# Dev Diary - 202605 - CryptographicAnchoring - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Cierre de brechas críticas de inmutabilidad y DoS (TIER 4) / Closing critical immutability and DoS gaps (TIER 4)  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto de esta entrada / Entry context:**  
Retomamos el diario después de `dev-diary-202605-HostileEnvHardening-01.md`. Una auditoría escéptica posterior reveló que la promesa central — “verificable e inmanipulable” — tenía grietas reales y verificables en código. Esta entrada documenta TIER 4: no añadir features, sino cerrar las brechas que un adversario competente realmente explotaría.

---

## [ES] Diario narrativo desde la última publicación

### 1) Qué cambió y por qué ahora
La entrada anterior celebró el endurecimiento, pero una re-auditoría honesta encontró tres debilidades estructurales: (C1) la cadena hash era puramente local —un atacante con acceso al disco podía reescribir un snapshot y recalcular todo hacia adelante sin ser detectado, porque la firma era opcional con fallo silencioso y el anclaje estaba apagado—; (C2) `write_atomic()` no hacía fsync, así que un crash inducido podía perder evidencia sin error visible; (C3) el endpoint que demuestra integridad podía usarse como vector de DoS. Más dos ALTAS: estado del circuit breaker manipulable (A1) y ausencia de cert pinning para el CNE (A2).

Lo hicimos ahora porque la entrada anterior prometía más de lo que el sistema entregaba bajo el modelo de amenaza que nosotros mismos definimos. En defensa electoral, esa distancia es inaceptable.

### 2) Decisiones de implementación
Mismo principio inviolable: no destruir lógica de hashing, solo reforzar; sin retrocesos.

- **C2 primero (trivial y crítico):** `write_atomic()` ahora hace fsync del temporal y del directorio padre. Diez líneas que convierten “probablemente durable” en “durable”.
- **C1 — firma obligatoria ruidosa:** un solo flag, `CENTINEL_REQUIRE_SIGNATURE`. En modo elección, un fallo de firma detiene el snapshot en lugar de persistir evidencia huérfana. El control es un interruptor, no un manual.
- **C1 — anclaje de costo cero:** nuevo módulo `transparency.py`. Raíz de Merkle SHA-256 sobre toda la cadena, log append-only con fsync, y OpenTimestamps→Bitcoin opcional y gratuito con degradación elegante. Sin blockchain de pago, sin infraestructura. Si el log se commitea a un repo Git público, hereda timestamps externos que el operador no controla. Expuesto en `GET /audit/transparency`.
- **C3 — cache TTL stdlib:** 15 segundos sobre la verificación cara. Bajo flood, se devuelve el último resultado en lugar de re-escanear el filesystem. Cero dependencias.
- **A1 — HMAC en el estado del breaker:** sobre manipulación, el breaker se fuerza a OPEN (fail-closed) con alerta crítica. El atacante que edita el JSON para reabrir el DoS obtiene lo contrario de lo que busca.
- **A2 — cert pinning del CNE:** `assert_fingerprint` nativo de urllib3, activado con `CENTINEL_CNE_CERT_SHA256`. Un MITM estatal con CA comprometida es rechazado en el handshake.

### 3) Impacto operativo
La promesa “inmanipulable” ahora es honesta bajo el modelo de amenaza real:
- evidencia durable ante crash inducido,
- cadena anclada externamente sin costo,
- el endpoint de integridad ya no es un arma de DoS,
- el circuit breaker no se reinicia por manipulación,
- los resultados presidenciales no se pueden MITM en silencio.

Estratégicamente, esto cierra la distancia entre “el mejor prototipo de la región” e “infraestructura que un Estado no puede romper en silencio” — el salto que hace honesta la promesa a la UPNFM y financiable el proyecto.

### 4) Aprendizaje de ciclo
La lección dura de este ciclo: una auditoría que solo confirma lo que ya creías no es una auditoría. El valor estuvo en buscar activamente dónde la promesa fallaba, verificarlo en código (archivo:línea), y arreglarlo antes de que un adversario lo hiciera por nosotros. Robustez no es lo que afirmas; es lo que sobrevive a un escéptico hostil leyendo tu fuente.

---

## [EN] Narrative diary since the previous publication

### 1) What changed and why now
The previous entry celebrated hardening, but an honest re-audit found three structural weaknesses: (C1) the hash chain was purely local — a disk-access attacker could rewrite a snapshot and recompute everything forward undetected, because signing was optional with a silent failure and anchoring was off; (C2) `write_atomic()` did not fsync, so an induced crash could lose evidence with no visible error; (C3) the integrity endpoint could itself be turned into a DoS vector. Plus two HIGHs: tamperable circuit-breaker state (A1) and no cert pinning for CNE (A2).

We did this now because the previous entry promised more than the system delivered under the very threat model we defined. In electoral defense that gap is unacceptable.

### 2) Implementation choices
Same inviolable rule: never destroy hashing logic, only reinforce; no regressions.

- **C2 first (trivial, critical):** `write_atomic()` now fsyncs the temp file and the parent directory.
- **C1 — loud mandatory signing:** a single flag, `CENTINEL_REQUIRE_SIGNATURE`. In election mode a signing failure halts the snapshot instead of persisting orphaned evidence.
- **C1 — zero-cost anchor:** new `transparency.py`. SHA-256 Merkle root over the whole chain, fsync-durable append-only log, optional free OpenTimestamps→Bitcoin with graceful degradation. No paid blockchain, no infrastructure. Committed to a public Git repo it inherits operator-independent timestamps. Exposed at `GET /audit/transparency`.
- **C3 — stdlib TTL cache:** 15s over the expensive verification; a flood returns the last result instead of rescanning.
- **A1 — HMAC on breaker state:** on tampering the breaker is forced OPEN (fail-closed) with a critical alert.
- **A2 — CNE cert pinning:** urllib3 native `assert_fingerprint`, enabled by `CENTINEL_CNE_CERT_SHA256`.

### 3) Operational impact
The “tamper-proof” promise is now honest under the real threat model: durable evidence, externally anchored chain at zero cost, integrity endpoint no longer a DoS weapon, breaker not resettable by tampering, presidential results not silently MITM-able. This closes the distance between “best regional prototype” and “infrastructure a state cannot silently break.”

### 4) Cycle takeaway
The hard lesson: an audit that only confirms what you already believed is not an audit. The value was in actively hunting where the promise failed, verifying it in code, and fixing it before an adversary did. Robustness is not what you claim; it is what survives a hostile skeptic reading your source.

---

## Cierre de entrada / Entry close
Sin features nuevas, sin adornos: solo cerramos las grietas que importaban, con interruptores simples en vez de manuales, y a costo cero. La promesa ahora es defendible — técnica y honestamente.
