# Dev Diary - 202605 - CryptographicAnchoring - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Cierre de brechas criticas de inmutabilidad y DoS (TIER 4) / Closing critical immutability and DoS gaps (TIER 4)  
**Version interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto de esta entrada / Entry context:**  
Retomo el diario despues de `dev-diary-202605-HostileEnvHardening-01.md`. Una auditoria esceptica posterior revelo que la promesa central -- "verificable e inmanipulable" -- tenia grietas reales y verificables en codigo. Esta entrada documenta TIER 4: no anadir features, sino cerrar las brechas que un adversario competente realmente explotaria.

---

## [ES] Diario narrativo desde la ultima publicacion

### 1) Que cambio y por que ahora
La entrada anterior celebro el endurecimiento, pero una re-auditoria honesta que hice encontro tres debilidades estructurales: (C1) la cadena hash era puramente local --un atacante con acceso al disco podia reescribir un snapshot y recalcular todo hacia adelante sin ser detectado, porque la firma era opcional con fallo silencioso y el anclaje estaba apagado--; (C2) `write_atomic()` no hacia fsync, asi que un crash inducido podia perder evidencia sin error visible; (C3) el endpoint que demuestra integridad podia usarse como vector de DoS. Mas dos ALTAS: estado del circuit breaker manipulable (A1) y ausencia de cert pinning para el CNE (A2).

Lo hice ahora porque la entrada anterior prometia mas de lo que el sistema entregaba bajo el modelo de amenaza que yo mismo defini. En defensa electoral, esa distancia es inaceptable.

### 2) Decisiones de implementacion
Mismo principio inviolable: no destruir logica de hashing, solo reforzar; sin retrocesos.

- **C2 primero (trivial y critico):** `write_atomic()` ahora hace fsync del temporal y del directorio padre. Diez lineas que convierten "probablemente durable" en "durable".
- **C1 -- firma obligatoria ruidosa:** un solo flag, `CENTINEL_REQUIRE_SIGNATURE`. En modo eleccion, un fallo de firma detiene el snapshot en lugar de persistir evidencia huerfana. El control es un interruptor, no un manual.
- **C1 -- anclaje de costo cero:** nuevo modulo `transparency.py`. Raiz de Merkle SHA-256 sobre toda la cadena, log append-only con fsync, y OpenTimestamps->Bitcoin opcional y gratuito con degradacion elegante. Sin blockchain de pago, sin infraestructura. Si el log se commitea a un repo Git publico, hereda timestamps externos que el operador no controla. Expuesto en `GET /audit/transparency`.
- **C3 -- cache TTL stdlib:** 15 segundos sobre la verificacion cara. Bajo flood, se devuelve el ultimo resultado en lugar de re-escanear el filesystem. Cero dependencias.
- **A1 -- HMAC en el estado del breaker:** sobre manipulacion, el breaker se fuerza a OPEN (fail-closed) con alerta critica. El atacante que edita el JSON para reabrir el DoS obtiene lo contrario de lo que busca.
- **A2 -- cert pinning del CNE:** `assert_fingerprint` nativo de urllib3, activado con `CENTINEL_CNE_CERT_SHA256`. Un MITM estatal con CA comprometida es rechazado en el handshake.

### 3) Impacto operativo
La promesa "inmanipulable" ahora es honesta bajo el modelo de amenaza real:
- evidencia durable ante crash inducido,
- cadena anclada externamente sin costo,
- el endpoint de integridad ya no es un arma de DoS,
- el circuit breaker no se reinicia por manipulacion,
- los resultados presidenciales no se pueden MITM en silencio.

Estrategicamente, esto cierra la distancia entre "el mejor prototipo de la region" e "infraestructura que un Estado no puede romper en silencio" -- el salto que hace honesta la promesa a la UPNFM y financiable el proyecto.

### 4) Aprendizaje de ciclo
La leccion dura de este ciclo: una auditoria que solo confirma lo que ya creias no es una auditoria. El valor estuvo en buscar activamente donde la promesa fallaba, verificarlo en codigo (archivo:linea), y arreglarlo antes de que un adversario lo hiciera por mi. Robustez no es lo que afirmas; es lo que sobrevive a un esceptico hostil leyendo tu fuente.

---

## [EN] Narrative diary since the previous publication

### 1) What changed and why now
The previous entry celebrated hardening, but an honest re-audit I conducted found three structural weaknesses: (C1) the hash chain was purely local -- a disk-access attacker could rewrite a snapshot and recompute everything forward undetected, because signing was optional with a silent failure and anchoring was off; (C2) `write_atomic()` did not fsync, so an induced crash could lose evidence with no visible error; (C3) the integrity endpoint could itself be turned into a DoS vector. Plus two HIGHs: tamperable circuit-breaker state (A1) and no cert pinning for CNE (A2).

I did this now because the previous entry promised more than the system delivered under the very threat model I defined. In electoral defense that gap is unacceptable.

### 2) Implementation choices
Same inviolable rule: never destroy hashing logic, only reinforce; no regressions.

- **C2 first (trivial, critical):** `write_atomic()` now fsyncs the temp file and the parent directory.
- **C1 -- loud mandatory signing:** a single flag, `CENTINEL_REQUIRE_SIGNATURE`. In election mode a signing failure halts the snapshot instead of persisting orphaned evidence.
- **C1 -- zero-cost anchor:** new `transparency.py`. SHA-256 Merkle root over the whole chain, fsync-durable append-only log, optional free OpenTimestamps->Bitcoin with graceful degradation. No paid blockchain, no infrastructure. Committed to a public Git repo it inherits operator-independent timestamps. Exposed at `GET /audit/transparency`.
- **C3 -- stdlib TTL cache:** 15s over the expensive verification; a flood returns the last result instead of rescanning.
- **A1 -- HMAC on breaker state:** on tampering the breaker is forced OPEN (fail-closed) with a critical alert.
- **A2 -- CNE cert pinning:** urllib3 native `assert_fingerprint`, enabled by `CENTINEL_CNE_CERT_SHA256`.

### 3) Operational impact
The "tamper-proof" promise is now honest under the real threat model: durable evidence, externally anchored chain at zero cost, integrity endpoint no longer a DoS weapon, breaker not resettable by tampering, presidential results not silently MITM-able. This closes the distance between "best regional prototype" and "infrastructure a state cannot silently break."

### 4) Cycle takeaway
The hard lesson: an audit that only confirms what you already believed is not an audit. The value was in actively hunting where the promise failed, verifying it in code, and fixing it before an adversary did it for me. Robustness is not what you claim; it is what survives a hostile skeptic reading your source.

---

## Cierre de entrada / Entry close
Sin features nuevas, sin adornos: solo cerre las grietas que importaban, con interruptores simples en vez de manuales, y a costo cero. La promesa ahora es defendible -- tecnica y honestamente.
