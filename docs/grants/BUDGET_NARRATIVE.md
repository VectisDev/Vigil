# VIGIL — Budget Narrative
# Narrativa Presupuestaria

**Grant:** OTF Internet Freedom Fund IFF-2026-06  
**Monto solicitado / Requested amount:** USD 75,000  
**Período / Period:** 12 meses / 12 months  
**Infraestructura de nube en este pedido / Cloud in this ask:** ninguna / none

---

## Principio presupuestario / Budgetary principle

Este es el único total del repositorio: **75,000 USD, 12 meses**. La nota
conceptual usa la misma tabla. Un bosquejo regional más amplio que estaba en
`REGIONAL-NARRATIVE.md` no es esta solicitud.

Los fondos no compran una granja de servidores. Sí pagan revisión, un release
comprobable, un detector de caídas para la próxima ventana (intentos con marca
de tiempo) y materiales. No hay una persona co-PI contratada.

---

## Hitos / Milestones

Cada fila nombra un artefacto que un tercero puede abrir. No hay viaje ni
conferencias en este pedido.

| # | Entregable | Dónde se ve | USD |
|---|---|---|---|
| 1 | Revisión estadística independiente, aún no contratada. Si las series anteriores a 2025 no se pueden archivar, el entregable es un resultado negativo escrito. | memo en `docs/research/` cuando exista; hoy el hueco está dicho en `docs/evidence/HN2025.md` | 22,000 |
| 2 | Release de software: tarball, CycloneDX, `SHA256SUMS`, firma keyless. El mantenedor corre el comando de `docs/operations/RELEASE.md`. Este cambio no publica el tag. | GitHub Release `vX.Y.Z` después de ese comando | 15,000 |
| 3 | Una caída es N intentos fallidos con marca de tiempo. La muestra de 2025 no se reetiqueta como caídas medidas. | `tests/fixtures/fetch_logs/` y `scripts/export_static_snapshot.py` | 10,000 |
| 4 | Materiales en español cuyo comando es el de `docs/VERIFY.md`. | `docs/VERIFY.md` | 12,000 |
| 5 | Notas de adaptación a un segundo portal público, sin trabajo de campo. | un documento futuro; no está prometido como piloto | 8,000 |
| 6 | Coordinación e imprevistos, 12 meses. | informes al financiador | 8,000 |
| | **Total** | | **75,000** |

## Lo que este presupuesto no incluye

- Servidores dedicados.
- Una persona co-investigadora ya nombrada.
- Viajes, conferencias, o un piloto de campo en otro país.
- Licencias de software cerrado.

## Después de los 12 meses

El código sigue en AGPL-3.0. Mantenerlo pide tiempo de quien lo publica, no una
subscripción de nube. No hay patrocinador fiscal en el repositorio; recibirlo
es un paso del mantenedor, fuera de git.

---

*VIGIL — AGPL-3.0 — docs/grants/BUDGET_NARRATIVE.md*  
*75,000 USD · 12 meses · misma tabla que `OTF_ConceptNote_IFF2026.md`*
