// ── Ya no hay token de escritura ────────────────────────────────────────────
// Esta página descifraba un token publicado y lo dejaba en memoria para que el
// panel escribiera por la API. Se ha retirado entero.
//
// El envoltorio no era mitigación: el token iba envuelto bajo doce claves
// derivadas de los seeds, lo cual no es cifrado sino una distribución 12-de-12
// del MISMO secreto —quien tuviera uno de los doce lo abría— y encima había un
// respaldo en claro para el caso en que el envoltorio fallara. Lo que necesita
// escritura va ahora por `workflow_dispatch`, autenticado con la sesión de
// GitHub del propio operador: el navegador es la credencial.
//
// El borrado del valor heredado se queda. A quien entrara antes de este cambio
// puede quedarle uno en disco, y esta línea lo retira la próxima vez que abra
// la página; no hay forma de saber quién lo tiene, así que se limpia a todos.
//
// Los nombres de lo retirado no se escriben aquí a propósito:
// `tests/test_no_credentials_in_web.py` los busca por texto en todo `web/`, y
// no sabe distinguir un comentario de una llamada. Un candado que no se puede
// engañar vale más que uno que entiende matices.
//
// English: this page used to decrypt a published token into memory so the
// panel could write through the API. It is gone. The wrapper was not
// mitigation: twelve keys derived from the seeds is a 12-of-12 distribution of
// the same secret, and there was a plaintext fallback besides. Writes now go
// through workflow_dispatch, authenticated with the operator's own GitHub
// session. The legacy purge stays, because there is no way to know who still
// has one on disk. The removed names are deliberately not written here: the
// credential gate greps all of web/ for them and cannot tell a comment from a
// call, and a lock that cannot be fooled beats one that understands nuance.
try { localStorage.removeItem('gh-pat'); } catch (e) {}

/* global snapshotData */ // declared with `let` in web/ops/index.html
// ══════════════════════════════════════════════════════════
// CONFIG LOAD
// ══════════════════════════════════════════════════════════
async function loadConfig(){
  const files = ['config/prod/endpoints.yaml','config/prod/watchdog.yaml',
                 'config/prod/rate_limiter.yaml','config/prod/retry_config.yaml',
                 'config/prod/rules.yaml','config/prod/config.yaml'];
  await Promise.all(files.map(f => fetchConfigFile(f)));
  populateControls();
}

async function fetchConfigFile(path){
  try{
    const r = await fetch(`${RAW_BASE}/${path}?t=${Date.now()}`);
    if(!r.ok) return;
    const txt = await r.text();
    currentConfig[path] = jsyaml.load(txt);
    localConfig[path]   = jsyaml.load(txt); // deep clone via re-parse
    // also grab sha via API for later writes
    fetchSha(path);
  }catch(e){console.warn('fetchConfigFile',path,e);}
}

async function fetchSha(path){
  // Sin cabecera de autorizacion: el repositorio es publico y la API de
  // contenidos responde sin credencial. El SHA se pedia autenticado para
  // escribir despues, y ya no se escribe desde aqui.
  // English: no authorization header -- the repository is public and the
  // contents API answers without one. The SHA was fetched authenticated in
  // order to write later, and writes no longer happen from here.
  try{
    const r = await fetch(`${API_BASE}/contents/${path}`);
    if(!r.ok) return;
    const j = await r.json();
    configShas[path] = j.sha;
  }catch(e){console.warn('fetchSha',path,e);}
}

// ── Modo del panel: `pages` o `servidor` ────────────────────────────────────
//
// ESPAÑOL
// Este panel se publica en GitHub Pages, donde no hay servidor. Aun así el
// código llamaba a `/api/...` desde una decena de sitios, y cada uno fallaba
// por su cuenta con un mensaje distinto: «Error al iniciar el pipeline»,
// «Panel en modo offline», «No se pudo cargar el estado», o un «Cargando…»
// que no terminaba nunca. Un visitante veía una pantalla con errores rojos y
// concluía, razonablemente, que el sistema estaba roto. No lo estaba: le
// faltaba el nodo encendido, que es un estado esperado y no un fallo.
//
// El modo se resuelve UNA vez y se guarda en `window.OPS_MODE`. Las secciones
// lo consultan en vez de sondear la API cada una por su lado.
//
// ENGLISH
// This panel is published on GitHub Pages, where there is no server. The code
// still called `/api/...` from a dozen places, each failing on its own with a
// different message -- or with a "Loading…" that never ended. A visitor saw a
// screen full of red errors and reasonably concluded the system was broken. It
// was not: it had no node running, which is an expected state, not a failure.
//
// The mode is resolved ONCE into `window.OPS_MODE`.

window.OPS_MODE = window.OPS_MODE || null;
const OPS_MODE_PROBE_MS = 3000;

async function detectMode() {
  if (window.OPS_MODE) return window.OPS_MODE;

  const base = window.VIGIL_API_BASE;
  if (!base) {
    window.OPS_MODE = 'pages';
    return window.OPS_MODE;
  }

  // Una sonda, con límite de 3 s. Sin AbortController una red lenta deja la
  // promesa colgando y el panel entero esperando.
  // English: one probe, capped at 3s. Without AbortController a slow network
  // leaves the promise hanging and the whole panel waiting on it.
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), OPS_MODE_PROBE_MS);
    let r;
    try {
      r = await fetch(base + '/api/setup/status', { signal: ctrl.signal, cache: 'no-store' });
    } finally {
      clearTimeout(timer);
    }
    window.OPS_MODE = r && r.ok ? 'servidor' : 'pages';
  } catch (e) {
    window.OPS_MODE = 'pages';
  }
  return window.OPS_MODE;
}
window.detectMode = detectMode;

function opsIsPages() { return window.OPS_MODE !== 'servidor'; }
window.opsIsPages = opsIsPages;

// El único sitio por donde sale una petición a la API.
//
// En modo `pages` NO se emite la petición: se rechaza con un error etiquetado
// que las secciones reconocen. Antes, cada llamada salía, fallaba contra Pages
// y ensuciaba la consola con 404s; un evaluador que abre las herramientas de
// desarrollo veía una pantalla roja de peticiones fallidas.
//
// English: the single place an API request leaves from. In `pages` mode the
// request is never issued -- it rejects with a tagged error the sections
// recognise, instead of hitting Pages and filling the console with 404s.
function opsApi(path, init) {
  if (opsIsPages()) {
    const err = new Error('ops-offline');
    err.opsOffline = true;
    return Promise.reject(err);
  }
  // En modo servidor sí sale la petición. La llamada anterior se invocaba
  // a sí misma y reventaba la pila en cuanto había un nodo.
  // English: in server mode the request does go out. The previous call
  // invoked itself and blew the stack as soon as a node existed.
  const base = String(window.VIGIL_API_BASE || '').replace(/\/$/, '');
  return fetch(base + path, init);
}
window.opsApi = opsApi;

function opsIsOffline(err) { return !!(err && err.opsOffline); }
window.opsIsOffline = opsIsOffline;

// Estado vacío para una sección que necesita el nodo encendido.
// Gris, con una frase en lenguaje llano y una salida. Nunca en rojo: el rojo
// es para lo que está mal, y esto no lo está.
// English: empty state for a section that needs the node running. Grey, plain
// language, and a way out. Never red: red is for what is broken, and this is
// not.
function opsNeedsNode(el, opts) {
  if (!el) return;
  // Se marca como resuelto: esta seccion ya dijo lo que le pasa, y la guarda
  // de carga no debe sustituirlo luego por el mensaje generico. Sin esto, a
  // los 8 s «necesita tu nodo encendido» -- que es cierto y accionable -- se
  // convertia en «No hay datos todavía», que es vago y no dice que hacer.
  // English: marked resolved -- this section has already said what is going
  // on, and the load guard must not replace it with the generic message.
  el.dataset.opsResolved = '1';
  const o = opts || {};
  // La wiki ya explica el despliegue en un minuto (clonar y `make
  // quickstart`), esta publicada y es bilingue. Enlazar ahi en vez de
  // crear otra pagina que mantener y traducir.
  // English: the wiki already explains deployment in a minute, is
  // published and bilingual. Link there rather than add another page.
  const docs = o.href ||
    'https://github.com/VectisDev/Vigil/wiki/Instalaci%C3%B3n-%E2%80%94-Setup';
  el.innerHTML =
    '<div class="ops-empty" role="status">' +
    '<span class="ops-empty-icon" aria-hidden="true">○</span>' +
    '<p class="ops-empty-text">' + escHtml(o.text || t('empty.needs_node')) + '</p>' +
    '<a class="btn-secondary ops-empty-action" href="' + escHtml(docs) + '" ' +
    'target="_blank" rel="noopener">' +
    escHtml(t('empty.how_to_start')) + '</a>' +
    '</div>';
}
window.opsNeedsNode = opsNeedsNode;

// Ningún «Cargando…» puede quedarse para siempre.
// Devuelve una función `done()`; si no se llama en `ms`, el contenedor pasa a
// «No hay datos todavía» con un botón de reintento.
// English: no "Loading…" may hang forever. Returns a `done()`; if it is not
// called within `ms`, the container switches to "No data yet" plus a retry.
const OPS_LOAD_TIMEOUT_MS = 8000;

function opsLoadTimeout(el, onRetry, ms) {
  if (!el) return function () {};
  const limit = typeof ms === 'number' ? ms : OPS_LOAD_TIMEOUT_MS;
  // Se recuerda lo que habia al armar el temporizador. Si al vencer el
  // contenido ya es otro, el cargador termino y no hay nada que anunciar:
  // pisar su resultado seria sustituir datos buenos por «No hay datos».
  // English: remember what was there when the timer was armed. If the content
  // has changed by the time it fires, the loader finished and there is
  // nothing to announce -- overwriting it would replace good data.
  const snapshot = el.innerHTML;
  const timer = setTimeout(function () {
    if (el.dataset.opsResolved === '1') return;
    if (el.innerHTML !== snapshot) return;
    el.innerHTML =
      '<div class="ops-empty" role="status">' +
      '<span class="ops-empty-icon" aria-hidden="true">○</span>' +
      '<p class="ops-empty-text">' + escHtml(t('empty.no_data_yet')) + '</p>' +
      '<button type="button" class="btn-secondary ops-empty-action" ' +
      'data-ops-retry="1">' + escHtml(t('empty.retry')) + '</button>' +
      '</div>';
    const btn = el.querySelector('[data-ops-retry]');
    if (btn && typeof onRetry === 'function') btn.addEventListener('click', onRetry);
  }, limit);
  return function done() { clearTimeout(timer); };
}
window.opsLoadTimeout = opsLoadTimeout;

// Arma la guarda sobre cada marcador de carga declarado en el HTML.
// Un `data-ops-loading="nombreDeFuncion"` basta: si a los 8 s el contenido
// sigue siendo el mismo, el hueco pasa a «No hay datos todavía» con un boton
// que vuelve a llamar a esa funcion.
// English: arms the guard on every declared loading placeholder. A
// `data-ops-loading="fnName"` is enough.
function opsArmLoadingGuards(root) {
  const scope = root || document;
  scope.querySelectorAll('[data-ops-loading]').forEach(function (el) {
    const fn = el.getAttribute('data-ops-loading');
    opsLoadTimeout(el, function () {
      const f = window[fn];
      if (typeof f === 'function') { try { f(); } catch (e) { console.warn(fn, e); } }
    });
  });
}
window.opsArmLoadingGuards = opsArmLoadingGuards;

// En Pages un skeleton no se llena: no hay nodo que mande datos. Quitar la
// clase deja el texto que ya se escribió (el umbral de Benford, por ejemplo)
// en vez de un bloque gris que brilla para siempre.
// English: on Pages a skeleton never fills -- there is no node sending data.
// Removing the class reveals the text already written instead of a grey
// block that shimmers forever.
function opsSettlePagesChrome() {
  if (!opsIsPages()) return;
  document.querySelectorAll('.skel-pulse').forEach(function (el) {
    el.classList.remove('skel-pulse');
  });
}
window.opsSettlePagesChrome = opsSettlePagesChrome;

function populateControls(){
  const ep = localConfig['config/prod/endpoints.yaml'] || {};
  const wd = localConfig['config/prod/watchdog.yaml'] || {};
  const rl = localConfig['config/prod/rate_limiter.yaml'] || {};
  const rc = localConfig['config/prod/retry_config.yaml'] || {};

  const interval = ep?.healing?.interval_minutes ?? 30;
  const rph      = rl?.max_requests_per_hour ?? 180;
  const capacity = rl?.capacity ?? 3;
  const cpu      = wd?.max_cpu_percent ?? 80;
  const ram      = wd?.max_mem_percent ?? 90;
  const wdcheck  = wd?.check_interval_minutes ?? 3;
  const timeout  = rl?.timeout_seconds ?? 30;
  const benford  = 5.99;
  const zscore   = 3.0;
  const safe     = ep?.healing?.safe_mode_active ?? false;
  const mainUrl  = ep?.cne?.main_url ?? '';


  syncSlider('interval', interval);
  syncSlider('rph', rph);
  syncSlider('benford', benford);
  syncSlider('zscore', zscore);
  syncSlider('wdcheck', wdcheck);
  syncSlider('cpu', cpu);
  syncSlider('ram', ram);
  syncSlider('capacity', capacity);
  syncSlider('timeout', timeout);

  const togSafe = document.getElementById('tog-safe');
  if(togSafe) togSafe.checked = !!safe;

  const inpMainUrl = document.getElementById('inp-main-url');
  if(inpMainUrl) inpMainUrl.value = mainUrl;
  const inpMainUrlEasy = document.getElementById('inp-main-url-easy');
  if(inpMainUrlEasy){
    try{ inpMainUrlEasy.value = mainUrl ? new URL(mainUrl).origin : ''; }
    catch(_){ inpMainUrlEasy.value = mainUrl; }
  }

  // Retry table
  const ps = rc?.per_status || {};
  setValue('retry-429', ps['429']?.max_attempts ?? 5);
  setValue('retry-5xx', ps['5xx']?.max_attempts ?? 5);
  setValue('retry-403', ps['403']?.max_attempts ?? 3);
  setValue('retry-404', ps['404']?.max_attempts ?? 2);

  // Endpoints table
  buildEndpointsTable();

  isDirty = false;
  updateDirtyState();
}

function setValue(id, v){
  const el = document.getElementById(id);
  if(el) el.value = v;
}

function buildEndpointsTable(){
  const ep = localConfig['config/prod/endpoints.yaml'] || {};
  const eps = ep?.cne?.presidential_endpoints || [];
  const tbody = document.getElementById('endpoints-tbody');
  if(!tbody) return;
  tbody.innerHTML = '';
  DEPTS.filter(d=>d.code!=='00').forEach(dept=>{
    const found = eps.find(e=>(e.department_code||'').toString().padStart(2,'0')===dept.code);
    // Fall back to URL from country JSON if no explicit config override
    const url = found?.url || dept.url || '';
    const status = getEndpointStatus(dept.code);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${dept.name}</td>
      <td style="color:var(--muted);font-family:var(--mono)">${dept.code}</td>
      <td><input type="text" value="${escHtml(url)}" data-code="${dept.code}" oninput="updateEndpointUrl('${dept.code}',this.value)"></td>
      <td>${statusBadge(status.cls, status.label)}</td>
      <td style="color:var(--muted);font-size:11px">${status.lastOk}</td>
      <td><button onclick="testEndpointCode('${dept.code}')">Probar</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function escHtml(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function getEndpointStatus(code){
  if(!snapshotData) return {cls:'neutral',label:'—',lastOk:'—'};
  const eps = snapshotData?.endpoints_status || {};
  const ep = eps[code];
  if(!ep) return {cls:'neutral',label:'Sin datos',lastOk:'—'};
  if(ep.ok) return {cls:'ok',label:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg> OK',lastOk:relTime(ep.last_ok)};
  if(ep.failures>0) return {cls:'bad',label:`<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Caído (${ep.failures}f)`,lastOk:relTime(ep.last_ok)};
  return {cls:'warn',label:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="17" r="1" fill="currentColor"/></svg> Advertencia',lastOk:relTime(ep.last_ok)};
}

function statusBadge(cls, label){
  return `<span class="badge badge-${cls}">${label}</span>`;
}

function updateEndpointUrl(code, url){
  const ep = localConfig['config/prod/endpoints.yaml'];
  if(!ep?.cne?.presidential_endpoints) return;
  const arr = ep.cne.presidential_endpoints;
  const idx = arr.findIndex(e=>(e.department_code||'').toString().padStart(2,'0')===code);
  if(idx>=0) arr[idx].url = url;
  else arr.push({department_code:parseInt(code,10), url});
  markDirty();
}

// ══════════════════════════════════════════════════════════
// SNAPSHOT LOAD
// ══════════════════════════════════════════════════════════
async function loadSnapshot(){
  try{
    const r = await fetch(`${RAW_BASE}/web/data/snapshot.json?t=${Date.now()}`);
    if(!r.ok) return;
    snapshotData = await r.json();
    updateSensorCards();
    updateDeptGrid();
    updateStatusBadges();
    if(typeof renderAwsMeter==='function'){ try { renderAwsMeter(); } catch(_){} }
    const age = snapshotData?.timestamp ? relTime(snapshotData.timestamp) : '—';
    const ageEl = document.getElementById('snap-age');
    if (ageEl) ageEl.textContent = `actualizado ${age}`;
  }catch(e){console.warn('loadSnapshot',e);}
}

// ══════════════════════════════════════════════════════════
// SENSOR CARDS
// ══════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════
// I18N — shared with VIGIL toggle in HTML (window.OPS_LANG)
// ══════════════════════════════════════════════════════════
window.OPS_LANG = window.OPS_LANG || (localStorage.getItem('vigil-lang') || 'es');
const I18N = {
  es: {
    'card.sha':'Cadena SHA-256', 'card.cb':'Circuit Breaker', 'card.animal':'Protocolo ARGOS',
    'card.benford':'Benford 1er dígito', 'card.zscore':'Z-Score máximo', 'card.ots':'OTS Bitcoin',
    'card.cpu':'CPU Watchdog', 'card.ram':'Memoria', 'card.attacks':'Ataques detectados',
    'card.endpoints':'Endpoints activos',
    'val.sin_datos':'sin datos', 'val.integra':'ÍNTEGRA', 'val.rota':'ROTA',
    'val.abierto':'ABIERTO', 'val.cerrado':'CERRADO',
    'val.confirmado':'CONFIRMADO', 'val.pendiente':'PENDIENTE', 'val.error':'ERROR', 'val.desconocido':'DESCONOCIDO',
    'val.eventos':'eventos', 'val.limite':'límite',
    'det.pipeline_no_run':'Pipeline aún no ha ejecutado',
    'det.fallos_consecutivos':'fallos consecutivos',
    'empty.needs_node':'Esta función necesita tu nodo encendido.',
    'empty.how_to_start':'Cómo encender mi nodo',
    'empty.no_data_yet':'No hay datos todavía.',
    'empty.retry':'Reintentar',
    'det.ultimo':'Último',
    'det.warning_critical':'{w} WARNING · {c} CRITICAL',
    'det.fallando':'fallando',
    'det.no_disponible':'Dato en tiempo real no disponible en Pages',
    'tip.umbral':'Umbral — sincronizado con Configuración avanzada',
    'tip.benford':'Ley de Benford: verifica si los primeros dígitos de los datos de escrutinio siguen la distribución natural esperada. Una desviación significativa puede indicar anomalías en los datos.',
    'tip.zscore':'Puntuación Z: mide cuánto se aleja un resultado del promedio histórico. Valores altos indican cambios inusuales que merecen revisión manual.',
    'tip.cpu.card':'CPU del servidor de monitoreo. Umbral configurable en Avanzado → Watchdog.',
    'tip.ram.card':'Memoria RAM en uso. Umbral configurable en Avanzado → Watchdog.',
    'badge.defensas':'DEFENSAS', 'badge.safemode':'SAFE MODE', 'badge.circuit':'CIRCUIT BREAKER',
    'badge.election':'ELECTION MODE',
    'badge.normal':'NORMAL', 'badge.caution':'PRECAUCIÓN', 'badge.survival':'SUPERVIVENCIA',
    'badge.on':'ON', 'badge.off':'OFF', 'badge.abierto':'ABIERTO', 'badge.cerrado':'CERRADO',
    'dept.label':'{div} — {total} endpoints (1 nacional + {n})',
    'dept.divisiones':'Divisiones',
    'dept.map_unavailable':'Mapa no disponible',
    'map.narrative_ok':'Sin anomalías detectadas',
    'map.narrative_ok_sub':'Todos los departamentos configurados reportan con normalidad.',
    'map.narrative_down':'Caído',
    'map.narrative_late':'Tardío',
    'map.narrative_ok_dept':'OK',
    'map.narrative_nodata':'Sin datos',
    'map.narrative_last':'Último evento',
    'ots.probing':'probando red…', 'ots.ok':'calendarios accesibles', 'ots.warn':'acceso parcial',
    'ots.bad':'sin acceso (air-gapped?)', 'ots.off':'desactivado',
    'ots.activo':'Activo', 'ots.inactivo':'Inactivo',
    'ots.ultimo_ancla':'Último ancla', 'ots.cadena':'Cadena', 'ots.bloques':'bloques', 'ots.hash':'Hash',
    'ots.probando':'Probando…',
    'ots.test_ok':'✓ Servidor responde (o CORS bloqueado — esto es normal, no indica error).',
    'ots.test_bad':'⚠ Sin respuesta. Puede ser CORS o entorno sin internet.',
    'ots.raiz':'raíz', 'ots.raices':'raíces', 'ots.pendiente':'pendiente', 'ots.pendientes':'pendientes', 'ots.de_anclaje':'de anclaje',
    'log.sin_actividad':'Sin actividad registrada.', 'log.inicia_monitoreo':'Inicia el monitoreo con ▶ Iniciar para ver eventos aquí.',
    'log.sin_entradas_filtros':'Sin entradas con los filtros seleccionados.',
    'log.sin_ataques':'Sin ataques registrados.', 'log.sistema_vigilando':'El sistema está vigilando — aparecerán aquí si se detecta actividad maliciosa.',
    'log.sin_eventos_filtro':'Sin eventos para el filtro seleccionado.',
    'log.sin_campos_extra':'Sin campos extra',
    'log.sin_commits':'Sin commits de configuración.', 'log.sin_commits_busqueda':'Sin commits que coincidan con la búsqueda.',
    'log.historial_cambios':'Historial de cambios en configuración.', 'log.modifica_control':'Modifica cualquier control para conectar tu GitHub PAT y cargar el historial.',
    'log.error':'Error',
    'log.total':'total',
    'log.auto_refresco_inactivo':'Auto-refresco inactivo', 'log.live_activo':'Live activo (30s) — clic para detener',
    'log.sin_acciones':'Sin acciones registradas.', 'log.acciones_tiempo_real':'Las acciones del operador aparecerán aquí en tiempo real.',
    'seed.configurado':'Sistema configurado', 'seed.pais':'País', 'seed.configurado_el':'Configurado',
    'seed.ultima_regen':'Última regeneración', 'seed.nunca':'Nunca', 'seed.claves_activas':'Claves activas',
    'seed.no_configurado':'Sistema no configurado aún. Ejecuta el wizard de inicio.',
    'seed.error_carga':'No se pudo cargar el estado.',
    'seed.ingresa_clave':'Ingresa la clave para autenticar.',
    'seed.regenerando':'Regenerando…', 'seed.si_regenerar':'Sí, regenerar ahora',
    'seed.error_prefix':'Error',
    'seed.modo_pages':'En modo Pages no hay API local.', 'seed.abre_workflow':'Abre el workflow "Regenerate Admin Seeds"',
    'seed.run_workflow_hint':'en GitHub Actions. Haz clic en "Run workflow", luego descarga el artifact de seeds (expira en 24h).',
    'ec.cerrado':'Cerrado', 'ec.eleccion_en_curso':'Elección en curso', 'ec.modo':'Modo',
    'ec.error_desconocido':'Error desconocido', 'ec.error':'Error',
    'ec.iniciando_raspe':'Iniciando raspe completo…', 'ec.descargando_fuentes':'Descargando fuentes CNE…',
    'ec.procesando_hash':'Procesando y hasheando snapshots…', 'ec.finalizando_cadena':'Finalizando cadena de hash…',
    'data.usados':'usados', 'data.ciclos_registrados':'ciclos registrados en cadena de hashes', 'data.dias_monitoreo':'días de monitoreo',
    'evidence.preparando':'⏳ Preparando…', 'evidence.descargar':'Descargar evidencia',
    'evidence.no_cadena':'No se encontró cadena de hashes',
    'evidence.descargada':'✅ Evidencia descargada. Guárdala en un lugar seguro fuera del repositorio.',
    'purge.clave_invalida':'Clave inválida — debe comenzar con ghp_',
    'purge.no_snapshots':'No se encontraron snapshots para eliminar.',
    'purge.eliminando':'Eliminando', 'purge.archivos_json':'archivos JSON',
    'purge.eliminados_ok':'snapshots eliminados. Cadena de hashes conservada intacta.',
    'purge.eliminados_parcial':'eliminados, {f} fallaron. Recarga para reintentar.',
    'swarm.en_red':'EN RED', 'swarm.nodo':'nodo', 'swarm.nodos':'nodos', 'swarm.activo':'activo', 'swarm.activos':'activos',
    'swarm.conectando':'CONECTANDO…', 'swarm.desconectado':'DESCONECTADO',
    'swarm.conectar':'Conectar a la red', 'swarm.desconectar':'Desconectar', 'swarm.desconectando':'Desconectando…',
    'swarm.confirm_desconectar':'¿Desconectar del enjambre? Tendrás que volver a conectar manualmente.',
    'swarm.error_conectar':'Error al conectar', 'swarm.error':'Error',
    'swarm.en_sync':'✓ en sync', 'swarm.diverge':'≠ diverge', 'swarm.kick':'Kick',
    'swarm.consenso_alcanzado':'Consenso alcanzado —', 'swarm.comparten_merkle':'comparten el mismo Merkle root', 'swarm.datos_consistentes':'Los datos del CNE son consistentes en la red.',
    'swarm.sin_consenso':'Sin consenso aún — esperando que más nodos sincronicen', 'swarm.coinciden':'coinciden',
  },
  en: {
    'card.sha':'SHA-256 Chain', 'card.cb':'Circuit Breaker', 'card.animal':'ARGOS Protocol',
    'card.benford':'Benford 1st Digit', 'card.zscore':'Max Z-Score', 'card.ots':'OTS Bitcoin',
    'card.cpu':'CPU Watchdog', 'card.ram':'Memory', 'card.attacks':'Attacks Detected',
    'card.endpoints':'Active Endpoints',
    'val.sin_datos':'no data', 'val.integra':'INTACT', 'val.rota':'BROKEN',
    'val.abierto':'OPEN', 'val.cerrado':'CLOSED',
    'val.confirmado':'CONFIRMED', 'val.pendiente':'PENDING', 'val.error':'ERROR', 'val.desconocido':'UNKNOWN',
    'val.eventos':'events', 'val.limite':'limit',
    'det.pipeline_no_run':'Pipeline has not run yet',
    'empty.needs_node':'This needs your node running.',
    'empty.how_to_start':'How to start my node',
    'empty.no_data_yet':'No data yet.',
    'empty.retry':'Retry',
    'det.fallos_consecutivos':'consecutive failures',
    'det.ultimo':'Last',
    'det.warning_critical':'{w} WARNING · {c} CRITICAL',
    'det.fallando':'failing',
    'det.no_disponible':'Real-time data not available on Pages',
    'tip.umbral':'Threshold — synced with Advanced Configuration',
    'tip.benford':"Benford's Law: checks if the leading digits of tally data follow the expected natural distribution. A significant deviation may indicate data anomalies.",
    'tip.zscore':'Z-Score: measures how far a result deviates from the historical average. High values indicate unusual changes that warrant review.',
    'tip.cpu.card':'Monitoring server CPU. Threshold configurable in Advanced → Watchdog.',
    'tip.ram.card':'RAM memory in use. Threshold configurable in Advanced → Watchdog.',
    'badge.defensas':'DEFENSES', 'badge.safemode':'SAFE MODE', 'badge.circuit':'CIRCUIT BREAKER',
    'badge.election':'ELECTION MODE',
    'badge.normal':'NORMAL', 'badge.caution':'CAUTION', 'badge.survival':'SURVIVAL',
    'badge.on':'ON', 'badge.off':'OFF', 'badge.abierto':'OPEN', 'badge.cerrado':'CLOSED',
    'dept.label':'{div} — {total} endpoints (1 national + {n})',
    'dept.divisiones':'Divisions',
    'dept.map_unavailable':'Map unavailable',
    'map.narrative_ok':'No anomalies detected',
    'map.narrative_ok_sub':'All configured departments are reporting normally.',
    'map.narrative_down':'Down',
    'map.narrative_late':'Delayed',
    'map.narrative_ok_dept':'OK',
    'map.narrative_nodata':'No data',
    'map.narrative_last':'Last event',
    'ots.probing':'probing network…', 'ots.ok':'calendars reachable', 'ots.warn':'partial access',
    'ots.bad':'no access (air-gapped?)', 'ots.off':'disabled',
    'ots.activo':'Active', 'ots.inactivo':'Inactive',
    'ots.ultimo_ancla':'Last anchor', 'ots.cadena':'Chain', 'ots.bloques':'blocks', 'ots.hash':'Hash',
    'ots.probando':'Testing…',
    'ots.test_ok':'✓ Server responds (or CORS blocked — this is normal, not an error).',
    'ots.test_bad':'⚠ No response. May be CORS or an offline environment.',
    'ots.raiz':'root', 'ots.raices':'roots', 'ots.pendiente':'pending', 'ots.pendientes':'pending', 'ots.de_anclaje':'to anchor',
    'log.sin_actividad':'No activity recorded.', 'log.inicia_monitoreo':'Start monitoring with ▶ Start to see events here.',
    'log.sin_entradas_filtros':'No entries match the selected filters.',
    'log.sin_ataques':'No attacks recorded.', 'log.sistema_vigilando':'The system is watching — they will appear here if malicious activity is detected.',
    'log.sin_eventos_filtro':'No events for the selected filter.',
    'log.sin_campos_extra':'No extra fields',
    'log.sin_commits':'No configuration commits.', 'log.sin_commits_busqueda':'No commits match the search.',
    'log.historial_cambios':'Configuration change history.', 'log.modifica_control':'Modify any control to connect your GitHub PAT and load the history.',
    'log.error':'Error',
    'log.total':'total',
    'log.auto_refresco_inactivo':'Auto-refresh inactive', 'log.live_activo':'Live active (30s) — click to stop',
    'log.sin_acciones':'No actions recorded.', 'log.acciones_tiempo_real':'Operator actions will appear here in real time.',
    'seed.configurado':'System configured', 'seed.pais':'Country', 'seed.configurado_el':'Configured',
    'seed.ultima_regen':'Last regeneration', 'seed.nunca':'Never', 'seed.claves_activas':'Active keys',
    'seed.no_configurado':'System not configured yet. Run the setup wizard.',
    'seed.error_carga':'Could not load status.',
    'seed.ingresa_clave':'Enter the key to authenticate.',
    'seed.regenerando':'Regenerating…', 'seed.si_regenerar':'Yes, regenerate now',
    'seed.error_prefix':'Error',
    'seed.modo_pages':'No local API available in Pages mode.', 'seed.abre_workflow':'Open the "Regenerate Admin Seeds" workflow',
    'seed.run_workflow_hint':'on GitHub Actions. Click "Run workflow", then download the seeds artifact (expires in 24h).',
    'ec.cerrado':'Closed', 'ec.eleccion_en_curso':'Election in progress', 'ec.modo':'Mode',
    'ec.error_desconocido':'Unknown error', 'ec.error':'Error',
    'ec.iniciando_raspe':'Starting full scrape…', 'ec.descargando_fuentes':'Downloading electoral sources…',
    'ec.procesando_hash':'Processing and hashing snapshots…', 'ec.finalizando_cadena':'Finalizing hash chain…',
    'data.usados':'used', 'data.ciclos_registrados':'cycles recorded in hash chain', 'data.dias_monitoreo':'days of monitoring',
    'evidence.preparando':'⏳ Preparing…', 'evidence.descargar':'Download evidence',
    'evidence.no_cadena':'Hash chain not found',
    'evidence.descargada':'✅ Evidence downloaded. Store it somewhere safe outside the repository.',
    'purge.clave_invalida':'Invalid key — must start with ghp_',
    'purge.no_snapshots':'No snapshots found to delete.',
    'purge.eliminando':'Deleting', 'purge.archivos_json':'JSON files',
    'purge.eliminados_ok':'snapshots deleted. Hash chain preserved intact.',
    'purge.eliminados_parcial':'deleted, {f} failed. Reload to retry.',
    'swarm.en_red':'ON NETWORK', 'swarm.nodo':'node', 'swarm.nodos':'nodes', 'swarm.activo':'active', 'swarm.activos':'active',
    'swarm.conectando':'CONNECTING…', 'swarm.desconectado':'DISCONNECTED',
    'swarm.conectar':'Connect to network', 'swarm.desconectar':'Disconnect', 'swarm.desconectando':'Disconnecting…',
    'swarm.confirm_desconectar':'Disconnect from the swarm? You will need to reconnect manually.',
    'swarm.error_conectar':'Connection error', 'swarm.error':'Error',
    'swarm.en_sync':'✓ in sync', 'swarm.diverge':'≠ diverges', 'swarm.kick':'Kick',
    'swarm.consenso_alcanzado':'Consensus reached —', 'swarm.comparten_merkle':'share the same Merkle root', 'swarm.datos_consistentes':'Electoral data is consistent across the network.',
    'swarm.sin_consenso':'No consensus yet — waiting for more nodes to sync', 'swarm.coinciden':'match',
  }
};
function t(key, vars){
  let s = (I18N[window.OPS_LANG]||I18N.es)[key] || key;
  if(vars) for(const k in vars) s = s.replace('{'+k+'}', vars[k]);
  return s;
}
function refreshOpsLang(){
  window.OPS_LANG = localStorage.getItem('vigil-lang') || 'es';
  try{ buildSensorCards(); }catch(e){}
  try{ updateSensorCards(); }catch(e){}
  try{ updateStatusBadges(); }catch(e){}
  try{ if(DEPTS && DEPTS.length) buildDeptGrid(); }catch(e){}
  try{ _syncOtsBtn(); }catch(e){}
  try{ loadOtsStatus(); }catch(e){}
  try{ _loadAwsState(); }catch(e){}
  try{ renderLog(); }catch(e){}
  try{ renderAttackLog(); }catch(e){}
  try{ renderAuditTrail(); }catch(e){}
  try{ _renderSessionLog(); }catch(e){}
  try{ loadSeedStatus(); }catch(e){}
  try{ loadElectionStatus(); }catch(e){}
  try{ loadDataSize(); }catch(e){}
  try{ loadSwarmStatus(); }catch(e){}
}
window.refreshOpsLang = refreshOpsLang;

const CARD_DEFS = [
  {id:'sha',    labelKey:'card.sha',      icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'},
  {id:'cb',     labelKey:'card.cb',     tier:'status', icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'},
  {id:'animal', labelKey:'card.animal', tier:'status',         icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'},
  {id:'benford',labelKey:'card.benford',  icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>', tipKey:'tip.benford'},
  {id:'zscore', labelKey:'card.zscore',   icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>', tipKey:'tip.zscore'},
  {id:'ots',    labelKey:'card.ots',    tier:'status',         icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'},
  {id:'cpu',    labelKey:'card.cpu',    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>', tipKey:'tip.cpu.card'},
  {id:'ram',    labelKey:'card.ram',    icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>', tipKey:'tip.ram.card'},
  {id:'attacks',labelKey:'card.attacks',  icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'},
  {id:'endpoints',labelKey:'card.endpoints', icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'},
];

function buildSensorCards(){
  const statusGrid = document.getElementById('status-cards');
  const grid = document.getElementById('sensor-cards');
  if(!grid) return;

  const cardHtml = def => `
    <div class="stat-card${def.tier==='status'?' status-card':''}" id="sc-${def.id}">
      <div class="sc-label">
        <span>${def.icon} ${t(def.labelKey)}</span>
        ${def.tipKey?`<span class="sec-tip" data-tip="${t(def.tipKey)}" style="font-size:10px;cursor:help">ⓘ</span>`:''}
      </div>
      <div class="sc-val val-neutral skel-pulse" id="scv-${def.id}">—</div>
      <div class="sc-detail skel-pulse" id="scd-${def.id}">—</div>
      <div class="sc-bar"><div class="sc-bar-fill" id="scb-${def.id}" style="width:0%;background:var(--muted)"></div></div>
      <div class="sc-age" id="sca-${def.id}"></div>
    </div>
  `;

  if(statusGrid) statusGrid.innerHTML = CARD_DEFS.filter(d=>d.tier==='status').map(cardHtml).join('');
  grid.innerHTML = CARD_DEFS.filter(d=>d.tier!=='status').map(cardHtml).join('');
}

function updateSensorCards(){
  if(!snapshotData) return;
  const s = snapshotData;
  const chain  = s?.chain || {};
  const cne    = s?.cne_status || {};
  const ep     = localConfig['config/prod/endpoints.yaml'] || {};
  const wd     = localConfig['config/prod/watchdog.yaml'] || {};

  // SHA chain
  const hasChainData = !!(chain.latest_hash || chain.chain_length > 0);
  const hashOk = chain.integrity !== false;
  const hashStr = chain.latest_hash ? chain.latest_hash.slice(-8) : '—';
  if(!hasChainData){
    setCard('sha', t('val.sin_datos'), t('det.pipeline_no_run'), 0, 'neutral', false);
  } else {
    setCard('sha', hashOk?t('val.integra'):t('val.rota'), hashStr, hashOk?100:0, hashOk?'ok':'bad');
  }

  // Circuit Breaker
  const cbOpen = cne.consecutive_failures >= 3;
  const cbFail = cne.consecutive_failures || 0;
  setCard('cb', cbOpen?t('val.abierto'):t('val.cerrado'), `${cbFail} ${t('det.fallos_consecutivos')}`, cbOpen?100:0, cbOpen?'bad':'ok');

  // Protocolo ARGOS mode
  const animal = ep?.healing?.argos_protocol || ep?.healing?.animal_mode || 'normal';
  const animalCls = {normal:'ok', caution:'warn', survival:'bad'}[animal]||'neutral';
  const animalLabel = {normal:t('badge.normal'), caution:t('badge.caution'), survival:t('badge.survival')}[animal] || animal.toUpperCase();
  setCard('animal', animalLabel, '', 0, animalCls, false);

  // OTS
  const ots = chain.ots_status || 'unknown';
  const otsCls   = {confirmed:'ok',pending:'warn',error:'bad'}[ots]||'neutral';
  const otsLabel = {confirmed:t('val.confirmado'),pending:t('val.pendiente'),error:t('val.error')}[ots]||t('val.desconocido');
  setCard('ots', otsLabel, chain.last_anchor ? `${t('det.ultimo')}: ${relTime(chain.last_anchor)}` : '', 0, otsCls, false);

  // Attacks
  const alerts = s?.alerts || [];
  const critical = alerts.filter(a=>a.level==='CRITICAL').length;
  const warnings = alerts.filter(a=>a.level==='WARNING').length;
  setCard('attacks', `${alerts.length} ${t('val.eventos')}`, t('det.warning_critical',{w:warnings,c:critical}), critical>0?100:warnings>0?50:0, critical>0?'bad':warnings>0?'warn':'ok');

  // Endpoints — distinguish "no pipeline data yet" from "active failures"
  const epsRaw = s?.endpoints_status;
  const hasEpData = epsRaw && (Array.isArray(epsRaw) ? epsRaw.length > 0 : Object.keys(epsRaw).length > 0);
  const eps = hasEpData ? Object.values(epsRaw) : [];
  const okEps = eps.filter(e=>e.ok).length;
  const total = Math.max(1, DEPTS.length - 1);
  if(!hasEpData){
    setCard('endpoints', t('val.sin_datos'), t('det.pipeline_no_run'), 0, 'neutral', false);
  } else {
    setCard('endpoints', `${okEps}/${total}`, `${total-okEps} ${t('det.fallando')}`, okEps/total*100, okEps===total?'ok':okEps>total*0.8?'warn':'bad');
  }

  // CPU/RAM — show actual usage if available in snapshot, else show configured threshold
  const cpuLimit = wd?.max_cpu_percent || 80;
  const ramLimit = wd?.max_mem_percent || 90;
  const cpuUsage = s?.system?.cpu_percent ?? s?.cpu_percent ?? null;
  const ramUsage = s?.system?.ram_percent ?? s?.ram_percent ?? s?.system?.mem_percent ?? null;
  if(cpuUsage !== null){
    const cpuCls = cpuUsage >= cpuLimit ? 'bad' : cpuUsage >= cpuLimit * 0.8 ? 'warn' : 'ok';
    setCard('cpu', `${Math.round(cpuUsage)}%`, `umbral: ${cpuLimit}%`, (cpuUsage/cpuLimit)*100, cpuCls);
  } else {
    setCard('cpu', `${cpuLimit}%`, 'umbral configurado', 0, 'neutral', false);
  }
  if(ramUsage !== null){
    const ramCls = ramUsage >= ramLimit ? 'bad' : ramUsage >= ramLimit * 0.8 ? 'warn' : 'ok';
    setCard('ram', `${Math.round(ramUsage)}%`, `umbral: ${ramLimit}%`, (ramUsage/ramLimit)*100, ramCls);
  } else {
    setCard('ram', `${ramLimit}%`, 'umbral configurado', 0, 'neutral', false);
  }

  // Global status banner
  const argosActive = (ep?.healing?.animal_mode || 'normal') === 'survival';
  const cbFails = cne.consecutive_failures || 0;
  const banner = document.getElementById('global-status-banner');
  if(banner){
    if(argosActive){
      banner.className = 'global-status-banner bad';
      banner.textContent = '⬛ CRÍTICO — Protocolo ARGOS activo';
    } else if(cbFails >= 3){
      banner.className = 'global-status-banner warn';
      banner.textContent = '⚠ PRECAUCIÓN — ' + cbFails + ' fallos consecutivos';
    } else {
      banner.className = 'global-status-banner nominal';
      banner.textContent = '● SISTEMA NOMINAL';
    }
  }
}

function setCard(id, val, detail, barPct, cls, showBar=true){
  const el = v=>document.getElementById(v);
  const clsMap = {ok:'val-ok',warn:'val-warn',bad:'val-bad',neutral:'val-neutral'};
  if(el(`scv-${id}`)){
    el(`scv-${id}`).textContent = val;
    el(`scv-${id}`).className = `sc-val ${clsMap[cls]||'val-neutral'}`;
  }
  if(el(`scd-${id}`)){
    el(`scd-${id}`).textContent = detail;
    el(`scd-${id}`).classList.remove('skel-pulse');
  }
  if(el(`scb-${id}`)){
    const fillCls = {ok:'var(--ok)',warn:'var(--warn)',bad:'var(--bad)',neutral:'var(--muted)'}[cls];
    el(`scb-${id}`).style.width = (showBar?barPct:0)+'%';
    el(`scb-${id}`).style.background = fillCls||'var(--muted)';
  }
}

// ══════════════════════════════════════════════════════════
// MAP
// ══════════════════════════════════════════════════════════


function buildDeptGrid(){
  // Defensive: DEPTS should always have entries (fallback list guarantees it)
  if(!DEPTS || DEPTS.length === 0) return;

  // Update section label with live count
  const lbl = document.getElementById('dept-section-label');
  const divCount = DEPTS.filter(d => d.code !== '00').length;
  const divLabel = COUNTRY_META?.divisions_label || t('dept.divisiones');
  if (lbl) lbl.textContent = t('dept.label', {div:divLabel, total:divCount+1, n:divCount});

  // Load/refresh the interactive country map, then bind department clicks
  loadOpsCountryMap(ACTIVE_COUNTRY_CODE).then(() => {
    bindMapPaths();
    updateDeptGrid();
  });
}

// ══════════════════════════════════════════════════════════
// INTERACTIVE COUNTRY MAP (Divisiones electorales)
// Mirrors web/monitor/'s loadCountryMap — same SVG assets,
// but here each department opens the editable endpoint popup
// (openMapPopupAtEvent) instead of a read-only side panel.
// ══════════════════════════════════════════════════════════
let _opsMapLoaded = null; // country code currently loaded into #hn-ops-map-container

async function loadOpsCountryMap(countryCode){
  const container = document.getElementById('hn-ops-map-container');
  if(!container) return;
  const code = (countryCode || 'HN').toUpperCase();
  if(_opsMapLoaded === code && container.querySelector('svg')) return; // already loaded
  try{
    const r = await fetch(`../assets/maps/${code}.svg`);
    if(!r.ok) throw new Error(r.status);
    const svgText = await r.text();
    container.innerHTML = svgText;
    const svg = container.querySelector('svg');
    if(svg){
      svg.id = 'ops-hn-map';
      svg.style.width = '100%';
      svg.style.height = 'auto';
      svg.style.display = 'block';
    }
    _opsMapLoaded = code;
  }catch(e){
    console.warn('Ops map SVG not available for', code, e);
    container.innerHTML = `<div style="text-align:center;color:var(--muted);font-size:12px;padding:24px 0;font-family:var(--mono)">${t('dept.map_unavailable')||'Mapa no disponible'} (${code})</div>`;
    _opsMapLoaded = null;
  }
}

function bindMapPaths(){
  const svg = document.getElementById('ops-hn-map');
  if(!svg) return;
  DEPTS.filter(d => d.code !== '00' && d.iso).forEach(dept => {
    const path = svg.querySelector('#'+dept.iso) || svg.getElementById(dept.iso);
    if(!path) return;
    path.style.cursor = 'pointer';
    path.style.transition = 'fill .15s';
    path.onclick = (e) => openMapPopupAtEvent(dept.code, e);
    // Native tooltip with department name + code
    let title = path.querySelector('title');
    if(!title){ title = document.createElementNS('http://www.w3.org/2000/svg','title'); path.appendChild(title); }
    title.textContent = `${dept.name} (${dept.code})`;
  });
}

function updateDeptGrid(){
  const epCfg = localConfig['config/prod/endpoints.yaml'] || {};
  const configured = (epCfg?.cne?.presidential_endpoints || [])
    .map(e => (e.department_code || '').toString().padStart(2,'0'));

  // National badge dot
  const natDot = document.getElementById('dep-dot-00');
  if(natDot) natDot.style.background = deptDotColor('00', configured);

  // Map path fills
  const svg = document.getElementById('ops-hn-map');
  if(svg){
    DEPTS.filter(d => d.code !== '00' && d.iso).forEach(dept => {
      const path = svg.querySelector('#'+dept.iso) || svg.getElementById(dept.iso);
      if(!path) return;
      path.style.fill = deptDotColor(dept.code, configured);
      path.classList.remove('dept-recent');
    });
  }

  updateMapNarrative(svg, configured);
}

// Fase D — panel narrativo: identifica el evento más reciente/relevante
// y resalta el departamento correspondiente sobre el mapa.
function updateMapNarrative(svg, configured){
  const panel = document.getElementById('map-narrative');
  if(!panel) return;
  let pick = null; // {dept, status, severity}
  const sevRank = {bad:2, warn:1, ok:0, neutral:-1};

  // Solo se promueve un departamento al panel narrativo si tiene una
  // severidad real (warn/bad). 'neutral' (sin datos) y 'ok' nunca deben
  // mostrarse aquí — de lo contrario el primer departamento configurado
  // (Atlántida) aparece por defecto como "Sin datos" sin ninguna razón.
  // Only promote a department to the narrative panel if it has real
  // severity (warn/bad). 'neutral' (no data) and 'ok' must never surface
  // here, otherwise the first configured department (Atlántida) shows up
  // by default as "Sin datos" for no actual reason.
  DEPTS.filter(d => d.code !== '00' && configured.includes(d.code)).forEach(dept => {
    const status = getEndpointStatus(dept.code);
    if(sevRank[status.cls] <= 0) return; // skip 'neutral' and 'ok'
    if(!pick || sevRank[status.cls] > sevRank[pick.status.cls]){
      pick = {dept, status};
    }
  });

  if(!pick || !snapshotData){
    panel.innerHTML = `
      <div class="mn-icon mn-icon-ok"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z"/><path d="m9 12 2 2 4-4"/></svg></div>
      <div class="mn-text">
        <div class="mn-title" data-lang-es="Sin anomalías detectadas" data-lang-en="No anomalies detected">${t('map.narrative_ok')||'Sin anomalías detectadas'}</div>
        <div class="mn-sub" data-lang-es="Todos los departamentos configurados reportan con normalidad." data-lang-en="All configured departments are reporting normally.">${t('map.narrative_ok_sub')||'Todos los departamentos configurados reportan con normalidad.'}</div>
      </div>`;
    return;
  }

  const {dept, status} = pick;
  const sevClass = {bad:'mn-icon-bad', warn:'mn-icon-warn', ok:'mn-icon-ok', neutral:'mn-icon-ok'}[status.cls];
  const verb = {bad:t('map.narrative_down')||'Caído', warn:t('map.narrative_late')||'Tardío', ok:t('map.narrative_ok_dept')||'OK', neutral:t('map.narrative_nodata')||'Sin datos'}[status.cls];

  panel.innerHTML = `
    <div class="mn-icon ${sevClass}"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg></div>
    <div class="mn-text">
      <div class="mn-title">${dept.name} <span class="mn-code">(${dept.code})</span></div>
      <div class="mn-sub"><span class="badge badge-${status.cls}" style="margin-right:6px">${verb}</span>${t('map.narrative_last')||'Último evento'}: ${status.lastOk}</div>
    </div>`;

  // Auto-highlight on the map
  if(svg && dept.iso && status.cls !== 'ok'){
    const path = svg.querySelector('#'+dept.iso) || svg.getElementById(dept.iso);
    if(path) path.classList.add('dept-recent');
  }
}

// Single source of truth for the 4-color legend
// (OK / Tardío / Caído / Sin configurar) shared by dots and map fills.
function deptDotColor(code, configured){
  // Gris neutro, no pizarra: #3a3f49 tiene tono azul y el panel no usa azul.
  // English: a neutral grey, not slate -- #3a3f49 carries a blue hue.
  if(!configured.includes(code)) return '#525252'; // Sin configurar
  const status = getEndpointStatus(code);
  if(!snapshotData) return '#525252';
  if(status.cls === 'ok')   return 'var(--ok)'; // OK
  if(status.cls === 'bad')  return 'var(--bad)'; // Caído / Error
  if(status.cls === 'warn') return 'var(--warn)'; // Tardío
  return '#525252'; // sin datos todavía
}
function updateStatusBadges(){
  const ep = localConfig['config/prod/endpoints.yaml'] || {};
  const animal = ep?.healing?.argos_protocol || ep?.healing?.animal_mode || 'normal';
  const safe   = ep?.healing?.safe_mode_active || false;
  const cne    = snapshotData?.cne_status || {};
  const cbOpen = (cne.consecutive_failures||0) >= 3;

  const bAnimal = document.getElementById('badge-animal');
  if(bAnimal){
    const cls = {normal:'ok', caution:'warn', survival:'bad'}[animal]||'neutral';
    const animalLabel = {normal:t('badge.normal'), caution:t('badge.caution'), survival:t('badge.survival')}[animal] || animal.toUpperCase();
    bAnimal.className = `badge badge-${cls}`;
    bAnimal.textContent = `${t('badge.defensas')}: ${animalLabel}`;
  }
  const bSafe = document.getElementById('badge-safemode');
  if(bSafe){
    bSafe.className = `badge badge-${safe?'warn':'neutral'}`;
    bSafe.textContent = `${t('badge.safemode')}: ${safe?t('badge.on'):t('badge.off')}`;
  }
  const bCb = document.getElementById('badge-circuit');
  if(bCb){
    bCb.className = `badge badge-${cbOpen?'bad':'ok'}`;
    bCb.textContent = `${t('badge.circuit')}: ${cbOpen?t('badge.abierto'):t('badge.cerrado')}`;
  }
  const bEl = document.getElementById('badge-election');
  if(bEl){
    const elMode = document.getElementById('tog-election')?.checked || false;
    bEl.className = `badge badge-${elMode?'warn':'neutral'}`;
    bEl.textContent = `${t('badge.election')}: ${elMode?t('badge.on'):t('badge.off')}`;
    document.body.classList.toggle('election-mode', elMode);
  }
  _updateMissionBar();
}

function _updateMissionBar() {
  const ep = localConfig['config/prod/endpoints.yaml'] || {};
  const animal = ep?.healing?.argos_protocol || ep?.healing?.animal_mode || 'normal';
  const elMode = document.getElementById('tog-election')?.checked || false;
  const nodeEl = document.getElementById('swarm-m-nodos');
  const nodeCount = nodeEl ? nodeEl.textContent.trim() : '—';

  const msCountry = document.getElementById('ms-country');
  const msElec = document.getElementById('ms-elec');
  const msDefense = document.getElementById('ms-defense');
  const msNodes = document.getElementById('ms-nodes');
  const msSystem = document.getElementById('ms-system');
  if (!msSystem) return;

  if (msCountry) msCountry.textContent = ACTIVE_COUNTRY_CODE || '—';
  if (msElec) {
    msElec.textContent = elMode ? 'ACTIVO' : 'INACTIVO';
    msElec.className = `cmd-stat-val ${elMode ? 'alerta' : ''}`;
  }
  if (msDefense) {
    const defCls = {normal:'', caution:'alerta', survival:'critico'}[animal] || '';
    msDefense.textContent = animal.toUpperCase();
    msDefense.className = `cmd-stat-val ${defCls}`;
  }
  if (msNodes) msNodes.textContent = (nodeCount === '—' || nodeCount === '') ? '—' : nodeCount;

  const hasCritical = ['badge-animal','badge-safemode','badge-circuit','badge-election'].some(id => {
    const el = document.getElementById(id);
    return el && el.classList.contains('badge-bad');
  });
  msSystem.textContent = hasCritical ? 'ALERTA' : 'NOMINAL';
  msSystem.className = `ring-sys-val ${hasCritical ? 'alerta' : 'nominal'}`;
  const ringWrap = document.getElementById('status-ring-wrap');
  if (ringWrap) ringWrap.classList.toggle('ring-alert', hasCritical);
}

// ══════════════════════════════════════════════════════════
// MAP POPUP
// ══════════════════════════════════════════════════════════
function openMapPopup(code){ openMapPopupAtEvent(code, null); }

function openMapPopupAtEvent(code, evt){
  currentPopupCode = code;
  const dept = DEPTS.find(d => d.code === code);
  if(!dept) return;
  const epCfg = localConfig['config/prod/endpoints.yaml'] || {};
  const eps = epCfg?.cne?.presidential_endpoints || [];
  const found = eps.find(e => (e.department_code||'').toString().padStart(2,'0') === code);
  const url = found?.url || '';
  const status = getEndpointStatus(code);

  document.getElementById('mp-dept-name').textContent = dept.name + ' (' + code + ')';
  document.getElementById('mp-url-input').value = url;
  document.getElementById('mp-status').textContent =
    'Estado: ' + status.label + ' · Último OK: ' + status.lastOk;

  const popup = document.getElementById('map-popup');
  const wrap  = document.getElementById('adm-map-wrap');
  const wr    = wrap.getBoundingClientRect();
  let px, py;
  if(evt){
    px = evt.clientX - wr.left + 8;
    py = evt.clientY - wr.top  + 8;
  } else {
    px = wr.width / 2 - 145;
    py = 10;
  }
  if(px + 300 > wr.width)  px = wr.width  - 305;
  if(py + 180 > wr.height) py = py - 195;
  if(px < 0) px = 4;
  if(py < 0) py = 4;
  popup.style.left = px + 'px';
  popup.style.top  = py + 'px';
  popup.style.display = 'block';
}

function closeMapPopup(){
  document.getElementById('map-popup').style.display='none';
  currentPopupCode = null;
}

function saveEndpointFromPopup(){
  if(!currentPopupCode) return;
  const url = document.getElementById('mp-url-input').value.trim();
  updateEndpointUrl(currentPopupCode, url);
  closeMapPopup();
}

async function testEndpoint(){
  if(!currentPopupCode) return;
  const url = document.getElementById('mp-url-input').value.trim();
  if(!url){document.getElementById('mp-status').textContent='Sin URL configurada.';return;}
  document.getElementById('mp-status').textContent='Probando…';
  try{
    await fetch(url,{method:'HEAD',mode:'no-cors',signal:AbortSignal.timeout(8000)});
    document.getElementById('mp-status').textContent='Respuesta recibida (puede ser ok).';
  }catch(e){
    document.getElementById('mp-status').textContent='No responde o CORS bloqueado: '+e.message;
  }
}

async function testEndpointCode(code){
  const ep = localConfig['config/prod/endpoints.yaml']?.cne?.presidential_endpoints||[];
  const found = ep.find(e=>(e.department_code||'').toString().padStart(2,'0')===code);
  const url = found?.url||'';
  if(!url){alert('Sin URL configurada para este endpoint.');return;}
  try{
    await fetch(url,{method:'HEAD',mode:'no-cors',signal:AbortSignal.timeout(8000)});
    alert('Respuesta recibida (OK o CORS).');
  }catch(e){alert('No responde: '+e.message);}
}

// ══════════════════════════════════════════════════════════
// SLIDERS SYNC (bidirectional: easy↔full↔cards)
// ══════════════════════════════════════════════════════════
const SLIDER_IDS = {
  interval:   ['sl-interval','sl-interval2','sc-sl-interval','sl-interval3'],
  rph:        ['sl-rph','sl-rph2','sl-rph3'],
  benford:    ['sl-benford','sl-benford2','sc-sl-benford'],
  zscore:     ['sl-zscore','sl-zscore2','sc-sl-zscore'],
  wdcheck:    ['sl-wdcheck'],
  cpu:        ['sl-cpu','sc-sl-cpu'],
  ram:        ['sl-ram','sc-sl-ram'],
  capacity:   ['sl-capacity','sl-capacity2'],
  timeout:    ['sl-timeout','sl-timeout2'],
  jitter:     ['sl-jitter'],
  concurrency:['sl-concurrency'],
};
const BADGE_IDS = {
  interval:   ['vb-interval','vb-interval2','sc-vb-interval','vb-interval3'],
  rph:        ['vb-rph','vb-rph2','vb-rph3'],
  benford:    ['vb-benford','vb-benford2','sc-vb-benford'],
  zscore:     ['vb-zscore','vb-zscore2','sc-vb-zscore'],
  wdcheck:    ['vb-wdcheck'],
  cpu:        ['vb-cpu','sc-vb-cpu'],
  ram:        ['vb-ram','sc-vb-ram'],
  capacity:   ['vb-capacity','vb-capacity2'],
  timeout:    ['vb-timeout','vb-timeout2'],
  jitter:     ['vb-jitter'],
  concurrency:['vb-concurrency'],
};

function syncSlider(key, val){
  let v = parseFloat(val);
  const requested = v;
  const isCustom = activePresetId && activePresetId.startsWith('custom-');
  if(!isCustom || !ceilingUnlocked){
    if(key==='rph')      v = Math.min(v, HARD_CEILING.maxRph);
    if(key==='interval') v = Math.max(v, HARD_CEILING.minInterval);
  }
  // Visible feedback when a security ceiling clamps the requested value
  if(v !== requested && typeof _ceilingFeedback==='function'){
    _ceilingFeedback(key, requested, v);
  }
  const display = Number.isInteger(v) ? v : v.toFixed(2);
  (SLIDER_IDS[key]||[]).forEach(id=>{
    const el = document.getElementById(id);
    if(el && parseFloat(el.value)!==v) el.value = v;
  });
  (BADGE_IDS[key]||[]).forEach(id=>{
    const el = document.getElementById(id);
    if(el) el.textContent = display;
  });
  if(key==='benford'){
    const sv = document.getElementById('scv-benford');
    const sd = document.getElementById('scd-benford');
    if(sv){ sv.textContent = `χ²=${v}`; sv.classList.remove('skel-pulse'); }
    if(sd){ sd.textContent = `Umbral: ${display}`; sd.classList.remove('skel-pulse'); }
  }
  if(key==='zscore'){
    const sv = document.getElementById('scv-zscore');
    const sd = document.getElementById('scd-zscore');
    if(sv){ sv.textContent = `${v}σ umbral`; sv.classList.remove('skel-pulse'); }
    if(sd) sd.classList.remove('skel-pulse');
  }
  markDirty();
}

// Called when the user edits the friendly URL field — only marks dirty, does NOT overwrite inp-main-url
function onEasyUrlInput(val){
  markDirty();
}


