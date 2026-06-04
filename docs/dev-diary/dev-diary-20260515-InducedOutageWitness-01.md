# Dev Diary - 202605 - InducedOutageWitness - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Desnudar el corte como manipulacion / Exposing the cut as manipulation  
**Version interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuacion de `dev-diary-202605-MonthLongEndurance-01.md`. El sistema ya aguanta un mes hostil sin agotarse. Faltaba responder la pregunta operativa real: cuando un actor corrupto no puede alterar los numeros, intenta cegar al testigo. Esta entrada hace que el corte deje huella firmada e inmutable -- y aborda el punto estrategico: si esto resiste el peor escenario de Honduras, sirve para cualquier pais.

---

## [ES]

### 1) Que cambio y por que ahora
Un scraper ingenuo registra "no pude conectar" como un fallo cualquiera. En un conteo disputado eso es exactamente lo que un Estado corrupto quiere: cegar al observador sin dejar rastro. Anadi `core/connectivity.py`: cuando una descarga falla, un diagnostico **acotado y sin efectos secundarios** clasifica el *porque* -- inoperancia de la autoridad vs. corte dirigido (redireccion DNS, MITM de TLS, inyeccion de reset, blackhole de ruta). La clasificacion es conservadora: nunca afirma fraude, registra **senales** (IPs resueltas, huella TLS presentada vs. la fijada, modo exacto de fallo) en el mismo flujo firmado, append-only y a prueba de manipulacion que la evidencia. Nuevo endpoint publico `GET /audit/degradation` lo expone a observadores: un timeline inmutable de si el testigo fue cegado.

### 2) Decisiones de implementacion
- **Agnostico de pais desde el dia uno.** Sin host ni autoridad hardcodeada: el objetivo sale de la URL que ya se estaba descargando; las expectativas (IPs esperadas, cert fijado) salen de config. Var nueva generica `CENTINEL_PINNED_CERT_SHA256` con respaldo a la legada `CENTINEL_CNE_CERT_SHA256` (sin retroceso). El mismo codigo defiende una eleccion en cualquier pais -- exactamente tu punto: si resiste el peor escenario, se abstrae.
- **Resistente a la duracion.** Cada sondeo tiene timeout corto y duro y un numero de intentos acotado: el diagnostico jamas puede colgar un bucle de captura que debe correr un mes.
- **A prueba de SSRF.** Solo sondea el host:puerto exacto ya contactado; no sigue redirecciones; no toca direcciones influidas por un atacante.
- **Cero dependencias nuevas.** Solo `socket`/`ssl` de stdlib. La firma y el hashing se reutilizan, nunca se reescriben ni se debilitan.
- **Durabilidad identica a transparency.py:** fsync del archivo y del directorio padre; append-only por contrato.

### 3) La leccion dura del ciclo
La prueba en aislamiento revelo una grieta real, no de sandbox: si la dependencia de criptografia esta rota o **saboteada**, su backend nativo lanza un *panic* que NO es subclase de `Exception`. El `except Exception` no lo atrapaba, y eso habria tumbado el bucle de captura de un mes. Lo correcto en el modelo de amenaza hostil: la firma es enriquecimiento **opcional**; su fallo debe degradar a un registro *sin firmar pero inmutable*, nunca matar al testigo. Ahora `_maybe_sign` y `diagnose_and_record` atrapan `BaseException` deliberadamente (con justificacion escrita). Verificado: con el backend cripto reventado, el evento se registra igual, sin firma, y la captura no cae.

### 4) Sobre exponer al creador (tu preocupacion explicita)
Auditoria honesta del codigo: no hay phone-home, ni telemetria, ni analitica, ni endpoint del creador hardcodeado. Los unicos identificadores son el seudonimo `userf8a2c4` y un correo de proyecto en `pyproject.toml` -- ya pseudonimos. Las alertas Telegram/webhook son **opt-in del operador** con su propio token, no del creador. El `operator_id` por defecto es el neutro `default-operator` y las claves son por variable de entorno. Riesgo residual real: metadatos de commits de git (operativo, fuera del codigo) y que un operador firme con clave ligada a su identidad -- pero eso expone al operador desplegador, no al creador, y es configurable. Conclusion defendible: el codigo no te expone; la disciplina operativa (git, claves) es el resto.

---

## [EN]

### 1) What changed and why now
A naive scraper logs "couldn't connect" as an ordinary failure -- exactly what a corrupt state wants when it cannot rig the numbers: blind the witness without a trace. I added `core/connectivity.py`: on fetch failure a **bounded, side-effect-free** diagnosis classifies *why* -- the authority's own inoperancy vs. a targeted cut (DNS redirection, TLS MITM, reset injection, route blackhole). Conservative by design: it never asserts fraud, it records **signals** (resolved IPs, presented TLS fingerprint vs. the pinned one, exact failure mode) into the same signed, append-only, tamper-evident stream as the evidence. New public `GET /audit/degradation` exposes it: an immutable timeline of whether the witness was blinded.

### 2) Implementation choices
- **Country-agnostic from day one.** No hardcoded host/authority: the target comes from the URL already fetched; expectations come from config. New generic `CENTINEL_PINNED_CERT_SHA256` with fallback to legacy `CENTINEL_CNE_CERT_SHA256` (no regression). The same code defends an election anywhere -- your point exactly: if it survives the worst case, it abstracts.
- **Endurance-safe.** Hard short timeout and capped attempts per probe: the diagnosis can never wedge a month-long capture loop.
- **SSRF-safe.** Probes only the exact host:port already contacted; no redirects; no attacker-influenced addresses.
- **Zero new dependencies.** Stdlib `socket`/`ssl` only. Signing/hashing reused, never reimplemented or weakened.
- **Durability identical to transparency.py:** fsync file + parent dir; append-only by contract.

### 3) The hard lesson
Isolation testing exposed a real gap, not a sandbox quirk: if the crypto dependency is broken or **sabotaged**, its native backend raises a *panic* that is NOT an `Exception` subclass. `except Exception` missed it, which would have killed a month-long capture loop. The correct stance under the hostile threat model: signing is **optional** enrichment; its failure must degrade to an *unsigned-but-immutable* record, never kill the witness. `_maybe_sign` and `diagnose_and_record` now catch `BaseException` deliberately (with written rationale). Verified: with the crypto backend blown up, the event still records, unsigned, and capture does not fall.

### 4) On exposing the creator (your explicit concern)
Honest code audit: no phone-home, telemetry, analytics, or hardcoded creator endpoint. The only identifiers are the pseudonym `userf8a2c4` and a project email in `pyproject.toml` -- already pseudonymous. Telegram/webhook alerts are **operator opt-in** with the operator's own token, not the creator's. Default `operator_id` is the neutral `default-operator`; keys are env-driven. Real residual risk: git commit metadata (operational, outside code) and an operator signing with an identity-linked key -- but that exposes the deploying operator, not the creator, and is configurable. Defensible conclusion: the code does not expose you; operational discipline (git, keys) covers the rest.

---

## Cierre / Close
El corte ya no es silencio: es una linea firmada e inmutable que un observador internacional puede leer. Agnostico de pais, resistente a la duracion y a una dependencia saboteada, sin exponer al creador por codigo. La promesa "operar estable y desnudar manipulaciones sin caer ni exponerse" es defendible -- y, por diseno, exportable a cualquier pais.
