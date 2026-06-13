# CENTINEL Lab — i18n (ES/EN) — Estado

Última actualización: commit `aa114d237d8a`. **Estado: COMPLETO.**

Toggle EN/ES: `#lang-toggle`, persistido en `localStorage.vigil-lang`.

## ✅ Cobertura completa (Capas 1–3h + Bloques P1–P2)

| Bloque | Alcance | Commit |
|---|---|---|
| 1 | Theme + lang toggle, paleta light | `a95310a5183f` |
| 2 | Indicadores, dataset bar, panel forense header, dept grid, 12 chart-toggles | `c63ab0c4c0a4` (+fix `afd15cac1bb4`) |
| 3a | Modal Citación + Modal Configuración | `a5626eef12bb` |
| 3b | Citas APA/BibTeX/ISO dinámicas + meta sesión + "Copiado" | `2e958ab932d5` |
| 3c | Tarjeta Herramientas Académicas | `76dee56b8287` |
| 3d | Drawer Metodología (9 secciones) + fix entidad `&gt;` | `de75f37db820`+`40696801bda1` |
| 3e | Selector dataset, Centro Telemetría, Modal Guardar Sesión, watermark | `e01445bd87be` |
| 3f | `EVENTS_EN` (22), Matriz Inyección, Builder dataset (3 tabs) | `69fe47ed9721`+fix `562cc472bdeb` |
| 3g | `EVENTS_EN` completo (32, +C1-C10), `_trMsg()` traductor | `635aa9f7ba26` |
| 3h | Panel Forense (36 verdicts), `emitEngineEvents` | `410aaa8f5419` |
| P1 | ~30 mensajes de control (play/pause/loop/exports/dataset/sesión) + tags inyección activa | `85a996219453` |
| P2 | Sección Swarm/Bizantino completa: 79 fragmentos estáticos + ~24 mensajes dinámicos (PBTM/CONSENSUS/GOSSIP/OUTAGE/RESTORE/BETRAYAL/SPEC) | `16512ffb99bb`+fix `aa114d237d8a` |

## Infraestructura
- `LAB_I18N` dict + `applyLabI18n(lang)` + `data-i18n` / `data-i18n-attr` / `data-i18n-html` / `data-i18n-title`
- `EVENTS_EN` (32 entries) + helpers `evLabel/evDesc/evBreakpoint/evParamLabel`
- `_trMsg(str)` — traductor por diccionario de frases (`_LOG_FULL_EN` + `_LOG_PHRASES_EN`, auto-ordenado por longitud)
- Todo se re-aplica automáticamente en `applyLabI18n` al togglear idioma (grids, tablas, alertas, swarm cards, métricas, checksums, KPIs)

## Notas
- Logs históricos generados ANTES de cambiar idioma permanecen en el idioma en que se generaron (comportamiento esperado — igual que cualquier consola de eventos).
- Si aparecen nuevos fragmentos en español en el futuro (nuevas features), añadir a `_LOG_FULL_EN`/`_LOG_PHRASES_EN` o `LAB_I18N` siguiendo el mismo patrón.
