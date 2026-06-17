// ══════════════════════════════════════════════════════════
// DOWNLOADS
// ══════════════════════════════════════════════════════════
function _logTxtContent(id){
  const ts = new Date().toISOString();
  if(id==='log-general'){
    const hdr = `# VIGIL — Actividad (alerts.json)\n# Exportado: ${ts}\n# Entradas: ${logData.length}\n${'─'.repeat(72)}\n`;
    const rows = logData.map(e=>`${e.timestamp||'—'}\t${(e.level||'INFO').padEnd(8)}\t${e.message||e.description||''}\t${[e.rule_id,e.kind,e.dept_code].filter(Boolean).join('|')||''}`).join('\n');
    return hdr + rows;
  }
  if(id==='log-attacks'){
    const hdr = `# VIGIL — Attack Log (attack_log.jsonl)\n# Exportado: ${ts}\n# Entradas: ${attackData.length}\n${'─'.repeat(72)}\n`;
    const rows = attackData.map(e=>JSON.stringify(e)).join('\n');
    return hdr + rows;
  }
  if(id==='log-audit'){
    const hdr = `# VIGIL — Audit Trail (commits de configuración)\n# Exportado: ${ts}\n# Entradas: ${auditData.length}\n${'─'.repeat(72)}\n`;
    const rows = auditData.map(c=>`${c.sha.slice(0,7)}\t${c.commit.author.date}\t${c.commit.author.name||''}\t${c.commit.message.split('\n')[0]}`).join('\n');
    return hdr + rows;
  }
  return '';
}

function downloadTxt(id, filename){
  const content = _logTxtContent(id);
  if(!content) return;
  const blob = new Blob([content],{type:'text/plain;charset=utf-8'});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a'); a.href=url; a.download=filename; a.click();
  URL.revokeObjectURL(url);
}

function downloadPdf(id){
  const exported = new Date().toISOString();
  const TITLES = {'log-general':'Actividad VIGIL (alerts.json)','log-attacks':'Attack Log (attack_log.jsonl)','log-audit':'Audit Trail — Commits de configuración'};
  const title = TITLES[id]||'Log';

  let tableHead = '', tableRows = '';
  if(id==='log-general'){
    tableHead='<tr><th>Timestamp</th><th>Nivel</th><th>Mensaje</th><th>Regla / Kind</th></tr>';
    const COLORS={INFO:'#1a6fd4',WARNING:'#b8860b',CRITICAL:'#b83250',PANIC:'#cc3333'};
    tableRows = logData.map(e=>{
      const lvl=(e.level||'INFO').toUpperCase();
      const c=COLORS[lvl]||'#555';
      return `<tr><td class="mono">${esc(e.timestamp||'—')}</td><td><span class="pill" style="background:${c}20;color:${c};border:1px solid ${c}40">${lvl}</span></td><td>${esc(e.message||e.description||'')}</td><td class="mono">${esc([e.rule_id,e.kind,e.dept_code].filter(Boolean).join(' · ')||'—')}</td></tr>`;
    }).join('');
  } else if(id==='log-attacks'){
    tableHead='<tr><th>Timestamp</th><th>Tipo</th><th>IP</th><th>Geo</th><th>Ruta</th><th>Freq</th><th>User-Agent</th></tr>';
    const COLORS={FLOOD:'#b83250',BRUTE:'#cc3333',SCAN:'#b8860b',PROXY_SUSPECT:'#6a4fc0',SUSPICIOUS:'#555'};
    tableRows = attackData.map(e=>{
      const type=(e.type||e.classification||e.event||'EVENT').toUpperCase();
      const c=COLORS[type]||'#555';
      const geo=e.geo?.country?`${e.geo.country}${e.geo.city&&e.geo.city!=='unknown'?' / '+e.geo.city:''}`:(e.country||'—');
      return `<tr><td class="mono">${esc(e.timestamp_utc||e.timestamp||'—')}</td><td><span class="pill" style="background:${c}20;color:${c};border:1px solid ${c}40">${type}</span></td><td class="mono">${esc(e.ip||'—')}</td><td class="mono">${esc(geo)}</td><td class="mono">${esc(e.route||'—')}</td><td class="mono">${e.frequency_count??'—'}</td><td class="mono small">${esc((e.user_agent||'—').slice(0,100))}</td></tr>`;
    }).join('');
  } else if(id==='log-audit'){
    tableHead='<tr><th>Commit</th><th>Timestamp</th><th>Autor</th><th>Mensaje</th></tr>';
    tableRows = auditData.map(c=>`<tr><td class="mono">${esc(c.sha.slice(0,7))}</td><td class="mono">${esc(c.commit.author.date)}</td><td>${esc(c.commit.author.name||'—')}</td><td>${esc(c.commit.message.split('\n')[0])}</td></tr>`).join('');
  }
  if(!tableRows) tableRows='<tr><td colspan="8" style="text-align:center;color:#888;padding:20px">Sin datos</td></tr>';

  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

  const html = `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>VIGIL — ${esc(title)}</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:11px;color:#1a1a1a;background:#fff;padding:32px}
.header{margin-bottom:24px;padding-bottom:16px;border-bottom:2px solid #1a1a1a}
.header h1{font-size:18px;font-weight:700;letter-spacing:-.02em;margin-bottom:4px}
.header .meta{font-size:10px;color:#555;font-family:ui-monospace,monospace}
table{width:100%;border-collapse:collapse;margin-top:8px}
thead tr{background:#f4f4f6}
th{padding:7px 10px;text-align:left;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#444;border-bottom:2px solid #ddd;white-space:nowrap}
td{padding:5px 10px;border-bottom:1px solid #ebebeb;vertical-align:top;line-height:1.5}
tr:nth-child(even) td{background:#fafafa}
.mono{font-family:ui-monospace,monospace;font-size:10px;color:#333}
.small{font-size:9px}
.pill{display:inline-block;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;letter-spacing:.04em}
.footer{margin-top:24px;padding-top:12px;border-top:1px solid #ddd;font-size:9px;color:#888;display:flex;justify-content:space-between}
@media print{body{padding:16px}@page{margin:20mm}}
</style></head><body>
<div class="header">
  <h1>VIGIL — ${esc(title)}</h1>
  <div class="meta">Exportado: ${esc(exported)} &nbsp;·&nbsp; Repo: ${esc(REPO_OWNER)}/${esc(REPO_NAME)} &nbsp;·&nbsp; Entradas: ${id==='log-general'?logData.length:id==='log-attacks'?attackData.length:auditData.length}</div>
</div>
<table><thead>${tableHead}</thead><tbody>${tableRows}</tbody></table>
<div class="footer"><span>VIGIL — Sistema de Monitoreo Electoral</span><span>${esc(exported)}</span></div>
<script>window.onload=()=>window.print();<\/script>
</body></html>`;

  const blob = new Blob([html],{type:'text/html;charset=utf-8'});
  const url  = URL.createObjectURL(blob);
  const w    = window.open(url,'_blank');
  if(!w) URL.revokeObjectURL(url);
}

function copyLog(id){
  const content = _logTxtContent(id);
  if(!content) return;
  navigator.clipboard.writeText(content).then(()=>{
    const wrap = document.getElementById(id);
    if(!wrap) return;
    const old = wrap.style.outline;
    wrap.style.outline='1px solid var(--ok)';
    setTimeout(()=>wrap.style.outline=old,600);
  });
}

function generateIncidentReport(){
  const ts = new Date().toISOString();
  const byType = attackData.reduce((acc,e)=>{const t=(e.type||e.classification||'UNKNOWN').toUpperCase();acc[t]=(acc[t]||0)+1;return acc;},{});
  const summary = Object.entries(byType).map(([k,v])=>`  ${k.padEnd(16)} ${v} eventos`).join('\n');
  const lines   = attackData.map(e=>JSON.stringify(e)).join('\n');
  const report  = `VIGIL — REPORTE DE INCIDENTE\n${'═'.repeat(60)}\nGenerado:  ${ts}\nRepo:      ${REPO_OWNER}/${REPO_NAME}\nEventos:   ${attackData.length}\n\nRESUMEN POR TIPO:\n${summary||'  (sin datos)'}\n\n${'─'.repeat(60)}\nDETALLE JSONL (attack_log.jsonl):\n${'─'.repeat(60)}\n${lines}`;
  const blob = new Blob([report],{type:'text/plain;charset=utf-8'});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href=url; a.download=`centinel-incident-${Date.now()}.txt`; a.click();
  URL.revokeObjectURL(url);
}

function exportCustodyReport(){
  function esc(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  const ts = new Date().toISOString();

  // ── Session metadata ──
  const role    = (typeof getCurrentRole === 'function') ? getCurrentRole() : (sessionStorage.getItem('centinel_role')||'operador');
  const seedId  = (typeof getCurrentSeedId === 'function') ? getCurrentSeedId() : (sessionStorage.getItem('centinel_seed_id')||'S??');
  const slog    = (typeof _getSessionLog === 'function') ? _getSessionLog() : [];
  const logStart = slog.length ? slog[0].ts : ts;

  // ── OTS data ──
  const chain   = snapshotData?.chain || {};
  const otsStatus = {confirmed:'CONFIRMADO',pending:'PENDIENTE',error:'ERROR',unknown:'—'}[chain.ots_status]||'—';
  const otsColor  = {confirmed:'#1d6b3e',pending:'#8a6200',error:'#9b2335',unknown:'#555'}[chain.ots_status]||'#555';
  const otsHash   = chain.latest_hash || '—';
  const otsLen    = chain.chain_length ?? '—';
  const otsLast   = chain.last_anchor ? new Date(chain.last_anchor).toISOString() : '—';

  // ── Alert summary ──
  const byLevel = {};
  logData.forEach(e=>{ const l=(e.level||'INFO').toUpperCase(); byLevel[l]=(byLevel[l]||0)+1; });
  const alertRows = Object.entries(byLevel).map(([l,n])=>{
    const c={INFO:'#1a6fd4',WARNING:'#8a6200',CRITICAL:'#9b2335',PANIC:'#cc3333'}[l]||'#555';
    return `<tr><td><span class="pill" style="background:${c}20;color:${c};border:1px solid ${c}40">${l}</span></td><td class="mono">${n}</td></tr>`;
  }).join('') || '<tr><td colspan="2" style="color:#888">Sin alertas</td></tr>';

  // ── Config commits (last 10) ──
  const commitRows = auditData.slice(0,10).map(c=>
    `<tr><td class="mono">${esc(c.sha.slice(0,7))}</td><td class="mono">${esc(c.commit.author.date)}</td><td>${esc(c.commit.author.name||'—')}</td><td>${esc(c.commit.message.split('\n')[0])}</td></tr>`
  ).join('') || '<tr><td colspan="4" style="color:#888">Sin commits</td></tr>';

  // ── Session actions ──
  const actionRows = slog.map(e=>
    `<tr><td class="mono">${esc(e.ts)}</td><td class="mono">${esc(e.role||'—')}</td><td>${esc(e.action)}${e.detail?` <span style="color:#666">— ${esc(e.detail)}</span>`:''}</td></tr>`
  ).join('') || '<tr><td colspan="3" style="color:#888">Sin acciones registradas</td></tr>';

  // ── Country info ──
  const flag    = document.getElementById('country-current-flag')?.textContent || '';
  const country = document.getElementById('country-current-name')?.textContent || '—';
  const uptime  = document.getElementById('ms-uptime')?.textContent || '—';
  const mainUrl = document.getElementById('inp-main-url')?.value ||
                  document.getElementById('inp-main-url-easy')?.value || '—';

  const html = `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>VIGIL — Cadena de Custodia Electoral</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:11px;color:#1a1a1a;background:#fff;padding:32px}
h2{font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#333;margin:24px 0 8px;padding-bottom:4px;border-bottom:1px solid #ddd}
.header{margin-bottom:20px;padding-bottom:16px;border-bottom:2px solid #1a1a1a}
.header h1{font-size:18px;font-weight:700;letter-spacing:-.02em;margin-bottom:4px}
.header .meta{font-size:10px;color:#555;font-family:ui-monospace,monospace}
.meta-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 24px;background:#f8f8fa;border:1px solid #e0e0e8;padding:12px 16px;margin-bottom:8px}
.meta-row{display:flex;gap:8px;align-items:baseline}
.meta-label{font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#888;min-width:90px}
.meta-val{font-family:ui-monospace,monospace;font-size:11px;color:#222}
table{width:100%;border-collapse:collapse;margin-top:6px}
thead tr{background:#f4f4f6}
th{padding:6px 10px;text-align:left;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#444;border-bottom:2px solid #ddd;white-space:nowrap}
td{padding:5px 10px;border-bottom:1px solid #ebebeb;vertical-align:top;line-height:1.5}
tr:nth-child(even) td{background:#fafafa}
.mono{font-family:ui-monospace,monospace;font-size:10px;color:#333}
.pill{display:inline-block;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;letter-spacing:.04em}
.ots-card{background:#f0f7f4;border:1px solid #b6d9c8;padding:12px 16px;margin-top:6px}
.ots-status{display:inline-block;padding:2px 8px;font-size:10px;font-weight:700;letter-spacing:.06em;background:${otsColor}20;color:${otsColor};border:1px solid ${otsColor}40}
.footer{margin-top:24px;padding-top:10px;border-top:1px solid #ddd;font-size:9px;color:#888;display:flex;justify-content:space-between}
.integrity{background:#fffbea;border:1px solid #d4b066;padding:8px 12px;font-size:10px;margin-top:20px;line-height:1.6}
@media print{body{padding:16px}@page{margin:18mm}h2{page-break-after:avoid}}
</style></head><body>
<div class="header">
  <h1>VIGIL — Cadena de Custodia Electoral</h1>
  <div class="meta">Generado: ${esc(ts)} &nbsp;·&nbsp; Repo: ${esc(REPO_OWNER)}/${esc(REPO_NAME)} &nbsp;·&nbsp; Clave: ${esc(seedId)} &nbsp;·&nbsp; Rol: ${esc(role.toUpperCase())}</div>
</div>

<h2>Período de monitoreo</h2>
<div class="meta-grid">
  <div class="meta-row"><span class="meta-label">País</span><span class="meta-val">${esc(flag)} ${esc(country)}</span></div>
  <div class="meta-row"><span class="meta-label">URL monitoreada</span><span class="meta-val">${esc(mainUrl)}</span></div>
  <div class="meta-row"><span class="meta-label">Tiempo activo</span><span class="meta-val">${esc(uptime)}</span></div>
  <div class="meta-row"><span class="meta-label">Inicio de sesión</span><span class="meta-val">${esc(logStart)}</span></div>
  <div class="meta-row"><span class="meta-label">Alertas totales</span><span class="meta-val">${logData.length}</span></div>
  <div class="meta-row"><span class="meta-label">Eventos de ataque</span><span class="meta-val">${attackData.length}</span></div>
</div>

<h2>Sello de integridad (OpenTimestamps)</h2>
<div class="ots-card">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
    <span class="ots-status">${esc(otsStatus)}</span>
    <span style="font-size:10px;color:#555">Último ancla: <span class="mono">${esc(otsLast)}</span></span>
  </div>
  <div class="meta-row" style="margin-bottom:4px"><span class="meta-label">Hash (últimos 12)</span><span class="meta-val">${esc(otsHash.slice(-12)||'—')}</span></div>
  <div class="meta-row"><span class="meta-label">Bloques en cadena</span><span class="meta-val">${esc(String(otsLen))}</span></div>
</div>

<h2>Resumen de alertas</h2>
<table><thead><tr><th>Nivel</th><th>Cantidad</th></tr></thead><tbody>${alertRows}</tbody></table>

<h2>Commits de configuración (últimos 10)</h2>
<table><thead><tr><th>Commit</th><th>Timestamp</th><th>Autor</th><th>Mensaje</th></tr></thead><tbody>${commitRows}</tbody></table>

<h2>Registro de acciones de sesión</h2>
<table><thead><tr><th>Timestamp</th><th>Rol</th><th>Acción</th></tr></thead><tbody>${actionRows}</tbody></table>

<div class="integrity">
  <strong>Nota de integridad:</strong> Este informe fue generado por la clave <strong>${esc(seedId)}</strong> (rol: ${esc(role)}) a las ${esc(ts)}. Las marcas de tiempo OTS están ancladas en la blockchain de Bitcoin y pueden verificarse independientemente en <em>opentimestamps.org</em> sin depender de este sistema.
</div>

<div class="footer"><span>VIGIL — Sistema de Monitoreo Electoral · ${esc(REPO_OWNER)}/${esc(REPO_NAME)}</span><span>Generado: ${esc(ts)}</span></div>
<script>window.onload=()=>window.print();<\/script>
</body></html>`;

  const blob = new Blob([html],{type:'text/html;charset=utf-8'});
  const url  = URL.createObjectURL(blob);
  const w    = window.open(url,'_blank');
  if(!w) URL.revokeObjectURL(url);
}

// ══════════════════════════════════════════════════════════
// UTILS
// ══════════════════════════════════════════════════════════
function relTime(ts){
  if(!ts) return '—';
  const d = new Date(ts);
  if(isNaN(d)) return ts;
  const s = Math.floor((Date.now()-d)/1000);
  if(s<60) return `hace ${s}s`;
  if(s<3600) return `hace ${Math.floor(s/60)}m`;
  if(s<86400) return `hace ${Math.floor(s/3600)}h`;
  return `hace ${Math.floor(s/86400)}d`;
}

function deepClone(o){ return JSON.parse(JSON.stringify(o)); }

// ── 3 País monitoreado ────────────────────────────────────────────────────
async function loadCountrySelector() {
  const sel  = document.getElementById('country-select');
  const flag = document.getElementById('country-current-flag');
  const name = document.getElementById('country-current-name');
  const auth = document.getElementById('country-current-auth');
  if (!sel) return;

  // Current country from API status (best-effort), fall back to localStorage
  let currentCode = ACTIVE_COUNTRY_CODE || 'HN';
  try {
    const s = await fetch((window.CENTINEL_API_BASE||'') + '/api/setup/status');
    if (s.ok) { const d = await s.json(); currentCode = d.country_code || currentCode; }
  } catch(_) {}

  // Countries list from static file (always available, no API dependency)
  try {
    const r = await fetch(`${RAW_BASE}/web/data/countries.json?t=${Date.now()}`);
    if (!r.ok) { sel.innerHTML = '<option value="">Sin conexión al repositorio</option>'; return; }
    const countries = await r.json();
    sel.innerHTML = countries.map(c =>
      `<option value="${c.code}"${c.code === currentCode ? ' selected' : ''} data-flag="${c.flag}" data-name="${c.name}" data-auth="${c.authority}">${c.flag} ${c.name} — ${c.authority}</option>`
    ).join('');
    const cur = countries.find(c => c.code === currentCode);
    if (cur) {
      if (flag) flag.textContent = cur.flag;
      if (name) name.textContent = cur.name;
      if (auth) auth.textContent = cur.authority;
      ACTIVE_COUNTRY_CODE = currentCode;
      _updateMissionBar();
    }
  } catch(e) {
    sel.innerHTML = '<option value="">Error al cargar países</option>';
  }
}

async function onCountrySelectChange(code) {
  if (!code) return;
  await doChangeCountry();
}

// ── Operaciones ───────────────────────────────────────────────────────────────
let _pipelinePollTimer = null;
let _uptimeTimer = null;

function _startUptimeClock() {
  if (!localStorage.getItem('centinel_pipeline_start')) {
    localStorage.setItem('centinel_pipeline_start', Date.now().toString());
  }
  if (_uptimeTimer) return;
  _uptimeTimer = setInterval(_tickUptime, 1000);
  _tickUptime();
}

function _stopUptimeClock() {
  if (_uptimeTimer) { clearInterval(_uptimeTimer); _uptimeTimer = null; }
  // Save last duration before clearing, so the operator can see how long it ran
  const start = parseInt(localStorage.getItem('centinel_pipeline_start') || '0');
  if (start) {
    const diff = Math.floor((Date.now() - start) / 1000);
    localStorage.setItem('centinel_pipeline_last_uptime', diff.toString());
  }
  localStorage.removeItem('centinel_pipeline_start');
  const el = document.getElementById('ms-uptime');
  if (el) {
    const last = parseInt(localStorage.getItem('centinel_pipeline_last_uptime') || '0');
    if (last > 0) {
      const d = Math.floor(last / 86400), h = Math.floor((last % 86400) / 3600),
            m = Math.floor((last % 3600) / 60);
      let s = '';
      if (d > 0) s += d + 'd ';
      if (d > 0 || h > 0) s += h + 'h ';
      s += m + 'm';
      el.textContent = 'Último: ' + s.trim();
    } else {
      el.textContent = '—';
    }
  }
}

function _tickUptime() {
  const start = parseInt(localStorage.getItem('centinel_pipeline_start') || '0');
  if (!start) return;
  const el = document.getElementById('ms-uptime');
  if (!el) return;
  const diff = Math.floor((Date.now() - start) / 1000);
  const d = Math.floor(diff / 86400);
  const h = Math.floor((diff % 86400) / 3600);
  const m = Math.floor((diff % 3600) / 60);
  const s = diff % 60;
  let str = '';
  if (d > 0) str += d + 'd ';
  if (d > 0 || h > 0) str += h + 'h ';
  if (d > 0 || h > 0 || m > 0) str += m + 'm ';
  str += s + 's';
  el.textContent = str.trim();
}

async function doIniciar() {
  const btn = document.getElementById('btn-iniciar');
  const bar = document.getElementById('pipeline-status-bar');

  // If already running, stop instead
  if (btn?.classList.contains('running')) {
    if (!confirm('¿Detener el monitoreo en curso?')) return;
    try {
      await fetch((window.CENTINEL_API_BASE || '') + '/api/pipeline/stop', { method: 'POST' });
    } catch (_) {}
    auditLog('monitoreo detenido', '', {msgid:'MONITORING_STOP', severity:'WARNING'});
    _setPipelineUI(false);
    return;
  }

  // Validate URL is present and valid
  const mainUrl = (document.getElementById('inp-main-url-easy')?.value ||
                   document.getElementById('inp-main-url')?.value || '').trim();

  if (!mainUrl) {
    _setPipelineUI(false, null, '❌ Ingresa la URL del ente electoral antes de iniciar. (Ej: https://resultados.registraduria.gov.co/)');
    return;
  }

  if (!mainUrl.startsWith('http://') && !mainUrl.startsWith('https://')) {
    _setPipelineUI(false, null, '❌ La URL debe comenzar con http:// o https://');
    return;
  }

  try {
    new URL(mainUrl);
  } catch (_) {
    _setPipelineUI(false, null, '❌ URL inválida. Verifica el formato.');
    return;
  }

  if (btn) { btn.disabled = true; btn.textContent = 'Iniciando…'; }

  // Collect current config to send
  const epYaml = localConfig['config/prod/endpoints.yaml'] || null;

  // 1. Apply config silently to server
  try {
    await fetch((window.CENTINEL_API_BASE || '') + '/api/config/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        endpoints_yaml: epYaml,
        country_code: ACTIVE_COUNTRY_CODE || 'HN',
        main_url: mainUrl,
      }),
    });
  } catch (_) {}

  // 2. Start the pipeline
  try {
    const r = await fetch((window.CENTINEL_API_BASE || '') + '/api/pipeline/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ main_url: mainUrl, country_code: ACTIVE_COUNTRY_CODE || 'HN' }),
    });
    if (r.ok) {
      const d = await r.json();
      auditLog('monitoreo iniciado', ACTIVE_COUNTRY_CODE || 'HN', {msgid:'MONITORING_START', severity:'NOTICE'});
      _setPipelineUI(true, d.pid);
      _startPipelinePoll();
    } else {
      const err = await r.json().catch(() => ({}));
      const detail = err.detail || 'Error al iniciar el pipeline.';
      _setPipelineUI(false, null, '❌ ' + detail + ' (Verifica que VIGIL esté corriendo en el servidor)');
    }
  } catch (_) {
    // Offline / GitHub Pages — show clear message
    _setPipelineUI(false, null, '❌ Panel en modo offline. Para iniciar el monitoreo, ejecuta VIGIL en el servidor local y recarga.');
  } finally {
    if (btn) btn.disabled = false;
  }
}

function _setPipelineUI(running, pid, errorMsg) {
  const btn  = document.getElementById('btn-iniciar');
  const btnS = document.getElementById('btn-sidebar-iniciar');
  const bar  = document.getElementById('pipeline-status-bar');
  if (!btn) return;

  if (running) {
    btn.classList.add('running');
    btn.textContent = '⏹ Detener';
    btn.title = 'Monitoreo en curso — click para detener';
    if (btnS) { btnS.classList.add('running'); btnS.textContent = '⏹ Detener'; }
    _startUptimeClock();
    if (bar) {
      bar.style.display = '';
      bar.style.background = 'rgba(87,192,141,.08)';
      bar.style.border = '1px solid rgba(87,192,141,.25)';
      bar.style.color = 'var(--ok)';
      bar.innerHTML = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px"><circle cx="12" cy="12" r="10"/></svg> Monitoreo activo${pid ? ' · PID ' + pid : ''} · ${ACTIVE_COUNTRY_CODE || '—'}`;
    }
  } else {
    btn.classList.remove('running');
    btn.textContent = '▶ Iniciar';
    btn.title = 'Inicia el proceso de monitoreo y scraping en modo electoral';
    if (btnS) { btnS.classList.remove('running'); btnS.textContent = '▶ Iniciar'; }
    _stopUptimeClock();
    if (bar) {
      if (errorMsg) {
        bar.style.display = '';
        bar.style.background = 'rgba(220,50,47,.08)';
        bar.style.border = '1px solid rgba(220,50,47,.25)';
        bar.style.color = 'var(--alert)';
        bar.textContent = errorMsg;
      } else {
        bar.style.display = 'none';
      }
    }
  }
}

function _startPipelinePoll() {
  if (_pipelinePollTimer) return;
  _pipelinePollTimer = setInterval(async () => {
    try {
      const r = await fetch((window.CENTINEL_API_BASE || '') + '/api/pipeline/status');
      if (r.ok) {
        const d = await r.json();
        if (!d.running) {
          clearInterval(_pipelinePollTimer);
          _pipelinePollTimer = null;
          _setPipelineUI(false);
        }
      }
    } catch (_) {
      clearInterval(_pipelinePollTimer);
      _pipelinePollTimer = null;
    }
  }, 10000); // poll every 10s
}

function doEmergencia() { openEmergencyModal(); }

function openEmergencyModal() {
  document.getElementById('emg-confirm-step1').style.display = '';
  document.getElementById('emg-confirm-step2').style.display = 'none';
  const modal = document.getElementById('emergency-modal');
  modal.style.display = 'flex';
}
function closeEmergencyModal() {
  document.getElementById('emergency-modal').style.display = 'none';
  clearInterval(_emgTimer);
  _emgTimer = null;
}
function emergencyStep2() {
  document.getElementById('emg-confirm-step1').style.display = 'none';
  document.getElementById('emg-confirm-step2').style.display = '';
  let t = 3;
  const cdEl = document.getElementById('emg-countdown');
  const btn = document.getElementById('btn-emg-confirm');
  if (cdEl) cdEl.textContent = t;
  if (btn) { btn.disabled = true; btn.innerHTML = `⚠ Detener todo (<span id="emg-countdown">${t}</span>)`; }
  _emgTimer = setInterval(() => {
    t--;
    const cd = document.getElementById('emg-countdown');
    if (cd) cd.textContent = t;
    if (t <= 0) {
      clearInterval(_emgTimer);
      _emgTimer = null;
      const b = document.getElementById('btn-emg-confirm');
      if (b) { b.disabled = false; b.textContent = '⚠ Detener todo'; }
    }
  }, 1000);
}
function executeEmergency() {
  auditLog('EMERGENCIA activada', '', {msgid:'EMERGENCY_STOP', severity:'EMERGENCY'});
  closeEmergencyModal();
  loadPreset('emergency');
  markDirty();
  applyChanges();
}

async function saveElectoralUrl() {
  const urlEl = document.getElementById('inp-main-url-easy');
  const url = (urlEl?.value || '').trim();
  const btn = document.getElementById('btn-discover');
  const res = document.getElementById('discover-result');

  if (!url) return;
  if(urlEl && !validateUrlField(urlEl)){
    if(res){ res.style.display=''; res.style.background='rgba(223,107,134,.08)'; res.style.border='1px solid rgba(223,107,134,.25)'; res.style.color='var(--bad)'; res.textContent='URL inválida — debe comenzar con https:// y contener un dominio válido.'; }
    return;
  }

  // Persist locally so the config saves regardless of API availability
  if (localConfig['config/prod/endpoints.yaml']?.cne) {
    localConfig['config/prod/endpoints.yaml'].cne.main_url = url;
  }
  markDirty();

  if (btn) { btn.disabled = true; btn.textContent = 'Buscando…'; }
  if (res) { res.style.display = ''; res.style.background = 'rgba(212,176,102,.08)'; res.style.border = '1px solid rgba(212,176,102,.25)'; res.style.color = 'var(--warn)'; res.textContent = 'Analizando el sitio del ente electoral…'; }

  try {
    const r = await fetch((window.CENTINEL_API_BASE || '') + '/api/setup/discover_endpoints', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ main_url: url, country_code: ACTIVE_COUNTRY_CODE || 'HN' }),
    });

    if (r.ok) {
      const d = await r.json();
      const n = d.endpoints_found || 0;

      // Update localConfig with discovered endpoints
      if (d.endpoints?.length) {
        if (!localConfig['config/prod/endpoints.yaml']) localConfig['config/prod/endpoints.yaml'] = {};
        if (!localConfig['config/prod/endpoints.yaml'].cne) localConfig['config/prod/endpoints.yaml'].cne = {};
        // Use the full discovered main_url from backend if provided; otherwise keep user's input
        const discoveredMainUrl = d.main_url || url;
        localConfig['config/prod/endpoints.yaml'].cne.main_url = discoveredMainUrl;
        localConfig['config/prod/endpoints.yaml'].cne.presidential_endpoints = d.endpoints;
        // Sync fields: technical gets full path, friendly gets just the origin
        const inpFull = document.getElementById('inp-main-url');
        const inpEasy = document.getElementById('inp-main-url-easy');
        if (inpFull) inpFull.value = discoveredMainUrl;
        if (inpEasy) {
          try { inpEasy.value = new URL(discoveredMainUrl).origin; } catch(_) {}
        }
        buildEndpointsTable();
      }

      if (res) {
        res.style.background = 'rgba(87,192,141,.08)';
        res.style.border = '1px solid rgba(87,192,141,.25)';
        res.style.color = 'var(--ok)';
        res.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg> ${n} endpoint${n !== 1 ? 's' : ''} descubierto${n !== 1 ? 's' : ''} — tabla actualizada`;
      }
    } else {
      // API error — show message but URL is saved locally
      const err = await r.json().catch(() => ({}));
      if (res) {
        res.style.background = 'rgba(220,50,47,.08)';
        res.style.border = '1px solid rgba(220,50,47,.25)';
        res.style.color = 'var(--alert)';
        res.textContent = err.detail || 'Error al descubrir endpoints. URL guardada localmente.';
      }
    }
  } catch (_) {
    // Offline / GitHub Pages — URL is already saved locally above
    if (res) {
      res.style.background = 'rgba(212,176,102,.08)';
      res.style.border = '1px solid rgba(212,176,102,.25)';
      res.style.color = 'var(--warn)';
      res.textContent = 'Servidor no disponible. URL guardada localmente — el descubrimiento se ejecutará al iniciar Centinel.';
    }
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Guardar y descubrir'; }
  }
}

// Populate localConfig endpoints from current DEPTS data (no API required).
// Runs after loadDepartments() so DEPTS is already filled.
function syncEndpointsFromDepts(force = false) {
  if (!DEPTS || DEPTS.length === 0) return;
  const nat = DEPTS.find(d => d.code === '00');
  const divs = DEPTS.filter(d => d.code !== '00');

  if (!localConfig['config/prod/endpoints.yaml']) localConfig['config/prod/endpoints.yaml'] = {};
  const ep = localConfig['config/prod/endpoints.yaml'];
  if (!ep.cne) ep.cne = {};

  if ((force || !ep.cne.main_url) && nat?.url) ep.cne.main_url = nat.url;

  ep.cne.presidential_endpoints = divs.map(d => ({
    department_code: parseInt(d.code, 10) || d.code,
    url: d.url || '',
  }));

  const inpMain = document.getElementById('inp-main-url');
  const inpMainEasy = document.getElementById('inp-main-url-easy');
  if (inpMain && (force || !inpMain.value) && nat?.url) inpMain.value = nat.url;
  if (inpMainEasy && (force || !inpMainEasy.value) && nat?.url) {
    try { inpMainEasy.value = new URL(nat.url).origin; } catch(_) { inpMainEasy.value = nat.url; }
  }

  markDirty();
  buildEndpointsTable();
}

async function doChangeCountry() {
  const sel = document.getElementById('country-select');
  const btn = document.getElementById('btn-change-country');
  const res = document.getElementById('country-change-result');
  const swWarn = document.getElementById('country-swarm-warn');
  if (!sel || !sel.value) return;
  const code = sel.value;

  if (btn) { btn.disabled = true; btn.textContent = 'Aplicando…'; }
  if (res) res.style.display = 'none';

  // Extract display data from the selected option
  const opt = sel.options[sel.selectedIndex];
  const optFlag = opt ? (opt.dataset.flag || '') : '';
  const optName = opt ? (opt.dataset.name || code) : code;
  const optAuth = opt ? (opt.dataset.auth || '') : '';

  // Update client-side state immediately (no API required)
  ACTIVE_COUNTRY_CODE = code;
  localStorage.setItem('centinel_country_code', code);

  const flagEl = document.getElementById('country-current-flag');
  const nameEl = document.getElementById('country-current-name');
  const authEl = document.getElementById('country-current-auth');
  if (flagEl) flagEl.textContent = optFlag;
  if (nameEl) nameEl.textContent = optName;
  if (authEl) authEl.textContent = optAuth;

  // Load country-specific departments and rebuild grid
  await loadDepartments(code);
  buildDeptGrid();

  // Auto-populate endpoints config from the new country's department URLs
  syncEndpointsFromDepts(true);

  // Best-effort API sync (silent on failure — works offline / GitHub Pages)
  let apiSynced = false;
  try {
    const r = await fetch((window.CENTINEL_API_BASE||'') + '/api/setup/change_country', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({country_code: code}),
    });
    if (r.ok) {
      const d = await r.json();
      if (d.success) {
        apiSynced = true;
        loadSeedStatus();
        if (swWarn) {
          try {
            const sw = await fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/status');
            const sd = sw.ok ? await sw.json() : {running: false};
            swWarn.style.display = (sd.running || sd.connected_peers > 0) ? '' : 'none';
          } catch(_) { swWarn.style.display = 'none'; }
        }
      }
    }
  } catch(_) {}

  if (res) {
    res.style.display = '';
    res.style.background = 'rgba(87,192,141,.08)';
    res.style.border = '1px solid rgba(87,192,141,.25)';
    res.style.color = 'var(--ok)';
    const syncNote = apiSynced ? '' : ' <span style="opacity:.6;font-size:.85em">(modo offline)</span>';
    res.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg> País establecido: ${optFlag} <strong>${optName}</strong>${optAuth ? ' — ' + optAuth : ''}${syncNote}`;
  }

  if (btn) { btn.disabled = false; btn.textContent = 'Cambiar país'; }
  auditLog('país cambiado', `${optFlag} ${optName}`, {msgid:'COUNTRY_CHANGE', severity:'NOTICE'});
  _updateMissionBar();

  // If swarm was running, reconnect with new country so isolation takes effect immediately
  try {
    const sw = await fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/status');
    if (sw.ok) {
      const sd = await sw.json();
      if (sd.running) {
        await fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/disconnect', { method: 'POST' });
        await fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/connect', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({}),
        });
      }
    }
  } catch(_) {}
}

// ── 7 Acceso y Seeds ──────────────────────────────────────────────────────
async function loadSeedStatus() {
  const el = document.getElementById('seed-status');
  if (!el) return;
  try {
    const r = await fetch((window.CENTINEL_API_BASE||'') + '/api/setup/status');
    const s = await r.json();
    if (s.configured) {
      const since = s.configured_at ? new Date(s.configured_at).toLocaleString() : '—';
      const regen = s.last_regenerated_at ? new Date(s.last_regenerated_at).toLocaleString() : t('seed.nunca');
      el.innerHTML = `
        <span style="color:var(--ok)"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg> ${t('seed.configurado')}</span><br>
        ${t('seed.pais')}: <strong>${s.country_name || s.country_code || '—'}</strong><br>
        ${t('seed.configurado_el')}: ${since}<br>
        ${t('seed.ultima_regen')}: ${regen}<br>
        ${t('seed.claves_activas')}: <strong>12</strong>
      `;
    } else {
      el.innerHTML = `<span style="color:var(--warn)"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="17" r="1" fill="currentColor"/></svg> ${t('seed.no_configurado')}</span>`;
      document.getElementById('btn-regen').disabled = true;
    }
  } catch(e) {
    el.innerHTML = `<span style="color:var(--muted)">${t('seed.error_carga')}</span>`;
  }
}

async function doRegenerate() {
  const btn = document.querySelector('#regen-confirm button[onclick="doRegenerate()"]');
  const errEl = document.getElementById('regen-err');
  errEl.textContent = '';

  if (window.CENTINEL_API_BASE) {
    const seedValue = ((document.getElementById('regen-seed-value')||{}).value||'').trim();
    if (!seedValue) {
      errEl.textContent = t('seed.ingresa_clave');
      return;
    }

    if (btn) { btn.disabled = true; btn.textContent = t('seed.regenerando'); }
    document.getElementById('regen-confirm').style.display = 'none';

    try {
      const statusR = await fetch(window.CENTINEL_API_BASE + '/api/setup/status');
      const status = await statusR.json();

      const r = await fetch(window.CENTINEL_API_BASE + '/api/setup/regenerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country_code: status.country_code || null,
          seed_value: seedValue,
        }),
      });

      if (!r.ok) {
        const err = await r.json().catch(()=>({}));
        document.getElementById('regen-confirm').style.display = 'block';
        errEl.textContent = err.detail || (t('seed.error_prefix') + ' ' + r.status);
        return;
      }

      const seedInput = document.getElementById('regen-seed-value');
      if (seedInput) seedInput.value = '';

      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `centinel-seeds-nuevos-${Date.now()}.pdf`;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 5000);

      await loadSeedStatus();
    } catch(e) {
      alert('Error: ' + e.message);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = t('seed.si_regenerar'); }
    }
  } else {
    const workflowUrl = `https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/regenerate-seeds.yml`;
    document.getElementById('regen-confirm').style.display = 'none';
    errEl.innerHTML = `<span style="color:var(--warn)">${t('seed.modo_pages')}<br>` +
      `<a href="${workflowUrl}" target="_blank" rel="noopener" style="color:var(--accent)">` +
      `${t('seed.abre_workflow')}</a> ${t('seed.run_workflow_hint')}</span>`;
  }
}


async function reloadConfig(){
  await loadConfig();
  await loadSnapshot();
  isDirty=false; updateDirtyState();
}

// Sidebar scroll
// scrollTo — view-aware: if the target section lives in another phase view,
// switch to that view first (setView lives in ops-command.js), then scroll.
function scrollTo(id){
  const el = document.getElementById(id);
  if(el){
    const phase = el.closest('[data-phase]')?.dataset.phase;
    if(phase && typeof setView==='function') setView(phase, {scroll:false});
    el.scrollIntoView({behavior:'smooth',block:'start'});
  }
  document.querySelectorAll('#sidebar a').forEach(a=>{
    a.classList.toggle('active', a.getAttribute('href')==='#'+id);
  });
}

// ── 8 Red de Nodos ────────────────────────────────────────────────────────────
let _swarmPollTimer = null;

async function loadSwarmStatus() {
  try {
    const r = await fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/status');
    if (!r.ok) return;
    const s = await r.json();
    _renderSwarmStatus(s);
  } catch(_) {}
}

function _renderSwarmStatus(s) {
  const dot   = document.getElementById('swarm-dot');
  const label = document.getElementById('swarm-label');
  const meta  = document.getElementById('swarm-meta');
  const nodeIdEl = document.getElementById('swarm-node-id');
  const lastBcast = document.getElementById('swarm-last-bcast');
  const consensusRow = document.getElementById('swarm-consensus-row');
  const consensusVal = document.getElementById('swarm-consensus-val');
  const btnConnect = document.getElementById('btn-connect');
  const btnDisconn = document.getElementById('btn-disconnect');
  const peersSection = document.getElementById('swarm-peers-section');
  const peerCount = document.getElementById('swarm-peer-count');
  const tbody = document.getElementById('swarm-peers-tbody');
  const banner = document.getElementById('swarm-consensus-banner');

  const hint = document.getElementById('swarm-hint');
  if (s.running && s.connected_peers > 0) {
    dot.style.background = 'var(--ok)';
    label.style.color = 'var(--ok)';
    label.textContent = `${t('swarm.en_red')}  ·  ${s.connected_peers} ${s.connected_peers!==1?t('swarm.nodos'):t('swarm.nodo')} ${s.connected_peers!==1?t('swarm.activos'):t('swarm.activo')}`;
    if (hint) hint.style.display = 'none';
    _stopSwarmPoll();
  } else if (s.running) {
    dot.style.background = 'var(--warn)';
    label.style.color = 'var(--warn)';
    label.textContent = t('swarm.conectando');
    if (hint) hint.style.display = 'none';
  } else {
    dot.style.background = 'var(--muted)';
    label.style.color = 'var(--muted)';
    label.textContent = t('swarm.desconectado');
    if (hint) hint.style.display = '';
  }

  meta.style.display = s.node_id && s.node_id !== 'unknown' ? '' : 'none';
  if (nodeIdEl) nodeIdEl.textContent = `Node ID: ${s.node_id || '—'}`;
  if (lastBcast) lastBcast.textContent = s.last_broadcast_utc ? relTime(s.last_broadcast_utc) : '—';

  if (s.consensus_reached && s.consensus_root) {
    consensusRow.style.display = '';
    consensusVal.textContent = `${s.consensus_count}/${s.connected_peers}  ·  ${s.consensus_root.slice(0,12)}…`;
    banner.style.display = '';
    banner.style.background = 'rgba(87,192,141,.08)';
    banner.style.border = '1px solid rgba(87,192,141,.3)';
    banner.style.color = 'var(--ok)';
    banner.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg> ${t('swarm.consenso_alcanzado')} <strong>${s.consensus_count} ${window.OPS_LANG==='en'?'of':'de'} ${s.connected_peers} ${t('swarm.nodos')}</strong> ${t('swarm.comparten_merkle')} (<code>${s.consensus_root.slice(0,16)}…</code>). ${t('swarm.datos_consistentes')}`;
  } else if (s.connected_peers > 0) {
    consensusRow.style.display = 'none';
    banner.style.display = '';
    banner.style.background = 'rgba(212,176,102,.08)';
    banner.style.border = '1px solid rgba(212,176,102,.3)';
    banner.style.color = 'var(--warn)';
    banner.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="17" r="1" fill="currentColor"/></svg> ${t('swarm.sin_consenso')} (${s.consensus_count || 0}/${s.connected_peers} ${t('swarm.coinciden')}).`;
  } else {
    consensusRow.style.display = 'none';
    banner.style.display = 'none';
  }

  btnConnect.style.display = s.running ? 'none' : '';
  btnDisconn.style.display = s.running ? '' : 'none';

  peersSection.style.display = (s.peers && s.peers.length) ? '' : 'none';
  if (peerCount) peerCount.textContent = s.connected_peers || 0;

  if (tbody && s.peers) {
    tbody.innerHTML = s.peers.map(p => {
      const inSync = s.consensus_root && p.merkle_root === s.consensus_root;
      const syncBadge = inSync
        ? `<span style="color:var(--ok)">${t('swarm.en_sync')}</span>`
        : `<span style="color:var(--warn)">${t('swarm.diverge')}</span>`;
      const ts = p.timestamp_utc ? relTime(p.timestamp_utc) : '—';
      const flagMap = {HN:'🇭🇳',GT:'🇬🇹',SV:'🇸🇻',NI:'🇳🇮',CR:'🇨🇷',PA:'🇵🇦',MX:'🇲🇽',CO:'🇨🇴',VE:'🇻🇪',PE:'🇵🇪',EC:'🇪🇨',BO:'🇧🇴',PY:'🇵🇾',UY:'🇺🇾',AR:'🇦🇷',CL:'🇨🇱',BR:'🇧🇷',DO:'🇩🇴',CU:'🇨🇺',PR:'🇵🇷'};
      const flag = flagMap[p.country_code] || '🌎';
      const specIcons = {temporal:'⏱', statistical:'📊', structural:'🔗', general:'⚙️'};
      const specLabel = p.specialization || 'general';
      const specBadge = `<span style="font-size:11px;opacity:.8">${specIcons[specLabel]||'⚙️'} ${specLabel}</span>`;
      return `<tr style="border-bottom:1px solid var(--border)">
        <td style="padding:7px 10px;font-family:var(--mono);font-size:11px">${p.node_id}</td>
        <td style="padding:7px 10px">${flag} ${p.country_code}</td>
        <td style="padding:7px 10px">${p.chain_length ?? '—'}</td>
        <td style="padding:7px 10px;font-family:var(--mono);font-size:11px">${(p.merkle_root||'').slice(0,12)}…</td>
        <td style="padding:7px 10px">${syncBadge}</td>
        <td style="padding:7px 10px">${specBadge}</td>
        <td style="padding:7px 10px;color:var(--muted)">${ts}</td>
        <td style="padding:7px 10px"><button class="kick-btn" onclick="kickPeer('${p.node_id}')">${t('swarm.kick')}</button></td>
      </tr>`;
    }).join('');
  }

  // Load consensus findings (works even without swarm running)
  loadSwarmConsensus();
}

async function loadSwarmConsensus() {
  try {
    const r = await fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/consensus_findings?min_nodes=1&limit=20');
    if (!r.ok) return;
    const d = await r.json();
    const items = d.consensus || [];
    const empty = document.getElementById('swarm-consensus-empty');
    const tableWrap = document.getElementById('swarm-consensus-table-wrap');
    const tbody = document.getElementById('swarm-consensus-tbody');
    if (!empty || !tableWrap || !tbody) return;
    if (!items.length) {
      empty.style.display = '';
      tableWrap.style.display = 'none';
      return;
    }
    empty.style.display = 'none';
    tableWrap.style.display = '';
    const sevColor = s => s === 'CRITICAL' ? 'var(--alert)' : 'var(--warn)';
    tbody.innerHTML = items.map(c => {
      const nc = parseInt(c.node_count, 10) || 1;
      const rowBg = nc >= 5 ? 'rgba(220,50,47,.08)' : nc >= 2 ? 'rgba(212,176,102,.08)' : '';
      const snap = (c.snapshot_id || '—').slice(0, 8);
      const ts = c.last_seen ? relTime(c.last_seen) : '—';
      return `<tr style="border-bottom:1px solid var(--border);background:${rowBg}">
        <td style="padding:7px 10px;font-family:var(--mono);font-size:11px">${c.rule_key}</td>
        <td style="padding:7px 10px;font-family:var(--mono);font-size:11px">${snap}…</td>
        <td style="padding:7px 10px;font-weight:600">${nc} ${nc!==1?t('swarm.nodos'):t('swarm.nodo')}</td>
        <td style="padding:7px 10px;color:${sevColor(c.severity)};font-weight:600">${c.severity}</td>
        <td style="padding:7px 10px;color:var(--muted)">${ts}</td>
      </tr>`;
    }).join('');
  } catch(_) {}
}

async function doSwarmConnect() {
  const btn = document.getElementById('btn-connect');
  if (btn) { btn.disabled = true; btn.textContent = t('swarm.conectando').replace('…','').trim() + '…'; }

  const myUrl = (document.getElementById('swarm-my-url')||{}).value || undefined;
  try {
    const r = await fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/connect', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ my_url: myUrl || null }),
    });
    if (!r.ok) {
      const err = await r.json().catch(()=>({}));
      alert(t('swarm.error_conectar') + ': ' + (err.detail || r.status));
      if (btn) { btn.disabled = false; btn.textContent = t('swarm.conectar'); }
      return;
    }
    await loadSwarmStatus();
    _startSwarmPoll();
  } catch(e) {
    alert(t('swarm.error') + ': ' + e.message);
    if (btn) { btn.disabled = false; btn.textContent = t('swarm.conectar'); }
  }
}

async function doSwarmDisconnect() {
  if(!confirm(t('swarm.confirm_desconectar'))) return;
  const btn = document.getElementById('btn-disconnect');
  if (btn) { btn.disabled = true; btn.textContent = t('swarm.desconectando'); }
  _stopSwarmPoll();
  try {
    await fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/disconnect', { method: 'POST' });
    await loadSwarmStatus();
  } catch(_) {}
  if (btn) { btn.disabled = false; btn.textContent = t('swarm.desconectar'); }
}

function _startSwarmPoll() {
  if (_swarmPollTimer) return;
  _swarmPollTimer = setInterval(() => { loadSwarmStatus(); refreshSwarmPanel(); }, 5000);
  refreshSwarmPanel();
}

function _stopSwarmPoll() {
  if (_swarmPollTimer) { clearInterval(_swarmPollTimer); _swarmPollTimer = null; }
  setTimeout(() => {
    _swarmPollTimer = setInterval(() => { loadSwarmStatus(); refreshSwarmPanel(); }, 30000);
  }, 100);
}

// ── 8 Sala management ───────────────────────────────────────────────────────
let _salaId = null;

function salaTab(tab) {
  document.getElementById('sala-pick').style.display = tab === 'reset' ? '' : 'none';
  document.getElementById('sala-crear-panel').style.display = tab === 'crear' ? '' : 'none';
  document.getElementById('sala-unirse-panel').style.display = tab === 'unirse' ? '' : 'none';
}

async function createSala() {
  const arr = new Uint8Array(3);
  crypto.getRandomValues(arr);
  _salaId = Array.from(arr).map(b => b.toString(16).padStart(2, '0')).join('');

  let nodeId = '—', myUrl = '';
  try {
    const r = await fetch((window.CENTINEL_API_BASE || '') + '/api/swarm/status');
    if (r.ok) { const s = await r.json(); nodeId = s.node_id || '—'; myUrl = s.my_url || document.getElementById('swarm-my-url')?.value || ''; }
  } catch(_) {}

  // Simple invite string: URL if available, else just the code
  const inviteStr = myUrl ? `${myUrl}#sala=${_salaId}` : _salaId;
  const inviteObj = { sala_id: _salaId, node_id: nodeId, organizer_url: myUrl || null };

  const inp = document.getElementById('sala-invite-text');
  if (inp) inp.value = inviteStr;
  const box = document.getElementById('sala-invite-json');
  if (box) box.textContent = JSON.stringify(inviteObj, null, 2);

  document.getElementById('sala-pick').style.display = 'none';
  document.getElementById('sala-unirse-panel').style.display = 'none';
  document.getElementById('sala-crear-panel').style.display = '';
  _addActivity('ok', `Enjambre creado — código ${_salaId}`, 'ahora');
}

function copyInviteText() {
  const val = document.getElementById('sala-invite-text')?.value || '';
  navigator.clipboard?.writeText(val).then(() => {
    const btn = document.getElementById('btn-copy-invite');
    if (btn) { btn.textContent = '✓ Copiado'; setTimeout(() => btn.textContent = 'Copiar', 1800); }
  });
}

function _showSalaDetails() {
  const d = document.getElementById('sala-tech-details');
  const b = document.getElementById('btn-sala-details');
  if (!d) return;
  const shown = d.style.display !== 'none';
  d.style.display = shown ? 'none' : '';
  if (b) b.textContent = shown ? 'Ver detalles técnicos' : 'Ocultar detalles';
}

async function joinSala() {
  const stat = document.getElementById('sala-join-stat');
  stat.textContent = 'Conectando…'; stat.style.color = 'var(--warn)';

  const raw = (document.getElementById('sala-join-input')?.value || '').trim();
  if (!raw) { stat.textContent = 'Pega la invitación primero.'; stat.style.color = 'var(--bad)'; return; }

  // Extract URL from invite string (may be URL#sala=code, plain URL, or raw JSON)
  let targetUrl = '';
  try {
    const parsed = JSON.parse(raw);
    targetUrl = parsed.organizer_url || '';
  } catch(_) {
    // Try as URL (strip #sala=… fragment)
    try { targetUrl = new URL(raw).origin + new URL(raw).pathname; } catch(_) { targetUrl = raw; }
  }
  if (!targetUrl) { stat.textContent = 'No se pudo leer la invitación.'; stat.style.color = 'var(--bad)'; return; }

  try {
    const r = await fetch((window.CENTINEL_API_BASE || '') + '/api/swarm/connect', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ my_url: targetUrl }),
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    stat.textContent = '✓ Conectado al enjambre.'; stat.style.color = 'var(--ok)';
    _addActivity('ok', `Unido al enjambre de ${targetUrl}`, 'ahora');
    await loadSwarmStatus();
    _startSwarmPoll();
  } catch(e) {
    stat.textContent = 'Error: ' + e.message; stat.style.color = 'var(--bad)';
  }
}

// ── Kick peer ────────────────────────────────────────────────────────────────
async function kickPeer(nodeId) {
  if (!confirm(`¿Expulsar nodo ${nodeId} del enjambre?\n\nEsto lo bloquea hasta que el engine reinicie.`)) return;
  try {
    const r = await fetch((window.CENTINEL_API_BASE || '') + `/api/swarm/peer/${nodeId}`, { method: 'DELETE' });
    if (!r.ok) { const e = await r.json().catch(() => ({})); alert('Error: ' + (e.detail || r.status)); return; }
    _addActivity('bad', `Nodo expulsado: ${nodeId}`, 'ahora');
    await loadSwarmStatus();
    await loadReputationPanel();
  } catch(e) { alert('Error: ' + e.message); }
}

// ── Reputation panel ─────────────────────────────────────────────────────────
let _repPollTimer = null;

async function loadReputationPanel() {
  try {
    const r = await fetch((window.CENTINEL_API_BASE || '') + '/api/swarm/reputation');
    if (!r.ok) return;
    const d = await r.json();
    _renderReputationPanel(d);
  } catch(_) {}
}

function _renderReputationPanel(d) {
  const nodes = d.nodes || [];
  const rc = d.ring_counts || {};
  const total = d.total || nodes.length;

  // Ring summary bar
  const sumEl = document.getElementById('rep-ring-summary');
  if (sumEl) sumEl.style.display = nodes.length ? '' : 'none';
  const r0 = rc.ring0 || 0, r1 = rc.ring1 || 0, r2 = rc.ring2 || 0;
  const _set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  _set('rep-r0-count', r0); _set('rep-r1-count', r1); _set('rep-r2-count', r2); _set('rep-total', total);
  const bar = document.getElementById('rep-ring-bar');
  if (bar && total > 0) {
    bar.innerHTML = [
      `<div style="flex:${r0};background:#b08cf0" title="Ring-0: ${r0}"></div>`,
      `<div style="flex:${r1};background:var(--ok)" title="Ring-1: ${r1}"></div>`,
      `<div style="flex:${r2};background:var(--border)" title="Ring-2: ${r2}"></div>`,
    ].join('');
  }

  // Node cards
  const list = document.getElementById('rep-nodes-list');
  if (!list) return;
  if (!nodes.length) {
    list.innerHTML = '<div style="font-size:12px;color:var(--muted);font-style:italic">Sin nodos registrados.</div>';
    return;
  }
  const ringCls = r => r === 0 ? 'r0' : r === 1 ? 'r1' : 'r2';
  const ringLabel = r => r === 0 ? 'Ring-0' : r === 1 ? 'Ring-1' : 'Ring-2';
  const trustColor = t => t >= 0.85 ? 'var(--ok)' : t >= 0.5 ? 'var(--warn)' : 'var(--bad)';
  const flagMap = {HN:'🇭🇳',GT:'🇬🇹',SV:'🇸🇻',NI:'🇳🇮',CR:'🇨🇷',PA:'🇵🇦',MX:'🇲🇽',CO:'🇨🇴',VE:'🇻🇪'};
  list.innerHTML = nodes.map(n => {
    const t = n.trust_score ?? 0.5;
    const pct = Math.round(t * 100);
    const flag = flagMap[n.country_code] || '🌎';
    const kickBtn = n.ring !== 0 ? `<button class="kick-btn" onclick="kickPeer('${n.node_id}')">Kick</button>` : '';
    return `<div class="rep-node-card">
      <span class="ring-badge ${ringCls(n.ring)}">${ringLabel(n.ring)}</span>
      <span style="font-family:var(--mono);font-size:12px;min-width:80px">${n.node_id}</span>
      <span style="font-size:11px;color:var(--muted)">${flag} arr:${n.arrival_order ?? '—'}</span>
      <div class="trust-bar-wrap" title="Trust: ${t}">
        <div style="font-size:11px;color:${trustColor(t)};margin-bottom:3px;font-weight:600">${pct}%</div>
        <div class="trust-bar-bg"><div class="trust-bar-fill" style="width:${pct}%;background:${trustColor(t)}"></div></div>
        <div style="font-size:10px;color:var(--muted);margin-top:2px">α ${n.alpha} · β ${n.beta}</div>
      </div>
      <div style="font-size:11px;color:var(--muted)">
        ${n.betrayal_count > 0 ? `<span style="color:var(--bad)">⚠ ${n.betrayal_count} traición${n.betrayal_count!==1?'es':''}</span>` : ''}
        ${n.outage_count > 0 ? ` · ${n.outage_count} corte${n.outage_count!==1?'s':''}` : ''}
      </div>
      <div class="rep-node-actions">
        <button class="hist-btn" onclick="openSwarmHist('${n.node_id}')">Historial</button>
        ${kickBtn}
      </div>
    </div>`;
  }).join('');
}

// ── Reputation history modal ──────────────────────────────────────────────────
async function openSwarmHist(nodeId) {
  document.getElementById('swarm-hist-modal').classList.add('open');
  document.getElementById('hist-modal-node').textContent = nodeId;
  document.getElementById('hist-modal-title').textContent = 'Historial de reputación';
  document.getElementById('hist-modal-body').innerHTML =
    '<div style="color:var(--muted);font-style:italic;font-size:12px">Cargando…</div>';
  try {
    const r = await fetch((window.CENTINEL_API_BASE || '') + `/api/swarm/reputation/${nodeId}/history?limit=50`);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    const evts = d.events || [];
    if (!evts.length) {
      document.getElementById('hist-modal-body').innerHTML =
        '<div style="color:var(--muted);font-style:italic;font-size:12px">Sin eventos registrados.</div>';
      return;
    }
    const evtCls = t => t.includes('BETRAY') || t.includes('DEMOTION') ? 'bad' : t.includes('PROMOTE') ? 'ok' : 'warn';
    document.getElementById('hist-modal-body').innerHTML = evts.map(e => `
      <div class="hist-event-row">
        <div class="hist-evt-type ${evtCls(e.event_type)}">${e.event_type}</div>
        <div style="color:var(--muted);font-size:11px">α ${e.alpha} · β ${e.beta} · trust ${(e.trust_score*100).toFixed(1)}% · Ring-${e.ring}</div>
        <div style="color:var(--muted);font-size:11px;margin-left:auto">${e.ts ? relTime(e.ts) : '—'}</div>
      </div>`).join('');
  } catch(e) {
    document.getElementById('hist-modal-body').innerHTML =
      `<div style="color:var(--bad);font-size:12px">Error: ${e.message}</div>`;
  }
}

function closeSwarmHist() {
  document.getElementById('swarm-hist-modal').classList.remove('open');
}

// ── Activity feed ────────────────────────────────────────────────────────────
const _activityFeed = [];

function _addActivity(type, msg, time) {
  _activityFeed.unshift({ type, msg, time: time || new Date().toLocaleTimeString() });
  if (_activityFeed.length > 50) _activityFeed.length = 50;
  const sec = document.getElementById('swarm-activity-section');
  const list = document.getElementById('swarm-activity-list');
  if (!sec || !list) return;
  sec.style.display = '';
  const dotColor = type === 'ok' ? 'var(--ok)' : type === 'bad' ? 'var(--bad)' : 'var(--warn)';
  list.innerHTML = _activityFeed.map(a => `
    <div class="activity-item">
      <div class="activity-dot" style="background:${a.type === 'ok' ? 'var(--ok)' : a.type === 'bad' ? 'var(--bad)' : 'var(--warn)'}"></div>
      <div style="flex:1">${a.msg}</div>
      <div class="activity-time">${a.time}</div>
    </div>`).join('');
}

// Hook into swarm connect/disconnect to feed activity
const _origConnect = doSwarmConnect;
// (activity entries added directly in joinSala / kickPeer / createSala)

// Auto-load reputation on swarm status change
const _origRenderSwarmStatus = _renderSwarmStatus;
function _renderSwarmStatus(s) {
  _origRenderSwarmStatus(s);
  if (s.running) loadReputationPanel();
}

// ══════════════════════════════════════════════════════════
// ELECTION FINALIZATION
// ══════════════════════════════════════════════════════════

async function loadElectionStatus() {
  try {
    const r = await fetch((window.CENTINEL_API_BASE||'') + '/api/election/status');
    if (!r.ok) return;
    const d = await r.json();
    const banner = document.getElementById('election-closed-banner');
    const openSec = document.getElementById('election-open-section');
    const dot = document.getElementById('ec-status-dot');
    const label = document.getElementById('ec-status-label');
    const modeLine = document.getElementById('ec-mode-line');

    if (d.election_closed) {
      if (banner) banner.style.display = '';
      if (openSec) openSec.style.display = 'none';
      const el = document.getElementById('ec-closed-at');
      if (el) el.textContent = t('ec.cerrado') + ': ' + (d.closed_at || '—');
      const em = document.getElementById('ec-merkle');
      if (em) em.textContent = d.merkle_root || '—';
      const ec = document.getElementById('ec-chain');
      if (ec) ec.textContent = d.chain_length;
    } else {
      if (banner) banner.style.display = 'none';
      if (openSec) openSec.style.display = '';
      if (dot) dot.style.background = 'var(--ok)';
      if (label) label.textContent = t('ec.eleccion_en_curso');
      if (modeLine) modeLine.textContent = t('ec.modo') + ': ' + (d.centinel_mode || '—') +
        '  ·  Snapshots: ' + d.chain_length;
    }
  } catch(_) {}
}

function openFinalizeModal() {
  const m = document.getElementById('finalize-modal');
  if (m) { m.style.display = 'flex'; }
  const inp = document.getElementById('finalize-confirm-input');
  if (inp) { inp.value = ''; inp.focus(); }
  const btn = document.getElementById('btn-finalize-confirm');
  if (btn) btn.disabled = true;
}

function closeFinalizeModal() {
  const m = document.getElementById('finalize-modal');
  if (m) m.style.display = 'none';
}

async function doFinalizeElection() {
  closeFinalizeModal();
  const progressDiv = document.getElementById('ec-progress');
  const progressMsg = document.getElementById('ec-progress-msg');
  const progressBar = document.getElementById('ec-progress-bar');
  const resultDiv = document.getElementById('ec-result');
  const errorDiv = document.getElementById('ec-error');
  const btnFinalize = document.getElementById('btn-finalize');

  if (progressDiv) progressDiv.style.display = '';
  if (resultDiv) resultDiv.style.display = 'none';
  if (errorDiv) errorDiv.style.display = 'none';
  if (btnFinalize) btnFinalize.disabled = true;

  // Animate progress bar (scrape takes up to ~10 min)
  let pct = 0;
  const ticker = setInterval(() => {
    pct = Math.min(pct + 0.4, 92);
    if (progressBar) progressBar.style.width = pct + '%';
    if (progressMsg) {
      if (pct < 30) progressMsg.textContent = t('ec.iniciando_raspe');
      else if (pct < 60) progressMsg.textContent = t('ec.descargando_fuentes');
      else if (pct < 85) progressMsg.textContent = t('ec.procesando_hash');
      else progressMsg.textContent = t('ec.finalizando_cadena');
    }
  }, 2000);

  try {
    const r = await fetch((window.CENTINEL_API_BASE||'') + '/api/election/finalize', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({}),
    });
    clearInterval(ticker);
    if (progressBar) progressBar.style.width = '100%';

    const d = await r.json();
    if (!r.ok) {
      throw new Error(d.detail || t('ec.error_desconocido'));
    }

    if (progressDiv) progressDiv.style.display = 'none';
    if (resultDiv) resultDiv.style.display = '';
    const rm = document.getElementById('ec-result-merkle');
    if (rm) rm.textContent = d.merkle_root || '—';
    const rc = document.getElementById('ec-result-chain');
    if (rc) rc.textContent = d.chain_length;
    const rt = document.getElementById('ec-result-time');
    if (rt) rt.textContent = d.closed_at || '—';

    await loadElectionStatus();
  } catch(err) {
    clearInterval(ticker);
    if (progressDiv) progressDiv.style.display = 'none';
    if (errorDiv) {
      errorDiv.style.display = '';
      errorDiv.textContent = t('ec.error') + ': ' + err.message;
    }
    if (btnFinalize) btnFinalize.disabled = false;
  }
}

// ════════════════════════════════════════════════════════════
// LAB: Simulación de Enjambres y Peer-Review
// ════════════════════════════════════════════════════════════

// ── Swarm Panel — métricas en vivo + tarjetas de nodos ────────────────────
async function refreshSwarmPanel() {
  try {
    const [statusRes, repRes] = await Promise.allSettled([
      fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/status'),
      fetch((window.CENTINEL_API_BASE||'') + '/api/swarm/reputation'),
    ]);
    const status = statusRes.status === 'fulfilled' && statusRes.value.ok ? await statusRes.value.json() : null;
    const rep = repRes.status === 'fulfilled' && repRes.value.ok ? await repRes.value.json() : null;
    renderSwarmMetrics(status, rep);
    if (rep) renderNodeCards(rep);
  } catch(_) {
    renderSwarmMetrics(null, null);
  }
}

function renderSwarmMetrics(status, rep) {
  const el = id => document.getElementById(id);
  const peers = status?.connected_peers ?? 0;
  const total = peers + (status ? 1 : 0);
  const bft = Math.floor((total - 1) / 3);
  const r0 = rep?.ring_summary?.ring0 ?? 0;
  const r1 = rep?.ring_summary?.ring1 ?? 0;
  const compromised = (rep?.nodes || []).filter(n => n.trust_score < 0.5).length;
  const consensus = status?.consensus || '—';

  if (el('swarm-m-nodos')) el('swarm-m-nodos').textContent = status ? total : '—';
  if (el('swarm-m-consenso')) {
    el('swarm-m-consenso').textContent = status ? consensus : '—';
    el('swarm-m-consenso').style.color = consensus === 'OK' ? 'var(--ok)' : consensus === 'DIVERGENT' ? 'var(--bad)' : 'var(--fg)';
  }
  if (el('swarm-m-bft')) el('swarm-m-bft').textContent = status ? bft : '—';
  if (el('swarm-m-ring0')) el('swarm-m-ring0').textContent = rep ? r0 : '—';
  if (el('swarm-m-ring1')) el('swarm-m-ring1').textContent = rep ? r1 : '—';
  if (el('swarm-m-compromised')) {
    el('swarm-m-compromised').textContent = rep ? compromised : '—';
    if (el('swarm-m-compromised')) el('swarm-m-compromised').style.color = compromised > 0 ? 'var(--bad)' : 'var(--ok)';
  }
}

function renderNodeCards(rep) {
  const container = document.getElementById('swarm-node-cards');
  if (!container || !rep?.nodes) return;
  container.innerHTML = '';
  for (const node of rep.nodes) {
    const trust = Math.round((node.trust_score ?? 0) * 100);
    const ring = node.ring ?? 2;
    const ringLabel = ring === 0 ? 'Ring-0' : ring === 1 ? 'Ring-1' : 'Ring-2';
    const ringColor = ring === 0 ? '#b08cf0' : ring === 1 ? 'var(--ok)' : 'var(--muted)';
    const trustColor = trust >= 85 ? 'var(--ok)' : trust >= 50 ? 'var(--warn)' : 'var(--bad)';
    const shortId = (node.node_id || '').slice(0, 8);
    const isSelf = node.is_self;
    const card = document.createElement('div');
    card.style.cssText = `padding:12px;background:var(--panel);border:1px solid ${isSelf ? 'var(--accent)' : 'var(--border)'};border-radius:10px;text-align:center;cursor:pointer;transition:.15s`;
    card.title = node.node_id || '';
    card.innerHTML = `
      <div style="font-size:11px;font-weight:700;color:var(--fg);font-family:var(--mono);margin-bottom:6px">${isSelf ? '(tú) ' : ''}${shortId}</div>
      <div style="font-size:24px;font-weight:700;color:${trustColor}">${trust}%</div>
      <div style="font-size:10px;color:${ringColor};font-weight:600;margin-top:4px">${ringLabel}</div>
      <div style="width:100%;height:4px;background:var(--bg);border-radius:2px;margin-top:8px;overflow:hidden">
        <div style="width:${trust}%;height:100%;background:${trustColor};border-radius:2px"></div>
      </div>
    `;
    card.onmouseover = () => { card.style.background = 'var(--panel2)'; card.style.transform = 'translateY(-2px)'; };
    card.onmouseout = () => { card.style.background = 'var(--panel)'; card.style.transform = ''; };
    card.onclick = () => openSwarmHist(node.node_id);
    container.appendChild(card);
  }
}

// Keyboard shortcut to open this panel (also registered in parent pages)
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){
    closeDiffModal(); closePatModal(); closeResultModal(); closeMapPopup();
    closeFinalizeModal(); closeEmergencyModal();
  }
});
