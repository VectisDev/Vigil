# Log Retention Policy — Vigil

> NIST SP 800-92 §2.4. Última actualización: 2026-06-23.

## Tipos de logs y retención

| Tipo | Descripción | Retención | Almacenamiento | Protección |
|---|---|---|---|---|
| Snapshots electorales (JSON) | Datos crudos del CNE con hash SHA-256 | **Permanente** — evidencia electoral | GitHub releases + backups cifrados | SHA-256 + OTS Bitcoin |
| Hash chain (`chain.json`) | Cadena completa de hashes encadenados | **Permanente** — integridad verificable | GitHub releases + IPFS | SHA-256 encadenado |
| Logs de polling (`vital_signs`) | Registro de cada ciclo de descarga: timestamp, URL, código HTTP, hash | **Mínimo 1 año** post-elección | GitHub Actions artifacts + backup local | Solo escritura durante operación |
| Alertas CRS | Eventos de anomalía detectados con timestamp y snap_index | **Permanente** dentro del hash chain | Embebidos en snapshots firmados | Ed25519 + OTS |
| Logs de errores del pipeline | Excepciones, timeouts, errores de red | **30 días** mínimo en operación activa | Local + vital_signs | No contienen PII |
| Timestamps de renderización UI | Cuándo se generó cada vista en /lab/ y /replay/ | **No retenidos** — solo se muestran en UI | Memoria del navegador (no se persisten) | N/A |

## Reglas de retención

1. **Evidencia electoral** (snapshots + hash chain): retención permanente. Son el artefacto primario del sistema; su eliminación destruiría la cadena de custodia.
2. **Logs operativos** (polling, errores): mínimo 1 año. Pueden eliminarse después si no hubo incidentes en ese período.
3. **Sin retención de PII**: el sistema no recopila ni retiene ningún dato personal identificable (PII) en ningún log.
4. **Inmutabilidad post-ancla**: cualquier snapshot anclado en Bitcoin via OpenTimestamps no puede ser eliminado sin romper la cadena de custodia — la política de retención permanente es técnicamente reforzada por el diseño.

## Procedimiento de eliminación controlada

Solo logs operativos (no evidencia) pueden eliminarse, mediante:
1. Verificar que el período de observación electoral ha concluido y no hay litigios activos.
2. Documentar la eliminación en el dev-diary con fecha y tipo de log eliminado.
3. Nunca eliminar snapshots ni hash chain — estos son permanentes por diseño.

---
*Ver también: `docs/operations/EVIDENCE-PUBLICATION-SLA.md`, `centinel_engine/secure_backup.py`.*
