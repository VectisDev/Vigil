# Dev Diary - 202605 - PBKDF2ZeroTrustNoSupabase - 01

**Fecha aproximada / Approximate date:** 20-may-2026 / May 20, 2026  
**Fase / Phase:** Eliminar toda dependencia de Supabase y completar la auth sin servidor externo / Eliminating all Supabase dependency and completing auth without external server  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v11)  
**Rama / Branch:** dev-v11  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuación de `dev-diary-202605-AutonomousSelfHealingOps-01.md`. Con el healer en marcha, la última dependencia externa con datos de usuario era Supabase — que contradecía directamente la promesa "no guardamos información de nadie". / With the healer running, the last external dependency holding user data was Supabase — which directly contradicted the promise "we store no one's information."

---

## [ES]

### 1) El Problema (Contexto)
Supabase era la dependencia de autenticación de CENTINEL: almacenaba emails de sesión, tokens de usuario, y metadatos de login para el panel de admin, el replay, y el academico. Era una cuenta de tercero con acceso de admin que procesaba y guardaba datos personales de los operadores. La promesa pública de CENTINEL — "no guardamos información de nadie" — era estructuralmente falsa mientras Supabase existiera en el stack. No era una cuestión de si se usaba activamente o no: la infraestructura para almacenar datos personales existía, lo que significa que el riesgo existía, independientemente de la intención. Además, Supabase como dependencia contradecía el principio de zero-trust y cero dependencias externas que el resto del sistema había ido construyendo ciclo a ciclo.

### 2) La Hipótesis
PBKDF2-SHA256 via la Web Crypto API nativa del navegador, combinada con un archivo `web/access.json` que almacena únicamente hashes derivados (nunca contraseñas en texto plano), puede reemplazar toda la funcionalidad de autenticación que Supabase proveía — sin servidor externo, sin email, sin base de datos remota, sin cuenta de tercero. El navegador hace toda la derivación criptográfica localmente. El resultado: auth completamente client-side con zero data almacenada o transmitida a terceros.

### 3) El Experimento / Implementación
Se implementó PBKDF2-SHA256 via Web Crypto API en los tres módulos que usaban Supabase: `web/admin/`, `web/replay/`, y `web/academico/`. El sistema de acceso Seed 1 fue diseñado: 12 códigos de acceso de 24 caracteres cada uno, con solo sus hashes PBKDF2 almacenados en `web/access.json` — nunca los códigos originales. Las sesiones se manejan con sessionStorage con TTL de 8 horas. `github_sync.py` fue creado para reemplazar `supabase_sync.py` en la sincronización de datos. MFA/TOTP fue removido (era Supabase-only sin equivalente en el modelo client-side). `supabase-py` fue eliminado de `requirements.txt` y `pyproject.toml`. `heal_web.py` fue integrado al ciclo de CI. Toda la documentación fue actualizada para reflejar el nuevo modelo de auth.

### 4) El Resultado (La Lección)
Cero referencias funcionales a Supabase en todo el repositorio. La autenticación es completamente client-side: el hash vive en `web/access.json` como un archivo estático en el repositorio, la derivación PBKDF2 ocurre en el navegador del usuario, y ningún dato de usuario es transmitido ni almacenado en ningún servidor externo. El admin panel, el replay, y el academico viven completamente en GitHub Pages sin ningún backend. La promesa "no guardamos información de nadie" es ahora estructuralmente verdadera: no existe la infraestructura para hacerlo.

### 5) La Decisión Final (Takeaway)
La única forma de garantizar que no se guarda información de nadie es no tener la infraestructura para hacerlo. Una promesa de privacidad que depende de una política de uso ("no guardamos aunque podríamos") es una promesa que puede ser rota por un cambio de configuración, una actualización de dependencia, o una decisión futura. Una garantía estructural ("no existe el servidor que almacenaría") no puede ser rota sin cambiar la arquitectura. La privacidad por diseño tiene que ser estructural, no intencional.

### 6) Qué cambió y por qué ahora
Supabase fue eliminado porque era la última contradicción entre la promesa de privacidad de CENTINEL y su implementación real. No fue una decisión de ingeniería motivada por performance o costo — fue una decisión ética que requería una solución técnica. El costo de mantener Supabase no era el precio del plan: era la credibilidad de la promesa de privacidad que CENTINEL hace a los observadores electorales que lo usan. Eso no tiene precio.

### 7) Decisiones de implementación
- **PBKDF2-SHA256 con Web Crypto API nativa:** zero dependencias de terceros para la criptografía. La Web Crypto API está disponible en todos los navegadores modernos y es auditable por cualquier desarrollador web.
- **`access.json` con solo hashes, nunca texto plano:** el archivo que vive en el repositorio no contiene información que pueda comprometer el acceso. Si `access.json` es público, solo revela que existen ciertos hashes — no los códigos que los generaron.
- **Sesiones en sessionStorage con TTL de 8h:** al cerrar la pestaña, la sesión termina. No hay cookies persistentes, no hay localStorage, no hay estado que sobreviva al navegador.
- **Seed 1 como sistema de distribución:** 12 códigos permiten distribución a múltiples operadores con revocación granular — se puede rotar un código sin afectar a los otros. La distribución ocurre fuera de banda, nunca a través del sistema.
- **`github_sync.py` como reemplazo de `supabase_sync.py`:** la sincronización de datos electorales ahora usa el repositorio `centinel-data` en GitHub como destino, sin ningún servicio de base de datos externo.

### 8) Impacto
El admin panel de CENTINEL vive completamente en GitHub Pages sin ningún backend. Ningún servidor externo almacena nada. La promesa de privacidad es ahora verificable por cualquier auditor de seguridad que revise el código fuente: no hay llamadas a APIs externas en el flujo de autenticación, no hay endpoints que reciban credenciales, no hay base de datos que las almacene. La auditabilidad de la privacidad es completa.

### 9) Aprendizaje de ciclo
La privacidad por diseño no es una feature que se agrega al final del ciclo de desarrollo: es un constraint arquitectural que define qué soluciones son aceptables desde el principio. Agregar Supabase fue la decisión fácil en su momento — funciona, está documentado, tiene SDKs para todo. Eliminarlo fue la decisión correcta. La lección no es que Supabase sea malo: es que cualquier dependencia que procesa datos personales requiere una justificación explícita de por qué esa dependencia existe, y esa justificación tiene que sobrevivir la pregunta "¿qué pasa si alguien la audita?".

---

## [EN]

### 1) The Problem (Context)
Supabase was CENTINEL's authentication dependency: it stored session emails, user tokens, and login metadata for the admin panel, replay, and academico. It was a third-party account with admin access that processed and stored operators' personal data. CENTINEL's public promise — "we store no one's information" — was structurally false while Supabase existed in the stack. It was not a question of whether it was actively used or not: the infrastructure to store personal data existed, which means the risk existed, regardless of intent. Additionally, Supabase as a dependency contradicted the zero-trust and zero-external-dependency principle that the rest of the system had been building cycle by cycle.

### 2) The Hypothesis
PBKDF2-SHA256 via the browser's native Web Crypto API, combined with a `web/access.json` file that stores only derived hashes (never plaintext passwords), can replace all authentication functionality that Supabase provided — without an external server, without email, without a remote database, without a third-party account. The browser does all the cryptographic derivation locally. The result: fully client-side auth with zero data stored or transmitted to third parties.

### 3) The Experiment / Implementation
PBKDF2-SHA256 via Web Crypto API was implemented in the three modules that used Supabase: `web/admin/`, `web/replay/`, and `web/academico/`. The Seed 1 access system was designed: 12 access codes of 24 characters each, with only their PBKDF2 hashes stored in `web/access.json` — never the original codes. Sessions are managed with sessionStorage with an 8-hour TTL. `github_sync.py` was created to replace `supabase_sync.py` for data synchronization. MFA/TOTP was removed (it was Supabase-only with no client-side equivalent). `supabase-py` was removed from `requirements.txt` and `pyproject.toml`. `heal_web.py` was integrated into the CI cycle. All documentation was updated to reflect the new auth model.

### 4) The Result (The Lesson)
Zero functional references to Supabase in the entire repository. Authentication is completely client-side: the hash lives in `web/access.json` as a static file in the repository, PBKDF2 derivation happens in the user's browser, and no user data is transmitted or stored on any external server. The admin panel, replay, and academico live entirely on GitHub Pages without any backend. The promise "we store no one's information" is now structurally true: the infrastructure to do so does not exist.

### 5) The Final Decision (Takeaway)
The only way to guarantee that no one's information is stored is to not have the infrastructure to do it. A privacy promise that depends on a usage policy ("we don't store even though we could") is a promise that can be broken by a configuration change, a dependency update, or a future decision. A structural guarantee ("the server that would store it does not exist") cannot be broken without changing the architecture. Privacy by design must be structural, not intentional.

### 6) What changed and why now
Supabase was removed because it was the last contradiction between CENTINEL's privacy promise and its real implementation. It was not an engineering decision motivated by performance or cost — it was an ethical decision that required a technical solution. The cost of keeping Supabase was not the price of the plan: it was the credibility of the privacy promise that CENTINEL makes to the electoral observers who use it. That has no price.

### 7) Implementation choices
- **PBKDF2-SHA256 with native Web Crypto API:** zero third-party dependencies for cryptography. The Web Crypto API is available in all modern browsers and is auditable by any web developer.
- **`access.json` with only hashes, never plaintext:** the file living in the repository contains nothing that could compromise access. If `access.json` is public, it only reveals that certain hashes exist — not the codes that generated them.
- **Sessions in sessionStorage with 8h TTL:** closing the tab ends the session. No persistent cookies, no localStorage, no state that survives the browser.
- **Seed 1 as distribution system:** 12 codes allow distribution to multiple operators with granular revocation — one code can be rotated without affecting the others. Distribution happens out of band, never through the system.
- **`github_sync.py` as replacement for `supabase_sync.py`:** electoral data synchronization now uses the `centinel-data` repository on GitHub as destination, with no external database service.

### 8) Impact
CENTINEL's admin panel lives entirely on GitHub Pages without any backend. No external server stores anything. The privacy promise is now verifiable by any security auditor reviewing the source code: no calls to external APIs in the authentication flow, no endpoints that receive credentials, no database that stores them. Privacy auditability is complete.

### 9) Cycle takeaway
Privacy by design is not a feature added at the end of the development cycle: it is an architectural constraint that defines which solutions are acceptable from the start. Adding Supabase was the easy decision at the time — it works, it is documented, it has SDKs for everything. Removing it was the correct decision. The lesson is not that Supabase is bad: it is that any dependency that processes personal data requires an explicit justification for why that dependency exists, and that justification must survive the question "what happens if someone audits it?"

---

## Cierre / Close
La eliminación de Supabase no fue una optimización técnica: fue el momento en que la promesa de privacidad dejó de depender de la intención y pasó a depender de la arquitectura. / Removing Supabase was not a technical optimization: it was the moment the privacy promise stopped depending on intent and started depending on architecture.
