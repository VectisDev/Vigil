# Dev Diary - 202606 - PonytailWorkflowsYMigracionVitalSigns - 01

**Fecha aproximada / Approximate date:** 18-jun-2026 / June 18, 2026
**Fase / Phase:** Consolidación de workflows GitHub Actions (25 → 22) y migración del motor vital-signs a watchdog.py / GitHub Actions workflow consolidation (25 → 22) and migration of the vital-signs engine to watchdog.py
**Version interna / Internal version:** v0.2.x (ciclo dev-v14)
**Rama / Branch:** dev-v14-refactor-ponytail → dev-v13 (merged PR #741, PR #744)
**Autor / Author:** userf8a2c4

**Contexto / Context:**
Segunda parte del ponytail refactor del 18-jun-2026. Con los módulos core limpios (Phase 1, entrada anterior), el foco se movió a dos problemas de arquitectura: workflows duplicados en `.github/workflows/` y un motor de resiliencia viviendo en el módulo equivocado.

---

## [ES]

### 1) Problema A — Workflows duplicados

`.github/workflows/` tenía 25 archivos. Varios de ellos eran pares que hacían exactamente lo mismo con configuración levemente diferente:

- `poller-A.yml` + `poller-B.yml`: dos pollers idénticos con crons offset para garantizar cobertura 24/7 sin gaps
- `sync-lab-thresholds.yml`: un workflow de un solo job que podía ser un job dentro de `ci.yml`
- `reputation-json-api.yml`: un workflow de un solo job que podía ser un job dentro de `hash-chain-commit.yml`

El problema de tener 25 archivos separados no es solo estético. Cuando un revisor externo (OEA, Carter Center, auditor de seguridad) examina la infraestructura de CI, cada archivo es una superficie de inspección. Menos archivos con comentarios explicativos claros son más auditables que muchos archivos con nombres crípticos.

### 2) Consolidación de pollers — el desafío técnico real

Mergear `poller-A.yml` + `poller-B.yml` en un solo archivo era obvio en teoría. El desafío era preservar la **estrategia de overlap**:

```
Slot A: 00:00, 06:00, 12:00, 18:00 UTC
Slot B: 03:00, 09:00, 15:00, 21:00 UTC
Overlap: 03:00→05:30, 09:00→11:30, 15:00→17:30, 21:00→23:30
Gap: CERO — al menos un poller activo en todo momento
```

Los pollers originales usaban `concurrency: group: centinel-poller` con `cancel-in-progress: false` — cada archivo tenía su propio grupo de concurrencia, lo que garantizaba que el Slot A y el Slot B fueran singletons independientes.

Si los mergeo en un archivo y uso el mismo grupo de concurrencia, los dos slots compiten entre sí y uno cancela al otro — destruyendo la cobertura 24/7.

La solución fue usar `${{ github.event.schedule }}` como parte del nombre del grupo:

```yaml
concurrency:
  group: centinel-poller-${{ github.event.schedule || 'manual' }}
  cancel-in-progress: false
```

Cuando el cron `0 0,6,12,18 * * *` dispara, `github.event.schedule` es `"0 0,6,12,18 * * *"`. Cuando dispara `0 3,9,15,21 * * *`, es `"0 3,9,15,21 * * *"`. Dos strings distintos → dos grupos de concurrencia distintos → singletons independientes. La cobertura 24/7 se preserva con un solo archivo.

### 3) Inline de sync-lab-thresholds en ci.yml

`sync-lab-thresholds.yml` era un archivo de 40 líneas con un solo job que:
1. Detectaba si archivos de threshold habían cambiado (`git diff HEAD~1 HEAD`)
2. Si sí, generaba `web/lab-thresholds.json` y hacía commit con `[skip ci]`
3. Solo corría en push a `main` o `dev-v12`

Se convirtió en el job `sync-lab-thresholds` al final de `ci.yml` con la misma lógica, usando `if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/dev-v12')` a nivel de job para que no corra en PRs.

### 4) Consolidación de reputation-json-api en hash-chain-commit.yml

`reputation-json-api.yml` exportaba el estado de `ReputationEngine` a `data/reputation/nodes.json` y lo committeaba a una rama `data/api`. Ya que `hash-chain-commit.yml` también corre diariamente a medianoche y tiene el mismo setup de Python, el job `reputation-api-export` se agregó como tercer job paralelo en `hash-chain-commit.yml`.

Resultado final: 25 → 22 workflows, cero capacidad perdida, todos con comentarios `# ponytail:` explicando la fusión.

### 5) Problema B — vital_signs.py en el módulo equivocado

`centinel_engine/vital_signs.py` (434 líneas) contenía el motor adaptativo de resiliencia: `ResilienceMode`, `check_vital_signs`, `DEFAULT_THRESHOLDS`, `update_status_after_scrape`, y siete funciones auxiliares.

El problema arquitectural: todo el motor de scraping vive en `scripts/watchdog.py`. El vital-signs engine es el cerebro que decide si el scraper debe correr en modo normal, conservativo o crítico. Conceptualmente pertenece a `watchdog.py`, no a `centinel_engine/`.

`centinel_engine/` debería ser la librería de utilidades reutilizables (hash chain, retry, config schemas, rate limiter). `scripts/watchdog.py` es el operador que usa esas utilidades para hacer scraping. Poner el motor de resiliencia en `centinel_engine/` era una inversión de dependencias.

### 6) Migración — el patrón shim

Mover 434 líneas de `vital_signs.py` a `watchdog.py` directamente rompería tres archivos de tests y `run_pipeline.py`, todos importando desde `centinel_engine.vital_signs`. Con 526 tests en la suite, no podía romper eso.

La solución fue el patrón shim: `centinel_engine/vital_signs.py` se convierte en un archivo de 25 líneas que re-exporta todo desde `scripts.watchdog`:

```python
"""Re-export shim: centinel_engine.vital_signs → scripts.watchdog.
ponytail: remove this shim once all callers import from scripts.watchdog directly.
Update: tests/test_vital_signs.py, tests/test_integration_loop.py,
tests/test_hostile_scenarios.py, and scripts/run_pipeline.py.
"""
from scripts.watchdog import (  # noqa: F401
    DEFAULT_HEALTH_STATE, DEFAULT_THRESHOLDS, ResilienceMode,
    _compute_avg_latency, _compute_request_pressure, _compute_success_rate,
    check_vital_signs, load_health_state, save_health_state,
    update_status_after_scrape, ...
)
```

Esto permite migrar los importadores uno por uno sin romper nada. Los tres archivos de tests se actualizaron en este ciclo:

```python
# Antes:
from centinel_engine.vital_signs import check_vital_signs
# Después:
from scripts.watchdog import check_vital_signs
```

`run_pipeline.py` usa `vital_signs` como referencia de módulo (`vital_signs.check_vital_signs(...)`) en ~8 puntos del código. El shim lo cubre transparentemente. La migración completa de `run_pipeline.py` es Phase 2b (bloqueada hasta que los tests de sleep-patching se refactoricen).

### 7) Un detalle técnico: importación circular

Al mover el código de `vital_signs.py` a `watchdog.py`, el archivo original de `watchdog.py` tenía:

```python
from centinel_engine.vital_signs import ResilienceMode
```

Ese import tenía que eliminarse antes de agregar la definición de `ResilienceMode` directamente en `watchdog.py`. De lo contrario, Python intentaría importar `vital_signs.py`, que importaría `watchdog.py`, que importaría `vital_signs.py` — un ciclo infinito. El orden de operaciones importó.

### 8) CI — todo verde

PR #744 (dev-v14-refactor-ponytail → dev-v13):

| Check | Resultado |
|-------|-----------|
| Lint (Python 3.11) | ✅ pass |
| Tests (Python 3.10) | ✅ pass |
| Tests (Python 3.11) | ✅ pass |
| Security Integration Tests | ✅ pass |
| Resilience Tests | ✅ pass |
| Sync Lab Thresholds | ⏭ skipped (correcto — PR no es push a main/dev-v12) |

Mergeado a `dev-v13` el 18-jun-2026.

### 9) Estado del shim

El shim `centinel_engine/vital_signs.py` permanece hasta que `run_pipeline.py` migre. La nota `# ponytail:` en el shim documenta exactamente los cuatro archivos que deben actualizarse antes de poder eliminarlo. Ningún trabajo oculto, ninguna deuda sorpresa.

---

## [EN]

### 1) Problem A — Duplicate workflows

`.github/workflows/` had 25 files. Several were pairs doing identical work with slightly different config: `poller-A.yml` + `poller-B.yml`, `sync-lab-thresholds.yml` (single job that could live in `ci.yml`), `reputation-json-api.yml` (single job that could live in `hash-chain-commit.yml`). External auditors — OEA, Carter Center — inspect CI files; fewer files with clear comments are more auditable than many cryptically named files.

### 2) Poller merge — the real technical challenge

The poller pair used offset cron slots to guarantee 24/7 coverage with zero gaps. Merging them naively into one file with a shared concurrency group would have made them compete and cancel each other. The fix: use `${{ github.event.schedule }}` as part of the concurrency group name. Each cron string is unique, so each slot gets its own singleton lock. Coverage preserved with one file.

### 3) vital_signs.py was in the wrong module

The adaptive resilience engine (434 lines) belonged conceptually in `scripts/watchdog.py` — the scraping operator — not in `centinel_engine/` — the utilities library. I moved it using the shim pattern: `centinel_engine/vital_signs.py` becomes a 25-line re-export shim so the 526 existing tests and `run_pipeline.py` continue working unchanged. Three test files were updated to import directly from `scripts.watchdog`. `run_pipeline.py` uses module-level attribute access (`vital_signs.check_vital_signs(...)`) and is covered transparently by the shim until Phase 2b.

### 4) Circular import note

Before adding `ResilienceMode` to `watchdog.py`, the old `from centinel_engine.vital_signs import ResilienceMode` had to be removed. Operation order mattered to avoid a Python circular import cycle.

### 5) Final state

- 25 → 22 workflow files, zero capability lost
- `scripts/watchdog.py` owns the vital-signs engine
- `centinel_engine/vital_signs.py` is a documented shim
- CI: all checks green, PR #744 merged to `dev-v13`
