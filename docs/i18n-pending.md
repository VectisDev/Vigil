# CENTINEL Lab — i18n (ES/EN) — Estado y Pendientes

Última actualización: commit `410aaa8f5419` (Capa 3h).
Toggle EN/ES: `#lang-toggle`, persistido en `localStorage.vigil-lang`.

## ✅ COMPLETADO (Capas 1–3h)

| Capa | Alcance | Commit |
|---|---|---|
| 1 | Theme + lang toggle, paleta light | `a95310a5183f` |
| 2 | Indicadores, dataset bar, panel forense header, dept grid, 12 chart-toggles | `c63ab0c4c0a4` (+fix `afd15cac1bb4`) |
| 3a | Modal Citación + Modal Configuración | `a5626eef12bb` |
| 3b | Citas APA/BibTeX/ISO dinámicas + meta sesión + "Copiado" | `2e958ab932d5` |
| 3c | Tarjeta Herramientas Académicas | `76dee56b8287` |
| 3d | Drawer Metodología (9 secciones) + fix entidad `&gt;` | `de75f37db820`+`40696801bda1` |
| 3e | Selector dataset, Centro Telemetría (header/sonido/empty), Modal Guardar Sesión, watermark | `e01445bd87be` |
| 3f | `EVENTS_EN` (A1-A9,B1-B13 = 22), Matriz Inyección, Builder dataset (3 tabs) | `69fe47ed9721`+fix `562cc472bdeb` |
| 3g | `EVENTS_EN` completo (+C1-C10 = 32), `_trMsg()` traductor por frases | `635aa9f7ba26` |
| 3h | Panel Forense (36 verdicts vía `card()`/`badge()`), `emitEngineEvents` | `410aaa8f5419` |

**Infraestructura clave ya disponible para lo que falta:**
- `LAB_I18N` dict + `applyLabI18n(lang)` + `data-i18n` / `data-i18n-attr` / `data-i18n-html`
- `EVENTS_EN` (32 entries: label/desc/breakpoint/param.label) + helpers `evLabel/evDesc/evBreakpoint/evParamLabel`
- `_trMsg(str)` — traductor de mensajes dinámicos por diccionario de frases (`_LOG_FULL_EN` 78 entradas + `_LOG_PHRASES_EN` 149 fragmentos, auto-ordenado por longitud)
- Todo esto se re-aplica automáticamente en `applyLabI18n` al togglear idioma (incluye re-render de grids, tabla builder, alertas)

---

## ⏳ PENDIENTE

### ✅ Bloque P1 — Mensajes de control sueltos — COMPLETADO
Commit `85a996219453`. Las ~30 cadenas (play/pause/stop/loop, exports PNG/CSV/BibTeX/ZIP/TXT, carga dataset/sesión, pre-registro, errores) ahora pasan por `_trMsg`/`_LOG_FULL_EN`/`_LOG_PHRASES_EN`. Bonus: tags de "Inyecciones activas"/"Cancelar" ahora usan `evLabel()` y son bilingües. Verificado en vivo sin errores.

### Bloque P2 — Sección Swarm/Bizantino (la más grande restante)
HTML: ~17,600 chars, 79 fragmentos visibles estáticos + ~10 funciones JS con contenido dinámico.

**P2.1 — HTML estático (79 fragmentos)**, incluye:
- Headers/labels: "Swarms en la Red", "Nodos y Estado de Consenso", "Métricas de Interacción", "Forensic Trail (Reproducible)" (ya en EN), "Estado de Validación por Swarm", "Verificación de Checksums (Hash Validation)", "LÍNEA DE TIEMPO — Elección en Progreso"
- Controles: "Nodos totales (N):", "Byzantine (M):", "BFT Threshold/tolerancia", "Nodos (máx 12):", "1 nodo".."12 nodos" (12 variantes), "Agregar swarm externo:", botones "+ Agregar"/"Limpiar"/"Desconectar"
- Leyenda/explicación: "Cómo leer esto:", "¿Qué está sucediendo?", "Cada círculo es un nodo. Los nodos...", "(Mira cómo se comunican los nodos entre swarms)", "(Todos los swarms auditan simultáneamente)"
- Estados/badges: "Comprometidos"/"Divergente"/"Pending"/"OK"/"Consenso"/"Resultado"/"Gossip"/"Embajador"/"LOCAL (nosotros)"/"Ring-0 semilla"/"Ring-1 confiable"/"Ring-2 observador"
- "Fase 1: Recopilación", "Esperando inicio de auditoría...", "Esperando fase de validación...", "0 externos activos", "✓ VÁLIDO"/"✗ INVÁLIDO"
- "▶ Iniciar Auditoría Distribuida", "⚡ Corte eléctrico", "✕ traición", "Rondas gossip", "Msgs/tick", "Rounds", "Status", "JSON", "Inicio", "Swarm TXT"

**P2.2 — Mensajes dinámicos (logSE/logSA/pushAlert)**, ~15 únicos con prefijos tipo `[PBTM]`, `[CONSENSUS]`, `[GOSSIP]`, `[OUTAGE]`, `[RESTORE]`, `[BETRAYAL]`, `[SPEC:...]` — candidatos a `_trMsg` (mismo patrón ya usado).

**Estimación:** el bloque más grande — comparable o mayor a Capa 3f+3g+3h combinadas. Alto volumen de HTML estático (mecánico, bajo riesgo) + lógica dinámica de swarm (requiere cuidado por los placeholders `${...}`).

---

## Recomendación de orden
1. **P1** primero — rápido, cierra "ruido" disperso, bajo riesgo.
2. **P2.1** (HTML estático del Swarm) — mecánico, igual patrón que capas anteriores.
3. **P2.2** (mensajes dinámicos swarm) — última, requiere más atención a los `${...}`.

Con P1+P2 completos, el lab quedaría **100% bilingüe** sin fragmentos conocidos en español.
