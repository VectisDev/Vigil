# Dev Diary - 202605 - HostileEnvHardening - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Endurecimiento integral para ambiente hostil y auditabilidad pública (TIER 1-3) / End-to-end hardening for hostile environments and public auditability (TIER 1-3)  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto de esta entrada / Entry context:**  
Retomamos el diario después de `dev-diary-202602-SecurityCiHardening-01.md`. Si la entrada anterior protegió la credibilidad del “verde” en CI, esta cierra un ciclo mucho más profundo: preparar a Centinel para defender una elección real en un ambiente hostil, sin margen de error. El trabajo se organizó en tres niveles (TIER 1: seguridad fundacional, TIER 2: verificabilidad independiente, TIER 3: resistencia y adoptabilidad), todos sobre dev-v9.

---

## [ES] Diario narrativo desde la última publicación

### 1) Qué cambió y por qué ahora
Desde la estabilización de CI, la pregunta dejó de ser “¿pasan los tests?” y pasó a ser “¿sobrevive esto a un adversario que quiere romper una elección?”. Esa pregunta cambia todo: ya no basta con código correcto, hace falta código que falle de forma segura, que sea reproducible por terceros y que no se pueda manipular silenciosamente.

Auditamos el sistema buscando puntos de falla, debilidades e incoherencias, y atacamos tres frentes en orden:
- **TIER 1 (seguridad fundacional):** se eliminó por completo el módulo de autenticación, porque un sistema ciudadano de datos públicos no debe tener credenciales (había además una contraseña predecible y un credencial hardcodeado). Se hicieron atómicas las cuatro rutas críticas de persistencia (snapshot, hash, checkpoint, backup) y se añadió un lock cross-process sobre el checkpoint para entornos multi-instancia.
- **TIER 2 (verificabilidad):** se añadió validación estricta de formato SHA-256, semántica strict-fail en la verificación de la cadena (con `broken_at` + ruta para precisión forense), timestamps de fallback con orden total (microsegundo UTC + contador monotónico), persistencia del circuit breaker entre reinicios y, sobre todo, endpoints públicos `/audit/*` sin autenticación para verificación independiente.
- **TIER 3 (resistencia y adoptabilidad):** thread safety en el rotador de proxies, rotación de logs del honeypot a prueba de colisiones, validación de esquema de configuración con Pydantic, un despliegue demo verificable en 5 minutos y documentación académica formal para la alianza con la UPNFM.

### 2) Decisiones de implementación
El criterio rector fue explícito y se respetó sin excepción: **prohibido destruir lógica de hashing o archivos; solo mejora/optimización; si el cambio implica retroceso, no se procede.**

- **Eliminar la autenticación en lugar de parchearla.** Un sistema público no necesita login; mantener auth era una contradicción filosófica y una superficie de ataque. La paradoja se resolvió por eliminación, no por mitigación.
- **Atomicidad vía `write_atomic()` + tempfile/fsync/rename.** Una escritura parcial en una snapshot es evidencia corrupta; preferimos fallar sin escribir a escribir algo no verificable.
- **Strict-fail en la cadena.** Antes la verificación podía continuar tras una discrepancia; ahora se detiene en el primer punto roto y reporta índice y ruta. Para una auditoría forense, “dónde se rompió” vale más que “cuántas pasaron”.
- **Endpoints públicos sin auth como decisión de diseño, no omisión.** La transparencia es el modelo de amenaza invertido: cuanto más fácil sea verificar, más caro es mentir.
- **Validación de config en boot.** Un atacante que reescribe `proxies.yaml` o baja un timeout a 0 ahora es detectado al arrancar, no durante la elección.

### 3) Impacto operativo
El impacto es estratégico, no cosmético:
- cero vulnerabilidades de autenticación (superficie eliminada),
- integridad de datos garantizada incluso ante crash o concurrencia,
- la cadena de custodia es reproducible por cualquier observador externo (OEA, UE, Carter Center, auditores ciudadanos, academia),
- el circuit breaker ya no es vulnerable a un “restart loop” como vector de DoS,
- y un investigador de la UPNFM puede reproducir matemáticamente la integridad y publicarlo.

En términos de posicionamiento regional, esto mueve a Centinel de un prototipo defendible a infraestructura de defensa democrática verificable: el competidor más cercano en LATAM no ofrece verificabilidad criptográfica open-source.

### 4) Aprendizaje de ciclo
La lección de este ciclo es distinta a las anteriores: en un ambiente hostil **no hace falta ser invulnerable, hace falta ser verificable**. Cada ataque detectado y documentado se convierte en evidencia de que el sistema funciona. La seguridad por oscuridad se invierte: aquí la fortaleza es que todo pueda comprobarse, y que la prueba la respalde una universidad.

---

## [EN] Narrative diary since the previous publication

### 1) What changed and why now
After CI stabilization, the question shifted from “do the tests pass?” to “does this survive an adversary trying to break an election?”. That reframing changes everything: correct code is not enough; the code must fail safely, be reproducible by third parties, and resist silent tampering.

We audited the system for failure points, weak spots, and inconsistencies, then attacked three workstreams in order:
- **TIER 1 (foundational security):** fully removed the authentication module (a public citizen data system should not have credentials — there was also a predictable password and a hardcoded credential). Made the four critical persistence paths atomic (snapshot, hash, checkpoint, backup) and added a cross-process lock on the checkpoint for multi-instance setups.
- **TIER 2 (verifiability):** added strict SHA-256 format validation, strict-fail chain verification (`broken_at` + path for forensic precision), totally-ordered fallback timestamps (microsecond UTC + monotonic counter), circuit-breaker state persistence across restarts, and — most importantly — public unauthenticated `/audit/*` endpoints for independent verification.
- **TIER 3 (resilience and adoptability):** proxy rotator thread safety, collision-safe honeypot log rotation, Pydantic config schema validation, a 5-minute verifiable demo deployment, and formal academic documentation for the UPNFM partnership.

### 2) Implementation choices
The governing rule was explicit and honored without exception: **no destruction of hashing logic or files; improvement/optimization only; if a change implies regression, do not proceed.**

- **Remove auth instead of patching it.** A public system needs no login; keeping auth was a philosophical contradiction and an attack surface. The paradox was resolved by removal, not mitigation.
- **Atomicity via `write_atomic()` + tempfile/fsync/rename.** A partial write to a snapshot is corrupt evidence; we prefer failing without writing over writing something unverifiable.
- **Strict-fail on the chain.** Verification used to continue past a mismatch; now it stops at the first break and reports index and path. For forensic audit, “where it broke” beats “how many passed”.
- **Public no-auth endpoints as a design decision, not an omission.** Transparency is the inverted threat model: the easier it is to verify, the more expensive it is to lie.
- **Config validation at boot.** An attacker rewriting `proxies.yaml` or lowering a timeout to 0 is now caught at startup, not during the election.

### 3) Operational impact
The impact is strategic, not cosmetic:
- zero authentication vulnerabilities (surface eliminated),
- data integrity guaranteed even under crash or concurrency,
- chain of custody reproducible by any external observer (OAS, EU, Carter Center, citizen auditors, academia),
- the circuit breaker is no longer vulnerable to a restart-loop DoS vector,
- and a UPNFM researcher can mathematically reproduce integrity and publish it.

In regional positioning terms, this moves Centinel from a defensible prototype to verifiable democratic-defense infrastructure: the nearest LATAM peer offers no open-source cryptographic verifiability.

### 4) Cycle takeaway
This cycle’s lesson differs from previous ones: in a hostile environment **you do not need to be invulnerable, you need to be verifiable**. Every detected and documented attack becomes evidence the system works. Security-by-obscurity is inverted here: the strength is that everything can be checked, and that the proof is backed by a university.

---

## Cierre de entrada / Entry close
Mismo principio de siempre, llevado a su consecuencia más exigente: cambios deliberados, razones explícitas y mejoras acumulativas — esta vez con un objetivo concreto e innegociable, defender una elección real sin margen de error.
