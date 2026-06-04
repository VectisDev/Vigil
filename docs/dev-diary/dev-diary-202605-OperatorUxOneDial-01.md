# Dev Diary - 202605 - OperatorUxOneDial - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** TIER 5 -- Traducir la potencia a algo que la gente comun pueda operar / Translating power into something ordinary people can operate  
**Version interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto de esta entrada / Entry context:**  
Continuacion directa de `dev-diary-202605-CryptographicAnchoring-01.md`. TIER 4 cerro las grietas tecnicas; pero una promesa central del proyecto (gratuito, potente y *operable por una persona comun sin presupuesto ni experiencia*) seguia sin cumplirse: la seguridad real exigia recordar seis interruptores de entorno la noche de la eleccion. TIER 5 no anade defensas nuevas -- hace usable las que ya existen.

---

## [ES] Diario narrativo desde la ultima publicacion

### 1) Que cambio y por que ahora
TIER 4 era honesto tecnicamente pero deshonesto operativamente: para que la cadena fuera realmente inmanipulable, el operador debia configurar firma obligatoria, cert pinning del CNE, clave HMAC del breaker y anclaje externo -- cada uno una variable de entorno independiente. Un observador de base de #StartSmall no va a recordar eso a las 20:00 cuando empiezan a llegar actas. La distancia entre "el sistema es seguro si lo configuras perfecto" y "el sistema es seguro" era una mentira por omision.

Lo hice ahora porque la auditoria de TIER 4 me obligo a ser esceptico hostil de mi propia promesa, y la promesa a NDI / Carter Center / #StartSmall incluye explicitamente "sin que a la gente comun le cueste entenderlo".

### 2) Decisiones de implementacion
Regla inviolable intacta: nada de hashing destruido, sin retrocesos.

- **Reutilizar el dial que ya existe, no inventar uno nuevo.** `CENTINEL_MODE` ya gobernaba la cadencia de captura (`maintenance`/`monitoring`/`election`) en `config.js` y `.env.example`. Inventar un vocabulario paralelo (demo/citizen/fortress) habria roto esos consumidores -- un retroceso. En su lugar, `profiles.py` *deriva la postura de seguridad del mismo dial*, sin tocar su significado de cadencia. El riesgo del modo dicta la exigencia: `election` exige firma y pinning; `maintenance` los recomienda.
- **Contrato de no-regresion explicito.** `apply_profile_defaults()` solo rellena interruptores que el operador dejo sin definir (`os.environ` solo si vacio). Lo que el operador fija a mano siempre gana. Un perfil nunca afloja lo que el operador endurece. Verifique en prueba: con `CENTINEL_REQUIRE_SIGNATURE=false` explicito, modo `election` lo respeta.
- **Verificacion previa, no fe.** `doctor.py` + `centinel doctor`: resuelve el perfil activo y comprueba el entorno real contra el. Devuelve READY / WARNING / BLOCKED con remedios en lenguaje llano bilingue. Sale con codigo 1 si BLOCKED (scriptable en CI). Es lectura pura: nunca fabrica la clave que falta -- la reporta. Los sondeos de escritura usan temporales que se limpian solos.
- **Documentacion donde el operador ya mira.** En vez de un `centinel.yaml` que nada cargaria (codigo muerto), extendi el `.env.example` que `config.py` ya consume, documentando el modelo de un solo dial y los overrides opcionales.

### 3) Impacto operativo
Un observador de #StartSmall ahora hace: pone `CENTINEL_MODE=election`, corre `centinel doctor`, y el sistema le dice en lenguaje humano exactamente que falta antes del martes electoral -- o confirma que esta listo. NDI escribe un runbook de una linea. Carter Center lee un archivo y entiende la postura de seguridad completa. La potencia de TIER 4 ya no depende de memoria perfecta bajo presion.

### 4) Aprendizaje de ciclo
Seguridad que solo existe si el operador la configura perfecto bajo estres no es seguridad: es una trampa con buena documentacion. El trabajo de TIER 5 no fue criptografico sino de honestidad -- cerrar la distancia entre lo que el sistema puede hacer y lo que una persona comun realmente lograra que haga.

---

## [EN] Narrative diary since the previous publication

### 1) What changed and why now
TIER 4 was technically honest but operationally dishonest: real immutability required the operator to configure mandatory signing, CNE cert pinning, breaker HMAC key, and external anchoring -- each an independent env switch. A grassroots #StartSmall observer will not remember that at 20:00 when tally sheets start arriving. The gap between "secure if you configure it perfectly" and "secure" was a lie by omission.

I did it now because the TIER 4 audit forced me to be a hostile skeptic of my own promise, and the promise to NDI / Carter Center / #StartSmall explicitly includes "without ordinary people having to understand it."

### 2) Implementation choices
Inviolable rule intact: no hashing destroyed, no regressions.

- **Reuse the dial that already exists.** `CENTINEL_MODE` already governed capture cadence in `config.js` and `.env.example`. A parallel vocabulary would have broken those consumers -- a regression. Instead `profiles.py` *derives security posture from the same dial* without changing its cadence meaning. Stakes dictate strictness: `election` requires signing and pinning; `maintenance` recommends them.
- **Explicit non-regression contract.** `apply_profile_defaults()` only fills switches the operator left unset. Explicit operator config always wins; a profile never loosens what the operator tightened. I verified: explicit `CENTINEL_REQUIRE_SIGNATURE=false` is respected even in `election`.
- **Preflight, not faith.** `doctor.py` + `centinel doctor`: resolves the active profile, checks the real environment, returns READY / WARNING / BLOCKED with plain bilingual remedies, exits 1 on BLOCKED (CI-scriptable). Pure read: it reports a missing key, never fabricates it. Write probes self-clean.
- **Docs where the operator already looks.** Instead of a `centinel.yaml` nothing would load (dead code), I extended the `.env.example` that `config.py` already consumes.

### 3) Operational impact
A #StartSmall observer now: sets `CENTINEL_MODE=election`, runs `centinel doctor`, and is told in human language exactly what is missing before election day -- or that it is ready. NDI writes a one-line runbook. TIER 4's power no longer depends on perfect memory under pressure.

### 4) Cycle takeaway
Security that only exists if the operator configures it perfectly under stress is not security -- it is a well-documented trap. TIER 5 was not cryptographic work but honesty work: closing the distance between what the system can do and what an ordinary person will actually get it to do.

---

## Cierre de entrada / Entry close
Sin defensas nuevas, sin vocabulario nuevo, sin codigo muerto: reutilice el dial existente, garantice no-regresion, y anadi una autoauditoria que habla claro. La promesa "potente y operable por cualquiera" ahora es defendible.
