// ══════════════════════════════════════════════════════════
// DIRTY STATE — auto-apply on change (debounced)
// ══════════════════════════════════════════════════════════
let _autoApplyEnabled = localStorage.getItem('centinel-autosave') !== 'false';
let _autoApplyTimer = null;
let _writeInProgress = false;

// ══════════════════════════════════════════════════════════
// SESSION ACTION LOG
// ══════════════════════════════════════════════════════════
const _SLOG_KEY = 'centinel-session-log';
const _SLOG_MAX = 100;

function auditLog(action, detail='', veEvent){
  try{
    const fp = sessionStorage.getItem('centinel_fp') || '';
    const entry = {ts:new Date().toISOString(), id:(typeof getCurrentSeedId==='function'?getCurrentSeedId():'S??'), fp, role:getCurrentRole(), action, detail:String(detail).slice(0,200)};
    const log = _getSessionLog();
    log.unshift(entry);
    if(log.length > _SLOG_MAX) log.length = _SLOG_MAX;
    localStorage.setItem(_SLOG_KEY, JSON.stringify(log));
    _renderSessionLog();
    // VELE: structured evidence log (RFC 5424 + ISO 27037)
    if(typeof VELE!=='undefined'){
      const sev = veEvent?.severity || 'INFO';
      const msgid = veEvent?.msgid || VELE.EVT.USER_ACTION;
      VELE.log(sev, msgid, {action, detail:String(detail).slice(0,200)}, veEvent);
    }
  }catch(_){}
}
function _getSessionLog(){ try{ return JSON.parse(localStorage.getItem(_SLOG_KEY)||'[]'); }catch(_){ return []; } }
function clearSessionLog(){ localStorage.removeItem(_SLOG_KEY); _renderSessionLog(); }
function _renderSessionLog(){
  const tbody = document.querySelector('#session-log-table tbody');
  if(!tbody) return;
  const log = _getSessionLog();
  const countEl = document.getElementById('session-log-count');
  if(countEl) countEl.textContent = String(log.length);
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  if(!log.length){
    tbody.innerHTML=`<tr class="log-empty"><td colspan="3">${t('log.sin_acciones')}<span class="log-empty-hint">${t('log.acciones_tiempo_real')}</span></td></tr>`;
    return;
  }
  const COLORS={'sesión iniciada':'var(--ok)','sesión cerrada':'var(--muted)','config aplicada':'var(--accent)',
    'límites desbloqueados':'var(--bad)','límites restaurados':'var(--ok)','monitoreo iniciado':'var(--ok)',
    'monitoreo detenido':'var(--warn)','EMERGENCIA activada':'var(--bad)','país cambiado':'var(--accent)','preset cargado':'var(--accent)'};
  tbody.innerHTML = log.map(e=>{
    const d = new Date(e.ts);
    const time = d.toLocaleString('es',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
    const color = COLORS[e.action]||'var(--fg)';
    const isObserver = e.role==='observer';
    const idColor  = isObserver ? 'var(--warn)' : 'var(--ok)';
    const seedId   = e.id || 'S??';
    const fp       = e.fp ? `<span style="color:var(--muted);font-size:9px;margin-left:4px">··${esc(e.fp)}</span>` : '';
    const roleTag  = isObserver ? '<span style="font-size:8px;color:var(--warn);margin-left:3px">RO</span>' : '';
    return `<tr><td class="col-ts">${esc(time)}</td><td style="white-space:nowrap"><span style="font-size:10px;font-weight:700;color:${idColor};font-family:var(--mono);letter-spacing:.05em">${esc(seedId)}</span>${fp}${roleTag}</td><td style="color:${color};font-weight:600">${esc(e.action)}${e.detail?`<span style="color:var(--muted);font-size:10px;font-weight:400"> — ${esc(e.detail)}</span>`:''}</td></tr>`;
  }).join('');
}

function toggleAutoApply(){
  _autoApplyEnabled = !_autoApplyEnabled;
  localStorage.setItem('centinel-autosave', _autoApplyEnabled ? 'true' : 'false');
  const el = document.getElementById('autosave-val');
  if(el){ el.textContent = _autoApplyEnabled ? 'ON' : 'OFF'; el.className = 'soz-autosave-val ' + (_autoApplyEnabled ? 'on' : 'off'); }
  if(!_autoApplyEnabled && _autoApplyTimer){ clearTimeout(_autoApplyTimer); _autoApplyTimer=null; }
  updateDirtyState();
}

function _initAutoSaveUI(){
  const el = document.getElementById('autosave-val');
  if(el){ el.textContent = _autoApplyEnabled ? 'ON' : 'OFF'; el.className = 'soz-autosave-val ' + (_autoApplyEnabled ? 'on' : 'off'); }
}

function markDirty(){
  isDirty = true;
  updateDirtyState();
  if(!_autoApplyEnabled) return;
  if(_autoApplyTimer) clearTimeout(_autoApplyTimer);
  _autoApplyTimer = setTimeout(()=>{ _autoApplyTimer=null; autoApply(); }, 1500);
}

async function autoApply(){
  if(!isDirty || _writeInProgress) return;
  const newEp  = buildNewEndpointsYaml();
  const newWd  = buildNewWatchdogYaml();
  const newRl  = buildNewRateLimiterYaml();
  const newCfg = buildNewConfigYaml();
  const changes = buildDiff(newEp, newWd, newRl, newCfg);
  if(!changes.length){ isDirty=false; updateDirtyState(); return; }
  // PAT silencioso: si tenemos PAT y autosave está ON, guardamos directo
  const pat = localStorage.getItem('gh-pat');
  if(pat && _autoApplyEnabled){
    _writeInProgress = true;
    try {
      await writeChanges(changes, {newEp, newWd, newRl, newCfg}, pat);
      _showSaveToast();
      _logSaveToActivity(changes);
    } finally {
      _writeInProgress = false;
    }
    return;
  }
  // Sin PAT: mostrar banner de onboarding (no modal)
  if(!pat){
    _showPatOnboarding(changes, {newEp, newWd, newRl, newCfg});
    return;
  }
  // Dev mode: mostrar diff modal (para depuración)
  if(document.body.classList.contains('dev-mode')){
    showDiffModal(changes, {newEp, newWd, newRl, newCfg});
    return;
  }
  // Autosave OFF y tenemos PAT — esperar acción manual (btn-apply-now)
}

function _showSaveToast(){
  let toast = document.getElementById('save-toast');
  if(!toast){
    toast = document.createElement('div');
    toast.id = 'save-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = '✓ Config guardada';
  toast.classList.add('show');
  setTimeout(()=>toast.classList.remove('show'), 2000);
}

function _logSaveToActivity(changes){
  try{
    const ts = new Date().toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
    const diffText = changes.map(c=>c.path.split('/').pop()).join(', ');
    const logPre = document.querySelector('.log-pre');
    if(logPre){
      const line = document.createElement('div');
      line.innerHTML = `<span class="lvl-info">[${ts}] Config guardada — <a class="log-diff-link" href="#" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none';return false">Ver cambios →</a><details style="display:none;margin-top:4px"><summary style="display:none"></summary><pre style="font-size:10px;color:var(--muted)">${escHtml(diffText)}</pre></details></span>`;
      logPre.appendChild(line);
    }
  }catch(_){}
}

function _showPatOnboarding(changes, newYamls){
  let banner = document.getElementById('pat-onboarding');
  if(!banner){
    // Create and insert after section-sep in s3
    banner = document.createElement('div');
    banner.id = 'pat-onboarding';
    const s3 = document.getElementById('s3');
    const sep = s3?.querySelector('.section-sep');
    if(sep) sep.insertAdjacentElement('afterend', banner);
    else document.body.appendChild(banner);
  }
  banner.innerHTML = `
    <div style="font-size:12px;font-weight:700;color:var(--warn);margin-bottom:8px">
      <span data-lang="es">Conecta tu GitHub PAT para guardar cambios automáticamente</span>
      <span data-lang="en">Connect your GitHub PAT to save changes automatically</span>
    </div>
    <div style="font-size:11px;color:var(--muted);margin-bottom:10px">
      <span data-lang="es">Solo se necesita una vez — se guarda en tu navegador de forma segura.</span>
      <span data-lang="en">Only needed once — stored securely in your browser.</span>
    </div>
    <input type="password" id="pat-onboarding-input" placeholder="ghp_..." style="">
    <button onclick="_confirmPatOnboarding()" style="background:var(--accent);color:#fff;border:none;border-radius:4px;padding:6px 14px;font-size:12px;font-weight:700;cursor:pointer">
      <span data-lang="es">Conectar</span><span data-lang="en">Connect</span>
    </button>
    <button onclick="document.getElementById('pat-onboarding').classList.remove('show')" style="background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:4px;padding:6px 14px;font-size:12px;cursor:pointer;margin-left:6px">
      <span data-lang="es">Ahora no</span><span data-lang="en">Not now</span>
    </button>
  `;
  banner._pendingChanges = changes;
  banner._pendingYamls = newYamls;
  banner.classList.add('show');
  // Apply current lang
  const lang = window.OPS_LANG || 'es';
  banner.querySelectorAll('[data-lang]').forEach(el=>{
    el.style.display = el.getAttribute('data-lang')===lang ? '' : 'none';
  });
}

async function _confirmPatOnboarding(){
  const input = document.getElementById('pat-onboarding-input');
  if(!input) return;
  const pat = input.value.trim();
  if(!pat){ input.focus(); return; }
  localStorage.setItem('gh-pat', pat);
  input.value = '';
  const banner = document.getElementById('pat-onboarding');
  if(banner){
    const changes = banner._pendingChanges;
    const newYamls = banner._pendingYamls;
    banner.classList.remove('show');
    if(changes && newYamls){
      _writeInProgress = true;
      try {
        await writeChanges(changes, newYamls, pat);
        _showSaveToast();
        _logSaveToActivity(changes);
      } finally {
        _writeInProgress = false;
      }
    }
  }
}

window.addEventListener('beforeunload', e => {
  if (isDirty) { e.preventDefault(); e.returnValue = ''; }
});

function updateDirtyState(){
  const dot = document.getElementById('dirty-dot');
  if(dot) dot.style.display = isDirty ? 'inline-block' : 'none';
  const applyBtn = document.getElementById('btn-apply-now');
  if(applyBtn) applyBtn.style.display = (isDirty && !_autoApplyEnabled) ? 'block' : 'none';
}

// ══════════════════════════════════════════════════════════
// ADVANCED CONFIG TOGGLE
// ══════════════════════════════════════════════════════════
function toggleAdvancedConfig(){
  const el    = document.getElementById('advanced-config');
  const btn   = document.getElementById('btn-adv-config');
  const arrow = document.getElementById('adv-config-arrow');
  const isOpen = el && el.style.display !== 'none';
  el.style.display = isOpen ? 'none' : 'block';
  btn.classList.toggle('adv-open', !isOpen);
  arrow.textContent = isOpen ? '▶' : '▼';
}

// ══════════════════════════════════════════════════════════
// TABS
// ══════════════════════════════════════════════════════════
function showTab(id){
  document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('#cfg-tabs button').forEach((b,i)=>{
    const panes=['t-endpoints','t-capture','t-alerts','t-network','t-rules'];
    b.className = panes[i]===id ? 'active' : '';
  });
  const pane = document.getElementById(id);
  if(pane) pane.classList.add('active');
}

// ══════════════════════════════════════════════════════════
// PRESETS
// ══════════════════════════════════════════════════════════
function loadCustomPresets(){
  try{ customPresets = JSON.parse(localStorage.getItem('centinel_custom_presets')||'[]'); }
  catch{ customPresets = []; }
  buildPresetsGrid();
}

function buildPresetsGrid(){
  const grid = document.getElementById('presets-grid');
  if(!grid) return;
  const all = [...FACTORY_PRESETS, ...customPresets];
  grid.innerHTML = all.map(p=>{
    const c = p.cfg || {};
    const modeLabels = {normal:'NORMAL',electoral:'ELECTORAL',aggressive:'AGRESIVO',conservative:'CONSERVADOR'};
    const vals = [
      c.rlMode ? (modeLabels[c.rlMode]||c.rlMode) : '',
      c.interval !== undefined ? `${c.interval}m`  : '',
      c.rph      !== undefined ? `${c.rph}/h`      : '',
      c.election ? 'ELECCIONES' : '',
      c.safe     ? 'SAFE'     : '',
    ].filter(Boolean);
    return `
    <div class="preset-card ${activePresetId===p.id?'active-preset':''}" onclick="loadPreset('${p.id}')">
      <div class="pc-name">${escHtml(p.name)}</div>
      <div class="pc-desc">${escHtml(p.desc||'')}</div>
      ${vals.length ? `<div class="pc-vals">${vals.map(v=>`<span>${escHtml(v)}</span>`).join('')}</div>` : ''}
    </div>`;
  }).join('');
}

function loadPreset(id){
  const all = [...FACTORY_PRESETS, ...customPresets];
  const p = all.find(x=>x.id===id);
  if(!p) return;
  activePresetId = id;
  const c = p.cfg;
  if(c.interval !== undefined) syncSlider('interval', c.interval);
  if(c.rph      !== undefined) syncSlider('rph',      c.rph);
  if(c.benford  !== undefined) syncSlider('benford',  c.benford);
  if(c.zscore   !== undefined) syncSlider('zscore',   c.zscore);
  const togEl  = document.getElementById('tog-election');
  const togSafe= document.getElementById('tog-safe');
  if(togEl  && c.election!==undefined) togEl.checked  = c.election;
  if(togSafe && c.safe!==undefined)    togSafe.checked = c.safe;
  _showActivePresetLabel(p.name);
  buildPresetsGrid();
}

function _showActivePresetLabel(name){
  const el = document.getElementById('active-preset-label');
  if(!el) return;
  if(name){ el.textContent = '⚙ ' + name; el.style.display = ''; }
  else { el.style.display = 'none'; }
}

async function saveCustomPreset(){
  const name = document.getElementById('preset-name').value.trim();
  if(!name){alert('Escribe un nombre para el preset.');return;}
  const cfg = getCurrentCfg();
  const preset = {id:'custom-'+Date.now(), name, desc:'Guardado el '+new Date().toLocaleString(), cfg};
  customPresets.push(preset);
  localStorage.setItem('centinel_custom_presets', JSON.stringify(customPresets));
  document.getElementById('preset-name').value='';
  buildPresetsGrid();
}

function getCurrentCfg(){
  return {
    interval: parseFloat(document.getElementById('sl-interval')?.value||30),
    rph:      parseFloat(document.getElementById('sl-rph')?.value||180),
    benford:  parseFloat(document.getElementById('sl-benford')?.value||5.99),
    zscore:   parseFloat(document.getElementById('sl-zscore')?.value||3),
    election: document.getElementById('tog-election')?.checked||false,
    safe:     document.getElementById('tog-safe')?.checked||false,
  };
}

// ══════════════════════════════════════════════════════════
// CEILING UNLOCK
// ══════════════════════════════════════════════════════════

function requestUnlock(wantsUnlock){
  if(!wantsUnlock){
    ceilingUnlocked = false;
    updateUnlockUI();
    enforceCurrentCeilings();
    auditLog('límites restaurados', '', {msgid:'CEILING_LOCK', severity:'NOTICE'});
    return;
  }
  const now = new Date().toISOString();
  const text = UNLOCK_LEGAL_TEXT
    .replace('{{TIMESTAMP}}', now)
    .replace('{{MAX_RPH}}', HARD_CEILING.maxRph)
    .replace('{{MIN_INTERVAL}}', HARD_CEILING.minInterval)
    .replace('{{MAX_BURST}}', HARD_CEILING.maxBurst);
  const _legalEl = document.getElementById('unlock-legal-text');
  if (_legalEl) _legalEl.textContent = text;
  const rphEl = document.getElementById('ul-rph');
  const intEl = document.getElementById('ul-int');
  const burstEl = document.getElementById('ul-burst');
  if(rphEl) rphEl.textContent = HARD_CEILING.maxRph;
  if(intEl) intEl.textContent = HARD_CEILING.minInterval;
  if(burstEl) burstEl.textContent = HARD_CEILING.maxBurst;
  document.getElementById('unlock-accept-chk').checked = false;
  document.getElementById('unlock-err').textContent = '';
  updateUnlockBtn();
  document.getElementById('unlock-modal').classList.add('open');
}

function updateUnlockBtn(){
  const btn = document.getElementById('unlock-confirm-btn');
  btn.disabled = !document.getElementById('unlock-accept-chk').checked;
}

function closeUnlockModal(){
  document.getElementById('unlock-modal').classList.remove('open');
}

async function executeUnlock(){
  const errEl = document.getElementById('unlock-err');
  const btn   = document.getElementById('unlock-confirm-btn');
  btn.disabled = true;
  btn.textContent = 'Desbloqueando…';
  errEl.textContent = '';

  const now = new Date().toISOString();
  const doc = UNLOCK_LEGAL_TEXT
    .replace('{{TIMESTAMP}}', now)
    .replace('{{MAX_RPH}}', HARD_CEILING.maxRph)
    .replace('{{MIN_INTERVAL}}', HARD_CEILING.minInterval)
    .replace('{{MAX_BURST}}', HARD_CEILING.maxBurst);

  // Log acceptance locally — always works, no PAT needed
  const record = { timestamp: now, action: 'ceiling_unlock', text: doc };
  try { localStorage.setItem('centinel_last_unlock', JSON.stringify(record)); } catch(_){}

  // Try Git commit as bonus if PAT is already available — non-blocking
  let sha7 = null;
  const pat = localStorage.getItem('gh-pat');
  if(pat){
    try{
      const safeTs = now.replace(/[:.]/g,'-');
      const filePath = `audit/ceiling-unlock/${safeTs}.txt`;
      const seedId = (typeof getCurrentSeedId==='function'?getCurrentSeedId():'S??');
      const commitMsg = `audit: ${seedId} acepta responsabilidad por desbloqueo de límites\n\nFecha: ${now}\nClave: ${seedId}\nLímites desbloqueados: RPH>${HARD_CEILING.maxRph}, interval<${HARD_CEILING.minInterval}s, burst>${HARD_CEILING.maxBurst}`;
      const encoded = btoa(unescape(encodeURIComponent(doc)));
      const r = await fetch(`${API_BASE}/contents/${filePath}`,{
        method:'PUT',
        headers:{Authorization:`Bearer ${pat}`,'Content-Type':'application/json'},
        body: JSON.stringify({ message: commitMsg, content: encoded }),
      });
      if(r.ok){
        const j = await r.json();
        sha7 = (j.commit?.sha||'').slice(0,7);
      }
    }catch(_){}
  }

  ceilingUnlocked = true;
  closeUnlockModal();
  updateUnlockUI();
  auditLog('límites desbloqueados', sha7 ? `commit ${sha7}` : 'sin commit', {msgid:'CEILING_UNLOCK', severity:'ALERT', git_sha:sha7||null});
  const msgs = [
    '✓ Límites de seguridad desbloqueados para esta sesión',
    `✓ Aceptación registrada: ${now}`,
  ];
  if(sha7) msgs.push(`✓ Firma en Git — commit ${sha7}`);
  showResultModal(msgs, false);

  btn.textContent = 'Firmar y desbloquear';
  btn.disabled = false;
}

function updateUnlockUI(){
  const bar    = document.getElementById('unlock-bar');
  const alertBar = document.getElementById('unlock-alert-bar');
  const btn    = document.getElementById('btn-unlock-toggle');
  const rphSliders = ['sl-rph','sl-rph2'];
  const intSliders = ['sl-interval','sl-interval2'];
  const unlockedPanel = document.getElementById('unlocked-scraping-panel');
  if(ceilingUnlocked){
    bar.classList.add('unlocked');
    bar.querySelector('.ub-icon').textContent = '🔓';
    bar.querySelector('.ub-text').innerHTML =
      '<strong>Límites desbloqueados para esta sesión</strong> — los controles pueden exceder '+
      'los límites de seguridad. La firma de responsabilidad ha sido registrada en Git.';
    if(btn){ btn.textContent='🔒 Volver a bloquear'; btn.style.borderColor='var(--ok)'; btn.style.background='rgba(87,192,141,.12)'; btn.style.color='var(--ok)'; }
    if(alertBar) alertBar.classList.add('visible');
    if(unlockedPanel) unlockedPanel.style.display = '';
    [...rphSliders,'sl-rph3'].forEach(id=>{ const el=document.getElementById(id); if(el) el.max=1200; });
    [...intSliders,'sl-interval3'].forEach(id=>{ const el=document.getElementById(id); if(el) el.min=0.5; });
  } else {
    bar.classList.remove('unlocked');
    bar.querySelector('.ub-icon').textContent = '🔒';
    bar.querySelector('.ub-text').innerHTML =
      '<strong>Límites de seguridad activos</strong> — los controles no pueden exceder '+
      '480 req/h, intervalo mínimo 1s, burst máximo 8. '+
      'Para desbloquear, se requiere firma de responsabilidad con commit a GitHub.';
    if(btn){ btn.textContent='⚠ Desbloquear límites'; btn.style.borderColor='var(--bad)'; btn.style.background='rgba(223,107,134,.12)'; btn.style.color='var(--bad)'; }
    if(alertBar) alertBar.classList.remove('visible');
    if(unlockedPanel) unlockedPanel.style.display = 'none';
    [...rphSliders,'sl-rph3'].forEach(id=>{ const el=document.getElementById(id); if(el) el.max=480; });
    [...intSliders,'sl-interval3'].forEach(id=>{ const el=document.getElementById(id); if(el) el.min=1; });
  }
  // Red tab: retry inputs — cap at 5 when locked, 20 when unlocked
  const retryIds = ['retry-429','retry-5xx','retry-403','retry-404'];
  retryIds.forEach(id=>{
    const el = document.getElementById(id);
    if(!el) return;
    el.max = ceilingUnlocked ? 20 : 5;
    if(!ceilingUnlocked && parseInt(el.value) > 5) el.value = 5;
  });
  const retryBadge = document.getElementById('retry-lock-badge');
  const rateBadge  = document.getElementById('rate-lock-badge');
  if(retryBadge) retryBadge.style.display = ceilingUnlocked ? 'none' : '';
  if(rateBadge)  rateBadge.style.display  = ceilingUnlocked ? 'none' : '';
}

function enforceCurrentCeilings(){
  const rph      = parseFloat(document.getElementById('sl-rph')?.value||240);
  const interval = parseFloat(document.getElementById('sl-interval')?.value||10);
  const capacity = parseFloat(document.getElementById('sl-capacity')?.value||3);
  if(rph > HARD_CEILING.maxRph)           syncSlider('rph', HARD_CEILING.maxRph);
  if(interval < HARD_CEILING.minInterval) syncSlider('interval', HARD_CEILING.minInterval);
  if(capacity > HARD_CEILING.maxBurst)    syncSlider('capacity', HARD_CEILING.maxBurst);
}

// ══════════════════════════════════════════════════════════
// APPLY CHANGES
// ══════════════════════════════════════════════════════════
async function applyChanges(){
  await autoApply();
}

function buildNewEndpointsYaml(){
  const base = deepClone(currentConfig['config/prod/endpoints.yaml']||{});
  const local = localConfig['config/prod/endpoints.yaml']||{};
  // interval
  if(!base.healing) base.healing={};
  base.healing.interval_minutes = parseInt(document.getElementById('sl-interval')?.value||30);
  base.healing.safe_mode_active = document.getElementById('tog-safe')?.checked||false;
  base.healing.argos_protocol = base.healing.argos_protocol || base.healing.animal_mode || 'normal';
  // endpoints
  if(!base.cne) base.cne={};
  // Prefer the technical full-path field; fall back to easy field (root origin) only if not set
  const mainUrlVal = document.getElementById('inp-main-url')?.value.trim()
    || document.getElementById('inp-main-url-easy')?.value.trim()
    || base.cne?.main_url || '';
  if(mainUrlVal) base.cne.main_url = mainUrlVal;
  base.cne.presidential_endpoints = local?.cne?.presidential_endpoints || base.cne?.presidential_endpoints || [];
  return base;
}

function buildNewWatchdogYaml(){
  const base = deepClone(currentConfig['config/prod/watchdog.yaml']||{});
  base.check_interval_minutes = parseInt(document.getElementById('sl-wdcheck')?.value||3);
  base.max_cpu_percent = parseInt(document.getElementById('sl-cpu')?.value||80);
  base.max_mem_percent = parseInt(document.getElementById('sl-ram')?.value||90);
  return base;
}

function buildNewRateLimiterYaml(){
  const base = deepClone(currentConfig['config/prod/rate_limiter.yaml']||{});
  const rph = parseInt(document.getElementById('sl-rph')?.value||240);
  const capacity = parseInt(document.getElementById('sl-capacity')?.value||5);
  const interval = parseInt(document.getElementById('sl-interval')?.value||10);

  // Determine active mode from preset
  const preset = [...FACTORY_PRESETS, ...customPresets].find(p=>p.id===activePresetId);
  const rlMode = preset?.cfg?.rlMode || 'normal';
  const isCustom = activePresetId && activePresetId.startsWith('custom-');
  const bypassCeiling = isCustom && ceilingUnlocked;

  base.active_mode = bypassCeiling ? 'custom-unlocked' : (isCustom ? 'custom' : rlMode);
  base.max_requests_per_hour = bypassCeiling ? rph : Math.min(rph, HARD_CEILING.maxRph);
  base.capacity = bypassCeiling ? capacity : Math.min(capacity, HARD_CEILING.maxBurst);
  base.timeout_seconds = parseInt(document.getElementById('sl-timeout')?.value||30);
  base.jitter_seconds  = parseInt(document.getElementById('sl-jitter')?.value||0);

  // Ensure hard_ceiling is always present
  if(!base.hard_ceiling) base.hard_ceiling = {};
  base.hard_ceiling.max_requests_per_hour = HARD_CEILING.maxRph;
  base.hard_ceiling.min_interval_seconds = HARD_CEILING.minInterval;
  base.hard_ceiling.max_burst = HARD_CEILING.maxBurst;

  return base;
}

function buildDiff(newEp, newWd, newRl, newCfg){
  const changes = [];
  const pairs = [
    ['config/prod/endpoints.yaml',   currentConfig['config/prod/endpoints.yaml'],   newEp],
    ['config/prod/watchdog.yaml',    currentConfig['config/prod/watchdog.yaml'],    newWd],
    ['config/prod/rate_limiter.yaml',currentConfig['config/prod/rate_limiter.yaml'],newRl],
    ['config/prod/config.yaml',      currentConfig['config/prod/config.yaml'],      newCfg],
  ];
  for(const [path, orig, updated] of pairs){
    const origYaml    = jsyaml.dump(orig||{});
    const updatedYaml = jsyaml.dump(updated||{});
    if(origYaml !== updatedYaml){
      changes.push({path, origYaml, updatedYaml});
    }
  }
  return changes;
}

function showDiffModal(changes, newYamls){
  const div = document.getElementById('diff-content');
  div.innerHTML = changes.map(c=>`
    <div style="margin-bottom:14px">
      <div style="font-size:12px;font-weight:700;color:var(--muted);margin-bottom:6px;font-family:var(--mono)">${c.path}</div>
      <div class="diff-block">${diffLines(c.origYaml, c.updatedYaml)}</div>
    </div>
  `).join('');
  // Show PAT field only if not already in session
  const patRow = document.getElementById('diff-pat-row');
  const patInput = document.getElementById('diff-pat-input');
  const hasPat = !!localStorage.getItem('gh-pat');
  if(patRow) patRow.style.display = hasPat ? 'none' : 'block';
  if(patInput) patInput.value = '';
  document.getElementById('diff-modal').classList.add('open');
  if(!hasPat && patInput) setTimeout(()=>patInput.focus(), 80);
  document.getElementById('diff-modal')._changes = changes;
  document.getElementById('diff-modal')._newYamls = newYamls;
}

function diffLines(a, b){
  const al = a.split('\n');
  const bl = b.split('\n');
  const lines = [];
  const max = Math.max(al.length, bl.length);
  for(let i=0; i<max; i++){
    const la = al[i], lb = bl[i];
    if(la===lb) lines.push(`<span class="diff-ctx">${escHtml(la||'')}</span>`);
    else{
      if(la!==undefined) lines.push(`<span class="diff-rem">- ${escHtml(la)}</span>`);
      if(lb!==undefined) lines.push(`<span class="diff-add">+ ${escHtml(lb)}</span>`);
    }
  }
  return lines.join('\n');
}

function closeDiffModal(){ document.getElementById('diff-modal').classList.remove('open'); }

async function confirmApply(){
  if(_writeInProgress) return;
  // Resolve PAT — prefer session, then inline field in diff modal
  let pat = localStorage.getItem('gh-pat');
  if(!pat){
    const inline = document.getElementById('diff-pat-input')?.value.trim();
    if(!inline){
      const errEl = document.getElementById('diff-pat-err');
      if(errEl) errEl.textContent = 'Ingresa la clave de acceso.';
      document.getElementById('diff-pat-input')?.focus();
      return;
    }
    localStorage.setItem('gh-pat', inline);
    pat = inline;
    document.getElementById('diff-pat-input').value = '';
  }
  _writeInProgress = true;
  const applyBtn = document.getElementById('btn-apply-now');
  if(applyBtn) applyBtn.disabled = true;
  const changes  = document.getElementById('diff-modal')._changes;
  const newYamls = document.getElementById('diff-modal')._newYamls;
  closeDiffModal();
  try {
    await writeChanges(changes, newYamls, pat);
  } finally {
    _writeInProgress = false;
    if(applyBtn) applyBtn.disabled = false;
  }
}

function requestPat(){
  return new Promise(resolve=>{
    document.getElementById('pat-modal').classList.add('open');
    document.getElementById('pat-modal')._resolve = resolve;
  });
}

function confirmPat(){
  const input = document.getElementById('pat-input');
  const pat = input.value.trim();
  input.value = ''; // clear immediately
  if(!pat){document.getElementById('pat-err').textContent='Ingresa el PAT.';return;}
  localStorage.setItem('gh-pat', pat);
  document.getElementById('pat-modal').classList.remove('open');
  const resolve = document.getElementById('pat-modal')._resolve;
  if(resolve) resolve(true);
}

function closePatModal(){
  document.getElementById('pat-modal').classList.remove('open');
  document.getElementById('pat-input').value='';
  const resolve = document.getElementById('pat-modal')._resolve;
  if(resolve) resolve(false);
}

async function writeChanges(changes, newYamls, pat){
  const pathMap = {
    'config/prod/endpoints.yaml':    jsyaml.dump(newYamls.newEp),
    'config/prod/watchdog.yaml':     jsyaml.dump(newYamls.newWd),
    'config/prod/rate_limiter.yaml': jsyaml.dump(newYamls.newRl),
    'config/prod/config.yaml':       jsyaml.dump(newYamls.newCfg),
  };
  const results = [];
  let anyError = false;
  for(const {path} of changes){
    const content = pathMap[path];
    if(!content) continue;
    try{
      // Refresh SHA
      await fetchSha(path);
      const sha = configShas[path];
      const encoded = btoa(unescape(encodeURIComponent(content)));
      const r = await fetch(`${API_BASE}/contents/${path}`,{
        method:'PUT',
        headers:{Authorization:`Bearer ${pat}`,'Content-Type':'application/json'},
        body: JSON.stringify({message:`config: actualizado por ${(typeof getCurrentSeedId==='function'?getCurrentSeedId():'S??')} — ${new Date().toISOString()}`, content:encoded, sha}),
      });
      if(r.status===409){
        show409Banner(); return;
      }
      if(!r.ok){
        const j = await r.json().catch(()=>({}));
        results.push(`❌ ${path}: ${j.message||r.status}`);
        anyError=true;
      } else {
        const j = await r.json();
        results.push(`✓ ${path} — commit ${(j.commit?.sha||'').slice(0,7)}`);
        // Update SHA for future writes
        configShas[path] = j.content?.sha;
        currentConfig[path] = jsyaml.load(content);
        localConfig[path]   = jsyaml.load(content);
      }
    }catch(e){
      results.push(`❌ ${path}: ${e.message}`);
      anyError=true;
    }
  }
  if(!anyError){
    isDirty=false; updateDirtyState();
    auditLog('config aplicada', changes.map(c=>c.path.split('/').pop()).join(', '), {msgid:'CONFIG_COMMIT', severity:'NOTICE'});
    // Show timing pill in header
    const interval = localConfig['config/prod/watchdog.yaml']?.check_interval_minutes || 15;
    const pill = document.getElementById('timing-pill');
    if(pill){
      const elMode = document.getElementById('tog-election')?.checked || false;
      pill.textContent = '→ Activo en próx. ciclo (~' + interval + 'min)';
      pill.className = 'timing-pill show pending' + (elMode ? ' election' : '');
      clearTimeout(pill._clearTimer);
      pill._clearTimer = setTimeout(()=>{
        pill.className = 'timing-pill show done';
        pill.textContent = '✓ Config activa';
        setTimeout(()=>{ pill.className = 'timing-pill'; }, 10000);
      }, interval * 2 * 60 * 1000);
    }
  }
  showResultModal(results, anyError);
}

function show409Banner(){
  const b = document.getElementById('banner-409');
  if(b) b.classList.add('show');
}

async function reloadShaAndReapply(){
  document.getElementById('banner-409').classList.remove('show');
  await loadConfig();
  applyChanges();
}

function discardEdits(){
  if(!confirm('¿Descartar todos los cambios locales? Se perderán las ediciones no guardadas.')) return;
  document.getElementById('banner-409').classList.remove('show');
  loadConfig();
}

function showResultModal(lines, isError){
  const div = document.getElementById('result-content');
  div.innerHTML = `
    <div style="margin-bottom:12px">${isError?'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--warn)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="17" r="1" fill="var(--warn)"/></svg>':'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--ok)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'}</div>
    <div style="font-size:15px;font-weight:700;margin-bottom:12px">${isError?'Errores al aplicar':'Cambios aplicados'}</div>
    ${lines.map(l=>`<div style="font-family:var(--mono);font-size:12px;color:var(--muted);text-align:left;margin-bottom:4px">${escHtml(l)}</div>`).join('')}
    ${!isError?'<div style="font-size:12px;color:var(--muted);margin-top:12px">Los cambios tomarán efecto en el próximo ciclo (~15 min)</div>':''}
  `;
  document.getElementById('result-modal').classList.add('open');
}


// ══════════════════════════════════════════════════════════
// OTS — OpenTimestamps Bitcoin Anchoring
// ══════════════════════════════════════════════════════════

function onOtsServerSelect(val) {
  const inp = document.getElementById('inp-ots-server');
  if (!inp) return;
  if (val === '__custom__') {
    inp.style.display = '';
    inp.value = '';
    inp.focus();
  } else {
    inp.style.display = 'none';
    inp.value = val;
  }
  markDirty();
}

// Update the connectivity dot + hint text in the heading
function _setOtsDot(state){ // 'probing'|'ok'|'warn'|'bad'|'off'
  const dot  = document.getElementById('ots-net-dot');
  const hint = document.getElementById('ots-net-hint');
  const map  = {
    probing: ['ots-dot-probing', t('ots.probing')],
    ok:      ['ots-dot-ok',      t('ots.ok')],
    warn:    ['ots-dot-warn',    t('ots.warn')],
    bad:     ['ots-dot-bad',     t('ots.bad')],
    off:     ['ots-dot-off',     t('ots.off')],
  };
  const [cls, text] = map[state] || map.probing;
  if(dot)  { dot.className = 'ots-dot ' + cls; dot.title = text; }
  if(hint) { hint.textContent = text; }
}

function _syncOtsBtn(){
  const enabled = document.getElementById('tog-ots')?.checked ?? true;
  const btn = document.getElementById('btn-ots-toggle');
  if(btn){
    if(enabled){
      btn.textContent = '⛓ ' + t('ots.activo');
      btn.style.borderColor = 'rgba(87,192,141,.4)';
      btn.style.background  = 'rgba(87,192,141,.08)';
      btn.style.color       = 'var(--ok)';
    } else {
      btn.textContent = '⛓ ' + t('ots.inactivo');
      btn.style.borderColor = 'rgba(139,146,156,.3)';
      btn.style.background  = 'rgba(139,146,156,.06)';
      btn.style.color       = 'var(--muted)';
    }
  }
}

// Silent background probe — returns true if reachable
async function _probeOtsNetwork(){
  const server = document.getElementById('inp-ots-server')?.value.trim()
    || 'https://alice.btc.calendar.opentimestamps.org';
  const warn = document.getElementById('ots-airgap-warn');
  try{
    await fetch(server, {method:'HEAD', mode:'no-cors', signal:AbortSignal.timeout(8000)});
    _setOtsDot('ok');
    if(warn) warn.style.display = 'none';
    return true;
  }catch(e){
    const enabled = document.getElementById('tog-ots')?.checked ?? true;
    _setOtsDot('bad');
    if(warn) warn.style.display = enabled ? 'flex' : 'none';
    return false;
  }
}

// Called by both the section button and the sidebar button
function onOtsToggle(){
  const chk = document.getElementById('tog-ots');
  if(chk) chk.checked = !chk.checked;
  markDirty();
  _syncOtsBtn();
  const enabled = chk?.checked ?? true;
  const warn    = document.getElementById('ots-airgap-warn');
  if(!enabled){
    _setOtsDot('off');
    if(warn) warn.style.display = 'none';
  } else {
    _setOtsDot('probing');
    _probeOtsNetwork();
  }
}

// Manual test button (inside <details>) — delegates to probe + shows result text
async function testOtsConnectivity(){
  const res = document.getElementById('ots-test-result');
  if(res){ res.style.display='block'; res.textContent=t('ots.probando'); res.style.color='var(--muted)'; }
  const ok = await _probeOtsNetwork();
  if(res){
    res.textContent = ok ? t('ots.test_ok') : t('ots.test_bad');
    res.style.color = ok ? 'var(--ok)' : 'var(--warn)';
  }
}

async function loadOtsStatus(){
  if(!snapshotData) return;
  const ots      = snapshotData?.chain?.ots_status || 'unknown';
  const last     = snapshotData?.chain?.last_anchor;
  const chainLen = snapshotData?.chain?.chain_length || '?';
  const badge    = document.getElementById('ots-status-badge');
  if(badge){
    // Show — when pipeline has no chain data yet (no anchors attempted)
    const hasChain = !!(snapshotData?.chain?.chain_length > 0 || snapshotData?.chain?.last_anchor);
    if(!hasChain || ots === 'unknown'){
      badge.className = 'badge badge-neutral';
      badge.textContent = '—';
    } else {
      const cls    = {confirmed:'ok', pending:'warn', error:'bad'}[ots] || 'neutral';
      const labels = {confirmed:t('val.confirmado'), pending:t('val.pendiente'), error:t('val.error')};
      badge.className = 'badge badge-' + cls;
      badge.textContent = labels[ots] || '—';
    }
  }
  const lastEl = document.getElementById('ots-last-anchor');
  if(lastEl) lastEl.textContent = t('ots.ultimo_ancla') + ': ' + (last ? relTime(last) : '—');
  const infoEl = document.getElementById('ots-chain-info');
  if(infoEl) infoEl.textContent = t('ots.cadena') + ': ' + chainLen + ' ' + t('ots.bloques') + ' · ' + t('ots.hash') + ': ' +
    ((snapshotData?.chain?.latest_hash || '—').slice(-12));
  try{
    const r = await fetch(`${RAW_BASE}/data/pending_ots.json?t=${Date.now()}`);
    if(r.ok){
      const pending = await r.json();
      const n = Array.isArray(pending) ? pending.length : 0;
      const pendEl = document.getElementById('ots-pending');
      if(pendEl && n > 0){
        pendEl.style.display = 'block';
        pendEl.textContent = n + ' ' + (n > 1 ? t('ots.raices') : t('ots.raiz')) + ' ' + (n > 1 ? t('ots.pendientes') : t('ots.pendiente')) + ' ' + t('ots.de_anclaje');
      }
    }
  }catch{}
  const cfg    = currentConfig['config/prod/config.yaml'] || {};
  const togOts = document.getElementById('tog-ots');
  if(togOts) togOts.checked = cfg?.opentimestamps?.enabled ?? true;
  const inpServer = document.getElementById('inp-ots-server');
  const selServer = document.getElementById('sel-ots-server');
  const savedServer = cfg?.opentimestamps?.primary_server || '';
  if (inpServer) inpServer.value = savedServer;
  if (selServer) {
    const knownOpt = [...selServer.options].find(o => o.value === savedServer);
    if (savedServer && !knownOpt) {
      selServer.value = '__custom__';
      inpServer.style.display = '';
    } else {
      selServer.value = savedServer || 'https://a.pool.opentimestamps.org';
      if (inpServer) inpServer.style.display = 'none';
    }
  }
  // Auto-probe on load — non-blocking
  const enabled = togOts?.checked ?? true;
  if(enabled){ _setOtsDot('probing'); _probeOtsNetwork(); }
  else { _setOtsDot('off'); }
  _syncOtsBtn();
}

function buildNewConfigYaml(){
  const base = deepClone(currentConfig['config/prod/config.yaml'] || {});
  if(!base.opentimestamps) base.opentimestamps = {};
  base.opentimestamps.enabled = document.getElementById('tog-ots')?.checked ?? true;
  const server = document.getElementById('inp-ots-server')?.value.trim();
  if(server) base.opentimestamps.primary_server = server;
  else delete base.opentimestamps.primary_server;
  base.max_concurrent_requests = parseInt(document.getElementById('sl-concurrency')?.value||1);
  return base;
}

function closeResultModal(){ document.getElementById('result-modal').classList.remove('open'); }

// ══════════════════════════════════════════════════════════
// LOGS
// ══════════════════════════════════════════════════════════
let activeFilters = new Set(['INFO','WARNING','CRITICAL','PANIC']);

function toggleChip(btn){
  const lvl = btn.dataset.lvl;
  if(activeFilters.has(lvl)){ activeFilters.delete(lvl); btn.classList.remove('active'); }
  else { activeFilters.add(lvl); btn.classList.add('active'); }
  renderLog();
}

async function fetchLog(){
  try{
    const r = await fetch(`${RAW_BASE}/data/alerts.json?t=${Date.now()}`);
    if(r.ok) logData = await r.json();
  }catch{}
  renderLog();
}

function _emptyRow(cols, msg, hint=''){
  return `<tr class="log-empty"><td colspan="${cols}">${escHtml(msg)}${hint?`<span class="log-empty-hint">${escHtml(hint)}</span>`:''}
  </td></tr>`;
}

function _renderLogSummary(){
  const el = document.getElementById('log-summary');
  if(!el) return;
  if(!logData.length){el.innerHTML='';return;}
  const counts = {INFO:0,WARNING:0,CRITICAL:0,PANIC:0};
  logData.forEach(e=>{const l=(e.level||'INFO').toUpperCase();if(counts[l]!==undefined)counts[l]++;});
  const PILL = {INFO:'lp-info',WARNING:'lp-warn',CRITICAL:'lp-crit',PANIC:'lp-panic'};
  el.innerHTML = Object.entries(counts).map(([lvl,n])=>
    `<span class="sum-item"><span class="lpill ${PILL[lvl]}">${lvl}</span> <strong>${n}</strong></span>`
  ).join('<span class="sum-sep">·</span>')+
  `<span style="margin-left:auto;font-size:10px;color:var(--muted);font-family:var(--mono)">${logData.length} ${t('log.total')}</span>`;
}

function _renderAttackSummary(){
  const el = document.getElementById('attack-summary');
  if(!el) return;
  if(!attackData.length){el.innerHTML='';return;}
  const counts={};
  attackData.forEach(e=>{const t=(e.type||e.classification||e.event||'OTHER').toUpperCase();counts[t]=(counts[t]||0)+1;});
  const PILL={FLOOD:'lp-flood',BRUTE:'lp-brute',SCAN:'lp-scan',PROXY_SUSPECT:'lp-proxy_suspect',SUSPICIOUS:'lp-suspicious'};
  el.innerHTML = Object.entries(counts).sort(([,a],[,b])=>b-a).map(([t,n])=>
    `<span class="sum-item"><span class="lpill ${PILL[t]||'lp-suspicious'}">${t}</span> <strong>${n}</strong></span>`
  ).join('<span class="sum-sep">·</span>')+
  `<span style="margin-left:auto;font-size:10px;color:var(--muted);font-family:var(--mono)">${attackData.length} ${t('log.total')}</span>`;
}

function buildAttackDetailRow(e){
  const fields=[
    ['http_method', e.http_method],
    ['content_length', e.content_length!=null?e.content_length+' bytes':null],
    ['sequence', Array.isArray(e.sequence)?e.sequence.join(' → '):e.sequence],
    ['user_agent', e.user_agent],
    ['freq_window', e.frequency_window_seconds?e.frequency_window_seconds+'s':null],
  ].filter(([,v])=>v!=null&&v!=='');
  if(!fields.length) return `<span style="color:var(--muted);font-size:10px">${t('log.sin_campos_extra')}</span>`;
  return `<dl class="attack-detail-grid">${fields.map(([k,v])=>`<dt>${escHtml(k)}</dt><dd>${escHtml(String(v).slice(0,400))}</dd>`).join('')}</dl>`;
}

function renderLog(){
  const n = parseInt(document.getElementById('log-lines')?.value||50);
  const wrap = document.getElementById('log-general');
  if(!wrap) return;
  const tbody = wrap.querySelector('tbody');
  if(!tbody) return;
  _renderLogSummary();
  if(!logData.length){tbody.innerHTML=_emptyRow(4,t('log.sin_actividad'),t('log.inicia_monitoreo'));return;}
  let slice = n===0 ? logData : logData.slice(-n);
  slice = slice.filter(e => activeFilters.has((e.level||'INFO').toUpperCase()));
  if(logSearch){
    const q=logSearch.toLowerCase();
    slice=slice.filter(e=>(e.message||e.description||'').toLowerCase().includes(q)||(e.rule_id||'').toLowerCase().includes(q)||(e.kind||'').toLowerCase().includes(q)||(e.dept_code||'').toLowerCase().includes(q));
  }
  const total=(n===0?logData:logData.slice(-n)).length;
  const countEl=document.getElementById('log-general-count');
  if(countEl) countEl.textContent = slice.length<total?`${slice.length} / ${total}`:`${total}`;
  if(!slice.length){tbody.innerHTML=_emptyRow(4,t('log.sin_entradas_filtros'));return;}
  const PILL = {INFO:'lp-info',WARNING:'lp-warn',CRITICAL:'lp-crit',PANIC:'lp-panic'};
  tbody.innerHTML = slice.map(e=>{
    const lvl = (e.level||'INFO').toUpperCase();
    const pc  = PILL[lvl]||'lp-info';
    const ts  = relTimestamps ? relTime(e.timestamp) : escHtml(e.timestamp||'—');
    const msg = escHtml(e.message||e.description||JSON.stringify(e));
    const meta= escHtml([e.rule_id, e.kind, e.dept_code].filter(Boolean).join(' · ')||'—');
    return `<tr><td class="col-ts">${ts}</td><td class="col-lvl"><span class="lpill ${pc}">${lvl}</span></td><td class="col-msg">${msg}</td><td class="col-meta">${meta}</td></tr>`;
  }).join('');
  wrap.scrollTop = wrap.scrollHeight;
}

async function fetchAttackLog(){
  try{
    const r = await fetch(`${RAW_BASE}/hashes/attack_log.jsonl?t=${Date.now()}`);
    if(r.ok){
      const txt = await r.text();
      attackData = txt.split('\n').filter(l=>l.trim()).map(l=>{try{return JSON.parse(l);}catch{return {raw:l};}});
    }
  }catch{}
  renderAttackLog();
}

function renderAttackLog(){
  const filter = document.getElementById('attack-filter')?.value||'';
  const wrap = document.getElementById('log-attacks');
  if(!wrap) return;
  const tbody = wrap.querySelector('tbody');
  if(!tbody) return;
  _renderAttackSummary();
  if(!attackData.length){tbody.innerHTML=_emptyRow(6,t('log.sin_ataques'),t('log.sistema_vigilando'));return;}
  let filtered = filter
    ? attackData.filter(e=>(e.type||e.classification||e.event||e.raw||'').toUpperCase().includes(filter))
    : attackData;
  if(attackSearch){
    const q=attackSearch.toLowerCase();
    filtered=filtered.filter(e=>(e.ip||'').includes(q)||(e.route||'').toLowerCase().includes(q)||(e.user_agent||'').toLowerCase().includes(q)||(e.geo?.country||'').toLowerCase().includes(q)||(e.geo?.city||'').toLowerCase().includes(q));
  }
  const countEl=document.getElementById('log-attacks-count');
  if(countEl) countEl.textContent=filtered.length<attackData.length?`${filtered.length} / ${attackData.length}`:`${attackData.length}`;
  if(!filtered.length){tbody.innerHTML=_emptyRow(6,t('log.sin_eventos_filtro'));return;}
  const PILL = {FLOOD:'lp-flood',BRUTE:'lp-brute',SCAN:'lp-scan',PROXY_SUSPECT:'lp-proxy_suspect',SUSPICIOUS:'lp-suspicious'};
  tbody.innerHTML = filtered.flatMap(e=>{
    const type = (e.type||e.classification||e.event||'EVENT').toUpperCase();
    const pc   = PILL[type]||'lp-suspicious';
    const ts   = relTimestamps ? relTime(e.timestamp_utc||e.timestamp) : escHtml(e.timestamp_utc||e.timestamp||'—');
    const ip   = escHtml(e.ip||'—');
    const geo  = e.geo?.country ? escHtml(`${e.geo.country}${e.geo.city&&e.geo.city!=='unknown'?' / '+e.geo.city:''}`) : (e.country ? escHtml(e.country) : '—');
    const route= escHtml(e.route||'—');
    const freq = e.frequency_count ? `${e.frequency_count} req` : '—';
    const ua   = e.user_agent ? `<span style="color:var(--muted)">${escHtml(String(e.user_agent).slice(0,80))}</span>` : '—';
    return [
      `<tr class="attack-row"><td class="col-ts">${ts}</td><td class="col-lvl"><span class="lpill ${pc}">${type}</span></td><td class="col-meta">${ip}<br><span style="color:var(--muted);font-size:10px">${geo}</span></td><td class="col-route" style="color:var(--accent);font-size:10px">${route}</td><td class="col-meta">${freq}</td><td class="col-meta" style="max-width:220px;overflow:hidden;text-overflow:ellipsis">${ua}</td></tr>`,
      `<tr class="attack-detail-row"><td colspan="6">${buildAttackDetailRow(e)}</td></tr>`
    ];
  }).join('');
  wrap.scrollTop = wrap.scrollHeight;
}

function renderAuditTrail(){
  const wrap = document.getElementById('log-audit');
  if(!wrap) return;
  const tbody = wrap.querySelector('tbody');
  if(!tbody) return;
  if(!auditData.length){tbody.innerHTML=_emptyRow(4,t('log.sin_commits'));return;}
  let filtered=auditData;
  if(auditSearch){
    const q=auditSearch.toLowerCase();
    filtered=auditData.filter(c=>c.sha.slice(0,7).includes(q)||(c.commit.author.name||'').toLowerCase().includes(q)||c.commit.message.toLowerCase().includes(q));
  }
  const countEl=document.getElementById('log-audit-count');
  if(countEl) countEl.textContent=filtered.length<auditData.length?`${filtered.length} / ${auditData.length}`:`${auditData.length}`;
  if(!filtered.length){tbody.innerHTML=_emptyRow(4,t('log.sin_commits_busqueda'));return;}
  tbody.innerHTML = filtered.map(c=>{
    const sha  = escHtml(c.sha.slice(0,7));
    const ts   = relTimestamps ? relTime(c.commit.author.date) : escHtml(c.commit.author.date);
    const author = escHtml(c.commit.author.name||c.commit.author.email||'—');
    const msg  = escHtml(c.commit.message.split('\n')[0]);
    return `<tr><td class="col-meta"><a href="${escHtml(c.html_url)}" target="_blank" style="color:var(--accent);text-decoration:none">${sha}</a></td><td class="col-ts">${ts}</td><td class="col-meta">${author}</td><td class="col-msg">${msg}</td></tr>`;
  }).join('');
  wrap.scrollTop = wrap.scrollHeight;
}

async function fetchAuditTrail(){
  const wrap = document.getElementById('log-audit');
  const tbody = wrap?.querySelector('tbody');
  const pat = localStorage.getItem('gh-pat');
  if(!pat){
    if(tbody) tbody.innerHTML=_emptyRow(4,t('log.historial_cambios'),t('log.modifica_control'));
    return;
  }
  try{
    const r = await fetch(`${API_BASE}/commits?path=config/prod/&per_page=30`,{
      headers:{Authorization:`Bearer ${pat}`}
    });
    if(!r.ok){if(tbody) tbody.innerHTML=`<tr class="log-empty"><td colspan="4">${t('log.error')}: ${r.status}</td></tr>`;return;}
    auditData = await r.json();
    renderAuditTrail();
  }catch(e){
    if(tbody) tbody.innerHTML=`<tr class="log-empty"><td colspan="4">${t('log.error')}: ${escHtml(e.message)}</td></tr>`;
  }
}

function toggleTimestamp(){
  relTimestamps = !relTimestamps;
  renderLog();
  renderAttackLog();
  renderAuditTrail();
}

function toggleLogLive(){
  const btn=document.getElementById('btn-log-live');
  const dot=document.getElementById('log-live-dot');
  if(_logLiveTimer){
    clearInterval(_logLiveTimer);_logLiveTimer=null;
    btn?.classList.remove('live-on');
    if(dot){dot.className='ots-dot ots-dot-off';dot.style.animation='';}
    if(btn) btn.title=t('log.auto_refresco_inactivo');
  } else {
    fetchLog();
    _logLiveTimer=setInterval(fetchLog,30000);
    btn?.classList.add('live-on');
    if(dot){dot.className='ots-dot ots-dot-ok';dot.style.animation='ots-pulse 1.4s ease-in-out infinite';}
    if(btn) btn.title=t('log.live_activo');
  }
}

function toggleAttackLive(){
  const btn=document.getElementById('btn-attack-live');
  const dot=document.getElementById('attack-live-dot');
  if(_attackLiveTimer){
    clearInterval(_attackLiveTimer);_attackLiveTimer=null;
    btn?.classList.remove('live-on');
    if(dot){dot.className='ots-dot ots-dot-off';dot.style.animation='';}
    if(btn) btn.title=t('log.auto_refresco_inactivo');
  } else {
    fetchAttackLog();
    _attackLiveTimer=setInterval(fetchAttackLog,30000);
    btn?.classList.add('live-on');
    if(dot){dot.className='ots-dot ots-dot-ok';dot.style.animation='ots-pulse 1.4s ease-in-out infinite';}
    if(btn) btn.title=t('log.live_activo');
  }
}

function onLogSearch(val){
  logSearch=val;clearTimeout(_sdTimer);
  _sdTimer=setTimeout(renderLog,150);
}
function onAttackSearch(val){
  attackSearch=val;clearTimeout(_sdTimer);
  _sdTimer=setTimeout(renderAttackLog,150);
}
function onAuditSearch(val){
  auditSearch=val;clearTimeout(_sdTimer);
  _sdTimer=setTimeout(renderAuditTrail,150);
}


// ══════════════════════════════════════════════════════════
// MIRROR EXTERNO — AMAZON S3 (real sync via GitHub Actions)
// Credentials: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY /
// AWS_BUCKET_NAME / AWS_REGION as GitHub Secrets in your fork.
// Status is read from data/s3_mirror_status.json — written by
// .github/workflows/s3-mirror.yml after each sync (every 6 h
// or on push to web/data/ or web/reports/).
// ══════════════════════════════════════════════════════════

let awsMirrorEnabled = false;
let _s3Status = null;

function loadAwsStatus(){
  fetch('data/s3_mirror_status.json?_=' + Date.now())
    .then(r => r.ok ? r.json() : null)
    .then(data => { _s3Status = data; _renderAwsStatus(); })
    .catch(() => { _s3Status = null; _renderAwsStatus(); });
}

function refreshAwsStatus(){
  const badge = document.getElementById('aws-status-badge');
  if(badge){
    badge.className = 'badge badge-neutral';
    badge.innerHTML = '<span data-lang="es">Cargando…</span><span data-lang="en">Loading…</span>';
  }
  loadAwsStatus();
}

function _fmtBytes(b){
  if(!b) return '0 B';
  if(b < 1024) return b + ' B';
  if(b < 1048576) return (b/1024).toFixed(1) + ' KB';
  if(b < 1073741824) return (b/1048576).toFixed(1) + ' MB';
  return (b/1073741824).toFixed(2) + ' GB';
}

function _fmtSyncDate(iso){
  if(!iso) return '—';
  try{
    return new Date(iso).toLocaleString(
      currentLang==='en' ? 'en-US' : 'es-HN',
      {day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'UTC',timeZoneName:'short'}
    );
  }catch(_){ return iso; }
}

function _renderAwsStatus(){
  const s         = _s3Status;
  const liveDiv   = document.getElementById('aws-live-status');
  const badge     = document.getElementById('aws-status-badge');
  const lastSync  = document.getElementById('aws-last-sync');
  const filesInfo = document.getElementById('aws-files-info');
  const uriRow    = document.getElementById('aws-s3-uri-row');
  const uriSpan   = document.getElementById('aws-s3-uri');
  const errRow    = document.getElementById('aws-error-row');
  const errMsg    = document.getElementById('aws-error-msg');
  const runLink   = document.getElementById('aws-run-link');
  const hint      = document.getElementById('aws-enabled-hint');

  if(!s){
    if(badge){ badge.className='badge badge-neutral'; badge.innerHTML='<span data-lang="es">Sin estado</span><span data-lang="en">No status</span>'; }
    if(liveDiv) liveDiv.style.display='none';
    return;
  }

  if(liveDiv) liveDiv.style.display='';

  if(s.status==='ok'){
    if(badge){ badge.className='badge badge-ok'; badge.innerHTML='<span data-lang="es">Activo</span><span data-lang="en">Active</span>'; }
    if(lastSync) lastSync.textContent=(currentLang==='en'?'Last sync: ':'Último sync: ')+_fmtSyncDate(s.last_sync_utc);
    if(filesInfo) filesInfo.textContent=s.files_synced+(currentLang==='en'?' files — ':' archivos — ')+_fmtBytes(s.bytes_synced);
    if(uriRow) uriRow.style.display='';
    if(uriSpan) uriSpan.textContent=s.s3_uri||'';
    if(errRow) errRow.style.display='none';
    if(hint){ hint.style.display=''; hint.textContent=(currentLang==='en'?'✓ S3 sync active — billing applies to your AWS account':'✓ Sync S3 activo — la facturación aplica a tu cuenta de AWS'); }
    awsMirrorEnabled=true;
  } else if(s.status==='error'){
    if(badge){ badge.className='badge badge-bad'; badge.innerHTML='<span data-lang="es">Error</span><span data-lang="en">Error</span>'; }
    if(lastSync) lastSync.textContent=(currentLang==='en'?'Last attempt: ':'Último intento: ')+_fmtSyncDate(s.last_sync_utc);
    if(filesInfo) filesInfo.textContent='';
    if(uriRow) uriRow.style.display='none';
    if(errRow) errRow.style.display='';
    if(errMsg) errMsg.textContent=s.error||(currentLang==='en'?'Sync failed.':'Error de sincronización.');
    if(runLink&&s.workflow_run_url){ runLink.href=s.workflow_run_url; runLink.style.display=''; }
    if(hint) hint.style.display='none';
    awsMirrorEnabled=false;
  } else {
    // not_configured
    if(badge){ badge.className='badge badge-neutral'; badge.innerHTML='<span data-lang="es">No configurado</span><span data-lang="en">Not configured</span>'; }
    if(lastSync) lastSync.textContent=currentLang==='en'?'Not yet configured — see instructions below.':'Sin configurar — ver instrucciones abajo.';
    if(filesInfo) filesInfo.textContent='';
    if(uriRow) uriRow.style.display='none';
    if(errRow) errRow.style.display='none';
    if(hint) hint.style.display='none';
    awsMirrorEnabled=false;
  }
}

function _loadAwsState(){
  try{
    const raw = localStorage.getItem('vigil_aws_mirror');
    if(raw){
      const st = JSON.parse(raw);
      if(st.bucket){ const b=document.getElementById('inp-aws-bucket'); if(b) b.value=st.bucket; }
      if(st.region){ const r=document.getElementById('inp-aws-region'); if(r) r.value=st.region; }
    }
  }catch(_){}
  loadAwsStatus();
}

// Expand/collapse config panel
function onAwsToggle(){
  const panel = document.getElementById('aws-config-panel');
  if(!panel) return;
  const opening = panel.style.display === 'none';
  panel.style.display = opening ? 'block' : 'none';
  const btn = document.getElementById('btn-aws-toggle');
  if(btn){
    btn.innerHTML = opening
      ? '<span data-lang="es">Ocultar</span><span data-lang="en">Hide</span>'
      : '<span data-lang="es">Configurar</span><span data-lang="en">Configure</span>';
  }
}

// Open informed-consent modal
function requestAwsEnable(){
  const bucket = document.getElementById('inp-aws-bucket')?.value?.trim() || '';
  const region = document.getElementById('inp-aws-region')?.value?.trim() || '';
  const err = document.getElementById('aws-err');
  if(err) err.textContent='';
  if(!bucket||!region){
    if(err) err.textContent=(currentLang==='en')
      ?'Enter a bucket name and AWS region first.'
      :'Ingresa primero el nombre del bucket y la región de AWS.';
    return;
  }
  document.getElementById('aws-accept-chk').checked=false;
  updateAwsBtn();
  document.getElementById('aws-modal').classList.add('open');
}

function updateAwsBtn(){
  const btn = document.getElementById('aws-confirm-btn');
  if(btn) btn.disabled=!document.getElementById('aws-accept-chk').checked;
}

function closeAwsModal(){
  document.getElementById('aws-modal').classList.remove('open');
}

// Confirm: save bucket/region preference and show setup instructions.
// Actual sync is performed by .github/workflows/s3-mirror.yml using
// GitHub Secrets — credentials never enter this page.
function executeAwsEnable(){
  const bucket = document.getElementById('inp-aws-bucket')?.value?.trim() || '';
  const region = document.getElementById('inp-aws-region')?.value?.trim() || '';
  try{
    localStorage.setItem('vigil_aws_mirror', JSON.stringify({
      enabled:true, bucket, region, acceptedAt: new Date().toISOString()
    }));
  }catch(_){}
  closeAwsModal();
  auditLog('mirror S3 activado', `bucket=${bucket} region=${region}`, {msgid:'AWS_MIRROR_ON', severity:'WARNING'});
  const msgs = (currentLang==='en')
    ? [
        '✓ Bucket and region saved locally.',
        `  Bucket: ${bucket}  Region: ${region}`,
        '',
        '→ To complete setup, add these 4 secrets to your fork:',
        '  GitHub → Settings → Secrets → Actions → New secret',
        '  • AWS_ACCESS_KEY_ID',
        '  • AWS_SECRET_ACCESS_KEY',
        `  • AWS_BUCKET_NAME  = ${bucket}`,
        `  • AWS_REGION       = ${region}`,
        '',
        '→ Then trigger the workflow to start syncing:',
        '  Actions → "S3 Mirror" → Run workflow',
        '',
        '  Status updates automatically after each sync run.',
      ]
    : [
        '✓ Bucket y región guardados localmente.',
        `  Bucket: ${bucket}  Región: ${region}`,
        '',
        '→ Para completar la configuración, agrega estos 4 secrets en tu fork:',
        '  GitHub → Settings → Secrets → Actions → New secret',
        '  • AWS_ACCESS_KEY_ID',
        '  • AWS_SECRET_ACCESS_KEY',
        `  • AWS_BUCKET_NAME  = ${bucket}`,
        `  • AWS_REGION       = ${region}`,
        '',
        '→ Luego activa el workflow para iniciar la sincronización:',
        '  Actions → "S3 Mirror" → Run workflow',
        '',
        '  El estado se actualiza automáticamente tras cada ejecución.',
      ];
  showResultModal(msgs, false);
}

function disableAwsMirror(){
  awsMirrorEnabled=false;
  try{
    const raw=localStorage.getItem('vigil_aws_mirror');
    const st=raw?JSON.parse(raw):{};
    st.enabled=false;
    localStorage.setItem('vigil_aws_mirror', JSON.stringify(st));
  }catch(_){}
  auditLog('mirror S3 desactivado','',{msgid:'AWS_MIRROR_OFF', severity:'NOTICE'});
  _renderAwsStatus();
}

// ══════════════════════════════════════════════════════════
// DEV MODE TOGGLE
// ══════════════════════════════════════════════════════════
function toggleDevMode(){
  document.body.classList.toggle('dev-mode');
  const on = document.body.classList.contains('dev-mode');
  try { localStorage.setItem('centinel-dev-mode', on?'1':'0'); } catch(_){}
  const badge = document.getElementById('dev-badge');
  if(badge) badge.style.display = on ? 'inline-flex' : 'none';
}
function _initDevMode(){
  try { if(localStorage.getItem('centinel-dev-mode')==='1') document.body.classList.add('dev-mode'); } catch(_){}
  const badge = document.getElementById('dev-badge');
  const on = document.body.classList.contains('dev-mode');
  if(badge) badge.style.display = on ? 'inline-flex' : 'none';
}

// THEME: handled solely by the header toggle (setOpsTheme / data-theme in
// index.html). The previous body.light-mode system was removed — it duplicated
// and conflicted with the header theme, producing a mixed/broken palette.
