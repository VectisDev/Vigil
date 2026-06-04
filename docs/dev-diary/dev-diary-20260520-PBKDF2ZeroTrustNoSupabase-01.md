# Dev Diary - 202605 - PBKDF2ZeroTrustNoSupabase - 01

**Fecha aproximada / Approximate date:** 20-may-2026 / May 20, 2026  
**Fase / Phase:** Eliminar toda dependencia de Supabase y completar la auth sin servidor externo / Eliminating all Supabase dependency and completing auth without external server  
**Version interna / Internal version:** v0.1.x (ciclo dev-v11)  
**Rama / Branch:** dev-v11  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuacion de `dev-diary-202605-AutonomousSelfHealingOps-01.md`. Con el healer en marcha, la ultima dependencia externa con datos de usuario era Supabase -- que contradecia directamente la promesa "no guardamos informacion de nadie". / With the healer running, the last external dependency holding user data was Supabase -- which directly contradicted the promise "we store no one's information."

---

## [ES]

### 1) El Problema (Contexto)
Supabase era la dependencia de autenticacion de CENTINEL: almacenaba emails de sesion, tokens de usuario, y metadatos de login para el panel de admin, el replay, y el academico. Era una cuenta de tercero con acceso de admin que procesaba y guardaba datos personales de los operadores. La promesa publica de CENTINEL -- "no guardamos informacion de nadie" -- era estructuralmente falsa mientras Supabase existiera en el stack. No era una cuestion de si se usaba activamente o no: la infraestructura para almacenar datos personales existia, lo que significa que el riesgo existia, independientemente de la intencion. Ademas, Supabase como dependencia contradecia el principio de zero-trust y cero dependencias externas que yo habia ido construyendo ciclo a ciclo en el resto del sistema.

### 2) La Hipotesis
PBKDF2-SHA256 via la Web Crypto API nativa del navegador, combinada con un archivo `web/access.json` que almacena unicamente hashes derivados (nunca contrasenas en texto plano), puede reemplazar toda la funcionalidad de autenticacion que Supabase proveia -- sin servidor externo, sin email, sin base de datos remota, sin cuenta de tercero. El navegador hace toda la derivacion criptografica localmente. El resultado: auth completamente client-side con zero data almacenada o transmitida a terceros.

### 3) El Experimento / Implementacion
Implemente PBKDF2-SHA256 via Web Crypto API en los tres modulos que usaban Supabase: `web/admin/`, `web/replay/`, y `web/academico/`. Disene el sistema de acceso Seed 1: 12 codigos de acceso de 24 caracteres cada uno, con solo sus hashes PBKDF2 almacenados en `web/access.json` -- nunca los codigos originales. Las sesiones las manejo con sessionStorage con TTL de 8 horas. Cree `github_sync.py` para reemplazar `supabase_sync.py` en la sincronizacion de datos. Removi MFA/TOTP (era Supabase-only sin equivalente en el modelo client-side). Elimine `supabase-py` de `requirements.txt` y `pyproject.toml`. Integre `heal_web.py` al ciclo de CI. Actualice toda la documentacion para reflejar el nuevo modelo de auth.

### 4) El Resultado (La Leccion)
Cero referencias funcionales a Supabase en todo el repositorio. La autenticacion es completamente client-side: el hash vive en `web/access.json` como un archivo estatico en el repositorio, la derivacion PBKDF2 ocurre en el navegador del usuario, y ningun dato de usuario es transmitido ni almacenado en ningun servidor externo. El admin panel, el replay, y el academico viven completamente en GitHub Pages sin ningun backend. La promesa "no guardamos informacion de nadie" es ahora estructuralmente verdadera: no existe la infraestructura para hacerlo.

### 5) La Decision Final (Takeaway)
La unica forma de garantizar que no se guarda informacion de nadie es no tener la infraestructura para hacerlo. Una promesa de privacidad que depende de una politica de uso ("no guardamos aunque podriamos") es una promesa que puede ser rota por un cambio de configuracion, una actualizacion de dependencia, o una decision futura. Una garantia estructural ("no existe el servidor que almacenaria") no puede ser rota sin cambiar la arquitectura. La privacidad por diseno tiene que ser estructural, no intencional.

### 6) Que cambio y por que ahora
Elimine Supabase porque era la ultima contradiccion entre la promesa de privacidad de CENTINEL y su implementacion real. No fue una decision de ingenieria motivada por performance o costo -- fue una decision etica que requeria una solucion tecnica. El costo de mantener Supabase no era el precio del plan: era la credibilidad de la promesa de privacidad que CENTINEL hace a los observadores electorales que lo usan. Eso no tiene precio.

### 7) Decisiones de implementacion
- **PBKDF2-SHA256 con Web Crypto API nativa:** zero dependencias de terceros para la criptografia. La Web Crypto API esta disponible en todos los navegadores modernos y es auditable por cualquier desarrollador web.
- **`access.json` con solo hashes, nunca texto plano:** el archivo que vive en el repositorio no contiene informacion que pueda comprometer el acceso. Si `access.json` es publico, solo revela que existen ciertos hashes -- no los codigos que los generaron.
- **Sesiones en sessionStorage con TTL de 8h:** al cerrar la pestana, la sesion termina. No hay cookies persistentes, no hay localStorage, no hay estado que sobreviva al navegador.
- **Seed 1 como sistema de distribucion:** 12 codigos permiten distribucion a multiples operadores con revocacion granular -- se puede rotar un codigo sin afectar a los otros. La distribucion ocurre fuera de banda, nunca a traves del sistema.
- **`github_sync.py` como reemplazo de `supabase_sync.py`:** la sincronizacion de datos electorales ahora usa el repositorio `centinel-data` en GitHub como destino, sin ningun servicio de base de datos externo.

### 8) Impacto
El admin panel de CENTINEL vive completamente en GitHub Pages sin ningun backend. Ningun servidor externo almacena nada. La promesa de privacidad es ahora verificable por cualquier auditor de seguridad que revise el codigo fuente: no hay llamadas a APIs externas en el flujo de autenticacion, no hay endpoints que reciban credenciales, no hay base de datos que las almacene. La auditabilidad de la privacidad es completa.

### 9) Aprendizaje de ciclo
La privacidad por diseno no es una feature que se agrega al final del ciclo de desarrollo: es un constraint arquitectural que define que soluciones son aceptables desde el principio. Agregar Supabase fue la decision facil en su momento -- funciona, esta documentado, tiene SDKs para todo. Eliminarlo fue la decision correcta. La leccion no es que Supabase sea malo: es que cualquier dependencia que procesa datos personales requiere una justificacion explicita de por que esa dependencia existe, y esa justificacion tiene que sobrevivir la pregunta "que pasa si alguien la audita?".

---

## [EN]

### 1) The Problem (Context)
Supabase was CENTINEL's authentication dependency: it stored session emails, user tokens, and login metadata for the admin panel, replay, and academico. It was a third-party account with admin access that processed and stored operators' personal data. CENTINEL's public promise -- "we store no one's information" -- was structurally false while Supabase existed in the stack. It was not a question of whether it was actively used or not: the infrastructure to store personal data existed, which means the risk existed, regardless of intent. Additionally, Supabase as a dependency contradicted the zero-trust and zero-external-dependency principle that I had been building cycle by cycle in the rest of the system.

### 2) The Hypothesis
PBKDF2-SHA256 via the browser's native Web Crypto API, combined with a `web/access.json` file that stores only derived hashes (never plaintext passwords), can replace all authentication functionality that Supabase provided -- without an external server, without email, without a remote database, without a third-party account. The browser does all the cryptographic derivation locally. The result: fully client-side auth with zero data stored or transmitted to third parties.

### 3) The Experiment / Implementation
I implemented PBKDF2-SHA256 via Web Crypto API in the three modules that used Supabase: `web/admin/`, `web/replay/`, and `web/academico/`. I designed the Seed 1 access system: 12 access codes of 24 characters each, with only their PBKDF2 hashes stored in `web/access.json` -- never the original codes. I manage sessions with sessionStorage with an 8-hour TTL. I created `github_sync.py` to replace `supabase_sync.py` for data synchronization. I removed MFA/TOTP (it was Supabase-only with no client-side equivalent). I removed `supabase-py` from `requirements.txt` and `pyproject.toml`. I integrated `heal_web.py` into the CI cycle. I updated all documentation to reflect the new auth model.

### 4) The Result (The Lesson)
Zero functional references to Supabase in the entire repository. Authentication is completely client-side: the hash lives in `web/access.json` as a static file in the repository, PBKDF2 derivation happens in the user's browser, and no user data is transmitted or stored on any external server. The admin panel, replay, and academico live entirely on GitHub Pages without any backend. The promise "we store no one's information" is now structurally true: the infrastructure to do so does not exist.

### 5) The Final Decision (Takeaway)
The only way to guarantee that no one's information is stored is to not have the infrastructure to do it. A privacy promise that depends on a usage policy ("we don't store even though we could") is a promise that can be broken by a configuration change, a dependency update, or a future decision. A structural guarantee ("the server that would store it does not exist") cannot be broken without changing the architecture. Privacy by design must be structural, not intentional.

### 6) What changed and why now
I removed Supabase because it was the last contradiction between CENTINEL's privacy promise and its real implementation. It was not an engineering decision motivated by performance or cost -- it was an ethical decision that required a technical solution. The cost of keeping Supabase was not the price of the plan: it was the credibility of the privacy promise that CENTINEL makes to the electoral observers who use it. That has no price.

### 7) Implementation choices
- **PBKDF2-SHA256 with native Web Crypto API:** zero third-party dependencies for cryptography. The Web Crypto API is available in all modern browsers and is auditable by any web developer.
- **`access.json` with only hashes, never plaintext:** the file living in the repository contains nothing that could compromise access. If `access.json` is public, it only reveals that certain hashes exist -- not the codes that generated them.
- **Sessions in sessionStorage with 8h TTL:** closing the tab ends the session. No persistent cookies, no localStorage, no state that survives the browser.
- **Seed 1 as distribution system:** 12 codes allow distribution to multiple operators with granular revocation -- one code can be rotated without affecting the others. Distribution happens out of band, never through the system.
- **`github_sync.py` as replacement for `supabase_sync.py`:** electoral data synchronization now uses the `centinel-data` repository on GitHub as destination, with no external database service.

### 8) Impact
CENTINEL's admin panel lives entirely on GitHub Pages without any backend. No external server stores anything. The privacy promise is now verifiable by any security auditor reviewing the source code: no calls to external APIs in the authentication flow, no endpoints that receive credentials, no database that stores them. Privacy auditability is complete.

### 9) Cycle takeaway
Privacy by design is not a feature added at the end of the development cycle: it is an architectural constraint that defines which solutions are acceptable from the start. Adding Supabase was the easy decision at the time -- it works, it is documented, it has SDKs for everything. Removing it was the correct decision. The lesson is not that Supabase is bad: it is that any dependency that processes personal data requires an explicit justification for why that dependency exists, and that justification must survive the question "what happens if someone audits it?"

---

## Cierre / Close
La eliminacion de Supabase no fue una optimizacion tecnica: fue el momento en que la promesa de privacidad dejo de depender de la intencion y paso a depender de la arquitectura. / Removing Supabase was not a technical optimization: it was the moment the privacy promise stopped depending on intent and started depending on architecture.
