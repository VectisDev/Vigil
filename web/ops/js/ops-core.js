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
  const pat = sessionStorage.getItem('gh-pat');
  const headers = pat ? {Authorization:`Bearer ${pat}`} : {};
  try{
    const r = await fetch(`${API_BASE}/contents/${path}`,{headers});
    if(!r.ok) return;
    const j = await r.json();
    configShas[path] = j.sha;
  }catch(e){console.warn('fetchSha',path,e);}
}

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
    const age = snapshotData?.timestamp ? relTime(snapshotData.timestamp) : '—';
    document.getElementById('snap-age').textContent = `actualizado ${age}`;
  }catch(e){console.warn('loadSnapshot',e);}
}

// ══════════════════════════════════════════════════════════
// SENSOR CARDS
// ══════════════════════════════════════════════════════════
const CARD_DEFS = [
  {id:'sha',    label:'Cadena SHA-256',      icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'},
  {id:'cb',     label:'Circuit Breaker',     icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'},
  {id:'animal', label:'Animal Mode',         icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'},
  {id:'benford',label:'Benford 1er dígito',  icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>', hasSlider:'benford', min:3, max:15, step:0.1},
  {id:'zscore', label:'Z-Score máximo',      icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>', hasSlider:'zscore',  min:1.5,max:5,step:0.1},
  {id:'ots',    label:'OTS Bitcoin',         icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'},
  {id:'cpu',    label:'CPU Watchdog',        icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>', hasSlider:'cpu',     min:50,max:95,step:1},
  {id:'ram',    label:'Memoria',             icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>', hasSlider:'ram',     min:50,max:95,step:1},
  {id:'attacks',label:'Ataques detectados',  icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'},
  {id:'endpoints',label:'Endpoints activos', icon:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'},
];

function buildSensorCards(){
  const grid = document.getElementById('sensor-cards');
  if(!grid) return;
  grid.innerHTML = CARD_DEFS.map(def=>`
    <div class="stat-card" id="sc-${def.id}">
      <div class="sc-label">
        <span>${def.icon} ${def.label}</span>
        ${def.hasSlider?`<span data-tip="Umbral — sincronizado con Configuración avanzada" style="font-size:10px;cursor:help">ⓘ</span>`:''}
      </div>
      <div class="sc-val val-neutral skel-pulse" id="scv-${def.id}">—</div>
      <div class="sc-detail skel-pulse" id="scd-${def.id}">—</div>
      <div class="sc-bar"><div class="sc-bar-fill" id="scb-${def.id}" style="width:0%;background:var(--muted)"></div></div>
      ${def.hasSlider?`
      <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
        <input type="range" min="${def.min}" max="${def.max}" step="${def.step}" value="${def.min}"
          id="sc-sl-${def.hasSlider}" style="flex:1;accent-color:var(--accent);cursor:pointer;height:4px"
          oninput="syncSlider('${def.hasSlider}',this.value)">
        <span class="val-badge" id="sc-vb-${def.hasSlider}" style="font-size:10px">—</span>
      </div>`:''}
      <div class="sc-age" id="sca-${def.id}"></div>
    </div>
  `).join('');
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
    setCard('sha', 'sin datos', 'Pipeline aún no ha ejecutado', 0, 'neutral', false);
  } else {
    setCard('sha', hashOk?'ÍNTEGRA':'ROTA', hashStr, hashOk?100:0, hashOk?'ok':'bad');
  }

  // Circuit Breaker
  const cbOpen = cne.consecutive_failures >= 3;
  const cbFail = cne.consecutive_failures || 0;
  setCard('cb', cbOpen?'ABIERTO':'CERRADO', `${cbFail} fallos consecutivos`, cbOpen?100:0, cbOpen?'bad':'ok');

  // Animal mode
  const animal = ep?.healing?.animal_mode || 'normal';
  const animalCls = {normal:'ok', caution:'warn', survival:'bad'}[animal]||'neutral';
  setCard('animal', animal.toUpperCase(), '', 0, animalCls, false);

  // OTS
  const ots = chain.ots_status || 'unknown';
  const otsCls   = {confirmed:'ok',pending:'warn',error:'bad'}[ots]||'neutral';
  const otsLabel = {confirmed:'CONFIRMADO',pending:'PENDIENTE',error:'ERROR'}[ots]||'DESCONOCIDO';
  setCard('ots', otsLabel, chain.last_anchor ? `Último: ${relTime(chain.last_anchor)}` : '', 0, otsCls, false);

  // Attacks
  const alerts = s?.alerts || [];
  const critical = alerts.filter(a=>a.level==='CRITICAL').length;
  const warnings = alerts.filter(a=>a.level==='WARNING').length;
  setCard('attacks', alerts.length+' eventos', `${warnings} WARNING · ${critical} CRITICAL`, critical>0?100:warnings>0?50:0, critical>0?'bad':warnings>0?'warn':'ok');

  // Endpoints — distinguish "no pipeline data yet" from "active failures"
  const epsRaw = s?.endpoints_status;
  const hasEpData = epsRaw && (Array.isArray(epsRaw) ? epsRaw.length > 0 : Object.keys(epsRaw).length > 0);
  const eps = hasEpData ? Object.values(epsRaw) : [];
  const okEps = eps.filter(e=>e.ok).length;
  const total = Math.max(1, DEPTS.length - 1);
  if(!hasEpData){
    setCard('endpoints', 'sin datos', 'Pipeline aún no ha ejecutado', 0, 'neutral', false);
  } else {
    setCard('endpoints', `${okEps}/${total}`, `${total-okEps} fallando`, okEps/total*100, okEps===total?'ok':okEps>total*0.8?'warn':'bad');
  }

  // CPU/RAM — use watchdog limits as context
  const cpuLimit = wd?.max_cpu_percent || 80;
  const ramLimit = wd?.max_mem_percent || 90;
  // synthetic values (real values would come from a health endpoint)
  setCard('cpu', cpuLimit+'% límite', 'Dato en tiempo real no disponible en Pages', 0, 'neutral', false);
  setCard('ram', ramLimit+'% límite', 'Dato en tiempo real no disponible en Pages', 0, 'neutral', false);
}

function setCard(id, val, detail, barPct, cls, showBar=true){
  const el = v=>document.getElementById(v);
  const clsMap = {ok:'val-ok',warn:'val-warn',bad:'val-bad',neutral:'val-neutral'};
  if(el(`scv-${id}`)){
    el(`scv-${id}`).textContent = val;
    el(`scv-${id}`).className = `sc-val ${clsMap[cls]||'val-neutral'}`;
  }
  if(el(`scd-${id}`)) el(`scd-${id}`).textContent = detail;
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
  const grid = document.getElementById('dept-ep-grid');
  if(!grid) return;
  grid.innerHTML = '';

  // Defensive: DEPTS should always have entries (fallback list guarantees it)
  if(!DEPTS || DEPTS.length === 0){
    grid.innerHTML = '<div style="grid-column:1/-1;font-size:12px;color:var(--muted);padding:12px 0">Cargando departamentos…</div>';
    return;
  }

  // Update section label with live count
  const lbl = document.getElementById('dept-section-label');
  const divCount = DEPTS.filter(d => d.code !== '00').length;
  const divLabel = COUNTRY_META?.divisions_label || 'Divisiones';
  if (lbl) lbl.textContent = `${divLabel} — ${divCount + 1} endpoints (1 nacional + ${divCount})`;

  // NACIONAL card first
  const natCard = document.createElement('div');
  natCard.className = 'dep-card dep-national';
  natCard.style.gridColumn = '1 / -1';
  natCard.innerHTML = `<div class="dep-abbr" style="font-size:10px">00 · NACIONAL</div><div class="dep-dot" style="background:var(--accent)"></div>`;
  natCard.onclick = () => openMapPopup('00');
  grid.appendChild(natCard);

  DEPTS.filter(d => d.code !== '00').forEach(dept => {
    const abbr = dept.abbr || dept.name.slice(0,2).toUpperCase();
    const card = document.createElement('div');
    card.className = 'dep-card';
    card.id = `dep-card-${dept.code}`;
    card.title = dept.name + ' (' + dept.code + ')';
    card.innerHTML = `<div class="dep-abbr">${abbr}</div><div class="dep-dot" id="dep-dot-${dept.code}" style="background:#3a3f49"></div>`;
    card.onclick = () => openMapPopup(dept.code);
    grid.appendChild(card);
  });
}
function getEndpointUrl(code){
  const ep = localConfig['config/prod/endpoints.yaml']?.cne?.presidential_endpoints || [];
  return ep.find(e => (e.department_code||'').toString().padStart(2,'0') === code)?.url || '';
}

function updateDeptGrid(){
  if(!snapshotData) return;
  const epsRaw = snapshotData?.endpoints_status;
  const hasPipelineData = epsRaw && (Array.isArray(epsRaw) ? epsRaw.length > 0 : Object.keys(epsRaw).length > 0);
  const eps = hasPipelineData && !Array.isArray(epsRaw) ? epsRaw : {};
  const epCfg = localConfig['config/prod/endpoints.yaml'] || {};
  const configured = (epCfg?.cne?.presidential_endpoints || [])
    .map(e => (e.department_code || '').toString().padStart(2,'0'));

  DEPTS.filter(d => d.code !== '00').forEach(dept => {
    const card = document.getElementById(`dep-card-${dept.code}`);
    const dot  = document.getElementById(`dep-dot-${dept.code}`);
    if(!card || !dot) return;
    const epStatus = eps[dept.code];
    let color = '#3a3f49', cls = '';
    if(configured.includes(dept.code)){
      if(!hasPipelineData){
        // Pipeline hasn't run yet — show neutral grey, not warning
        color = '#3a3f49'; cls = '';
      } else if(epStatus?.ok){ color='#57c08d'; cls='dep-ok'; }
      else if(epStatus && (epStatus.failures||0)>0){ color='#df6b86'; cls='dep-bad'; }
      else { color='#d4b066'; cls='dep-warn'; }
    }
    dot.style.background = color;
    card.className = 'dep-card' + (cls ? ' ' + cls : '');
  });
}
function updateStatusBadges(){
  const ep = localConfig['config/prod/endpoints.yaml'] || {};
  const animal = ep?.healing?.animal_mode || 'normal';
  const safe   = ep?.healing?.safe_mode_active || false;
  const cne    = snapshotData?.cne_status || {};
  const cbOpen = (cne.consecutive_failures||0) >= 3;

  const bAnimal = document.getElementById('badge-animal');
  if(bAnimal){
    const cls = {normal:'ok', caution:'warn', survival:'bad'}[animal]||'neutral';
    bAnimal.className = `badge badge-${cls}`;
    bAnimal.textContent = `DEFENSAS: ${animal.toUpperCase()}`;
  }
  const bSafe = document.getElementById('badge-safemode');
  if(bSafe){
    bSafe.className = `badge badge-${safe?'warn':'neutral'}`;
    bSafe.textContent = `SAFE MODE: ${safe?'ON':'OFF'}`;
  }
  const bCb = document.getElementById('badge-circuit');
  if(bCb){
    bCb.className = `badge badge-${cbOpen?'bad':'ok'}`;
    bCb.textContent = `CIRCUIT: ${cbOpen?'ABIERTO':'CERRADO'}`;
  }
  const bEl = document.getElementById('badge-election');
  if(bEl){
    const elMode = document.getElementById('tog-election')?.checked || false;
    bEl.className = `badge badge-${elMode?'warn':'neutral'}`;
    bEl.textContent = `ELECTION MODE: ${elMode?'ON':'OFF'}`;
  }
  _updateMissionBar();
}

function _updateMissionBar() {
  const ep = localConfig['config/prod/endpoints.yaml'] || {};
  const animal = ep?.healing?.animal_mode || 'normal';
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
    msElec.className = `ms-val ${elMode ? 'alerta' : ''}`;
  }
  if (msDefense) {
    const defCls = {normal:'nominal', caution:'alerta', survival:'critico'}[animal] || '';
    msDefense.textContent = animal.toUpperCase();
    msDefense.className = `ms-val ${defCls}`;
  }
  if (msNodes) msNodes.textContent = (nodeCount === '—' || nodeCount === '') ? '—' : nodeCount;

  const hasCritical = ['badge-animal','badge-safemode','badge-circuit','badge-election'].some(id => {
    const el = document.getElementById(id);
    return el && el.classList.contains('badge-bad');
  });
  msSystem.textContent = hasCritical ? 'ALERTA' : 'NOMINAL';
  msSystem.className = `ms-val ${hasCritical ? 'critico' : 'nominal'}`;
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
    const r = await fetch(url,{method:'HEAD',mode:'no-cors',signal:AbortSignal.timeout(8000)});
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
  const isCustom = activePresetId && activePresetId.startsWith('custom-');
  if(!isCustom || !ceilingUnlocked){
    if(key==='rph')      v = Math.min(v, HARD_CEILING.maxRph);
    if(key==='interval') v = Math.max(v, HARD_CEILING.minInterval);
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
    if(sv) sv.textContent = `χ²=${v}`;
    if(sd) sd.textContent = `Umbral: ${display}`;
  }
  if(key==='zscore'){
    const sv = document.getElementById('scv-zscore');
    if(sv) sv.textContent = `${v}σ umbral`;
  }
  markDirty();
}

// Called when the user edits the friendly URL field — only marks dirty, does NOT overwrite inp-main-url
function onEasyUrlInput(val){
  markDirty();
}

function syncText(key, val){
  const ids = {
    mainurl:['inp-main-url'],  // easy field handled separately via onEasyUrlInput
  };
  (ids[key]||[]).forEach(id=>{
    const el = document.getElementById(id);
    if(el && el.value!==val) el.value=val;
  });
  markDirty();
}

