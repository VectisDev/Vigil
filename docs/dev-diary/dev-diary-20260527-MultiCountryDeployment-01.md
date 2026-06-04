# Dev Diary - 202605 - MultiCountryDeployment - 01

**Fecha aproximada / Approximate date:** 27-may-2026 / May 27, 2026  
**Fase / Phase:** Separar la identidad del nodo del contexto de monitoreo para hacer CENTINEL reutilizable por eleccion / Separating node identity from monitoring context to make CENTINEL reusable across elections  
**Version interna / Internal version:** v0.2.x (ciclo dev-v12)  
**Rama / Branch:** dev-v12  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuacion de `dev-diary-202605-ForkUxSetupWizard-01.md`. El wizard de setup generaba seeds PBKDF2, configuraba el pais y generaba `departments.json`. Pero "cambiar de pais" requeria regenerar seeds -- lo que rompia la cadena de custodia y obligaba a redistribuir credenciales. Guatemala 2027, Venezuela, Bolivia, Mexico estan en el horizonte. La reutilizacion requeria separar dos cosas que estaban mezcladas. / Continuation of `dev-diary-202605-ForkUxSetupWizard-01.md`. The setup wizard generated PBKDF2 seeds, configured the country, and generated `departments.json`. But "changing the country" required regenerating seeds -- breaking the chain of custody and forcing redistribution of credentials. Guatemala 2027, Venezuela, Bolivia, and Mexico are on the horizon. Reuse required separating two things that were mixed together.

---

## [ES]

### 1) El Problema (Contexto)
Construi CENTINEL para Honduras. Los 12 seeds de acceso generados durante el setup inicial con PBKDF2-SHA256 son la credencial del nodo: los operadores en campo los tienen memorizados o guardados, y son la unica forma de acceder al panel de administracion. Cuando llegara la siguiente eleccion -- Guatemala 2027, Venezuela, Bolivia, Mexico -- un operador que quisiera redirigir el mismo nodo CENTINEL a un nuevo contexto se encontraba con un problema estructural: el unico camino existente era `POST /api/setup/regenerate`, que genera 12 seeds nuevos, invalida los anteriores, y entrega un PDF nuevo. Eso requiere redistribuir credenciales a todos los operadores en campo, lo que en un contexto de presion politica puede ser operacionalmente imposible. La identidad del nodo (quien puede acceder) y el contexto del monitoreo (que pais, que endpoints, que autoridad electoral) estaban mezclados en la misma operacion.

### 2) La Hipotesis
Si anado un endpoint dedicado `POST /api/setup/change_country` que actualiza el contexto de monitoreo -- `country_code`, `country_name`, `cne_domains` en `config.yaml` -- sin tocar los seeds ni regenerar credenciales, un operador puede redirigir el nodo a cualquier eleccion LATAM en segundos. Los seeds anteriores siguen siendo validos. La configuracion de pais se actualiza. El panel /ops refleja el nuevo contexto inmediatamente. No hay PDF nuevo, no hay redistribucion de credenciales, no hay interrupcion del acceso.

### 3) El Experimento / Implementacion
Anade `POST /api/setup/change_country` a `src/centinel/api/routes/setup.py`. El endpoint lee `.centinel-setup.json` existente, actualiza `country_code`, `country_name` y anade `last_changed_country_at`, y escribe de vuelta preservando `configured_at` y todos los hashes de seeds. Llama a `_update_config_yaml()` que ya existia en `setup_init()` -- reutilizacion directa sin duplicacion -- para actualizar `cne_domains`, `country_code` y `country_name` en `command_center/config.yaml`. No hay generacion de seeds, no hay PDF, no hay invalidacion de credenciales.

En el frontend, `/ops S3` recibio una nueva seccion "Pais monitoreado" como el primer control de configuracion, antes de la fuente de datos CNE. Muestra el pais activo con su bandera, nombre y autoridad electoral. El dropdown se puebla desde `GET /api/setup/countries` con los 23 paises LATAM disponibles, con el pais activo preseleccionado. Al aplicar, el panel muestra el nuevo pais con un mensaje de confirmacion y activa un aviso si el swarm esta conectado con el pais anterior -- indicando al operador que tiene que desconectar y reconectar el swarm para que use los endpoints del nuevo CNE.

El grid de departamentos en `/ops S2` ya usaba `departments.json` generado por el wizard con los presets del pais elegido. El selector de pais en /ops actualiza solo la configuracion -- el wizard debe correrse de nuevo si se requiere regenerar `departments.json` para el nuevo pais con URLs de endpoints especificas. El grid se recarga en runtime desde el archivo existente.

### 4) El Resultado (La Leccion)
Funciono. El operador que configuro el nodo para Honduras puede abrir `/ops S3`, seleccionar Guatemala del dropdown, hacer clic en "Aplicar", y en menos de 3 segundos el panel confirma "Pais cambiado a Guatemala - Tribunal Supremo Electoral". Los 12 seeds anteriores siguen siendo validos. `.centinel-setup.json` ahora tiene `country_code: GT` con un timestamp de `last_changed_country_at`. `config.yaml` tiene los dominios del TSE de Guatemala en `cne_domains`. El grid de departamentos muestra la bandera y autoridad del nuevo pais.

### 5) La Decision Final (Takeaway)
La identidad del nodo y el contexto del monitoreo son dos capas que no deberian estar acopladas. La identidad del nodo es quien puede acceder -- los seeds, generados una vez, validos por el ciclo completo. El contexto del monitoreo es que eleccion observar -- el pais, los endpoints, la autoridad electoral, que cambian con cada ciclo. Mezclar las dos en la misma operacion significaba que cada nueva eleccion era un nuevo despliegue desde cero. Separarlas convierte CENTINEL en infraestructura reutilizable entre ciclos electorales.

### 6) Que cambio y por que ahora
El cambio fue necesario en este momento porque la siguiente eleccion en el roadmap de CENTINEL ya no es Honduras. Los presets de 23 paises LATAM ya estaban en `LATAM_COUNTRIES`; el wizard ya generaba `departments.json` para cualquier pais; la unica pieza faltante era el endpoint de cambio sin regeneracion de seeds. Construirlo ahora, antes del proximo ciclo electoral, es la unica forma de garantizar que la reutilizacion sea posible sin improvisacion en campo bajo presion.

### 7) Decisiones de implementacion
- **Preservar `configured_at` en el JSON de setup:** la auditoria necesita saber cuando fue la configuracion inicial del nodo, no solo cuando fue el ultimo cambio de pais. `configured_at` es el timestamp de identidad del nodo; `last_changed_country_at` es el timestamp de contexto. Son datos distintos con propositos distintos.
- **Reutilizar `_update_config_yaml()` sin duplicacion:** la funcion ya existia en `setup_init()` y actualizaba exactamente los tres campos necesarios (`cne_domains`, `country_code`, `country_name`). No duplicar logica es una decision de mantenibilidad, no solo de elegancia.
- **Aviso swarm explicito en /ops:** si el swarm esta corriendo con el pais anterior, los peers del enjambre esperan endpoints del CNE anterior. El operador tiene que reconectar explicitamente. El aviso es el recordatorio -- sin el, el swarm seguiria operando con la configuracion anterior silenciosamente.
- **Dropdown desde `/api/setup/countries`:** los 23 paises LATAM con sus banderas, nombres de autoridad electoral y etiquetas de divisiones administrativas. El dropdown es legible por cualquier operador sin conocimiento tecnico del sistema.
- **Grid S2 auto-escalable:** `grid-column: 1 / -1` para el NACIONAL card y `repeat(auto-fill, minmax(60px, 1fr))` para el grid de divisiones. Se adapta a 7 divisiones (Costa Rica), 18 (Honduras), 22 (Guatemala), 32 (Mexico) sin cambiar una linea de JS ni CSS.
- **Separacion wizard/selector en /ops:** el wizard genera la configuracion completa inicial incluyendo `departments.json` con URLs de endpoints. El selector de pais en /ops actualiza solo el contexto basico (pais, CNE domain). Si el operador necesita los endpoints del nuevo pais configurados, corre el wizard; si solo necesita cambiar el contexto de monitoreo para el nuevo CNE, usa el selector.

### 8) Impacto
Un nodo CENTINEL configurado para Honduras puede estar monitoreando Guatemala en menos de 3 segundos sin interrumpir el acceso de ningun operador. Para una organizacion que planea cubrir multiples elecciones LATAM en el mismo ciclo presupuestario -- NDI, Carter Center, observadores nacionales -- eso significa que el mismo nodo confiable puede ser redirigido sin friccion operacional. Los seeds son el activo de confianza acumulado; el pais es solo el contexto actual. Esa separacion reduce el costo operacional de desplegar CENTINEL en un nuevo contexto electoral de "nuevo despliegue" a "3 segundos y un clic".

### 9) Aprendizaje de ciclo
Los sistemas que mezclan identidad y contexto en la misma operacion obligan al usuario a reconstruir la confianza cada vez que cambia el contexto. En el caso de CENTINEL, "reconstruir la confianza" significaba redistribuir 12 seeds a operadores en campo en condiciones potencialmente adversas. Separar las dos capas no es solo una decision de arquitectura -- es una decision sobre quien tiene que hacer que trabajo bajo que presion. El operador en campo bajo un conteo disputado no puede redistribuir credenciales: tiene que poder cambiar el contexto de monitoreo con el mismo acceso que ya tiene.

---

## [EN]

### 1) The Problem (Context)
I built CENTINEL for Honduras. The 12 access seeds generated during initial setup with PBKDF2-SHA256 are the node's credential: field operators have them memorized or saved, and they are the only way to access the administration panel. When the next election arrived -- Guatemala 2027, Venezuela, Bolivia, Mexico -- an operator wanting to redirect the same CENTINEL node to a new context faced a structural problem: the only existing path was `POST /api/setup/regenerate`, which generates 12 new seeds, invalidates the previous ones, and delivers a new PDF. That requires redistributing credentials to all field operators, which in a context of political pressure can be operationally impossible. Node identity (who can access) and monitoring context (which country, which endpoints, which electoral authority) were mixed into the same operation.

### 2) The Hypothesis
If I add a dedicated endpoint `POST /api/setup/change_country` that updates the monitoring context -- `country_code`, `country_name`, `cne_domains` in `config.yaml` -- without touching seeds or regenerating credentials, an operator can redirect the node to any LATAM election in seconds. Previous seeds remain valid. Country configuration updates. The `/ops` panel reflects the new context immediately. No new PDF, no credential redistribution, no access interruption.

### 3) The Experiment / Implementation
I added `POST /api/setup/change_country` to `src/centinel/api/routes/setup.py`. The endpoint reads the existing `.centinel-setup.json`, updates `country_code`, `country_name` and adds `last_changed_country_at`, and writes back preserving `configured_at` and all seed hashes. It calls `_update_config_yaml()` that already existed in `setup_init()` -- direct reuse without duplication -- to update `cne_domains`, `country_code`, and `country_name` in `command_center/config.yaml`. No seed generation, no PDF, no credential invalidation.

On the frontend, `/ops S3` received a new "Pais monitoreado" (Monitored Country) section as the first configuration control, before the CNE data source. It shows the active country with its flag, name, and electoral authority. The dropdown is populated from `GET /api/setup/countries` with the 23 available LATAM countries, with the active country preselected. Upon applying, the panel shows the new country with a confirmation message and activates a warning if the swarm is connected with the previous country -- indicating to the operator that they need to disconnect and reconnect the swarm to use the new CNE's endpoints.

The department grid in `/ops S2` already used `departments.json` generated by the wizard with the chosen country's presets. The country selector in `/ops` only updates the configuration -- the wizard must be run again if `departments.json` needs to be regenerated for the new country with specific endpoint URLs. The grid reloads at runtime from the existing file.

### 4) The Result (The Lesson)
It worked. The operator who configured the node for Honduras can open `/ops S3`, select Guatemala from the dropdown, click "Apply," and in under 3 seconds the panel confirms "Country changed to Guatemala - Tribunal Supremo Electoral." The 12 previous seeds remain valid. `.centinel-setup.json` now has `country_code: GT` with a `last_changed_country_at` timestamp. `config.yaml` has Guatemala's TSE domains in `cne_domains`. The department grid shows the new country's flag and authority.

### 5) The Final Decision (Takeaway)
Node identity and monitoring context are two layers that should not be coupled. Node identity is who can access -- the seeds, generated once, valid for the full cycle. Monitoring context is which election to observe -- the country, endpoints, electoral authority, which change with each cycle. Mixing the two in the same operation meant every new election was a fresh deployment from scratch. Separating them turns CENTINEL into infrastructure reusable across electoral cycles.

### 6) What Changed and Why Now
The change was necessary at this point because the next election on CENTINEL's roadmap is not Honduras. The 23 LATAM country presets were already in `LATAM_COUNTRIES`; the wizard already generated `departments.json` for any country; the only missing piece was the country-change endpoint without seed regeneration. Building it now, before the next electoral cycle, is the only way to guarantee that reuse is possible without improvisation in the field under pressure.

### 7) Implementation Choices
- **Preserve `configured_at` in the setup JSON:** the audit needs to know when the node was initially configured, not just when the country was last changed. `configured_at` is the node identity timestamp; `last_changed_country_at` is the context timestamp. They are different data with different purposes.
- **Reuse `_update_config_yaml()` without duplication:** the function already existed in `setup_init()` and updated exactly the three needed fields (`cne_domains`, `country_code`, `country_name`). Not duplicating logic is a maintainability decision, not just elegance.
- **Explicit swarm warning in /ops:** if the swarm is running with the previous country, the swarm's peers expect the previous CNE's endpoints. The operator needs to reconnect explicitly. The warning is the reminder -- without it, the swarm would keep operating with the previous configuration silently.
- **Dropdown from `/api/setup/countries`:** 23 LATAM countries with their flags, electoral authority names, and administrative division labels. The dropdown is readable by any operator without technical knowledge of the system.
- **Auto-scaling S2 grid:** `grid-column: 1 / -1` for the NACIONAL card and `repeat(auto-fill, minmax(60px, 1fr))` for the division grid. It adapts to 7 divisions (Costa Rica), 18 (Honduras), 22 (Guatemala), 32 (Mexico) without changing a line of JS or CSS.
- **Separation of wizard / /ops selector:** the wizard generates the complete initial configuration including `departments.json` with endpoint URLs. The country selector in `/ops` only updates the basic context (country, CNE domain). If the operator needs the new country's endpoints configured, they run the wizard; if they only need to update the monitoring context for the new CNE, they use the selector.

### 8) Impact
A CENTINEL node configured for Honduras can be monitoring Guatemala in under 3 seconds without interrupting any operator's access. For an organization planning to cover multiple LATAM elections in the same budget cycle -- NDI, Carter Center, national observers -- that means the same trusted node can be redirected without operational friction. Seeds are the accumulated trust asset; the country is just the current context. That separation reduces the operational cost of deploying CENTINEL in a new electoral context from "new deployment" to "3 seconds and one click."

### 9) Cycle Takeaway
Systems that mix identity and context in the same operation force the user to rebuild trust every time the context changes. In CENTINEL's case, "rebuilding trust" meant redistributing 12 seeds to field operators under potentially adverse conditions. Separating the two layers is not just an architecture decision -- it is a decision about who has to do what work under what pressure. The field operator under a disputed count cannot redistribute credentials: they need to be able to change the monitoring context with the same access they already have.

---

## Cierre / Close
Los seeds son la identidad del nodo; el pais es el contexto actual -- mezclarlos en la misma operacion significa que cada nueva eleccion obliga a reconstruir la confianza desde cero, y eso no es operacionalmente posible en campo bajo presion. / Seeds are the node's identity; the country is the current context -- mixing them in the same operation means every new election forces rebuilding trust from scratch, and that is not operationally possible in the field under pressure.
