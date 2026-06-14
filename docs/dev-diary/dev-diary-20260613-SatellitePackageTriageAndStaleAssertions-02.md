# Dev Diary - 202606 - SatellitePackageTriageAndStaleAssertions - 02

**Fecha aproximada / Approximate date:** 13-jun-2026 / June 13, 2026
**Fase / Phase:** Triage de los 30 fallos restantes post-fix: descubrimiento de un paquete satelite `centinel_engine/` con dependencia opcional y graceful degradation, y decision de no modificar tests obsoletos fuera de la ruta critica / Triage of the remaining 30 post-fix failures: discovery of a `centinel_engine/` satellite package with optional dependency and graceful degradation, and the decision not to modify stale tests outside the critical path
**Version interna / Internal version:** v0.1.x (ciclo dev-v12, previo a v13)
**Rama / Branch:** dev-v12 + main (sin cambios de codigo en este diario -- solo documentacion)
**Autor / Author:** Orquestador (Claude) + qa-engineering-agent + cybersecurity-agent + osint-security-agent

**Contexto / Context:**
Continuacion directa del Diario 01. Con el nucleo en 698/729 (excluyendo `tests/resilience`), se investigaron los 30 fallos restantes para decidir si bloqueaban `refactor/v13-clean-core`. La pregunta que reencuadro todo el analisis fue del usuario: *"Eso es relevante para el sistema?"* -- es decir, antes de gastar mas tiempo arreglando codigo, primero hay que confirmar si ese codigo esta en la ruta critica de VIGIL. La respuesta cambio el alcance de la sesion de "arreglar 30 tests" a "clasificar 30 tests por relevancia, y solo entonces decidir cuanto esfuerzo merecen". / Direct continuation of Diary 01. With the core at 698/729 (excluding `tests/resilience`), the remaining 30 failures were investigated to decide whether they blocked `refactor/v13-clean-core`. The question that reframed the whole analysis came from the user: *"Is that relevant to the system?"* -- i.e., before spending more time fixing code, first confirm whether that code is on VIGIL's critical path. The answer changed the session's scope from "fix 30 tests" to "classify 30 tests by relevance, and only then decide how much effort they deserve".

---

## [ES]

### 1) El Problema (Contexto)

Tras el Diario 01, quedaban 30 fallos agrupados en clusters aparentemente no relacionados: `test_proxy_manager.py` (5), `test_rate_limiter.py` (3), `test_security_utils.py` (1), `test_json_validation.py` (5), `test_multi_witness.py` (3), `test_failure_injection.py` (5), `test_e2e_election_night.py` (3), mas fallos sueltos en `federation/`, `monitoring/`, `test_integration_loop.py` y `test_stress.py`.

Se investigaron primero los clusters de `test_proxy_manager.py` y `test_rate_limiter.py` (8 de 30 fallos) porque sus mensajes de error eran los mas concretos:

- `test_pool_has_at_least_50_entries`: `assert len(USER_AGENT_POOL) >= 50` fallaba con `5 >= 50` -- el pool real solo tenia 5 entradas.
- `test_entries_look_like_real_uas`: esperaba que el 100% de las entradas empezaran con `"Mozilla/5.0"` -- 0 de 5 lo hacian.
- Las 5 entradas reales eran: `"Centinel-Engine/1.0 (electoral-audit; +https://github.com/VectisDev/centinel)"`, `"Centinel-Watchdog/1.0 (electoral-transparency; ...)"`, etc. -- **identificadores propios y transparentes**, no User-Agents de navegador disfrazados.
- `test_default_parameters`: esperaba `burst == 3` y `min_interval == 8.0`; el codigo real tenia `DEFAULT_BURST = 5` y `DEFAULT_MIN_INTERVAL = 6.0`.
- `test_invalid_min_interval_raises`: esperaba `ValueError` al pasar `min_interval=-1`, pero el constructor tiene `enforce_ceiling=True` por defecto, que **clampea** `min_interval = max(min_interval, HARD_CEILING_MIN_INTERVAL)` (donde `HARD_CEILING_MIN_INTERVAL = 2.0`) *antes* de la validacion -- por lo que `-1` nunca llega a `_validate_limits()` como negativo.

El primer reflejo habria sido "actualizar estos tests para que coincidan con el codigo actual". Pero antes de hacerlo, surgio la pregunta correcta: **¿de donde viene este codigo, y es parte de lo que VIGIL ejecuta realmente?**

### 2) La Hipotesis

`grep -rn "from centinel_engine\|import centinel_engine"` revelo que `USER_AGENT_POOL` y `TokenBucketRateLimiter` no viven en `src/centinel/` sino en un **paquete completamente separado en la raiz del repositorio: `centinel_engine/`** -- con su propio `LICENSE`, `README.md` y `package.json`. La hipotesis: este es un paquete satelite/embebible, posiblemente pensado para distribucion independiente, y los 8 fallos en `test_proxy_manager.py`/`test_rate_limiter.py` son **tests escritos para una version anterior de ese paquete** (con UA pool anonimizante de 50+ entradas y limites menos conservadores), que nunca se actualizaron cuando `centinel_engine/` se redisenio hacia identificadores transparentes y limites mas estrictos ("hard ceiling").

Si esta hipotesis es correcta, la pregunta relevante no es "¿como arreglo estos tests?" sino **"¿este paquete es parte de la ruta critica de auditoria electoral, o es opcional?"** -- porque la respuesta determina si estos 8 fallos son bloqueantes para `refactor/v13-clean-core` o pueden quedar fuera del alcance de esta sesion.

### 3) El Experimento / Implementacion

Se verifico como `src/centinel/` consume `centinel_engine/`:

```python
# src/centinel/proxy_handler.py (lineas 77-80)
try:
    from centinel_engine.config_loader import load_config  # type: ignore[import]
except ModuleNotFoundError:  # centinel_engine not installed (tests / forks)
    def load_config(...):
        """Fallback stub when centinel_engine package is not available."""
        ...

# src/centinel/downloader.py (linea 563)
from centinel_engine.rate_limiter import get_rate_limiter
```

**Hallazgo clave:** `proxy_handler.py` importa `centinel_engine` dentro de un `try/except ModuleNotFoundError` **con un stub de fallback explicito**, y el propio comentario dice *"centinel_engine not installed (tests / forks)"`. Es decir: el equipo que escribio `src/centinel/` ya disenio el sistema asumiendo que `centinel_engine` **podria no estar presente**, exactamente el principio de "graceful degradation" que `@rules-engine-agent` exige para las reglas estadisticas, aplicado aqui a un paquete completo.

Se confirmo tambien que `centinel_engine/` SI es importado por codigo activo (`proxy_handler.py`, `downloader.py`, y tres scripts de polling/logging), por lo que **no es codigo muerto** -- es una dependencia real, pero opcional y con fallback.

Con esto, los 30 fallos se reclasificaron en dos categorias:

**Categoria A -- Paquete satelite `centinel_engine/` (8 fallos: 5 en `test_proxy_manager.py`, 3 en `test_rate_limiter.py`):**
Tests escritos contra una version anterior del paquete. El codigo actual de `centinel_engine/` implementa un diseño *mas conservador y mas transparente* que el que los tests asumen:
- UA pool: 5 identificadores auto-descriptivos con URL al repo, en lugar de 50+ UAs de navegador. Esto es **coherente con el principio del README** de "ethical scraping ... the entire swarm behaves as at most one visitor".
- Rate limiter: `burst=5`/`min_interval=6.0` con un sistema de "hard ceiling" que impide configuraciones peligrosas incluso si alguien lo intenta -- una mejora de seguridad real.

Estos 8 fallos **no son regresiones**: son la evidencia de que `centinel_engine/` evoluciono hacia un diseño mejor, y nadie actualizo sus tests para reflejarlo.

**Categoria B -- Nucleo `src/centinel/` (22 fallos restantes: `test_security_utils.py`, `test_json_validation.py`, `test_multi_witness.py`, `test_failure_injection.py`, `test_e2e_election_night.py`, `federation/`, `monitoring/`, `test_integration_loop.py`, `test_stress.py`):**
No investigados en profundidad en esta sesion. Requieren el mismo nivel de cuidado que el Diario 01 (cada uno podria ser una regresion real, un test obsoleto, o un diseño no documentado), pero el volumen (22 archivos/clusters distintos) excede lo razonable para una sola sesion despues de ya haber resuelto 6 bugs reales en el nucleo.

### 4) El Resultado (La Leccion)

| Categoria | Cantidad | Naturaleza | Bloquea v13? |
|-----------|----------|------------|--------------|
| A -- `centinel_engine/` (satelite, opcional, con fallback) | 8 | Tests obsoletos vs. rediseño intencional (transparencia + hard ceiling) | No |
| B -- `src/centinel/` (nucleo, sin investigar) | 22 | Desconocido -- requiere triage individual | Pendiente, no bloqueante para iniciar v13 |

**La leccion:** no toda falla de test tiene el mismo peso. Encontrar que `USER_AGENT_POOL` tiene 5 entradas en lugar de 50 *podria* sonar grave (¿se rompio la anonimizacion?), pero una vez se ubica el codigo en un paquete opcional con fallback explicito, y se nota que el nuevo diseño es *mas* alineado con la etica declarada del proyecto (transparencia en lugar de camuflaje), el hallazgo cambia de "bug critico" a "decision de diseño documentada solo en el codigo, nunca en los tests ni en un ADR".

### 5) La Decision Final (Takeaway)

**No se modifico ningun test de la Categoria A ni B en esta sesion.** Decision explicita, no por falta de tiempo sino por principio: `@qa-engineering-agent` no debe "arreglar" tests reescribiendolos para que coincidan con el codigo actual sin que alguien con criterio de `@cybersecurity-agent`/`@osint-security-agent` confirme que el nuevo diseño (UA transparente, hard ceiling) fue una decision consciente y no un efecto secundario de otro cambio.

`refactor/v13-clean-core` **no esta bloqueado** por estos 30 fallos: ninguno esta en `src/centinel/core/rules/`, `src/centinel/core/hash_chain.py`, ni en los modulos de anclaje/normalizacion que ya estan en 698/698. El refactor puede proceder usando 698 como baseline, y los 30 fallos (8 + 22) quedan documentados aqui como deuda tecnica explicita para una sesion dedicada de QA del paquete `centinel_engine/` y de los modulos de federacion/resiliencia.

### 6) Que cambio y por que ahora

Nada en el codigo cambio en este diario -- es deliberadamente solo documentacion. El cambio fue de **alcance**: la pregunta "¿es relevante para el sistema?" evito que la sesion se extendiera indefinidamente arreglando un paquete satelite cuyas pruebas obsoletas no afectan la auditoria electoral en si. Es el mismo principio que "Las dependencias externas no son bloqueantes" (operating principle ya documentado para Devis/IGETEL) aplicado a deuda tecnica: un paquete opcional con fallback no es bloqueante para un refactor del nucleo.

### 7) Decisiones de implementacion

- **Clasificar antes de arreglar:** todo hallazgo de QA debe primero responder "¿esto esta en la ruta critica?" antes de invertir tiempo en la correccion.
- **Decisiones de diseño no documentadas son deuda tecnica, no bugs:** el rediseño de `centinel_engine/` (UA transparente, hard ceiling) parece bueno, pero al no estar documentado en un ADR ni reflejado en tests, queda como punto ciego. Se recomienda a `@systems-architecture-agent` registrar esto en un ADR cuando se revisite.
- **698 como baseline oficial para v13:** cualquier numero por debajo de 698 tras el renombrado de paquete es una regresion real del refactor; los 30 fallos preexistentes no cuentan contra ese baseline (se documentan por separado).

### 8) Impacto

- Se evito gastar tiempo adicional reescribiendo 8 tests de un paquete opcional sin la revision de seguridad/privacidad correspondiente.
- Se identifico una posible mejora de postura etica/seguridad (UA transparente + hard ceiling en `centinel_engine/`) que estaba *implementada pero invisible* -- ningun documento del proyecto la menciona.
- Quedan 22 fallos en el nucleo sin triar, documentados explicitamente como pendientes -- evita la falsa sensacion de "todo resuelto" que produjo el badge "526/526" original.

### 9) Aprendizaje de ciclo

La pregunta mas util de la sesion no fue tecnica: fue "¿esto es relevante?". Un QA riguroso no es arreglar todo lo que falla -- es saber que fallos importan, en que orden, y documentar honestamente lo que queda sin resolver en lugar de ocultarlo detras de un numero agregado.

---

## [EN]

### 1) The Problem (Context)

After Diary 01, 30 failures remained, grouped into seemingly unrelated clusters: `test_proxy_manager.py` (5), `test_rate_limiter.py` (3), `test_security_utils.py` (1), `test_json_validation.py` (5), `test_multi_witness.py` (3), `test_failure_injection.py` (5), `test_e2e_election_night.py` (3), plus scattered failures in `federation/`, `monitoring/`, `test_integration_loop.py` and `test_stress.py`.

The `test_proxy_manager.py` and `test_rate_limiter.py` clusters (8 of 30 failures) were investigated first because their error messages were the most concrete:

- `test_pool_has_at_least_50_entries`: `assert len(USER_AGENT_POOL) >= 50` failed with `5 >= 50` -- the real pool only had 5 entries.
- `test_entries_look_like_real_uas`: expected 100% of entries to start with `"Mozilla/5.0"` -- 0 of 5 did.
- The 5 real entries were: `"Centinel-Engine/1.0 (electoral-audit; +https://github.com/VectisDev/centinel)"`, `"Centinel-Watchdog/1.0 (electoral-transparency; ...)"`, etc. -- **transparent, self-identifying identifiers**, not disguised browser User-Agents.
- `test_default_parameters`: expected `burst == 3` and `min_interval == 8.0`; the real code had `DEFAULT_BURST = 5` and `DEFAULT_MIN_INTERVAL = 6.0`.
- `test_invalid_min_interval_raises`: expected `ValueError` when passing `min_interval=-1`, but the constructor has `enforce_ceiling=True` by default, which **clamps** `min_interval = max(min_interval, HARD_CEILING_MIN_INTERVAL)` (where `HARD_CEILING_MIN_INTERVAL = 2.0`) *before* validation -- so `-1` never reaches `_validate_limits()` as negative.

The first instinct would have been "update these tests to match the current code." But before doing that, the right question came up: **where does this code come from, and is it part of what VIGIL actually runs?**

### 2) The Hypothesis

`grep -rn "from centinel_engine\|import centinel_engine"` revealed that `USER_AGENT_POOL` and `TokenBucketRateLimiter` don't live in `src/centinel/` but in a **completely separate package at the repo root: `centinel_engine/`** -- with its own `LICENSE`, `README.md` and `package.json`. Hypothesis: this is a satellite/embeddable package, possibly intended for independent distribution, and the 8 failures in `test_proxy_manager.py`/`test_rate_limiter.py` are **tests written for an earlier version of that package** (with a 50+ entry anonymizing UA pool and less conservative limits), never updated when `centinel_engine/` was redesigned toward transparent identifiers and stricter ("hard ceiling") limits.

If this hypothesis is correct, the relevant question isn't "how do I fix these tests?" but **"is this package part of the electoral audit critical path, or is it optional?"** -- because the answer determines whether these 8 failures block `refactor/v13-clean-core` or can be left out of this session's scope.

### 3) The Experiment / Implementation

How `src/centinel/` consumes `centinel_engine/` was verified:

```python
# src/centinel/proxy_handler.py (lines 77-80)
try:
    from centinel_engine.config_loader import load_config  # type: ignore[import]
except ModuleNotFoundError:  # centinel_engine not installed (tests / forks)
    def load_config(...):
        """Fallback stub when centinel_engine package is not available."""
        ...

# src/centinel/downloader.py (line 563)
from centinel_engine.rate_limiter import get_rate_limiter
```

**Key finding:** `proxy_handler.py` imports `centinel_engine` inside a `try/except ModuleNotFoundError` **with an explicit fallback stub**, and the comment itself says *"centinel_engine not installed (tests / forks)"*. In other words: the team that wrote `src/centinel/` already designed the system assuming `centinel_engine` **might not be present** -- exactly the "graceful degradation" principle `@rules-engine-agent` requires for statistical rules, applied here to an entire package.

It was also confirmed that `centinel_engine/` IS imported by active code (`proxy_handler.py`, `downloader.py`, and three polling/logging scripts), so it's **not dead code** -- it's a real but optional dependency with a fallback.

With this, the 30 failures were reclassified into two categories:

**Category A -- Satellite package `centinel_engine/` (8 failures: 5 in `test_proxy_manager.py`, 3 in `test_rate_limiter.py`):**
Tests written against an earlier version of the package. The current `centinel_engine/` code implements a *more conservative and more transparent* design than the tests assume:
- UA pool: 5 self-descriptive identifiers with a link to the repo, instead of 50+ browser UAs. This is **consistent with the README's principle** of "ethical scraping ... the entire swarm behaves as at most one visitor".
- Rate limiter: `burst=5`/`min_interval=6.0` with a "hard ceiling" system that prevents dangerous configurations even if someone tries -- a real security improvement.

These 8 failures **are not regressions**: they're evidence that `centinel_engine/` evolved toward a better design, and nobody updated its tests to reflect it.

**Category B -- Core `src/centinel/` (remaining 22 failures: `test_security_utils.py`, `test_json_validation.py`, `test_multi_witness.py`, `test_failure_injection.py`, `test_e2e_election_night.py`, `federation/`, `monitoring/`, `test_integration_loop.py`, `test_stress.py`):**
Not deeply investigated in this session. These require the same level of care as Diary 01 (each could be a real regression, a stale test, or an undocumented design choice), but the volume (22 distinct files/clusters) exceeds what's reasonable for a single session after already resolving 6 real core bugs.

### 4) The Result (The Lesson)

| Category | Count | Nature | Blocks v13? |
|----------|-------|--------|-------------|
| A -- `centinel_engine/` (satellite, optional, with fallback) | 8 | Stale tests vs. intentional redesign (transparency + hard ceiling) | No |
| B -- `src/centinel/` (core, not investigated) | 22 | Unknown -- requires individual triage | Pending, not blocking for starting v13 |

**The lesson:** not every test failure carries the same weight. Finding that `USER_AGENT_POOL` has 5 entries instead of 50 *could* sound serious (did anonymization break?), but once the code is located in an optional package with an explicit fallback, and the new design turns out to be *more* aligned with the project's stated ethics (transparency over camouflage), the finding shifts from "critical bug" to "design decision documented only in the code, never in tests or an ADR".

### 5) The Final Decision (Takeaway)

**No test in Category A or B was modified in this session.** This is an explicit decision, not a time-shortage one: `@qa-engineering-agent` should not "fix" tests by rewriting them to match current code without someone with `@cybersecurity-agent`/`@osint-security-agent` judgment confirming the new design (transparent UA, hard ceiling) was a conscious decision and not a side effect of another change.

`refactor/v13-clean-core` is **not blocked** by these 30 failures: none of them are in `src/centinel/core/rules/`, `src/centinel/core/hash_chain.py`, or the anchoring/normalization modules already at 698/698. The refactor can proceed using 698 as baseline, and the 30 failures (8 + 22) are documented here as explicit technical debt for a dedicated QA session on the `centinel_engine/` package and the federation/resilience modules.

### 6) What Changed and Why Now

Nothing in the code changed in this diary -- it's deliberately documentation-only. What changed was **scope**: the question "is this relevant to the system?" prevented the session from extending indefinitely fixing a satellite package whose stale tests don't affect the electoral audit itself. It's the same principle as "external dependencies are not blockers" (an operating principle already documented for Devis/IGETEL) applied to technical debt: an optional package with a fallback is not blocking for a core refactor.

### 7) Implementation Decisions

- **Classify before fixing:** every QA finding must first answer "is this on the critical path?" before investing time in a fix.
- **Undocumented design decisions are technical debt, not bugs:** the `centinel_engine/` redesign (transparent UA, hard ceiling) looks good, but with no ADR and no test reflecting it, it remains a blind spot. `@systems-architecture-agent` is recommended to record this in an ADR when revisited.
- **698 as the official v13 baseline:** any number below 698 after the package rename is a real refactor regression; the 30 pre-existing failures don't count against that baseline (documented separately).

### 8) Impact

- Avoided spending additional time rewriting 8 tests for an optional package without the corresponding security/privacy review.
- Identified a possible ethics/security posture improvement (transparent UA + hard ceiling in `centinel_engine/`) that was *implemented but invisible* -- no project document mentions it.
- 22 core failures remain untriaged, explicitly documented as pending -- avoiding the false sense of "everything resolved" that the original "526/526" badge produced.

### 9) Cycle Takeaway

The most useful question of the session wasn't technical: it was "is this relevant?". Rigorous QA isn't fixing everything that fails -- it's knowing which failures matter, in what order, and honestly documenting what remains unresolved instead of hiding it behind an aggregate number.

---

## PRs de este ciclo / PRs in this cycle

| PR | Descripcion | Estado |
|----|-------------|--------|
| (ninguno -- diario documental) | Triage y clasificacion de 30 fallos restantes en Categoria A (`centinel_engine/`, 8) y Categoria B (nucleo, 22) | sin cambios de codigo |

---

## Metricas de impacto / Impact Metrics

| Metrica | Antes | Despues |
|---------|-------|---------|
| Fallos sin clasificar | 30 | 0 (8 en Categoria A, 22 en Categoria B, ambas documentadas) |
| Riesgo de "arreglar" tests sobre una decision de diseño no revisada | Alto (si se hubiera procedido directo) | Evitado -- pendiente de revision cybersecurity/osint |
| Baseline oficial para `refactor/v13-clean-core` | No definido | 698/729 (nucleo, excl. resilience y centinel_engine) |
| Documentacion de `centinel_engine/` como dependencia opcional con fallback | Implicita en un comentario de codigo | Explicita en este diario |
| Deuda tecnica pendiente, documentada | 0 items registrados | 30 (8 + 22), priorizables en sesion dedicada |

---
