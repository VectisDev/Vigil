# Dev Diary - 202606 - PonytailRefactorConceptoYFase1 - 01

**Fecha aproximada / Approximate date:** 18-jun-2026 / June 18, 2026
**Fase / Phase:** Introducción del patrón "ponytail" y limpieza de eficiencia en módulos core / Introduction of the "ponytail" pattern and efficiency cleanup in core modules
**Version interna / Internal version:** v0.2.x (ciclo dev-v14)
**Rama / Branch:** dev-v14-refactor-ponytail → dev-v13 (merged PR #741, PR #744)
**Autor / Author:** userf8a2c4

**Contexto / Context:**
Con VIGIL funcionando y la suite a 526 tests, llegó el momento de preparar el código para presentación pública. No un refactor cosmético sino uno de fondo: módulos más pequeños, dependencias justificadas, sin código muerto ni abstracciones prematuras. El objetivo era reducir la superficie sin reducir la capacidad. Para hacerlo sin romper nada y sin dejar deuda oculta, inventé una convención de código que llamé "ponytail".

---

## [ES]

### 1) El Problema (Contexto)

El código de VIGIL había crecido en capas: primero la lógica base, luego el motor de resiliencia, luego scraping, luego federación, luego dashboards. Cada iteración dejó dependencias que se justificaban en su momento pero que al revisarlas en conjunto resultaban redundantes o sobredimensionadas:

- `requests` y `aiohttp` coexistiendo cuando `httpx` hace ambas cosas
- `vital_signs.py` (434 líneas) viviendo en `centinel_engine/` cuando todo el motor de scraping ya está en `scripts/watchdog.py`
- `config_schemas.py` con 4 schemas donde 2 eran suficientes
- `healthcheck.py` usando `subprocess` + `curl` para llamadas HTTP que httpx hace directamente
- `retry.py` inexistente: la lógica de backoff estaba inlineada en `run_pipeline.py` como un while loop manual
- `download_and_hash.py` importando `hashlib` directamente en lugar de usar el módulo `hash_chain.py`

La pregunta que me hice fue: ¿puedo limpiar todo esto sin romper los 526 tests y sin eliminar funcionalidad real?

### 2) La Hipótesis — El patrón "ponytail"

El riesgo de cualquier refactor es que el programador simplifica algo que parece redundante pero que en realidad sostiene un caso edge que los tests no cubren. La solución habitual es documentar cada decisión en un PR o en commits — pero eso se pierde con el tiempo.

Inventé la convención `# ponytail:` para marcar explícitamente **lo que se simplificó intencionalmente** y **cuándo volver a añadirlo**. La analogía es un peinado de cola de caballo: el pelo está todo ahí, simplemente recogido y fuera del camino. No se cortó nada; está guardado con una nota de cuándo soltarlo.

Ejemplo concreto en `requirements.txt`:

```
# ponytail: aiohttp retained for legacy poller scripts.
# Remove once poller_async.py is fully migrated to httpx.
aiohttp>=3.9.0,<4.0.0
```

Y en código:

```python
# ponytail: playwright-based fallback for JS-rendered pages skipped.
# Add back if CNE Honduras starts requiring JS execution (unlikely before 2029).
```

Esto hace que cualquier revisor externo — una organización de observación, un auditor de código, un nuevo contribuidor — pueda ver exactamente qué se dejó afuera y por qué, en lugar de preguntarse si fue un olvido.

### 3) Implementación — Phase 1

#### `centinel_engine/retry.py` (nuevo)

Extraje la lógica de backoff exponencial que estaba inlineada como while loop en `run_pipeline.py` y la encapsulé en un decorador usando `tenacity`:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

def retry_backoff(max_attempts: int = 3, min_wait: float = 1.0, max_wait: float = 60.0):
    """Exponential backoff decorator using tenacity."""
    ...
```

Nota importante: `run_pipeline.py` tiene tests que parchean `run_pipeline.time.sleep` directamente. Cambiar el while loop a tenacity rompería esos tests porque tenacity usa su propio mecanismo de sleep. Dejé el while loop original en `run_pipeline.py` con un comentario `# ponytail:` explicando el bloqueo, y el nuevo módulo `retry.py` queda disponible para código nuevo.

#### `centinel_engine/hash_chain.py` (nuevo)

`download_and_hash.py` tenía llamadas directas a `hashlib.sha256()` mezcladas con la lógica de descarga. Extraí las funciones de hash a un módulo dedicado:

```python
def compute_hash(data: bytes) -> str:
    """SHA-256 hex digest of raw bytes."""

def chain_hash(previous_hash: str, current_hash: str) -> str:
    """Chain two hashes: SHA-256(prev_hash + curr_hash)."""
```

El invariante SHA-256 del hash chain está protegido — no toqué la lógica criptográfica, solo la moví a su módulo natural.

#### `centinel_engine/config_schemas.py` — de 4 a 2 schemas

Los schemas `PipelineConfig` y `PipelineScrapeConfig` eran subconjuntos parciales de `PipelineNetworkConfig` y `PipelineEndpointsConfig`. Los fusioné. Los tests que importaban los schemas antiguos siguen funcionando porque el módulo re-exporta los nombres originales.

#### `scripts/healthcheck.py` — reescritura completa a httpx

El healthcheck original usaba `subprocess.run(["curl", ...])` y parseaba stdout. Reemplazado por llamadas directas `httpx.get()` con timeouts explícitos. Más simple, más testeable, sin dependencia de que `curl` esté instalado en el runner.

#### `scripts/download_and_hash.py` — migración a httpx

Las llamadas de swarm usaban `requests.Session`. Migradas a `httpx.Client` con los mismos parámetros de timeout y retry. El `assert_fingerprint` para TLS cert pinning se mantiene con `urllib3` porque httpx no expone ese parámetro directamente — marcado con `# ponytail:` para cuando httpx lo soporte.

#### `centinel_engine/electoral_authority_healer.py` y `proxy_manager.py`

Anotaciones `# ponytail:` en ambos sin cambio de lógica:
- `healer.py`: el fallback de Playwright para páginas JS está documentado como "agregar si CNE Honduras requiere JS antes de 2029"
- `proxy_manager.py`: `secrets.choice` vs `random.choice` — la versión criptográficamente segura está anotada para cuando el threat model lo justifique

### 4) Resultado

Commits mergeados en `dev-v13` via PR #741:

| Módulo | Cambio |
|--------|--------|
| `centinel_engine/retry.py` | Nuevo — decorador tenacity |
| `centinel_engine/hash_chain.py` | Nuevo — funciones hash extraídas |
| `centinel_engine/config_schemas.py` | 4 schemas → 2 |
| `scripts/healthcheck.py` | subprocess+curl → httpx |
| `scripts/download_and_hash.py` | requests → httpx, usa hash_chain.py |
| `requirements.txt` | Anotaciones ponytail en requests/aiohttp |

526 tests: ninguno roto.

### 5) Lo que queda (próximas fases)

- **Phase 2b**: migrar `safe_run_pipeline` → tenacity (bloqueado: requiere refactorizar los tests que parchean `time.sleep`)
- **Phase 6a**: extraer `_persist_snapshot_payload` a `hash_chain.py`
- Cuando `run_pipeline.py` migre a `from scripts import watchdog` directamente, el shim `centinel_engine/vital_signs.py` puede eliminarse

---

## [EN]

### 1) The Problem (Context)

VIGIL's code had grown in layers — base logic, then the resilience engine, then scraping, then federation, then dashboards. Each iteration left dependencies that made sense individually but were redundant or oversized when reviewed together: `requests` and `aiohttp` coexisting when `httpx` handles both; `vital_signs.py` (434 lines) living in `centinel_engine/` when the scraping engine already lives in `scripts/watchdog.py`; retry logic as a manual while loop instead of a proper decorator; `download_and_hash.py` calling `hashlib` directly instead of using the `hash_chain.py` module.

### 2) The "Ponytail" Pattern

The risk in any refactor is simplifying something that looks redundant but actually handles an edge case the tests don't cover. The usual solution is documenting decisions in PRs or commits — but that gets lost over time.

I invented the `# ponytail:` convention to explicitly mark **what was intentionally simplified** and **when to add it back**. The analogy is a ponytail hairstyle: the hair is all there, just gathered and out of the way. Nothing was cut; it's stored with a note for when to release it.

This means any external reviewer — an observation organization, a code auditor, a new contributor — can see exactly what was left out and why, instead of wondering if it was an oversight.

### 3) Implementation — Phase 1

- `centinel_engine/retry.py`: new tenacity-based backoff decorator (while loop in `run_pipeline.py` kept unchanged due to test patching constraint, documented with `# ponytail:`)
- `centinel_engine/hash_chain.py`: extracted `compute_hash()` and `chain_hash()` from inline hashlib calls
- `centinel_engine/config_schemas.py`: 4 schemas → 2 by merging partial duplicates
- `scripts/healthcheck.py`: complete rewrite from `subprocess.run(["curl", ...])` to `httpx.get()`
- `scripts/download_and_hash.py`: swarm calls migrated from `requests.Session` to `httpx.Client`; TLS cert pinning kept on urllib3 with `# ponytail:` note
- `requirements.txt`: ponytail annotations on `requests` and `aiohttp`

526 tests: zero broken.
