# Auditoría — código muerto / duplicado (pasada "ponytail" dev-v14)

Fecha: 2026-07-03
Rama: `claude/dev-v14-ponytail-qakwa5`
Metodología: aplicación manual de la filosofía del plugin
[DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (no instalable en esta
sesión de agente remoto) — escalera de decisión "¿hace falta? → ¿ya existe? → ¿stdlib? →
¿una línea? → mínimo necesario" aplicada como auditoría de solo-lectura.

**Alcance de este reporte:** `src/centinel/core`, `src/centinel/federation`,
`src/centinel/defense`, `src/centinel/api`, `command_center/`, `verify/verify_chain.py`, y
duplicación de primitivas hash/merkle en `scripts/`. Ninguno de estos hallazgos fue aplicado
como cambio de código en esta sesión — el núcleo forense/criptográfico de VIGIL requiere
revisión de `crypto-security-agent`/`stats-phd-agent` antes de tocarlo, y varias de las
"duplicaciones" resultaron ser independencia de verificación intencional (ver más abajo).

---

## 1. `src/centinel/core/blockchain.py` — DEAD, alta confianza

53 líneas. Encabezado explícito:

```
DEPRECATED — Este módulo fue eliminado por violar el principio de Costo Cero.
DEPRECATED — This module was removed for violating the Zero Cost principle.
```

Ambas funciones son stubs que apuntan al reemplazo real
(`centinel.core.anchoring.anchor_snapshot_chain()`). **Cero llamadores** en todo el repo
fuera del propio archivo (`grep -rl` en `src/`, `scripts/`, `command_center/`, `tests/` no
encontró ninguna referencia externa).

**Recomendación:** eliminar el archivo. Es el candidato más limpio de todo el hallazgo —
literalmente se documenta a sí mismo como muerto y no rompe nada. Bajo riesgo, pero se deja
fuera de esta sesión por estar en `src/centinel/core` (fuera de alcance acordado).

## 2. `src/centinel/core/rules/benford_unified.py` — no está muerto, contiene código legacy interno

Comentarios en el docstring marcan como DEPRECATED dos rutas internas ("Rule 2 per-candidate"
y el sub-test granular de Rule 10e), absorbidas en la implementación unificada. El módulo en
sí **sí tiene llamadores activos**: `benford_law_rule.py`, `benford_first_digit_rule.py`, y
`tests/rules/test_unified_stats.py`.

**Recomendación:** requiere lectura completa del archivo (no realizada en esta sesión) para
confirmar si las rutas "absorbidas" siguen presentes como código muerto dentro del módulo o
si ya fueron removidas y solo queda el comentario histórico. Candidato para
`stats-phd-agent` — cualquier cambio a la lógica de Benford debe preservar el comportamiento
matemático validado.

## 3. `src/centinel/core/rules/granular_anomaly_rule.py` — hallazgo menor, no accionable

El marcador DEPRECATED es sobre una única línea comentada (`# _config_z = ...`, línea 318) y
un campo de config legacy (`zscore_threshold`) ya reemplazado por umbrales unificados. El
archivo está activamente en uso (`rules_engine.py`, `README.md`, `scripts/
validate_false_positive_rate.py`, `command_center/rules.yaml`). Es una sola línea de
ceremonia (comentario histórico) — de bajo valor tocar sin acompañarlo de una limpieza más
amplia del archivo completo.

## 4. Duplicación de primitivas hash/merkle en `scripts/` — mayormente intencional, NO fusionar

Se encontraron funciones con el mismo nombre en múltiples scripts:

| Función | Archivos |
|---|---|
| `sha256_file` | `evidence_bundle.py`, `verify_evidence_bundle.py`, `verify_snapshot_bundle.py` |
| `merkle_root` | `evidence_bundle.py`, `verify_evidence_bundle.py` |
| `_sha256_file` | `cli.py`, `generate_observer_pack.py` |

**Análisis:** `evidence_bundle.py` genera evidencia; `verify_evidence_bundle.py` y
`verify_snapshot_bundle.py` la verifican de forma independiente. Esto replica el mismo patrón
que `verify/verify_chain.py` — un verificador standalone que un observador internacional
(OEA, Carter Center) puede auditar sin depender del mismo código que generó la evidencia. Si
se fusionara `sha256_file`/`merkle_root` en un módulo compartido, un bug en ese módulo
afectaría tanto al generador como al verificador simultáneamente, **anulando el propósito de
la verificación independiente**.

**Recomendación:** NO fusionar. Documentar la intención (comentario en cada archivo indicando
que la duplicación es deliberada) para que futuras pasadas de limpieza no la interpreten como
descuido.

## 5. Duplicación de validación bootstrap — candidato real, pendiente de revisión dedicada

| Función | Archivos |
|---|---|
| `_canonical_json` | `bootstrap.py`, `validate_hashes.py` |
| `_validate_hash_dir` | `bootstrap.py`, `validate_hashes.py` |
| `_validate_sqlite` | `bootstrap.py`, `validate_hashes.py` |

A diferencia del punto 4, estas son funciones de sanity-check de arranque/validación, no
primitivas de evidencia forense — el riesgo de fusionarlas es menor. No se fusionaron en esta
sesión por falta de tiempo para el proceso completo descrito en el plan (diff de cuerpos,
localizar todos los llamadores, correr tests antes/después). Candidato de alta confianza para
una sesión de seguimiento dedicada a `scripts/`.

---

## Resumen de acciones recomendadas (ninguna aplicada en esta sesión)

| Hallazgo | Confianza | Acción sugerida |
|---|---|---|
| `src/centinel/core/blockchain.py` | Alta | Eliminar (cero llamadores, auto-documentado como muerto) |
| `benford_unified.py` rutas legacy internas | Media | Lectura completa + revisión de `stats-phd-agent` |
| `granular_anomaly_rule.py` línea comentada | Baja | Limpieza cosmética, no urgente |
| `sha256_file`/`merkle_root` en scripts de evidencia | N/A | **No tocar** — duplicación intencional (verificación independiente) |
| `_canonical_json`/`_validate_hash_dir`/`_validate_sqlite` (bootstrap vs validate_hashes) | Media-alta | Consolidar en sesión dedicada a `scripts/` |
