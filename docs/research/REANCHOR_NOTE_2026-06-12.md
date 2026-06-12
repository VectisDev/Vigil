# Re-anchoring Note — 2026-06-12

## Re-anclaje de pruebas OTS (`rules_yaml.ots`, `preregistration.ots`)

Los 4 archivos `.ots` originales (`rules_yaml.ots`, `rules_yaml_finney.ots`,
`preregistration.ots`, `preregistration_finney.ots`), generados el
2026-06-10, estaban **corruptos**: les faltaba el header mágico de
OpenTimestamps (`\x00OpenTimestamps\x00\x00Proof\x00...`) debido a un bug en
`anchor_snapshot_chain()` (`src/centinel/core/anchoring.py`) que serializaba
el objeto `Timestamp` directamente en lugar de envolverlo en un
`DetachedTimestampFile`. `ots verify`/`ots info` los rechazaban con
*"is not a timestamp file"* — nunca fueron pruebas válidas.

**Fix aplicado** (mismo bug, mismo fix que para `MERKLE_ROOT_HN2025.ots`,
commit `8285b4a`): `anchor_snapshot_chain()` ahora produce
`DetachedTimestampFile(OpSHA256(), ts)` correctamente serializado.

**Re-anclaje:** Se sometieron de nuevo los MISMOS digests documentados en
`THRESHOLD_PREREGISTRATION.md` (sin modificar ese archivo, para no invalidar
su propio hash pre-registrado) a los calendarios `bob.btc.calendar` y
`finney.calendar.eternitywall`:

| Archivo | Digest (SHA-256) | Atestigua |
|---|---|---|
| `rules_yaml.ots` / `rules_yaml_finney.ots` | `a15df9d95d96e5f10a6935b2e5a18b71640a6008e1bcd649882453924625493f` | `command_center/rules.yaml` |
| `preregistration.ots` / `preregistration_finney.ots` | `139f75cf1fe606a8a1560e040e759b0ab8764fead9d6e21817fc23f8872c2626` | `docs/research/THRESHOLD_PREREGISTRATION.md` (commit 2026-06-10, sin cambios) |

Ambos digests fueron verificados contra el contenido actual en `main` antes
de re-anclar — coinciden exactamente con los valores documentados en
`THRESHOLD_PREREGISTRATION.md`.

**Estado:** PENDING en ambos calendarios (Bitcoin, ~1 bloque).

**Verificación (no requiere los archivos originales en disco):**
```bash
pip install opentimestamps-client
ots verify -d a15df9d95d96e5f10a6935b2e5a18b71640a6008e1bcd649882453924625493f docs/research/rules_yaml.ots
ots verify -d 139f75cf1fe606a8a1560e040e759b0ab8764fead9d6e21817fc23f8872c2626 docs/research/preregistration.ots
```

**Verificación contra los archivos originales (una vez confirmado en Bitcoin):**
```bash
ots verify docs/research/rules_yaml.ots -f command_center/rules.yaml
ots verify docs/research/preregistration.ots -f docs/research/THRESHOLD_PREREGISTRATION.md
```

**Nota de cadena de custodia:** El pre-registro original tiene fecha de
commit 2026-06-10 (sigue siendo la fecha de "lock" de los umbrales en git
history). Esta nota documenta que la *prueba criptográfica externa* (anclaje
Bitcoin) de ese mismo contenido fue efectivamente publicada el 2026-06-12,
tras corregirse el bug de serialización. El contenido anclado es idéntico
(mismos hashes) — solo se corrigió el mecanismo de prueba.
