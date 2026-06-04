# Dev Diary - 202606 - OpsUXOverhaulAndOTSExtraction - 01

**Fecha aproximada / Approximate date:** 04-jun-2026 / June 4, 2026  
**Fase / Phase:** Rediseno completo de la experiencia del operador: limpieza post-SpaceX, extraccion de OTS como seccion independiente, auto-guardado, y controles avanzados tras el desbloqueo / Complete operator experience redesign: post-SpaceX cleanup, OTS extraction as standalone section, auto-save, and advanced controls behind the unlock gate  
**Version interna / Internal version:** v0.2.x (ciclo dev-v14)  
**Rama / Branch:** claude/zealous-carson-o0dva  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuacion del rediseno SpaceX del panel de operador (`/ops`). Con la estetica base ya mergeada (PR #695), tome una captura de pantalla real del panel en uso y descubri 5 problemas concretos que impedian que la interfaz fuera production-ready. Ese diagnostico me llevo a hacer una auditoria UX completa de 12 puntos, que a su vez genero 3 tandas de mejoras prioritizadas. En este ciclo tambien resolvi inconsistencias estructurales (OTS embebido dentro de Presets en lugar de tener seccion propia), elimine friccion operativa innecesaria (boton "Aplicar cambios", requisito de PAT para desbloqueo), y sume inteligencia contextual (controles de raspado avanzados que aparecen solo cuando el operador acepta responsabilidad explicita). Todo el trabajo vive en un unico archivo: `web/ops/index.html`. / Continuation of the SpaceX redesign of the operator panel (`/ops`). With the base aesthetic already merged (PR #695), I took a real screenshot of the panel in use and discovered 5 concrete problems preventing the interface from being production-ready. That diagnosis led me to a 12-point UX audit, which in turn generated 3 prioritized improvement batches. In this cycle I also resolved structural inconsistencies (OTS embedded inside Presets instead of having its own section), eliminated unnecessary operational friction ("Aplicar cambios" button, PAT requirement for unlock), and added contextual intelligence (advanced scraping controls that appear only when the operator explicitly accepts responsibility). All work lives in a single file: `web/ops/index.html`.

---

## [ES]

### 1) El Problema (Contexto)

El rediseno SpaceX habia entregado la estetica correcta pero cuando vi el panel en produccion identifique 5 problemas funcionales:

1. **SISTEMA mostraba "ALERTA" incorrectamente** — `_updateMissionBar()` usaba `querySelectorAll('.badge-bad')` que recogia *todos* los elementos con esa clase en el DOM (filas de logs, tablas), no solo los 4 badges de estado del sistema. Resultado: el sistema marcaba alerta cuando en realidad estaba nominal.

2. **"PAIS: CO" no se actualizaba** — `loadCountrySelector()` detectaba el codigo correcto del pais pero nunca actualizaba `ACTIVE_COUNTRY_CODE` ni llamaba `_updateMissionBar()`. El pais en la mission bar quedaba desincronizado tras la carga inicial.

3. **Etiqueta "DEFENSES" en ingles** — un hardcode en ingles habia sobrevivido al rediseno.

4. **Numeros de seccion obsoletos en los titulos** — "3 Presets", "4 Logs y terminales", "5 Manual"... el orden habia cambiado pero los prefijos numericos no.

5. **Botones INICIAR/FINALIZAR inaccesibles desde el sidebar** — el operador tenia que scrollear hasta el panel principal para iniciar o finalizar el monitoreo.

Resueltos esos 5, hice la auditoria UX de 12 puntos e identifique tres capas adicionales de problemas: (a) UX tier 1 — sidebar sin estado activo, etiquetas de estado cripticas, estados vacios sin contexto; (b) UX tier 2 — hint del swarm innecesario, OTS sin estado "idle", uptime sin valor ultimo; (c) UX tier 3 — warning de cambios no guardados al recargar, reloj local visible en mission bar, label del preset activo.

Ademas, me di cuenta de tres problemas estructurales mas profundos:
- **OTS enterrado dentro de Presets**: el anclaje Bitcoin no tenia seccion propia, rompia la jerarquia de informacion.
- **"Aplicar cambios" como boton explicito**: anadia friccion sin valor — el operador hace un cambio, tiene que recordar hacer click en aplicar; en momentos de presion electoral, eso es un error esperando ocurrir.
- **Desbloqueo de limites requeria PAT**: abria un modal de GitHub Personal Access Token solo para registrar una aceptacion. Innecesario y bloqueante para operadores no-tecnicos.

### 2) La Hipotesis

Todos los problemas eran resolubles sin cambiar la arquitectura. El panel es un unico HTML — cada fix es quirurgico y aislado. Las 5 correcciones post-SpaceX son bugs de logica JS o hardcodes HTML. La auditoria UX son mejoras de estado y feedback visual. Los problemas estructurales (OTS, auto-apply, PAT) requieren refactorizacion de JS pero sin nuevos archivos ni dependencias.

Mi hipotesis central sobre auto-apply: si el sistema puede detectar cambios (ya lo hace con `isDirty`) y puede commitear a GitHub (ya lo hace en `writeChanges()`), entonces un debounce de 1.5s en `markDirty()` que llame directamente a `writeChanges()` elimina el boton sin perder funcionalidad.

### 3) El Experimento / Implementacion

**5 correcciones post-SpaceX (PR #695-fixes -> PRs implicitos en el ciclo):**

- `_updateMissionBar()`: reemplace `querySelectorAll('.badge-bad')` por iteracion sobre los 4 IDs especificos de badges de estado (`badge-animal`, `badge-safemode`, `badge-circuit`, `badge-election`).
- `loadCountrySelector()`: anadi `ACTIVE_COUNTRY_CODE = currentCode; _updateMissionBar();` al final del bloque `try`.
- `doChangeCountry()`: anadi `_updateMissionBar();` al final.
- HTML mission bar: cambie `DEFENSES` -> `DEFENSAS`.
- Titulos de seccion: elimine prefijos numericos ("3 Presets" -> "Presets", etc.).
- Sidebar: anadi `#sidebar-ops-zone` con botones INICIAR y FINALIZAR sobre la zona de emergencia, con CSS de colores acorde (verde para iniciar, ambar para finalizar).
- `_setPipelineUI()`: sincronice `btn-sidebar-iniciar` junto con `btn-iniciar` en cada transicion running/stopped.

**Contador de tiempo activo — TIEMPO ACTIVO (PR #700):**

Anadi la funcion `_startUptimeClock()` que inicia al arrancar el pipeline, guarda el timestamp en `localStorage`, y formatea el tiempo transcurrido como `Xd Xh Xm Xs`. `_stopUptimeClock()` preserva la ultima duracion como "Ultimo: Xh Xm" para mostrarlo en el siguiente arranque. El item aparece en la mission bar entre DEFENSAS y UTC.

**Tooltips de seccion (PR #702):**

A cada titulo de seccion le puse un `<span class="sec-tip" data-tip="...">i</span>` con descripcion en lenguaje llano. Sin jerga tecnica — escribi las descripciones para un operador electoral, no para un desarrollador.

**Simplificacion del campo de URL electoral (PR #703):**

El campo dejo de pedir la ruta exacta del API (`/api/presidencial/nacional`). Ahora pide solo el dominio raiz (`https://resultados.organismo-electoral.gov`). Centinel descubre los endpoints automaticamente. Cambie el label a "Sitio de resultados" con descripcion explicita: "no necesitas saber nada mas".

**Evolucion del boton OTS (PRs #701, #704):**

Itere tres veces basandome en feedback visual:
1. Toggle checkbox -> boton en panel + fila en sidebar
2. Feedback: el boton enmedio rompia estetica, sidebar innecesario
3. Resultado final: boton `Activo / Inactivo` en el header del ctrl-section, sidebar row eliminado. Estado "idle" (OTS configurado pero pipeline detenido) con mensaje contextual.

**Auditoria UX de 12 puntos — 3 tandas (PRs #705, #706, #707):**

*Tanda 1 (tier 1 — critico):*
- Sidebar: cambie el scroll observer de IntersectionObserver a posicion relativa — mas confiable para highlight de seccion activa en scroll.
- Etiquetas de estado: `badge-animal` ahora muestra "NORMAL / CAUTION / SURVIVAL" en lugar de codigo interno; `badge-circuit` muestra "ACTIVO / ABIERTO".
- Estados vacios: logs y tablas muestran hint contextual en lugar de celda vacia.
- Tarjeta de Cierre Electoral: anadi indicador visual de estado (pendiente/en progreso/completo) con colores del sistema.

*Tanda 2 (tier 2 — medio):*
- Hint del swarm: ahora aparece solo cuando hay nodos conectados (antes era permanente).
- OTS idle: cuando el pipeline esta detenido, el badge OTS muestra "IDLE" en muted en lugar de mantener el ultimo estado.
- Uptime "ultimo conocido": al detener el pipeline, la mission bar muestra "Ultimo: Xh Xm" en lugar de resetear a "—".

*Tanda 3 (tier 3 — bajo):*
- Warning de cambios no guardados: `beforeunload` ya existia; anadi indicator visual en el titulo de seccion con `dirty-dot`.
- Reloj local: la mission bar muestra la hora local del operador junto a UTC.
- Label de preset activo: badge en el topbar del panel que indica que preset esta cargado.

**Desbloqueo sin PAT (PR #708):**

Refactorice `executeUnlock()`: el flujo ya no abre el modal de PAT. La aceptacion se registra en `localStorage` con timestamp y texto completo del documento legal. Si hay un PAT disponible en `sessionStorage` (de una sesion anterior de apply), hago un commit como bonus — pero no bloquea el flujo. La firma siempre queda registrada; el commit de Git es opcional.

**Extraccion de OTS como seccion independiente — s9 (PR #709):**

Extraje el bloque OTS de `#s3` (Presets) y lo converti en `<div class="section" id="s9">` con:
- Titulo: "Anclaje Bitcoin"
- Tooltip: descripcion de OpenTimestamps en lenguaje claro
- `<hr class="section-sep">` y `ctrl-section` con el contenido completo
- CSS order actualizado: `#s9{order:4}` — entre Presets y Logs
- Sidebar: nueva entrada "Anclaje Bitcoin" bajo sec-header "Integridad"
- `_updateSidebarActive()` actualizado con `'s9'` en el array de IDs

**Auto-guardado — eliminacion de "Aplicar cambios" (PR #709):**

Hice que `markDirty()` ahora inicie un timer de debounce de 1.5s. Si no hay mas cambios en ese tiempo, llama a `autoApply()` — que construye los YAMLs, calcula el diff, pide PAT si no hay uno en sessionStorage, y commitea directamente a GitHub. Elimine el boton "Aplicar cambios" del header. `applyChanges()` es ahora un alias de `autoApply()` para los casos internos que lo llaman directamente (emergencia, reload-reapply).

El diff modal (`showDiffModal`) sigue existiendo en el DOM pero ya no se usa en el flujo normal. Lo mantuve por si acaso se necesita en el futuro.

**Controles de raspado ampliados — unlock gate (PR #710):**

Cuando `ceilingUnlocked === true`, aparece en la seccion Presets un panel `#unlocked-scraping-panel` con borde ambar y etiqueta de advertencia. Contiene 6 controles visibles con rangos extendidos:

| Control | Normal | Desbloqueado |
|---------|--------|-------------|
| Intervalo | 1-60 min | 0.5-60 min |
| Requests/hora | 60-480 | 60-1200 |
| Rafaga (burst) | 1-10 | 1-30 |
| Jitter | — | 0-60 seg (nuevo) |
| Concurrencia | — | 1-10 endpoints (nuevo) |
| Timeout | solo en tab avanzado | visible aqui |

Anadi los sliders nuevos (`sl-interval3`, `sl-rph3`, `sl-capacity2`, `sl-timeout2`) a `SLIDER_IDS` y `BADGE_IDS` para sincronizacion bidireccional con los existentes. `jitter_seconds` escribe a `rate_limiter.yaml`; `max_concurrent_requests` escribe a `config.yaml`.

**Seguridad — CodeQL alerts #37 y #38 (PRs #709, #711):**

Encontre dos workflows que tenian `softprops/action-gh-release@v1` — tag mutable, CWE-829. Pinee ambos al SHA de commit de v2.6.2: `3bb12739c298aeb8a4eeaf626c5b8d85266b0e65`.

### 4) El Resultado (La Leccion)

Todos los cambios funcionaron. El panel paso de "visualmente renovado pero con bugs" a "operativamente correcto". La mission bar muestra el estado real del sistema. El pais se actualiza. El OTS tiene su seccion propia con la misma jerarquia visual que el resto.

El hallazgo mas importante del ciclo no fue tecnico — fue de diseno de flujo: **el boton "Aplicar cambios" era una trampa de friccion**. En una interfaz de monitoreo electoral bajo presion, anadir un paso manual entre "hice el cambio" y "el cambio esta en produccion" es introducir un error esperando ocurrir. El operador cambia el preset de `election` a `aggressive`, ve que el cambio esta en la UI, y asume que esta aplicado — pero si no hizo click en "Aplicar", no lo esta. El debounce de 1.5s que implemente elimina esa trampa sin reducir el control: el operador sigue siendo quien inicia el cambio.

### 5) La Decision Final (Takeaway)

La friccion operativa en sistemas de monitoreo no es "seguridad adicional" — es superficie de error. Un paso manual extra no hace el sistema mas seguro; hace mas probable que el operador cometa un error de omision. Auto-aplicar con debounce es el patron correcto: captura la intencion del usuario (el cambio) sin requerir confirmacion de la intencion (el click).

El unlock gate para controles avanzados implementa el principio opuesto con la misma logica: los controles de raspado agresivo (sub-minuto, >480 req/h, jitter, concurrencia) no deben estar disponibles por defecto — no porque el operador no pueda usarlos, sino porque su disponibilidad visual implica que son opciones normales. Al ocultarlos tras el desbloqueo explicito, el panel comunica que usarlos es una decision deliberada con consecuencias, no una configuracion de rutina.

### 6) Que cambio y por que ahora

El ciclo lo disparo una captura de pantalla real del panel en uso. Sin ese feedback visual concreto, los bugs habrian permanecido indefinidamente — todos eran invisibles en el codigo, solo visibles en la interaccion real.

La extraccion de OTS vino de un diagnostico que me hice yo mismo: "soy yo o no tenemos esto como una seccion propia?" — pregunta legitima. El anclaje Bitcoin es la caracteristica de integridad mas importante del sistema (es la que permite verificacion independiente de los datos), y estaba enterrada dentro de Presets como si fuera un ajuste de configuracion menor. La jerarquia de informacion no reflejaba la jerarquia de importancia.

### 7) Decisiones de implementacion

- **Debounce de 1.5s (no 500ms ni 5s):** 500ms es demasiado agresivo — dispara ante cambios intermedios en sliders. 5s hace que el operador espere demasiado para ver el resultado. 1.5s captura el final de una interaccion sin sobrecargar el API de GitHub.
- **PAT en sessionStorage (no localStorage):** El PAT desaparece al cerrar el browser — lo hice intencional. Un PAT guardado permanentemente es un riesgo de seguridad. La friccion de ingresarlo una vez por sesion es el trade-off correcto.
- **Unlock en localStorage (no solo en memoria):** El estado desbloqueado persiste entre recargas de la misma sesion de trabajo. Si el operador desbloquea, recarga la pagina, y vuelve a entrar, el sistema recuerda el desbloqueo. Decidi esto para evitar que una recarga accidental fuerce un re-desbloqueo en el peor momento.
- **Jitter como control nuevo (no existente):** El jitter no existia en la config. Lo anadi como campo nuevo en `rate_limiter.yaml`. Es la capacidad mas util en entornos de monitoreo agresivo — hace impredecible el timing de las peticiones, reduciendo la detectabilidad del scraper.
- **Concurrencia en config.yaml (no rate_limiter):** Decision de semantica: `max_concurrent_requests` es un parametro de comportamiento del scheduler, no del rate limiter. El rate limiter controla velocidad; el scheduler controla paralelismo.
- **OTS como s9 (no s2 o junto a Presets):** Evalue ponerlo antes de Presets. Lo descarte porque el flujo logico del operador es: Panel -> Red -> Presets (configuracion) -> Anclaje (integridad de lo configurado) -> Logs (que paso). El anclaje va despues de la configuracion, no antes.
- **Scroll observer por posicion (no IntersectionObserver):** El IntersectionObserver tiene comportamiento complejo cuando multiples secciones son visibles simultaneamente (pantallas grandes). El observer por posicion — "que seccion tiene el top mas cercano a 90px sin pasarlo?" — es determinista y predecible.

### 8) Impacto

**Operativo:** La mission bar ahora muestra informacion confiable. Un operador que ve "SISTEMA: NOMINAL" puede confiar en que el sistema esta nominal — antes, el bug de `querySelectorAll` podia mostrar ALERTA permanentemente aunque todo estuviera bien.

**Estructural:** OTS tiene seccion propia con la jerarquia visual correcta. Un auditor externo que abra el panel puede encontrar el anclaje Bitcoin directamente en el sidebar, sin saber donde buscar.

**Flujo de trabajo:** El auto-apply elimina una clase entera de errores operativos. El operador ya no puede estar en el estado "creo que aplique el cambio pero no estoy seguro".

**Seguridad:** Cerre CodeQL alerts #37 y #38. Los dos workflows que usan `softprops/action-gh-release` ahora apuntan a un SHA de commit inmutable, eliminando el vector de supply chain attack por tag hijacking.

**Inteligencia contextual:** El unlock gate de controles avanzados implementa el principio de menor privilegio en la interfaz: la capacidad de hacer dano (raspado agresivo) solo esta disponible cuando el operador ha aceptado explicitamente la responsabilidad de usarla.

### 9) Aprendizaje de ciclo

Una interfaz de operador no es una aplicacion de usuario final. Las aplicaciones de usuario final optimizan para facilidad de descubrimiento. Las interfaces de operador optimizan para **claridad de estado bajo presion**. Son objetivos diferentes.

En una noche electoral, el operador tiene 30 segundos para decidir si cambiar el preset de `election` a `aggressive`. En ese momento no puede: buscar en menus, confirmar modales innecesarios, o dudar sobre si un cambio se aplico. El panel tiene que comunicar el estado del sistema sin ambiguedad, ejecutar los cambios sin friccion, y reservar la friccion para decisiones que realmente la merecen (desbloqueo de limites, parada de emergencia, cierre electoral).

Ese principio — **friccion proporcional a la consecuencia** — es lo que guio todas mis decisiones en este ciclo.

---

## [EN]

### 1) The Problem (Context)

The SpaceX redesign delivered the right aesthetic but when I looked at the panel in production I identified 5 functional problems:

1. **SISTEMA showing "ALERTA" incorrectly** — `_updateMissionBar()` used `querySelectorAll('.badge-bad')` which collected *all* elements with that class in the DOM (log rows, tables), not just the 4 system status badges. Result: the system flagged alert when it was actually nominal.

2. **"PAIS: CO" not updating** — `loadCountrySelector()` detected the correct country code but never updated `ACTIVE_COUNTRY_CODE` or called `_updateMissionBar()`. The country in the mission bar stayed out of sync after initial load.

3. **"DEFENSES" label in English** — a hardcoded English string had survived the redesign.

4. **Obsolete section numbers in titles** — "3 Presets", "4 Logs y terminales", "5 Manual"... the order had changed but the numeric prefixes hadn't.

5. **INICIAR/FINALIZAR buttons inaccessible from sidebar** — the operator had to scroll to the main panel to start or stop monitoring.

Once I resolved those 5, I ran a 12-point UX audit and identified three additional layers: (a) tier 1 — no active sidebar state, cryptic status labels, empty states without context; (b) tier 2 — unnecessary swarm hint, OTS without "idle" state, uptime without last-known value; (c) tier 3 — unsaved changes warning on reload, local clock in mission bar, active preset label.

Plus three deeper structural problems I spotted:
- **OTS buried inside Presets**: Bitcoin anchoring had no own section, breaking the information hierarchy.
- **"Aplicar cambios" as explicit button**: added friction with no value — in electoral pressure moments, that's an error waiting to happen.
- **Unlock required PAT**: opened a GitHub Personal Access Token modal just to record an acceptance. Unnecessary and blocking for non-technical operators.

### 2) The Hypothesis

All problems were solvable without changing the architecture. The panel is a single HTML file — each fix is surgical and isolated. The 5 post-SpaceX corrections are JS logic bugs or HTML hardcodes. The UX audit items are state and visual feedback improvements. The structural problems (OTS, auto-apply, PAT) require JS refactoring but no new files or dependencies.

My central hypothesis on auto-apply: if the system can detect changes (it already does with `isDirty`) and can commit to GitHub (it already does in `writeChanges()`), then a 1.5s debounce in `markDirty()` that calls `writeChanges()` directly eliminates the button without losing functionality.

### 3) The Experiment / Implementation

**5 post-SpaceX fixes:**

- `_updateMissionBar()`: I replaced `querySelectorAll('.badge-bad')` with iteration over the 4 specific status badge IDs (`badge-animal`, `badge-safemode`, `badge-circuit`, `badge-election`).
- `loadCountrySelector()`: I added `ACTIVE_COUNTRY_CODE = currentCode; _updateMissionBar();` at the end of the `try` block.
- `doChangeCountry()`: I added `_updateMissionBar();` at the end.
- HTML mission bar: I changed `DEFENSES` to `DEFENSAS`.
- Section titles: I removed numeric prefixes ("3 Presets" -> "Presets", etc.).
- Sidebar: I added `#sidebar-ops-zone` with INICIAR and FINALIZAR buttons above the emergency zone, with color-coded CSS (green for start, amber for finalize).
- `_setPipelineUI()`: I synced `btn-sidebar-iniciar` alongside `btn-iniciar` on each running/stopped transition.

**Active uptime counter — TIEMPO ACTIVO:**

I added `_startUptimeClock()` that starts when the pipeline launches, saves the timestamp to `localStorage`, and formats elapsed time as `Xd Xh Xm Xs`. `_stopUptimeClock()` preserves the last duration as "Ultimo: Xh Xm" to show on next launch. The item appears in the mission bar between DEFENSAS and UTC.

**Section tooltips:**

I gave each section title a `<span class="sec-tip" data-tip="...">i</span>` with plain-language description. No technical jargon — I wrote the descriptions for an electoral operator, not a developer.

**Electoral URL field simplification:**

The field no longer asks for the exact API path (`/api/presidencial/nacional`). It now asks for only the root domain (`https://resultados.organismo-electoral.gov`). Centinel discovers endpoints automatically. I changed the label to "Sitio de resultados" with explicit description: "you don't need to know anything more."

**OTS button evolution (three iterations based on visual feedback):**

1. Toggle checkbox -> button in panel + row in sidebar
2. Feedback: button in the middle broke aesthetics, sidebar unnecessary
3. Final result: `Activo / Inactivo` button in the ctrl-section header, sidebar row eliminated. "Idle" state (OTS configured but pipeline stopped) with contextual message.

**12-point UX audit — 3 batches:**

*Batch 1 (tier 1 — critical):* I changed the sidebar scroll observer from IntersectionObserver to position-based — more reliable for active section highlighting. Status labels: `badge-animal` now shows "NORMAL / CAUTION / SURVIVAL" instead of internal code; `badge-circuit` shows "ACTIVO / ABIERTO". Empty states show contextual hint instead of empty cell. I added a Cierre Electoral card with visual state indicator (pending/in-progress/complete) using system colors.

*Batch 2 (tier 2 — medium):* Swarm hint now appears only when nodes are connected. OTS idle: when pipeline is stopped, OTS badge shows "IDLE" in muted instead of holding last state. Uptime "last known": on pipeline stop, mission bar shows "Ultimo: Xh Xm" instead of resetting to "—".

*Batch 3 (tier 3 — low):* Unsaved changes warning: `beforeunload` already existed; I added a visual indicator on the section title with `dirty-dot`. Local clock in mission bar alongside UTC. Active preset label: badge in panel topbar indicating which preset is loaded.

**PAT-free unlock:**

I refactored `executeUnlock()`: the flow no longer opens the PAT modal. Acceptance is recorded in `localStorage` with timestamp and full legal document text. If a PAT is available in `sessionStorage` (from a previous apply session), I make a commit as a bonus — but it doesn't block the flow. The acceptance is always recorded; the Git commit is optional.

**OTS extraction as standalone section — s9:**

I extracted the OTS block from `#s3` (Presets) and converted it to `<div class="section" id="s9">` with: title "Anclaje Bitcoin", tooltip, section separator, and full ctrl-section content. CSS order: `#s9{order:4}` — between Presets and Logs. Sidebar: new entry "Anclaje Bitcoin" under "Integridad" sec-header. I updated `_updateSidebarActive()` with `'s9'` in the IDs array.

**Auto-save — elimination of "Aplicar cambios":**

I made `markDirty()` start a 1.5s debounce timer. If no more changes arrive in that time, it calls `autoApply()` — which builds the YAMLs, calculates the diff, requests PAT if not in sessionStorage, and commits directly to GitHub. I removed the "Aplicar cambios" button from the header. `applyChanges()` is now an alias of `autoApply()` for internal callers (emergency, reload-reapply).

**Advanced scraping controls — unlock gate:**

When `ceilingUnlocked === true`, a `#unlocked-scraping-panel` appears in Presets with amber border and warning label. Contains 6 visible controls with extended ranges:

| Control | Normal | Unlocked |
|---------|--------|----------|
| Interval | 1-60 min | 0.5-60 min |
| Requests/hour | 60-480 | 60-1200 |
| Burst | 1-10 | 1-30 |
| Jitter | — | 0-60 sec (new) |
| Concurrency | — | 1-10 endpoints (new) |
| Timeout | advanced tab only | visible here |

I added the new sliders to `SLIDER_IDS`/`BADGE_IDS` for bidirectional sync. `jitter_seconds` writes to `rate_limiter.yaml`; `max_concurrent_requests` writes to `config.yaml`.

**Security — CodeQL alerts #37 and #38:**

I found two workflows with `softprops/action-gh-release@v1` — mutable tag, CWE-829. I pinned both to the commit SHA of v2.6.2: `3bb12739c298aeb8a4eeaf626c5b8d85266b0e65`.

### 4) The Result (The Lesson)

All changes worked. The panel went from "visually renovated but buggy" to "operationally correct." The mission bar shows real system state. The country updates. OTS has its own section with the same visual hierarchy as the rest.

The most important finding of the cycle wasn't technical — it was about flow design: **the "Aplicar cambios" button was a friction trap**. In an electoral monitoring interface under pressure, adding a manual step between "I made the change" and "the change is in production" is introducing an error waiting to happen. The 1.5s debounce I implemented eliminates that trap without reducing control.

### 5) The Final Decision (Takeaway)

Operational friction in monitoring systems is not "additional safety" — it's error surface. An extra manual step doesn't make the system safer; it makes it more likely the operator will make an omission error. Auto-apply with debounce is the correct pattern: it captures user intent (the change) without requiring confirmation of intent (the click).

The unlock gate for advanced controls implements the opposite principle with the same logic: aggressive scraping controls shouldn't be available by default — not because the operator can't use them, but because their visual availability implies they're normal options. By hiding them behind explicit unlock, the panel communicates that using them is a deliberate decision with consequences, not routine configuration.

### 6) What Changed and Why Now

The cycle was triggered by a real screenshot of the panel in use. Without that concrete visual feedback, the bugs would have remained indefinitely — all were invisible in code, only visible in real interaction.

The OTS extraction came from a question I asked myself: "am I wrong or don't we have this as its own section?" — legitimate question. Bitcoin anchoring is the most important integrity feature of the system (it enables independent verification of data), and it was buried inside Presets as if it were a minor configuration adjustment. The information hierarchy didn't reflect the importance hierarchy.

### 7) Implementation Decisions

- **1.5s debounce (not 500ms or 5s):** 500ms is too aggressive — fires on intermediate slider values. 5s makes the operator wait too long for confirmation. 1.5s captures the end of an interaction without overloading the GitHub API.
- **PAT in sessionStorage (not localStorage):** Disappears on browser close — I made this intentional. A permanently stored PAT is a security risk. The friction of entering it once per session is the correct trade-off.
- **Unlock state in localStorage (not just memory):** Persists between reloads of the same work session. If the operator unlocks, reloads the page, and returns, the system remembers the unlock. I chose this to prevent an accidental reload from forcing a re-unlock at the worst moment.
- **Jitter as new control (not existing):** Jitter didn't exist in the config. I added it as a new field in `rate_limiter.yaml`. It's the most useful capability in aggressive monitoring environments — makes request timing unpredictable, reducing scraper detectability.
- **Concurrency in config.yaml (not rate_limiter):** Semantic decision: `max_concurrent_requests` is a scheduler behavior parameter, not a rate limiter parameter. The rate limiter controls speed; the scheduler controls parallelism.
- **OTS as s9 (not s2 or next to Presets):** I evaluated placing it before Presets. I rejected that because the logical operator flow is: Panel -> Network -> Presets (configuration) -> Anchoring (integrity of what was configured) -> Logs (what happened). Anchoring goes after configuration, not before.
- **Position-based scroll observer (not IntersectionObserver):** IntersectionObserver has complex behavior when multiple sections are visible simultaneously (large screens). The position-based observer — "which section has its top closest to 90px without exceeding it?" — is deterministic and predictable.

### 8) Impact

**Operational:** The mission bar now shows reliable information. An operator who sees "SISTEMA: NOMINAL" can trust the system is nominal — before, the `querySelectorAll` bug could show ALERTA permanently even if everything was fine.

**Structural:** OTS has its own section with the correct visual hierarchy. An external auditor opening the panel can find Bitcoin anchoring directly in the sidebar without knowing where to look.

**Workflow:** Auto-apply eliminates an entire class of operational errors. The operator can no longer be in the state "I think I applied the change but I'm not sure."

**Security:** I closed CodeQL alerts #37 and #38. Both workflows using `softprops/action-gh-release` now point to an immutable commit SHA, eliminating the supply chain attack vector via tag hijacking.

**Contextual intelligence:** The unlock gate for advanced controls implements the principle of least privilege in the interface: the ability to cause damage (aggressive scraping) is only available when the operator has explicitly accepted responsibility for using it.

### 9) Cycle Takeaway

An operator interface is not an end-user application. End-user applications optimize for ease of discovery. Operator interfaces optimize for **clarity of state under pressure**. These are different objectives.

On an election night, the operator has 30 seconds to decide whether to switch from `election` to `aggressive` preset. In that moment they cannot: search through menus, confirm unnecessary modals, or doubt whether a change was applied. The panel must communicate system state without ambiguity, execute changes without friction, and reserve friction for decisions that genuinely deserve it (limit unlock, emergency stop, electoral closing).

That principle — **friction proportional to consequence** — is what guided every decision I made in this cycle.

---

## PRs de este ciclo / PRs in this cycle

| PR | Descripcion | Estado |
|----|-------------|--------|
| #699 | 5 correcciones post-SpaceX + unlock alert bar | mergeado |
| #700 | Contador TIEMPO ACTIVO en mission bar | mergeado |
| #701 | OTS: espanol, boton, sidebar | mergeado |
| #702 | Tooltips de seccion | mergeado |
| #703 | URL electoral simplificada | mergeado |
| #704 | OTS: boton en header, sidebar eliminado | mergeado |
| #705 | UX batch 1: sidebar activo, estados vacios, labels | mergeado |
| #706 | UX batch 2: swarm hint, OTS idle, uptime | mergeado |
| #707 | UX batch 3: dirty warning, reloj local, preset label | mergeado |
| #708 | Desbloqueo sin PAT | mergeado |
| #709 | OTS como s9 + auto-guardado | mergeado |
| #710 | Controles avanzados tras unlock | mergeado |
| #711 | Fix CodeQL #37 y #38 (pinned actions) | mergeado |

---

## Metricas de impacto / Impact Metrics

| Metrica | Antes | Despues |
|---------|-------|---------|
| Clics para iniciar monitoreo desde sidebar | no existia — habia que scrollear al panel | 1 clic (▶ INICIAR visible siempre) |
| Cambios perdidos por olvido de "Aplicar" | posible en cualquier sesion | imposible — se aplican solos en 1.5s |
| Estado del sistema confiable (badge bug) | ALERTA falso permanente posible | corregido — solo 4 badges de estado reales |
| Controles avanzados de scraping accesibles | 0 (ocultos sin ruta clara) | 6 controles visibles tras unlock explicito |
| Tiempo de configuracion hasta primer commit | manual (boton + confirmacion) | 1.5s despues del ultimo cambio |
| Anclaje Bitcoin ubicable sin conocimiento previo | enterrado en Presets | seccion propia s9 en sidebar |
| País en mission bar correcto al cargar | desincronizado (bug de init) | correcto desde el primer frame |
| Desbloqueo de limites sin friccion tecnica | requeria PAT de GitHub | 1 clic + confirmacion legal |

---

_Hito alcanzado / Milestone reached: 04-jun-2026_  
_Archivo modificado / File modified: `web/ops/index.html` (unico archivo de todo el ciclo)_  
_PRs mergeados / Merged PRs: 13 (#699-#711)_  
_Principio guia / Guiding principle: Friccion proporcional a la consecuencia / Friction proportional to consequence_
