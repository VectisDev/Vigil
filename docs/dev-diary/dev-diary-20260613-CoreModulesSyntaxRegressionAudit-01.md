# Dev Diary - 202606 - CoreModulesSyntaxRegressionAudit - 01

**Fecha aproximada / Approximate date:** 13-jun-2026 / June 13, 2026
**Fase / Phase:** Auditoria de QA pre-refactor: descubrimiento de modulos nucleo no importables tras la limpieza Arbitrum/blockchain, y restauracion a un baseline ejecutable / Pre-refactor QA audit: discovery of non-importable core modules after the Arbitrum/blockchain cleanup, and restoration to a runnable baseline
**Version interna / Internal version:** v0.1.x (ciclo dev-v12, previo a v13)
**Rama / Branch:** dev-v12 + main (commits directos en paralelo)
**Autor / Author:** Orquestador (Claude) + qa-engineering-agent (nuevo)

**Contexto / Context:**
Antes de iniciar `refactor/v13-clean-core` (renombrar `src/centinel/` -> `src/vigil/`), el recien creado `@qa-engineering-agent` ejecuto su primer mandato: correr la suite real y reportar numeros exactos, no asumidos. El README declaraba "526/526 tests passing". La realidad medida fue otra: la coleccion de `pytest` fallaba con 32 errores antes de instalar dependencias, y persistian errores de sintaxis reales en archivos de `src/` que impedian incluso importar el paquete. La causa raiz: la limpieza previa de codigo de pago (Arbitrum, IPFS/Pinata, blockchain anchoring) habia dejado fragmentos de codigo huerfanos -- bloques `except` sin `try`, clases sin `__init__`, columnas SQL duplicadas, comas faltantes -- que nunca se habian detectado porque nadie habia corrido la suite completa despues de ese cleanup. / Before starting `refactor/v13-clean-core` (renaming `src/centinel/` -> `src/vigil/`), the newly created `@qa-engineering-agent` executed its first mandate: run the real suite and report exact numbers, not assumed ones. The README claimed "526/526 tests passing." The measured reality was different: pytest collection failed with 32 errors before installing dependencies, and real syntax errors persisted in `src/` files that prevented even importing the package. Root cause: the prior cleanup of paid-service code (Arbitrum, IPFS/Pinata, blockchain anchoring) had left orphaned code fragments -- `except` blocks without `try`, classes without `__init__`, duplicated SQL columns, missing commas -- that nobody had detected because nobody had run the full suite after that cleanup.

---

## [ES]

### 1) El Problema (Contexto)

El README de VIGIL ostenta el badge "tests: 526 passing". Al clonar `dev-v12` y ejecutar `pytest tests/ --collect-only`, la coleccion abortaba con **32 errores** antes de llegar a ejecutar una sola prueba. Tras instalar `pydantic` y el paquete en modo editable (`pip install -e .`), la coleccion bajo a 6 errores, y entre ellos aparecieron tres que NO eran por dependencias faltantes sino **SyntaxError / IndentationError reales dentro de `src/centinel/`**:

1. `src/centinel/core/storage.py:128` -- `IndentationError: unexpected indent`. El metodo `store_snapshot()` tenia una linea `tx_hash = None` duplicada con indentacion de modulo (columna 0) seguida de un bloque `except Exception as exc:` **sin ningun `try` correspondiente** -- restos de un bloque que originalmente llamaba `publish_hash_to_chain()` (la integracion Arbitrum eliminada).

2. `src/centinel/anchor/opentimestamps_client.py:266` -- `SyntaxError: invalid syntax`. La clase `MultichainAnchor` no tenia linea `class MultichainAnchor:` -- el bloque arrancaba directamente con fragmentos de un docstring (`Design:\n- Primary: OpenTimestamps...`), seguido de un `__init__` sin firma `def __init__(self, testnet: bool = False) -> None:`, y un metodo `anchor_checkpoint` sin su `def` ni docstring de apertura.

3. `src/centinel/utils/logging_config.py:80` -- `SyntaxError: invalid syntax. Perhaps you forgot a comma?`. En la lista `SECRET_PATTERNS`, el patron de `arbitrum_private_key` (marcado "legacy" tras el cleanup) terminaba con `)  # legacy,` -- la coma quedo *dentro del comentario* en lugar de despues del parentesis, rompiendo la lista.

Ademas, `tests/test_config.py` tenia **dos** instancias del mismo patron: un diccionario `"alerts": {...}` seguido directamente de `"rules": {...}` sin coma entre ambos -- exactamente el mismo tipo de error que en `logging_config.py`, sugiriendo un patron sistemico de "comas perdidas al eliminar bloques `blockchain`/`arbitrum`".

Un sexto error -- `tests/resilience -- UnboundLocalError: cannot access local variable '_imm'` -- era distinto: el bloque de stubs para `centinel.defense.*` en `conftest.py` usaba `_imm.ModuleSpec(...)` sin que `_imm` (alias de `importlib.machinery`) estuviera importado en ese scope especifico (si estaba importado en dos bloques anteriores, pero no en este tercero).

### 2) La Hipotesis

Todos estos errores comparten una causa raiz unica: **la limpieza de codigo de pago (Arbitrum/blockchain/IPFS) se hizo con ediciones de texto que dejaron fragmentos huerfanos**, y como esos archivos nunca volvieron a importarse exitosamente despues, ningun test los ejecuto, y la suite jamas reporto el problema -- simplemente colapsaba en la fase de coleccion con un numero de errores que probablemente se interpreto como "ruido de dependencias" sin investigar cada uno.

La hipotesis de reparacion: cada error es **localmente reconstruible** sin cambiar comportamiento -- basta identificar que pieza de codigo faltaba (una firma de funcion, una coma, un nombre de clase) usando el contexto inmediato (que variables se usan despues, que firma tienen clases hermanas como `OpenTimestampsClient`) y restaurarla minimamente.

### 3) El Experimento / Implementacion

**Paso 1 -- Inventario de dependencias.** `pip install -e .` resolvio la mayoria de los 32 errores de coleccion iniciales (pydantic y otras dependencias del `pyproject.toml` no estaban instaladas en el entorno de auditoria). De 32 errores bajamos a 6.

**Paso 2 -- `storage.py` (bloque `except` huerfano):**
```python
# ANTES (roto):
snapshot_hash = compute_hash(canonical_json, previous_hash=previous_hash)
tx_hash = None
# tx_hash = publish_hash_to_chain() — REMOVED (Zero Cost)
    tx_hash = None  # OTS handles anchoring: centinel.core.anchoring
        except Exception as exc:  # noqa: BLE001
            logger.warning("blockchain_publish_failed error=%s", exc)
        department_code = snapshot.meta.department_code

# DESPUES (reparado):
snapshot_hash = compute_hash(canonical_json, previous_hash=previous_hash)
tx_hash = None  # OTS handles anchoring: centinel.core.anchoring (Zero Cost)
department_code = snapshot.meta.department_code
```

Tras esta correccion, `storage.py` importo correctamente pero **expuso 3 bugs adicionales** que habian estado dormidos por no poder ejecutarse nunca:

- Esquema de `snapshot_index` y de las tablas por departamento declaraban `tx_hash TEXT TEXT TEXT` (tipo de columna triplicado -- resto de columnas `ipfs_cid`/`arbitrum_tx` colapsadas en el cleanup).
- Dos sentencias `INSERT OR REPLACE` tenian **13 placeholders `?` para 11 columnas** (y para 6 columnas, respectivamente) -- mismatch directo `sqlite3.OperationalError: N values for M columns`.
- `export_department_json()` y `export_department_csv()` incluian una clave/columna `""` (string vacio) en el payload -- `row[""]` lanzaba `IndexError: No item with that key`.

Las cuatro correcciones (esquema, dos `VALUES (...)`, dos exports) son ediciones quirurgicas de una linea cada una, sin cambiar la forma del modelo de datos real (11 columnas + indice).

**Paso 3 -- `opentimestamps_client.py` (clase `MultichainAnchor` reconstruida):**

Usando `OpenTimestampsClient` (la clase hermana, completa) como plantilla de estilo, se restauro:
```python
class MultichainAnchor:
    """Anchors checkpoints using OpenTimestamps (Bitcoin), Zero Cost.
    ES: Ancla checkpoints usando OpenTimestamps (Bitcoin), Costo Cero.
    Design:
    - Primary: OpenTimestamps (fast, free, proven)
    - Non-fatal: if both fail, publish without anchor (lower assurance)
    """

    def __init__(self, testnet: bool = False) -> None:
        """Initialize multi-chain anchor (OTS Bitcoin only)."""
        self.ots_client = OpenTimestampsClient(use_testnet=testnet)
        self.testnet = testnet

    def anchor_checkpoint(self, checkpoint: dict) -> dict:
        """Anchor a checkpoint's merkle root via OpenTimestamps.
        ...
        """
        merkle_root = checkpoint.get("merkle_root", "")
        ...
```

El cuerpo de `anchor_checkpoint` (logica de stamp + fallback no-fatal) ya existia intacto -- solo faltaban la firma de clase, el `__init__` y la apertura de docstring del metodo.

**Paso 4 -- `logging_config.py` y `test_config.py` (comas):** tres correcciones de una sola linea, moviendo la coma de dentro del comentario `# legacy,` a su posicion correcta `),  # legacy`, y agregando la coma faltante tras dos diccionarios `"alerts": {...}`.

**Paso 5 -- `tests/resilience/conftest.py`:** se agrego `import importlib.machinery as _imm` al inicio del bloque de stubs de `centinel.defense.*`, que carecia de el (los otros dos bloques similares en el mismo archivo si lo tenian).

**Paso 6 -- `tests/test_opentimestamps_client.py`:** el archivo de test correspondiente a `MultichainAnchor` tenia el mismo problema que el codigo de produccion -- faltaba `class TestMultichainAnchor:` (las 4 funciones de test estaban anidadas dentro de `TestOpenTimestampsClient` por error de indentacion/estructura), y las 4 funciones referenciaban una variable `anchor` que nunca se instanciaba. Se agrego la clase, el import de `MultichainAnchor`, y `anchor = MultichainAnchor()` en cada test. Un quinto detalle: `test_anchor_checkpoint_ots_fails` no configuraba `mock_stamp.return_value = None`, por lo que el mock devolvia un `MagicMock` truthy y el test fallaba con el resultado opuesto al esperado.

### 4) El Resultado (La Leccion)

| Paso | Tests recolectados | Pasando | Fallando | Errores |
|------|---------------------|---------|----------|---------|
| Estado inicial (sin deps) | no calculable | -- | -- | 32 (coleccion) |
| Tras `pip install -e .` | 660 | -- | -- | 6 (coleccion) |
| Tras fixes de sintaxis en `src/` y `test_config.py` | 728 | -- | -- | 1 (coleccion) |
| Tras fix de `_imm` en `conftest.py` | 729 | -- | -- | 0 (coleccion) |
| Suite completa (sin `tests/resilience`, ver Diario 02) | -- | 650 | 75 | 4 |
| Tras instalar `pytest-asyncio` | -- | 685 | 40 | 4 |
| Tras fixes de `storage.py` (4 bugs adicionales) | -- | 694 | 34 | 1 |
| Tras fixes de `test_opentimestamps_client.py` | -- | **698** | 30 | 1 |

**La leccion central:** un badge de "526/526 passing" en el README puede estar describiendo un estado que **dejo de ser cierto en el momento exacto del ultimo cleanup masivo**, y nadie lo habria sabido sin ejecutar la suite -- el repositorio seguia "viendose bien" porque nadie habia intentado importar esos modulos especificos desde entonces. La causa raiz de los 6 bugs en `storage.py`/`opentimestamps_client.py`/`logging_config.py` fue siempre la misma operacion (remocion de Arbitrum/IPFS), ejecutada probablemente con find-and-replace o ediciones de bloque que no preservaron la estructura sintactica circundante.

### 5) La Decision Final (Takeaway)

`@qa-engineering-agent` queda formalmente incorporado al roster (20/20) con un mandato no negociable: **antes de declarar cualquier cambio en `src/` o `web/ops/` como completo, ejecutar la suite relevante y reportar numeros exactos**. Este hallazgo es la justificacion empirica de por que esa regla existe -- sin ella, el proyecto habia estado operando durante un tiempo indeterminado con un nucleo que no podia ni importarse, sin que nadie lo supiera.

Los 6 archivos corregidos se commitearon directamente a `main` y `dev-v12` en paralelo (convencion vigente del proyecto). `refactor/v13-clean-core` ahora tiene un baseline real (698 passing en el nucleo) contra el cual medir regresiones del renombrado de paquete.

### 6) Que cambio y por que ahora

Este trabajo se disparo porque el usuario pidio iniciar `refactor/v13-clean-core` (renombrar `src/centinel/` -> `src/vigil/` como parte del rebranding CENTINEL -> VIGIL). El `@qa-engineering-agent`, recien creado en esta misma sesion con el mandato explicito de "no declarar tests pasando sin haberlos corrido", ejecuto ese mandato antes de tocar una sola linea del refactor -- y el resultado cambio el plan: no se puede medir el impacto de un renombrado masivo de paquete sobre una base que ni siquiera importa.

### 7) Decisiones de implementacion

- **Reconstruccion minima, no redisenio:** cada fix restauro la forma mas probable del codigo original (usando clases hermanas y el resto del archivo como referencia de estilo), sin agregar funcionalidad nueva ni cambiar el modelo de datos.
- **Una operacion = un commit message compartido:** los 6 archivos se commitearon con el mismo mensaje descriptivo (remanentes de limpieza Arbitrum/blockchain), para que el historial documente la causa raiz comun.
- **No se tocaron los 30 fallos restantes en esta sesion** -- ver Diario 02 para el analisis de por que esos no son regresiones del mismo tipo y no bloquean el refactor.

### 8) Impacto

- El nucleo de VIGIL (`src/centinel/core/`, `src/centinel/anchor/`) ahora importa y ejecuta correctamente. Antes de este trabajo, **3 modulos centrales (storage, anchoring OTS, logging seguro) tenian SyntaxError/IndentationError** y cualquier codigo que los importara fallaria en tiempo de importacion, no solo en tests.
- `store_snapshot()`, `export_department_json()` y `export_department_csv()` -- funciones usadas para la cadena de custodia y exportacion a observadores -- tenian bugs de SQL (placeholders desalineados, columnas vacias) que habrian fallado en produccion la primera vez que se invocaran con datos reales.
- Baseline establecido: 698 tests pasando en el nucleo, listo como punto de referencia para `refactor/v13-clean-core`.

### 9) Aprendizaje de ciclo

Un badge verde en el README no es evidencia de nada si nadie lo recalcula despues de cada cambio estructural grande. La regla "ejecutar y reportar numeros exactos" del `@qa-engineering-agent` no es burocracia -- es la unica defensa contra que el codigo nucleo de un sistema de auditoria electoral este, silenciosamente, roto.

---

## [EN]

### 1) The Problem (Context)

VIGIL's README displays a "tests: 526 passing" badge. Cloning `dev-v12` and running `pytest tests/ --collect-only` aborted with **32 errors** before executing a single test. After installing `pydantic` and the package in editable mode (`pip install -e .`), collection errors dropped to 6, and among them were three that were NOT missing-dependency issues but **real SyntaxError / IndentationError inside `src/centinel/`**:

1. `src/centinel/core/storage.py:128` -- `IndentationError: unexpected indent`. The `store_snapshot()` method had a duplicated `tx_hash = None` line at module-level indentation (column 0), followed by an `except Exception as exc:` block **with no corresponding `try`** -- remnants of a block that originally called `publish_hash_to_chain()` (the removed Arbitrum integration).

2. `src/centinel/anchor/opentimestamps_client.py:266` -- `SyntaxError: invalid syntax`. The `MultichainAnchor` class had no `class MultichainAnchor:` line -- the block started directly with docstring fragments (`Design:\n- Primary: OpenTimestamps...`), followed by an `__init__` with no `def __init__(self, testnet: bool = False) -> None:` signature, and an `anchor_checkpoint` method with no `def` or opening docstring.

3. `src/centinel/utils/logging_config.py:80` -- `SyntaxError: invalid syntax. Perhaps you forgot a comma?`. In the `SECRET_PATTERNS` list, the `arbitrum_private_key` pattern (marked "legacy" after the cleanup) ended with `)  # legacy,` -- the comma ended up *inside the comment* instead of after the parenthesis, breaking the list.

Additionally, `tests/test_config.py` had **two** instances of the same pattern: a `"alerts": {...}` dict immediately followed by `"rules": {...}` with no comma between them -- exactly the same error type as in `logging_config.py`, suggesting a systemic pattern of "lost commas while removing `blockchain`/`arbitrum` blocks".

A sixth error -- `tests/resilience -- UnboundLocalError: cannot access local variable '_imm'` -- was different: the stub block for `centinel.defense.*` in `conftest.py` used `_imm.ModuleSpec(...)` without `_imm` (alias for `importlib.machinery`) being imported in that specific scope (it was imported in two earlier blocks, but not this third one).

### 2) The Hypothesis

All these errors share a single root cause: **the paid-service cleanup (Arbitrum/blockchain/IPFS) was done with text edits that left orphaned fragments**, and since those files never successfully imported again afterward, no test exercised them, and the suite never reported the issue -- it simply collapsed at collection time with an error count likely written off as "dependency noise" without investigating each one.

Repair hypothesis: each error is **locally reconstructible** without changing behavior -- it's enough to identify which piece of code was missing (a function signature, a comma, a class name) using immediate context (what variables are used afterward, what signature sibling classes like `OpenTimestampsClient` have) and restore it minimally.

### 3) The Experiment / Implementation

**Step 1 -- Dependency inventory.** `pip install -e .` resolved most of the initial 32 collection errors (pydantic and other `pyproject.toml` dependencies weren't installed in the audit environment). 32 errors dropped to 6.

**Step 2 -- `storage.py` (orphaned `except` block):**
```python
# BEFORE (broken):
snapshot_hash = compute_hash(canonical_json, previous_hash=previous_hash)
tx_hash = None
# tx_hash = publish_hash_to_chain() — REMOVED (Zero Cost)
    tx_hash = None  # OTS handles anchoring: centinel.core.anchoring
        except Exception as exc:  # noqa: BLE001
            logger.warning("blockchain_publish_failed error=%s", exc)
        department_code = snapshot.meta.department_code

# AFTER (fixed):
snapshot_hash = compute_hash(canonical_json, previous_hash=previous_hash)
tx_hash = None  # OTS handles anchoring: centinel.core.anchoring (Zero Cost)
department_code = snapshot.meta.department_code
```

After this fix, `storage.py` imported correctly but **exposed 3 additional bugs** that had been dormant because the file could never run:

- The `snapshot_index` schema and per-department table schemas declared `tx_hash TEXT TEXT TEXT` (tripled column type -- remnants of collapsed `ipfs_cid`/`arbitrum_tx` columns from the cleanup).
- Two `INSERT OR REPLACE` statements had **13 `?` placeholders for 11 columns** (and for 6 columns, respectively) -- a direct mismatch causing `sqlite3.OperationalError: N values for M columns`.
- `export_department_json()` and `export_department_csv()` included an empty-string `""` key/column in the payload -- `row[""]` raised `IndexError: No item with that key`.

The four fixes (schema, two `VALUES (...)`, two exports) are single-line surgical edits that don't change the actual data model shape (11 columns + index).

**Step 3 -- `opentimestamps_client.py` (`MultichainAnchor` class reconstructed):**

Using `OpenTimestampsClient` (the complete sibling class) as a style template, the following was restored:
```python
class MultichainAnchor:
    """Anchors checkpoints using OpenTimestamps (Bitcoin), Zero Cost.
    ES: Ancla checkpoints usando OpenTimestamps (Bitcoin), Costo Cero.
    Design:
    - Primary: OpenTimestamps (fast, free, proven)
    - Non-fatal: if both fail, publish without anchor (lower assurance)
    """

    def __init__(self, testnet: bool = False) -> None:
        """Initialize multi-chain anchor (OTS Bitcoin only)."""
        self.ots_client = OpenTimestampsClient(use_testnet=testnet)
        self.testnet = testnet

    def anchor_checkpoint(self, checkpoint: dict) -> dict:
        """Anchor a checkpoint's merkle root via OpenTimestamps.
        ...
        """
        merkle_root = checkpoint.get("merkle_root", "")
        ...
```

The body of `anchor_checkpoint` (stamp + non-fatal fallback logic) already existed intact -- only the class signature, `__init__`, and the method's opening docstring were missing.

**Step 4 -- `logging_config.py` and `test_config.py` (commas):** three single-line fixes, moving the comma from inside the `# legacy,` comment to its correct position `),  # legacy`, and adding the missing comma after two `"alerts": {...}` dicts.

**Step 5 -- `tests/resilience/conftest.py`:** added `import importlib.machinery as _imm` at the start of the `centinel.defense.*` stub block, which lacked it (the other two similar blocks in the same file had it).

**Step 6 -- `tests/test_opentimestamps_client.py`:** the test file for `MultichainAnchor` had the same problem as the production code -- it was missing `class TestMultichainAnchor:` (the 4 test functions were nested inside `TestOpenTimestampsClient` due to a structural/indentation error), and all 4 functions referenced an `anchor` variable that was never instantiated. Added the class, the `MultichainAnchor` import, and `anchor = MultichainAnchor()` in each test. A fifth detail: `test_anchor_checkpoint_ots_fails` didn't set `mock_stamp.return_value = None`, so the mock returned a truthy `MagicMock` and the test failed with the opposite of the expected result.

### 4) The Result (The Lesson)

| Step | Tests collected | Passing | Failing | Errors |
|------|------------------|---------|---------|--------|
| Initial state (no deps) | not computable | -- | -- | 32 (collection) |
| After `pip install -e .` | 660 | -- | -- | 6 (collection) |
| After syntax fixes in `src/` and `test_config.py` | 728 | -- | -- | 1 (collection) |
| After `_imm` fix in `conftest.py` | 729 | -- | -- | 0 (collection) |
| Full suite (excluding `tests/resilience`, see Diary 02) | -- | 650 | 75 | 4 |
| After installing `pytest-asyncio` | -- | 685 | 40 | 4 |
| After `storage.py` fixes (4 additional bugs) | -- | 694 | 34 | 1 |
| After `test_opentimestamps_client.py` fixes | -- | **698** | 30 | 1 |

**The central lesson:** a "526/526 passing" badge in the README can describe a state that **stopped being true at the exact moment of the last major cleanup**, and nobody would have known without running the suite -- the repository kept "looking fine" because nobody had tried to import those specific modules since then. The root cause of the 6 bugs across `storage.py`/`opentimestamps_client.py`/`logging_config.py` was always the same operation (Arbitrum/IPFS removal), likely executed with find-and-replace or block edits that didn't preserve surrounding syntactic structure.

### 5) The Final Decision (Takeaway)

`@qa-engineering-agent` is formally added to the roster (20/20) with a non-negotiable mandate: **before declaring any change to `src/` or `web/ops/` complete, run the relevant suite and report exact numbers**. This finding is the empirical justification for why that rule exists -- without it, the project had been operating for an unknown amount of time with a core that couldn't even import, with nobody aware.

The 6 fixed files were committed directly to `main` and `dev-v12` in parallel (current project convention). `refactor/v13-clean-core` now has a real baseline (698 passing in the core) against which to measure package-renaming regressions.

### 6) What Changed and Why Now

This work was triggered because the user asked to start `refactor/v13-clean-core` (renaming `src/centinel/` -> `src/vigil/` as part of the CENTINEL -> VIGIL rebrand). The `@qa-engineering-agent`, created earlier in this same session with the explicit mandate "never declare tests passing without having run them", executed that mandate before touching a single line of the refactor -- and the result changed the plan: you cannot measure the impact of a massive package rename on a baseline that doesn't even import.

### 7) Implementation Decisions

- **Minimal reconstruction, not redesign:** each fix restored the most probable shape of the original code (using sibling classes and the rest of the file as style reference), without adding new functionality or changing the data model.
- **One operation = one shared commit message:** the 6 files were committed with the same descriptive message (Arbitrum/blockchain cleanup remnants), so the history documents the common root cause.
- **The remaining 30 failures were not touched in this session** -- see Diary 02 for why those aren't regressions of the same type and don't block the refactor.

### 8) Impact

- VIGIL's core (`src/centinel/core/`, `src/centinel/anchor/`) now imports and runs correctly. Before this work, **3 central modules (storage, OTS anchoring, secure logging) had SyntaxError/IndentationError** and any code importing them would fail at import time, not just in tests.
- `store_snapshot()`, `export_department_json()` and `export_department_csv()` -- functions used for the custody chain and observer-facing exports -- had SQL bugs (misaligned placeholders, empty columns) that would have failed in production the first time they were invoked with real data.
- Baseline established: 698 tests passing in the core, ready as a reference point for `refactor/v13-clean-core`.

### 9) Cycle Takeaway

A green badge in the README is not evidence of anything if nobody recomputes it after every major structural change. The `@qa-engineering-agent`'s "run and report exact numbers" rule isn't bureaucracy -- it's the only defense against an electoral audit system's core code being silently broken.

---

## PRs de este ciclo / PRs in this cycle

| PR | Descripcion | Estado |
|----|-------------|--------|
| (commit directo) | Fix bloque `except` huerfano y esquema SQL en `storage.py` | mergeado (main + dev-v12) |
| (commit directo) | Reconstruccion de clase `MultichainAnchor` en `opentimestamps_client.py` | mergeado (main + dev-v12) |
| (commit directo) | Fix coma faltante en `SECRET_PATTERNS` (`logging_config.py`) | mergeado (main + dev-v12) |
| (commit directo) | Fix 2 comas faltantes en `test_config.py` | mergeado (main + dev-v12) |
| (commit directo) | Fix `_imm` no importado en `tests/resilience/conftest.py` | mergeado (main + dev-v12) |
| (commit directo) | Reconstruccion de `TestMultichainAnchor` en `test_opentimestamps_client.py` | mergeado (main + dev-v12) |

---

## Metricas de impacto / Impact Metrics

| Metrica | Antes | Despues |
|---------|-------|---------|
| Errores de coleccion de pytest | 32 (sin deps) / 6 (con deps) | 0 |
| Modulos de `src/centinel/core` y `anchor/` importables | No (3 con SyntaxError/IndentationError) | Si |
| Tests pasando en nucleo (excl. resilience) | 650 | 698 |
| Tests fallando en nucleo (excl. resilience) | 75 | 34 (ver Diario 02) |
| Bugs de SQL latentes en `storage.py` detectados | 0 (codigo nunca corria) | 4 encontrados y corregidos |
| Veracidad del badge README "526/526" | No verificable / probablemente falso | Pendiente actualizacion (ver Diario 02) |

---
