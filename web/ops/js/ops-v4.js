// Panel OPS v4. La maqueta fija la disposicion y el texto. Donde el
// servidor no tiene la operacion, el panel lo dice y no finge el exito.
'use strict';

const OPS_V4_GEO = [
  {code:'01', name:'Atlántida', iso:'HN-AT'},
  {code:'02', name:'Choluteca', iso:'HN-CH'},
  {code:'03', name:'Colón', iso:'HN-CL'},
  {code:'04', name:'Comayagua', iso:'HN-CM'},
  {code:'05', name:'Copán', iso:'HN-CP'},
  {code:'06', name:'Cortés', iso:'HN-CR'},
  {code:'07', name:'El Paraíso', iso:'HN-EP'},
  {code:'08', name:'Francisco Morazán', iso:'HN-FM'},
  {code:'09', name:'Gracias a Dios', iso:'HN-GD'},
  {code:'10', name:'Intibucá', iso:'HN-IN'},
  {code:'11', name:'Islas de la Bahía', iso:'HN-IB'},
  {code:'12', name:'La Paz', iso:'HN-LP'},
  {code:'13', name:'Lempira', iso:'HN-LE'},
  {code:'14', name:'Ocotepeque', iso:'HN-OC'},
  {code:'15', name:'Olancho', iso:'HN-OL'},
  {code:'16', name:'Santa Bárbara', iso:'HN-SB'},
  {code:'17', name:'Valle', iso:'HN-VA'},
  {code:'18', name:'Yoro', iso:'HN-YO'},
];

const V4 = {
  lang: 'es',
  capture: 'active',
  captureKnown: false,
  dept: 'all',
  severity: 'all',
  from: '',
  to: '',
  rows: null,
  readError: null,
  mapSvg: '',
  pending: null,
  returnFocus: null,
  focusAfterClose: null,
  helpOpen: null,
  room: null,
};

const v4$ = (s) => document.querySelector(s);
const v4$$ = (s) => [...document.querySelectorAll(s)];
const v4t = (es, en) => (V4.lang === 'es' ? es : en);
const v4esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[c]));

function v4Role() {
  const raw = (sessionStorage.getItem('centinel_role') || 'operador').toLowerCase();
  if (raw === 'observer' || raw === 'observador') return 'observer';
  if (raw === 'admin' || raw === 'administrador') return 'admin';
  return 'operator';
}
function v4CanOperate() { return v4Role() !== 'observer'; }
function v4CanAdmin() { return v4Role() === 'admin'; }
function v4Pages() { return typeof opsIsPages === 'function' ? opsIsPages() : true; }

function v4Btn(es, en, action, cls, disabled, id) {
  return `<button type="button" ${id ? `id="${id}"` : ''} data-action="${action}" class="${cls || ''}" ${disabled ? 'disabled' : ''}>${v4t(es, en)}</button>`;
}
function v4P(es, en, cls) {
  return `<p class="${cls || ''}">${v4t(es, en)}</p>`;
}

const V4_HELP = {
  finding: ['Qué es un hallazgo', 'What a finding is',
    'Un hallazgo es algo en los datos publicados que no cuadra con lo esperado. Puede tener una explicación normal. Hay que revisarlo con la fuente original.',
    'A finding is something in published data that does not match what was expected. It may have a normal explanation. Check it against the original source.'],
  capture: ['Qué es una captura', 'What a capture is',
    'Una copia de lo que el sitio de resultados mostraba en ese momento. Última captura es la última vez que VIGIL guardó esa copia.',
    'A copy of what the results website showed at that moment. Last capture is the last time VIGIL saved that copy.'],
  fingerprint: ['Qué significa la huella', 'What a fingerprint means',
    'Permite comparar huellas para detectar cambios en el archivo. No confirma que el contenido sea verdadero.',
    'Lets you compare fingerprints to detect changes in the file. It does not confirm the content is true.'],
  stamp: ['Qué significa el sello', 'What a date stamp means',
    'Permite comprobar que el archivo ya existía en cierta fecha. No dice cuándo se creó ni si su contenido es correcto. Esta vista no incluye un recibo verificable.',
    'It shows the file already existed by a certain date. It does not say when it was created or whether its content is correct. This view includes no verifiable receipt.'],
  computer: ['Equipo y nodo: qué significa', 'Computer and node: what they mean',
    'Equipo es la computadora donde corre VIGIL y guarda capturas. Nodo es el nombre técnico de esa instalación. No es el teléfono desde el que consultas este panel.',
    'Computer means the machine running VIGIL and storing captures. Node is the technical name for that installation. It is not the phone you use to view this panel.'],
  room: ['Qué es una sala', 'What a room is',
    'Grupo de observadores que comparan lo que ven. Estar conectado no significa coincidir. No publicamos nombres, direcciones ni invitaciones.',
    'A group of observers comparing what they see. Being connected does not mean agreeing. We show no names, addresses or invitations.'],
  corroboration: ['Por qué no mostramos 9 de 12', 'Why we do not show 9 of 12',
    'No hay datos que acrediten pertenencia a una misma sala, captura y regla. 9 de 12 es una regla prevista, no una confirmación.',
    'No data certifies membership of the same room, capture and rule. 9 of 12 is a planned rule, not confirmation.'],
  severity: ['Qué significa la prioridad', 'What priority means',
    'Crítica: conviene revisarla primero. Advertencia: algo poco común que vale la pena mirar. Ninguna prueba una irregularidad por sí sola.',
    'Critical: review it first. Warning: something unusual worth a look. Neither proves an irregularity by itself.'],
  source: ['Qué se observa', 'What is observed',
    'VIGIL observa lo publicado; no cuenta votos. Sin comprobar no significa que una fuente esté caída.',
    'VIGIL watches what is published; it does not count votes. Unchecked does not mean a source is down.'],
  downloads: ['Qué incluye cada descarga', 'What each download includes',
    'CSV abre en hoja de cálculo; JSON es para programas. Ambos aplican filtros. ZIP incluye el conjunto sin filtros, con manifiesto y hashes. No acredita custodia.',
    'CSV opens in a spreadsheet; JSON is for software. Both apply filters. ZIP includes the dataset without filters, with manifest and hashes. It does not certify custody.'],
  analysis: ['Qué significa el análisis técnico', 'What technical analysis means',
    'Las pruebas matemáticas buscan patrones raros. Solo son una pista. Aquí no hay resultado publicado de Benford ni de Z-score.',
    'Math tests look for unusual patterns. They are only clues. No Benford or Z-score result is published here.'],
  rate: ['Qué es el ritmo de consultas', 'What query rate means',
    'Cuántas veces por hora VIGIL consulta el sitio. Un límite bajo ayuda a reducir la carga. Sin un nodo, no hay una medición.',
    'How often per hour VIGIL checks the site. A low limit helps reduce load. Without a node there is no measurement.'],
  chain: ['Qué es la cadena de capturas', 'What a capture chain is',
    'Cada captura guarda la huella de la anterior. Una raíz resume muchas huellas; no prueba captura en vivo ni veracidad.',
    'Each capture stores the previous fingerprint. A root summarizes many fingerprints; it does not prove live capture or truth.'],
  guide: ['Cómo leer este panel', 'How to read this panel',
    'Inicio dice qué pasa; Evidencia muestra las señales; Sala resume la coordinación. Controles reserva lo avanzado. Sin dato no es cero ni falla.',
    'Home says what is happening; Evidence shows signals; Room summarizes coordination. Controls keeps advanced options separate. Unknown is not zero or failure.'],
};

function v4Help(id) {
  const a = V4_HELP[id];
  return `<div class="help-unit"><button type="button" id="help-${id}" class="help-toggle" data-help="${id}" aria-expanded="false" aria-controls="help-panel-${id}">${v4t(a[0], a[1])}</button><div id="help-panel-${id}" class="help-panel" hidden><p>${v4t(a[2], a[3])}</p></div></div>`;
}

function v4GeoName(code) {
  if (code === '00') return v4t('Nacional', 'National');
  if (!code) return v4t('Lugar no publicado', 'Place not published');
  const found = OPS_V4_GEO.find((d) => d.code === code);
  return found ? found.name : v4t('Lugar no publicado', 'Place not published');
}

const V4_MES = {
  es: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
};
function v4Parts(d) {
  const o = {};
  new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Tegucigalpa', year: 'numeric', month: 'numeric', day: 'numeric',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(d).forEach((x) => { o[x.type] = x.value; });
  return o;
}
function v4Day(y, m, d) {
  return `${+d} ${V4_MES[V4.lang === 'es' ? 'es' : 'en'][m - 1]} ${y}`;
}
function v4DateTime(iso) {
  const o = v4Parts(new Date(iso));
  return `${v4Day(o.year, o.month, o.day)}, ${o.hour}:${o.minute}`;
}
function v4Hn(iso) { return `${v4DateTime(iso)} · ${v4t('hora Honduras', 'Honduras time')}`; }
function v4InputDay(v) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v || '')) return v4t('ninguna', 'none');
  const [y, m, d] = v.split('-');
  return v4Day(y, +m, d);
}

function v4Rule(rule) {
  if (['velocity', 'anomalous_resolution_velocity', 'high_impact_resolution', 'bulk_resolution'].includes(rule)) {
    return v4t('Cambio inusual en actas resueltas', 'Unusual change in resolved tally sheets');
  }
  if (rule === 'prolonged_stagnation') return v4t('Sin cambios durante un período prolongado', 'No changes for an extended period');
  if (rule === 'blackout_with_trend_shift') return v4t('Interrupción con cambio de tendencia', 'Interruption with trend shift');
  return v4t('Cambio entre dos capturas', 'Change between two captures');
}

function v4BadDates() { return V4.from && V4.to && V4.from > V4.to; }
function v4Filtered(ignorePlace) {
  const rows = V4.rows || [];
  return rows.filter((r) => (
    (ignorePlace || V4.dept === 'all' || (V4.dept === 'unknown' ? r.place == null : r.place === V4.dept))
    && (V4.severity === 'all' || r.severity === V4.severity)
    && (!V4.from || Date.parse(r.time) >= Date.parse(`${V4.from}T00:00:00-06:00`))
    && (!V4.to || Date.parse(r.time) <= Date.parse(`${V4.to}T23:59:59.999-06:00`))
  ));
}

function v4NormalizeAlerts(list) {
  return (list || []).map((a, i) => ({
    id: `alert-${i}`,
    place: a.department_code || a.place || null,
    severity: String(a.severity || 'warning').toUpperCase() === 'CRITICAL' ? 'CRITICAL' : 'WARNING',
    rule: a.kind || a.rule || 'change',
    time: a.timestamp || a.time,
    before: a.before ?? null,
    after: a.after ?? null,
    provenance: a.capture_hash || a.provenance || null,
    message: a.message || '',
  }));
}

async function v4LoadAlerts() {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 4000);
  try {
    const r = await fetch(new URL('../data/alerts.json', location.href).href, { signal: ctrl.signal, cache: 'no-store' });
    if (!r.ok) throw new Error('http');
    V4.rows = v4NormalizeAlerts(await r.json());
    V4.readError = null;
  } catch (e) {
    V4.rows = null;
    V4.readError = e && e.name === 'AbortError' ? 'timeout' : 'missing';
  } finally {
    clearTimeout(timer);
  }
}

async function v4LoadMap() {
  try {
    const r = await fetch(new URL('../assets/maps/HN.svg', location.href).href, { cache: 'force-cache' });
    if (!r.ok) return;
    let svg = await r.text();
    svg = svg.replace(/<svg\b/, '<svg role="group"');
    OPS_V4_GEO.forEach((d) => {
      const re = new RegExp(`(<path\\b[^>]*\\bid="${d.iso}"[^>]*)(/?>)`);
      svg = svg.replace(re, `$1 role="button" tabindex="0" data-place="${d.code}" aria-pressed="false" aria-label="${d.name}"$2`);
    });
    V4.mapSvg = svg;
  } catch (_) { V4.mapSvg = ''; }
}

function v4Banner() {
  const el = v4$('#sim-banner');
  if (!el) return;
  el.textContent = v4Pages()
    ? v4t('Sin nodo de control · esta página no para ni borra nada', 'No control node · this page does not stop or delete anything')
    : v4t('Nodo de control conectado · parada de emergencia y destrucción no están disponibles', 'Control node connected · emergency stop and destruction are not available');
}

function v4CaptureBlock(buttonId) {
  if (!v4CanOperate()) {
    return v4P('Vista de observador: sin acciones de operación.', 'Observer view: no operating actions.', 'note');
  }
  const paused = V4.capture === 'paused' && V4.captureKnown;
  const id = buttonId || 'capture-button';
  const label = paused
    ? v4Btn('Reanudar captura', 'Resume capture', 'resume', '', false, id)
    : v4Btn('Pausar captura', 'Pause capture', 'pause', '', false, id);
  const note = v4Pages()
    ? v4P('Sin nodo, pausar y reanudar no están disponibles todavía. Confirmar no cambia la captura.', 'Without a node, pause and resume are not available yet. Confirming does not change capture.', 'small')
    : v4P(paused
      ? 'Reanudar pide al nodo que inicie de nuevo con una captura inmediata. No recupera un proceso suspendido.'
      : 'Pausar pide al nodo que detenga solo la captura. Una tarea en marcha puede terminar. No borra lo guardado.',
      paused
      ? 'Resume asks the node to start again with an immediate capture. It does not recover a suspended process.'
      : 'Pause asks the node to stop capture alone. A task in progress may finish. Saved data is not deleted.');
  return `<div class="action-unit">${label}${note}</div>`;
}

function v4Home() {
  const n = V4.rows ? V4.rows.length : null;
  const count = V4.rows == null
    ? v4t('Sin dato', 'Unknown')
    : `${n} ${v4t('hallazgos', 'findings')}`;
  return `<div class="meta">${v4Pages()
    ? v4t('Solo este equipo · sin conexión a un nodo real', 'This computer only · not connected to a real node')
    : v4t('Nodo de control · solo este equipo', 'Control node · this computer only')}</div>
<section class="hero" id="hero-state">
  <div class="eyebrow" id="hero-eyebrow"></div>
  <h1 id="hero-headline" class="page-title" tabindex="-1"></h1>
  <p id="hero-detail"></p>
  <div class="actions">${v4Btn('Ver evidencia', 'View evidence', 'nav-evidencia', 'primary')}</div>
  ${v4CaptureBlock()}
</section>
<div class="cards">
  <section class="metric"><span>${v4t('Última captura', 'Last capture')}</span><b>${v4t('Sin dato', 'Unknown')}</b><small>${v4t('Captura no publicada en el archivo HN 2025', 'Capture not published in the HN 2025 archive')}</small></section>
  <section class="metric"><span>${v4t('Hallazgos en el conjunto', 'Findings in dataset')}</span><b>${count}</b><small>${V4.rows == null
    ? v4t('No hay lectura. No es cero.', 'No reading. This is not zero.')
    : v4t('Históricos, no de hoy', 'Historical, not today')}</small></section>
  <section class="metric"><span>${v4t('Computadoras observadas', 'Observed computers')}</span><b>${v4t('No publicado', 'Not published')}</b><small>${v4t('Corroboración no disponible', 'Corroboration unavailable')}</small></section>
</div>
<div class="grid">
  <section class="card"><h2>${v4t('Qué estamos observando', 'What we are watching')}</h2>
    ${v4P('VIGIL observa lo publicado; no cuenta votos.', 'VIGIL watches what is published; it does not count votes.')}
    ${v4P('Sitio del Consejo Nacional Electoral (CNE) · Honduras. Fuentes departamentales: sin comprobar.', 'National Electoral Council (CNE) website · Honduras. Department sources: unchecked.', 'small')}
    ${v4Help('source')}${v4Help('computer')}</section>
  <section class="card"><h2>${v4t('De la captura al sello', 'From capture to date stamp')}</h2>
    ${v4P('Copia → huella del archivo → sello de fecha', 'Copy → file fingerprint → date stamp')}
    ${v4P('Sello no disponible todavía. No se ha verificado un recibo.', 'Date stamp not available yet. No receipt has been verified.', 'note')}
    ${v4Help('capture')}${v4Help('stamp')}</section>
</div>
${v4Help('guide')}`;
}

function v4FindingList() {
  if (V4.rows == null) {
    return `<div class="empty"><h3>${v4t('No hay lectura disponible para comprobar', 'No data to check')}</h3>${v4P('No hay lectura actual. No equivale a cero hallazgos.', 'No current reading. This is not zero findings.')}</div>`;
  }
  if (v4BadDates()) return v4P('Corrige las fechas para mostrar resultados. No interpretamos el error como cero hallazgos.', 'Correct the dates to show results. A date error is not zero findings.', 'error');
  const rows = v4Filtered().slice().sort((a, b) => (a.severity === 'CRITICAL' ? 0 : 1) - (b.severity === 'CRITICAL' ? 0 : 1));
  if (!rows.length) {
    return `<div class="empty"><h3>${v4t('Nada coincide con esta selección', 'Nothing matches this selection')}</h3>${v4P('Sin resultados no significa ausencia de irregularidades. Puedes limpiar los filtros.', 'No results does not mean no irregularities. You can clear the filters.')}</div>`;
  }
  return rows.map((r) => `<article class="finding">
    <div class="meta-line"><span class="tag">${v4esc(v4GeoName(r.place))}</span><strong class="${r.severity === 'CRITICAL' ? 'red' : ''}">${r.severity === 'CRITICAL' ? `! ${v4t('Crítica', 'Critical')}` : v4t('Advertencia', 'Warning')}</strong></div>
    <h3>${v4esc(v4Rule(r.rule))}</h3>
    <p class="small">${v4esc(r.time ? v4Hn(r.time) : v4t('Hora no publicada', 'Time not published'))}</p>
    <p class="small">${v4t('Departamento no disponible todavía. Procedencia de la captura no disponible todavía.', 'Department not available yet. Capture provenance not available yet.')}</p>
    <p class="small">${v4t('Corroboración no disponible. Es una señal para revisar, no una prueba por sí sola.', 'Corroboration unavailable. A signal to review, not proof by itself.')}</p>
    <details><summary>${v4t('Ver contexto y límites', 'View context and limits')}</summary>
      ${v4P('Compara la fuente original cuando esté disponible. No inventamos el departamento ni la captura que faltan.', 'Compare the original source when it is available. We do not invent the missing department or capture.')}
      <p class="mono small">${v4esc(r.rule)}</p>
    </details>
  </article>`).join('');
}

function v4Filters() {
  return `<details id="filters"><summary>${v4t('Filtrar por lugar, prioridad y fecha', 'Filter by place, priority and date')}</summary>
    <div class="filters">
      <div><label for="place-filter">${v4t('Lugar del hallazgo', 'Finding location')}</label>
        <select id="place-filter"><option value="all">${v4t('Todos', 'All')}</option><option value="00">${v4t('Nacional', 'National')}</option>${OPS_V4_GEO.map((d) => `<option value="${d.code}">${d.name}</option>`).join('')}<option value="unknown">${v4t('Lugar no publicado', 'Place not published')}</option></select></div>
      <div><label for="severity-filter">${v4t('Prioridad de revisión', 'Review priority')}</label>
        <select id="severity-filter"><option value="all">${v4t('Todas', 'All')}</option><option value="CRITICAL">${v4t('Crítica', 'Critical')}</option><option value="WARNING">${v4t('Advertencia', 'Warning')}</option></select></div>
      <div><label for="from">${v4t('Desde · día, mes y año (hora Honduras)', 'From · day, month and year (Honduras time)')}</label>
        <input type="date" id="from" aria-describedby="from-echo date-error" value="${V4.from}"><small id="from-echo" class="small" aria-live="polite"></small></div>
      <div><label for="to">${v4t('Hasta · día, mes y año (hora Honduras)', 'To · day, month and year (Honduras time)')}</label>
        <input type="date" id="to" aria-describedby="to-echo date-error" value="${V4.to}"><small id="to-echo" class="small" aria-live="polite"></small></div>
    </div>
    <p id="date-error" class="error" hidden>${v4t('La fecha inicial debe ser anterior o igual a la final.', 'The start date must be before or equal to the end date.')}</p>
    <div class="actions">${v4Btn('Limpiar filtros', 'Clear filters', 'clear-filters', '', false, 'clear-filters')}</div>
  </details>`;
}

function v4Geo() {
  const map = V4.mapSvg || `<p class="note">${v4t('Mapa no disponible todavía. La lista sigue sirviendo para elegir un lugar.', 'Map not available yet. The list still works for choosing a place.')}</p>`;
  return `<details id="geography"><summary>${v4t('Explorar lugares · mapa y lista equivalentes', 'Explore places · equivalent map and list')}</summary>
    ${v4P('Lugares de la evidencia, no ubicación de observadores. Nacional es un ámbito separado. El archivo HN 2025 no trae departamento.', 'Evidence locations, not observer locations. National is a separate scope. The HN 2025 archive has no department.', 'small')}
    <p id="unknown-places" class="note"></p>
    <div class="geo-layout"><div class="map-wrap">${map}</div>
      <div class="table-wrap"><table><caption>${v4t('18 departamentos y ámbito nacional', '18 departments and national scope')}</caption>
        <thead><tr><th>${v4t('Lugar', 'Place')}</th><th>${v4t('Hallazgos', 'Findings')}</th></tr></thead>
        <tbody>${[{code:'00', name: v4t('Nacional', 'National')}, ...OPS_V4_GEO].map((d) => `<tr><th scope="row"><button type="button" data-place="${d.code}" aria-pressed="false">${d.name}</button></th><td data-count="${d.code}"></td></tr>`).join('')}</tbody>
      </table></div></div></details>`;
}

function v4Evidence() {
  const blocked = V4.rows == null;
  return `<div class="page-title"><div class="eyebrow">${v4t('Honduras', 'Honduras')}</div><h1 id="page-title" tabindex="-1">${v4t('Evidencia para revisar', 'Evidence to review')}</h1></div>
    ${v4P('Un hallazgo no demuestra por sí solo una irregularidad. Puede ser una corrección, un error de carga o una demora normal.', 'A finding does not by itself prove an irregularity. It may be a correction, an upload error or a normal delay.')}
    <div id="operation-status" class="status"></div>
    <div class="actions">${v4Btn('Descargar hallazgos', 'Download findings', 'jump-download')}${v4Btn('Filtrar hallazgos', 'Filter findings', 'jump-filters')}</div>
    <section class="card"><h2 id="result-count"></h2><p class="small" id="filter-summary"></p><div id="finding-list">${v4FindingList()}</div>
      ${v4Help('finding')}${v4Help('severity')}${v4Filters()}</section>
    ${v4Geo()}
    <section class="card"><h2 id="downloads-title" tabindex="-1">${v4t('Comprobar y descargar', 'Check and download')}</h2>
      ${v4P('Huella del archivo: no disponible todavía. Sello de fecha: sin recibo verificable.', 'File fingerprint: not available yet. Date stamp: no verifiable receipt.', 'note')}
      ${v4Help('fingerprint')}${v4Help('stamp')}${v4Help('chain')}
      <p id="download-unavailable" class="note" ${blocked ? '' : 'hidden'}>${v4t('Descarga no disponible: falta la lectura. Un archivo vacío no demostraría ausencia de hallazgos.', 'Download unavailable: no reading. An empty file would not prove absence of findings.')}</p>
      <p id="download-status" role="status" hidden></p>
      <div class="downloads">${v4Btn('Descargar selección · CSV', 'Download selection · CSV', 'csv', '', blocked)}${v4Btn('Descargar selección · JSON', 'Download selection · JSON', 'json', '', blocked)}${v4Btn('Descargar conjunto · ZIP', 'Download dataset · ZIP', 'zip', '', blocked)}</div>
      ${v4P('ZIP no aplica los filtros y lo dice en el manifiesto. No es evidencia certificada.', 'ZIP ignores filters and says so in the manifest. It is not certified evidence.', 'small')}
      ${v4Help('downloads')}</section>`;
}

function v4Room() {
  return `<div class="page-title"><div class="eyebrow">${v4t('Honduras', 'Honduras')}</div><h1 id="page-title" tabindex="-1">${v4t('Sala de observación', 'Observation room')}</h1></div>
    ${v4P('Puedes consultar evidencia sin entrar a una sala.', 'You can read evidence without joining a room.')}
    <div id="operation-status" class="status"></div>
    <div class="grid">
      <section class="card"><h2>${v4t(V4.room ? 'Sala indicada por el nodo' : 'Sin sala comprobada', V4.room ? 'Room reported by the node' : 'No verified room')}</h2>
        ${v4P('Computadoras observadas: no publicado. No mostramos identidades ni direcciones.', 'Observed computers: not published. No identities or addresses are shown.')}
        ${v4Help('room')}
        ${v4CanOperate()
          ? `<div class="actions">${v4Btn('Unirme a una sala', 'Join a room', 'join')}${v4Btn('Crear sala', 'Create room', 'create')}</div>${v4P('Crear o unir una sala real no está disponible todavía desde este panel. No pegues claves.', 'Creating or joining a real room is not available yet from this panel. Do not paste keys.', 'small')}`
          : v4P('Solo consulta. Unirse requiere un equipo autorizado.', 'View only. Joining requires an authorized computer.', 'note')}
      </section>
      <section class="card"><h2>${v4t('Corroboración no disponible', 'Corroboration unavailable')}</h2>
        ${v4P('No hay dato que certifique coincidencia entre equipos de una misma sala. Conectados no significa de acuerdo.', 'No data certifies matching observations from computers in the same room. Connected does not mean agreeing.')}
        ${v4Help('corroboration')}${v4Help('computer')}</section>
    </div>`;
}

function v4Controls() {
  const admin = v4CanAdmin();
  return `<div class="page-title"><div class="eyebrow">${v4t('Honduras', 'Honduras')}</div><h1 id="page-title" tabindex="-1">${v4t('Controles avanzados', 'Advanced controls')}</h1></div>
    ${v4P('Consultar no requiere claves. El rol sale de la clave con la que entraste; cambiarlo aquí no autoriza nada.', 'Reading requires no keys. The role comes from the key you used to sign in; changing it here authorizes nothing.', 'note')}
    <div id="operation-status" class="status"></div>
    <section class="card"><h2>${v4t('Fuente y captura', 'Source and capture')}</h2>
      ${v4P('Fuente: sitio del Consejo Nacional Electoral (CNE) · Honduras. Sin URL privada ni credenciales.', 'Source: National Electoral Council (CNE) website · Honduras. No private URL or credentials.')}
      ${v4CaptureBlock('capture-controls')}
      <details><summary>${v4t('Ritmo, reglas y recursos', 'Query rate, rules and resources')}</summary>
        ${v4P('Sin un nodo no hay una medición del ritmo. Las reglas experimentales no son una conclusión.', 'Without a node there is no rate measurement. Experimental rules are not a conclusion.')}
        ${v4Help('rate')}
        ${v4P('Edición técnica y límites firmados: no disponibles todavía en este panel.', 'Technical editing and signed limits: not available yet in this panel.', 'note')}
      </details>
    </section>
    ${admin ? `<section class="card"><h2>${v4t('Administración', 'Administration')}</h2>
      <div class="option"><h3>${v4t('Cambiar claves', 'Replace keys')}</h3>
        ${v4P('No recogemos ni mostramos claves. Regenerar claves abre el workflow del repositorio. La clave nueva sale una sola vez en el artefacto, no en esta página.', 'We do not collect or display keys. Regenerar claves opens the repository workflow. The new key appears once in the artifact, not on this page.')}
        <p><a id="btn-regen" href="https://github.com/VectisDev/Vigil/actions/workflows/regenerate-seeds.yml">Regenerar claves</a></p>
      </div>
    </section>
    <section class="card critical"><h2 class="red">${v4t('Destrucción local', 'Local destruction')}</h2>
      ${v4P('Solo este equipo. No modifica evidencia publicada ni sellos existentes. No elimina copias externas ni garantiza un borrado forense.', 'This computer only. Published evidence and existing stamps are not changed. External copies are not deleted and forensic erasure is not guaranteed.')}
      ${v4Btn('Destruir datos locales', 'Destroy local data', 'destroy', 'danger', false, 'destroy-open')}
      ${v4P('La destrucción real no está disponible todavía. Confirmar no borra archivos.', 'Real destruction is not available yet. Confirming does not delete files.', 'small')}
    </section>` : v4P('Administración y destrucción no disponibles para este rol.', 'Administration and destruction are unavailable for this role.', 'note')}`;
}

function v4Fill(tab) {
  const root = document.querySelector(`#main-area > [data-tab="${tab}"]`);
  if (!root) return;
  const html = { inicio: v4Home, evidencia: v4Evidence, red: v4Room, avanzado: v4Controls }[tab];
  if (html) root.innerHTML = html();
  if (tab === 'evidencia') v4UpdateEvidence(false);
  const status = root.querySelector('#operation-status');
  if (status && tab !== 'inicio') {
    const head = document.getElementById('hero-headline');
    status.textContent = head && head.textContent
      ? head.textContent
      : (v4Pages()
        ? v4t('Sin nodo de control. Puede seguir habiendo actividad en el equipo.', 'No control node. The computer may still be active.')
        : v4t('Estado del nodo en la barra de inicio.', 'Node status is on Home.'));
  }
}

function v4UpdateEvidence(announce) {
  if (!v4$('#finding-list')) return;
  ['from', 'to'].forEach((id) => {
    const echo = document.getElementById(`${id}-echo`);
    const input = document.getElementById(id);
    if (echo && input) echo.textContent = `${v4t('Elegida: ', 'Selected: ')}${v4InputDay(input.value)}`;
  });
  const invalid = !!v4BadDates();
  const err = v4$('#date-error');
  if (err) err.hidden = !invalid;
  ['from', 'to'].forEach((id) => v4$(`#${id}`)?.setAttribute('aria-invalid', String(invalid)));
  const placeSel = v4$('#place-filter');
  if (placeSel) placeSel.value = V4.dept;
  const sevSel = v4$('#severity-filter');
  if (sevSel) sevSel.value = V4.severity;
  const blocked = V4.rows == null;
  const rows = v4Filtered();
  const count = v4$('#result-count');
  if (count) {
    count.textContent = invalid
      ? v4t('Revisa las fechas', 'Review the dates')
      : blocked
        ? v4t('Cantidad no disponible', 'Count unavailable')
        : `${rows.length} ${v4t('hallazgos en la selección', 'findings in selection')}`;
  }
  const summary = v4$('#filter-summary');
  if (summary) {
    summary.textContent = `${V4.dept === 'all' ? v4t('Todos los lugares', 'All places') : v4GeoName(V4.dept === 'unknown' ? null : V4.dept)} · ${v4t('Fechas en hora Honduras', 'Dates in Honduras time')}`;
  }
  v4$('#finding-list').innerHTML = v4FindingList();
  const unknown = (V4.rows || []).filter((r) => !r.place).length;
  const note = v4$('#unknown-places');
  if (note) {
    note.textContent = blocked
      ? v4t('Cantidad de lugares desconocida: falta la lectura.', 'Place count unknown: no reading.')
      : `${unknown} ${v4t('hallazgos sin lugar publicado. No se asignan a Nacional ni al mapa.', 'findings without a published place. Not assigned to National or the map.')}`;
  }
  v4$$('[data-count]').forEach((el) => {
    el.textContent = blocked ? v4t('Sin dato', 'Unknown') : String(v4Filtered(true).filter((r) => r.place === el.dataset.count).length);
  });
  v4$$('[data-place]').forEach((el) => {
    const on = el.dataset.place === V4.dept;
    el.setAttribute('aria-pressed', String(on));
    el.classList.toggle('selected', on);
  });
  const unavail = v4$('#download-unavailable');
  if (unavail) unavail.hidden = !blocked;
  v4$$('[data-action=csv],[data-action=json],[data-action=zip]').forEach((b) => { b.disabled = blocked; });
  if (announce && count && summary) {
    const live = v4$('#announcement');
    if (live) live.textContent = `${count.textContent} · ${summary.textContent}`;
  }
}

function v4EmergencyAccess() {
  const slot = v4$('#emergency-access');
  if (!slot) return;
  if (!v4CanOperate()) { slot.hidden = true; slot.innerHTML = ''; return; }
  slot.hidden = false;
  slot.innerHTML = `${v4Btn('Parar VIGIL ahora', 'Stop VIGIL now', 'emergency', 'danger', false, 'emergency-button')}<p><strong>${v4t('Solo este equipo', 'This computer only')}</strong><br>${v4t('No disponible todavía', 'Not available yet')}</p>`;
}

function v4NavLabels() {
  const labels = {
    inicio: v4t('Inicio', 'Home'),
    evidencia: v4t('Evidencia', 'Evidence'),
    red: `${v4t('Sala', 'Room')}<small>${v4t('observadores conectados', 'connected observers')}</small>`,
    avanzado: v4t('Controles', 'Controls'),
  };
  v4$$('[data-tab-btn]').forEach((b) => {
    const id = b.getAttribute('data-tab-btn');
    if (labels[id]) b.innerHTML = labels[id];
  });
  const lang = v4$('#lang-toggle');
  if (lang) {
    lang.textContent = v4t('EN', 'ES');
    lang.setAttribute('aria-label', v4t('Cambiar a inglés', 'Switch to Spanish'));
  }
  const cover = v4$('#screen-cover');
  if (cover) cover.textContent = v4t('Ocultar pantalla', 'Hide screen');
  const foot = v4$('#ops-footer');
  if (foot) {
    foot.textContent = v4t(
      'Panel v4 · blanco, rojo y negro. Parada de emergencia, destrucción local, departamento y procedencia de las alertas: no disponibles todavía. 8 nov 2026, hora Honduras.',
      'Panel v4 · white, red and black. Emergency stop, local destruction, department and alert provenance: not available yet. 8 Nov 2026, Honduras time.');
  }
}

function v4Render(tab) {
  V4.helpOpen = null;
  document.documentElement.lang = V4.lang;
  window.OPS_LANG = V4.lang;
  v4Banner();
  v4EmergencyAccess();
  v4NavLabels();
  const current = tab || document.documentElement.getAttribute('data-ops-tab') || 'inicio';
  v4Fill(current);
  if (typeof renderOverallState === 'function') renderOverallState();
}

function v4OpenSheet(kind, trigger) {
  if (['pause', 'resume', 'emergency', 'destroy', 'keys', 'join', 'create'].includes(kind) && !v4CanOperate()) return;
  if (['destroy', 'keys'].includes(kind) && !v4CanAdmin()) return;
  V4.returnFocus = trigger && trigger.isConnected ? trigger : document.activeElement;
  V4.pending = kind;
  V4.focusAfterClose = null;
  let heading = '';
  let body = '';
  let confirm = '';
  let danger = false;
  if (kind === 'pause' || kind === 'resume') {
    const resume = kind === 'resume';
    heading = v4t(resume ? '¿Reanudar la captura?' : '¿Pausar la captura?', resume ? 'Resume capture?' : 'Pause capture?');
    body = v4Pages()
      ? v4P('No disponible todavía: esta página no tiene un nodo al que pedir la pausa o la reanudación. Confirmar no cambia nada.', 'Not available yet: this page has no node to ask for pause or resume. Confirming changes nothing.')
      : v4P(resume
        ? 'Se pedirá al nodo que inicie de nuevo. No recupera un proceso suspendido. Un HTTP de aceptación no comprueba que la captura haya empezado.'
        : 'Se pedirá al nodo que detenga solo la captura. No borra lo guardado. Un HTTP de aceptación no comprueba que los procesos hayan terminado.',
        resume
        ? 'The node will be asked to start again. It does not recover a suspended process. An acceptance response does not prove capture started.'
        : 'The node will be asked to stop capture alone. Saved data is not deleted. An acceptance response does not prove processes have ended.');
    confirm = v4t(resume ? 'Reanudar captura' : 'Pausar captura', resume ? 'Resume capture' : 'Pause capture');
  }
  if (kind === 'emergency') {
    heading = v4t('Parar VIGIL ahora', 'Stop VIGIL now');
    danger = true;
    body = v4P('Solo este equipo: la computadora que ejecuta VIGIL, no el teléfono desde el que miras ni los demás equipos.', 'This computer only: the machine running VIGIL, not the phone you are looking from or other computers.')
      + v4P('No disponible todavía. No hay un supervisor que pare procesos, hijos, red y reinicios. Confirmar no para nada y no borra datos.', 'Not available yet. There is no supervisor that stops processes, children, network and restarts. Confirming stops nothing and deletes nothing.', 'note');
    confirm = v4t('Confirmar parada', 'Confirm stop');
  }
  if (kind === 'destroy') {
    heading = v4t('Destruir datos locales', 'Destroy local data');
    danger = true;
    body = v4P('Solo este equipo. No modifica evidencia publicada ni sus sellos. No elimina copias externas ni garantiza un borrado forense.', 'This computer only. Published evidence and stamps are not modified. External copies are not deleted and forensic erasure is not guaranteed.')
      + v4P('No disponible todavía. Confirmar no borra archivos, credenciales ni almacenamiento.', 'Not available yet. Confirming does not delete files, credentials or storage.', 'note')
      + `<label for="destroy-word">${v4t('Escribe DESTRUIR para continuar', 'Type DESTRUIR to continue')}</label><input id="destroy-word" type="text" autocomplete="off" autocapitalize="characters" spellcheck="false" aria-describedby="destroy-note"><p id="destroy-note" class="small">${v4t('La palabra es DESTRUIR. Es una barrera de intención, no una autenticación. Enter en este campo no confirma.', 'The word is DESTRUIR. This is an intent barrier, not authentication. Enter in this field does not confirm.')}</p>`;
    confirm = v4t('Destruir datos locales', 'Destroy local data');
  }
  if (kind === 'keys' || kind === 'join' || kind === 'create') {
    heading = v4t('No disponible todavía', 'Not available yet');
    body = v4P('Esta operación no está disponible todavía en el panel. No se envió nada y no se mostró ningún secreto.', 'This operation is not available yet in the panel. Nothing was sent and no secret was shown.');
    confirm = v4t('Entendido', 'Understood');
  }
  const sheet = v4$('#sheet');
  if (!sheet || !heading) return;
  v4$('#sheet-content').innerHTML = `<div class="eyebrow">${v4t('Solo este equipo', 'This computer only')}</div><h2 id="sheet-title" tabindex="-1">${heading}</h2>${body}<div class="actions cancel"><button type="button" id="sheet-cancel" data-action="cancel">${v4t('Cancelar', 'Cancel')}</button><button type="button" id="sheet-confirm" data-action="confirm" class="${danger ? 'solid' : 'primary'}" ${kind === 'destroy' ? 'disabled' : ''}>${confirm}</button></div>`;
  if (typeof sheet.showModal === 'function') sheet.showModal();
  else sheet.setAttribute('open', '');
  v4$('#sheet-cancel')?.focus();
}

function v4CloseSheet(afterId) {
  V4.pending = null;
  V4.focusAfterClose = afterId || null;
  const sheet = v4$('#sheet');
  if (sheet && sheet.open && typeof sheet.close === 'function') sheet.close();
  else sheet?.removeAttribute('open');
}

async function v4AskNode(path) {
  if (v4Pages() || typeof opsApi !== 'function') return { ok: false, unavailable: true };
  try {
    const r = await opsApi(path, { method: 'POST' });
    if (r && r.ok) return { ok: true };
    return { ok: false };
  } catch (e) {
    if (e && e.opsOffline) return { ok: false, unavailable: true };
    return { ok: false };
  }
}

async function v4ConfirmSheet() {
  const kind = V4.pending;
  if (!kind) return;
  if (kind === 'destroy' && v4$('#destroy-word')?.value !== 'DESTRUIR') return;
  if (kind === 'keys' || kind === 'join' || kind === 'create') {
    v4CloseSheet('page-title');
    const live = v4$('#announcement');
    if (live) live.textContent = v4t('No disponible todavía. No se envió la operación.', 'Not available yet. The operation was not sent.');
    return;
  }
  if (kind === 'emergency' || kind === 'destroy') {
    v4CloseSheet(kind === 'emergency' ? 'emergency-button' : 'destroy-open');
    const live = v4$('#announcement');
    const msg = kind === 'destroy'
      ? v4t('No disponible todavía. No se borró ningún archivo.', 'Not available yet. No file was deleted.')
      : v4t('No disponible todavía. VIGIL no se detuvo.', 'Not available yet. VIGIL did not stop.');
    if (live) live.textContent = msg;
    const status = document.createElement('div');
    status.className = 'status attention';
    status.setAttribute('role', 'status');
    status.textContent = msg;
    v4$('#main-area > [data-tab]:not([hidden])')?.prepend(status);
    return;
  }
  if (kind === 'pause' || kind === 'resume') {
    const result = await v4AskNode(kind === 'pause' ? '/api/pipeline/stop' : '/api/pipeline/start');
    if (!result.ok) {
      v4CloseSheet('capture-button');
      const msg = v4t('No disponible todavía. La captura no cambió.', 'Not available yet. Capture did not change.');
      const live = v4$('#announcement');
      if (live) live.textContent = msg;
      return;
    }
    V4.capture = kind === 'pause' ? 'paused' : 'active';
    V4.captureKnown = true;
    window._opsPipelineState = Object.assign({}, window._opsPipelineState || {}, { running: kind === 'resume' });
    v4Render(document.documentElement.getAttribute('data-ops-tab') || 'inicio');
    v4CloseSheet('capture-button');
    const live = v4$('#announcement');
    if (live) {
      live.textContent = kind === 'pause'
        ? v4t('El nodo aceptó la orden de pausar. No comprobamos que los procesos hayan terminado.', 'The node accepted the pause order. We did not check that processes have ended.')
        : v4t('El nodo aceptó la orden de reanudar. No comprobamos que la captura haya empezado.', 'The node accepted the resume order. We did not check that capture has started.');
    }
  }
}

function v4SelectPlace(code) {
  V4.dept = V4.dept === code ? 'all' : code;
  const sel = v4$('#place-filter');
  if (sel) sel.value = V4.dept;
  v4UpdateEvidence(true);
}

function v4Save(name, content, type) {
  const blob = content instanceof Blob ? content : new Blob([content], { type });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function v4Csv(rows) {
  const fields = ['departamento', 'department_code', 'regla', 'severidad', 'hora_honduras', 'timestamp', 'mensaje'];
  const q = (x) => {
    let v = x == null ? '' : String(x);
    if (/^[=+\-@\t\r]/.test(v)) v = `'${v}`;
    return `"${v.replace(/"/g, '""')}"`;
  };
  const lines = [fields.join(',')].concat(rows.map((r) => [
    v4GeoName(r.place), r.place, r.rule, r.severity, r.time ? v4Hn(r.time) : '', r.time, r.message,
  ].map(q).join(',')));
  return `\ufeff${lines.join('\r\n')}\r\n`;
}

async function v4Sha(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
function v4Crc(bytes) {
  let c = 0xffffffff;
  for (const b of bytes) {
    c ^= b;
    for (let k = 0; k < 8; k += 1) c = (c >>> 1) ^ ((c & 1) ? 0xedb88320 : 0);
  }
  return (c ^ 0xffffffff) >>> 0;
}
function v4Zip(files) {
  const enc = new TextEncoder();
  const chunks = [];
  const central = [];
  let off = 0;
  files.forEach((f) => {
    const name = enc.encode(f.name);
    const b = enc.encode(f.text);
    const crc = v4Crc(b);
    const local = new Uint8Array(30 + name.length + b.length);
    const v = new DataView(local.buffer);
    v.setUint32(0, 0x04034b50, true);
    v.setUint16(4, 20, true);
    v.setUint16(8, 0, true);
    v.setUint32(14, crc, true);
    v.setUint32(18, b.length, true);
    v.setUint32(22, b.length, true);
    v.setUint16(26, name.length, true);
    local.set(name, 30);
    local.set(b, 30 + name.length);
    chunks.push(local);
    const cd = new Uint8Array(46 + name.length);
    const d = new DataView(cd.buffer);
    d.setUint32(0, 0x02014b50, true);
    d.setUint16(4, 20, true);
    d.setUint16(6, 20, true);
    d.setUint32(16, crc, true);
    d.setUint32(20, b.length, true);
    d.setUint32(24, b.length, true);
    d.setUint16(28, name.length, true);
    d.setUint32(42, off, true);
    cd.set(name, 46);
    central.push(cd);
    off += local.length;
  });
  const clen = central.reduce((n, x) => n + x.length, 0);
  const end = new Uint8Array(22);
  const e = new DataView(end.buffer);
  e.setUint32(0, 0x06054b50, true);
  e.setUint16(8, files.length, true);
  e.setUint16(10, files.length, true);
  e.setUint32(12, clen, true);
  e.setUint32(16, off, true);
  return new Blob([...chunks, ...central, end], { type: 'application/zip' });
}

async function v4Download(format) {
  const status = v4$('#download-status');
  if (V4.rows == null) {
    if (status) {
      status.hidden = false;
      status.className = 'error';
      status.textContent = v4t('Descarga no disponible: falta la lectura.', 'Download unavailable: no reading.');
    }
    return;
  }
  if (format !== 'zip' && v4BadDates()) {
    const filters = v4$('#filters');
    if (filters) filters.open = true;
    v4$('#from')?.focus();
    return;
  }
  try {
    const rows = format === 'zip' ? (V4.rows || []) : v4Filtered();
    if (format === 'csv') v4Save('vigil-seleccion.csv', v4Csv(rows), 'text/csv;charset=utf-8');
    else if (format === 'json') {
      v4Save('vigil-seleccion.json', JSON.stringify({
        filters_applied: true,
        department_available: false,
        provenance_available: false,
        rows,
      }, null, 2), 'application/json');
    } else {
      const findings = JSON.stringify({ filters_applied: false, rows: V4.rows }, null, 2);
      const note = 'Dataset only. Filters not applied. Department and provenance are not in the source file. Not certified custody.\n';
      const entries = [
        { name: 'findings.json', text: findings },
        { name: 'README.txt', text: note },
      ];
      const listed = [];
      for (const f of entries) {
        listed.push({ path: f.name, bytes: new TextEncoder().encode(f.text).length, sha256: await v4Sha(f.text) });
      }
      entries.push({ name: 'manifest.json', text: JSON.stringify({ count: (V4.rows || []).length, filters_applied: false, files: listed }, null, 2) });
      v4Save('vigil-conjunto.zip', v4Zip(entries), 'application/zip');
    }
    if (status) {
      status.hidden = false;
      status.className = '';
      status.textContent = v4t('Archivo preparado en este navegador. Comprueba la carpeta de descargas. No es una verificación de custodia.', 'File prepared in this browser. Check your downloads folder. This is not a custody verification.');
    }
  } catch (e) {
    if (status) {
      status.hidden = false;
      status.className = 'error';
      status.textContent = v4t('No se pudo preparar la descarga. Vuelve a intentarlo; no se entregó un archivo verificado.', 'Could not prepare the download. Try again; no verified file was delivered.');
    }
  }
}

function v4CloseHelp() {
  if (!V4.helpOpen) return;
  const id = V4.helpOpen;
  v4$(`#help-${id}`)?.setAttribute('aria-expanded', 'false');
  const panel = v4$(`#help-panel-${id}`);
  if (panel) panel.hidden = true;
  V4.helpOpen = null;
  return id;
}

function v4OnClick(e) {
  if (!e.target.closest || !e.target.closest('#admin-shell')) return;
  const helpButton = e.target.closest('[data-help]');
  if (helpButton) {
    const id = helpButton.dataset.help;
    const was = V4.helpOpen === id;
    v4CloseHelp();
    if (!was) {
      V4.helpOpen = id;
      helpButton.setAttribute('aria-expanded', 'true');
      const panel = v4$(`#help-panel-${id}`);
      if (panel) panel.hidden = false;
    }
    return;
  }
  if (V4.helpOpen && !e.target.closest('.help-unit')) v4CloseHelp();
  const place = e.target.closest('[data-place]');
  if (place) { v4SelectPlace(place.dataset.place); return; }
  const b = e.target.closest('[data-action]');
  if (!b || b.disabled) return;
  const action = b.dataset.action;
  if (action.startsWith('nav-')) { if (typeof goTab === 'function') goTab(action.slice(4)); return; }
  if (action === 'cancel') { v4CloseSheet(); return; }
  if (action === 'confirm') { v4ConfirmSheet(); return; }
  if (action === 'jump-download') { v4$('#downloads-title')?.focus(); return; }
  if (action === 'jump-filters') {
    const filters = v4$('#filters');
    if (filters) filters.open = true;
    v4$('#place-filter')?.focus();
    return;
  }
  if (action === 'clear-filters') {
    V4.dept = 'all'; V4.severity = 'all'; V4.from = ''; V4.to = '';
    ['place-filter', 'severity-filter', 'from', 'to'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = id === 'place-filter' || id === 'severity-filter' ? 'all' : '';
    });
    v4UpdateEvidence(true);
    return;
  }
  if (action === 'csv' || action === 'json' || action === 'zip') { v4Download(action); return; }
  if (action === 'pause' || action === 'resume' || action === 'emergency' || action === 'destroy' || action === 'keys' || action === 'join' || action === 'create') {
    v4OpenSheet(action, b);
  }
}

function v4OnChange(e) {
  const id = e.target.id;
  if (id === 'place-filter') V4.dept = e.target.value;
  else if (id === 'severity-filter') V4.severity = e.target.value;
  else if (id === 'from') V4.from = e.target.value;
  else if (id === 'to') V4.to = e.target.value;
  else return;
  v4UpdateEvidence(true);
  if (e.target && e.target.focus) e.target.focus();
}
function v4OnInput(e) {
  if (e.target.id === 'destroy-word') {
    const confirm = v4$('#sheet-confirm');
    if (confirm) confirm.disabled = e.target.value !== 'DESTRUIR';
  }
}
function v4OnKey(e) {
  if (e.key === 'Escape' && V4.helpOpen) {
    const id = v4CloseHelp();
    v4$(`#help-${id}`)?.focus();
    e.preventDefault();
  }
  const place = e.target.closest && e.target.closest('path[data-place]');
  if (place && (e.key === 'Enter' || e.key === ' ')) {
    e.preventDefault();
    v4SelectPlace(place.dataset.place);
  }
  if (e.target.id === 'destroy-word' && e.key === 'Enter') e.preventDefault();
}

function v4FocusReturn() {
  const target = V4.focusAfterClose
    ? document.getElementById(V4.focusAfterClose)
    : (V4.returnFocus && V4.returnFocus.isConnected && !V4.returnFocus.disabled ? V4.returnFocus : document.getElementById('hero-headline'));
  (target || document.getElementById('hero-headline'))?.focus();
  V4.focusAfterClose = null;
  V4.pending = null;
}

function v4Cover() {
  const c = v4$('#cover');
  if (!c) return;
  c.innerHTML = `<h1 id="cover-title">${v4t('Pantalla oculta', 'Screen hidden')}</h1>${v4P('No bloquea el equipo ni borra el historial.', 'Does not lock the computer or erase history.')}${v4Btn('Volver al panel', 'Return to the panel', 'uncover', 'primary', false, 'cover-return')}`;
  c.hidden = false;
  const skip = v4$('#skip');
  const mast = document.querySelector('.mast');
  const wrap = document.querySelector('.wrap');
  if (skip) skip.inert = true;
  if (mast) mast.inert = true;
  if (wrap) wrap.inert = true;
  const back = v4$('#cover-return');
  if (back) {
    back.focus();
    back.onclick = () => {
      c.hidden = true;
      if (skip) skip.inert = false;
      if (mast) mast.inert = false;
      if (wrap) wrap.inert = false;
      v4$('#screen-cover')?.focus();
    };
  }
}

async function opsV4Start() {
  V4.lang = (localStorage.getItem('vigil-lang') === 'en') ? 'en' : 'es';
  window.OPS_LANG = V4.lang;
  await Promise.all([v4LoadAlerts(), v4LoadMap()]);
  if (!v4Pages() && typeof opsApi === 'function') {
    try {
      const r = await opsApi('/api/pipeline/status');
      if (r && r.ok) {
        const d = await r.json();
        V4.capture = d.running ? 'active' : 'paused';
        V4.captureKnown = true;
        window._opsPipelineState = { running: !!d.running };
      }
    } catch (_) { /* sin nodo: la captura no se afirma */ }
  }
  v4Render();
}
window.opsV4Start = opsV4Start;
window.opsV4OnTab = function (tab) { v4Render(tab); };

document.addEventListener('click', v4OnClick);
document.addEventListener('change', v4OnChange);
document.addEventListener('input', v4OnInput);
document.addEventListener('keydown', v4OnKey);
document.addEventListener('DOMContentLoaded', () => {
  const sheet = document.getElementById('sheet');
  if (sheet) {
    sheet.addEventListener('close', v4FocusReturn);
    sheet.addEventListener('cancel', () => { V4.pending = null; V4.focusAfterClose = null; });
    sheet.addEventListener('keydown', (ev) => {
      if (ev.target && ev.target.id === 'destroy-word' && ev.key === 'Enter') {
        ev.preventDefault();
        ev.stopPropagation();
      }
    });
  }
  document.getElementById('lang-toggle')?.addEventListener('click', () => {
    V4.lang = V4.lang === 'es' ? 'en' : 'es';
    localStorage.setItem('vigil-lang', V4.lang);
    window.OPS_LANG = V4.lang;
    v4Render();
    document.getElementById('lang-toggle')?.focus();
  });
  document.getElementById('screen-cover')?.addEventListener('click', v4Cover);
});
