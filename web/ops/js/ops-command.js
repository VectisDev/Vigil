// ══════════════════════════════════════════════════════════
// ops-command.js — Phase view router, command palette, keyboard
// shortcuts, and setup wizard for the VIGIL ops panel.
//
// This file changes navigation/presentation only. It wraps existing
// functions (doIniciar, loadPreset, doChangeCountry, …) and never
// duplicates their logic.
// ══════════════════════════════════════════════════════════

// ── PHASE VIEW ROUTER ──────────────────────────────────────
const OPS_PHASES = ['vigilar','configurar','verificar','cerrar'];

function setView(phase, opts){
  if(!OPS_PHASES.includes(phase)) phase = 'vigilar';
  opts = opts || {};
  document.body.dataset.opsView = phase;
  try { localStorage.setItem('ops-view', phase); } catch(_){}
  // Highlight the active phase tab + first sub-link of that phase
  document.querySelectorAll('.phase-tab').forEach(b=>{
    b.classList.toggle('active', b.dataset.phaseTab===phase);
  });
  document.querySelectorAll('#sidebar a').forEach(a=>{
    const href = a.getAttribute('href')||'';
    const target = document.querySelector(href.startsWith('#')?'['+'id="'+href.slice(1)+'"]':href);
    const inPhase = target && target.closest('[data-phase]')?.dataset.phase===phase;
    a.classList.toggle('phase-hidden', !inPhase);
    a.classList.remove('active');
  });
  if(opts.scroll!==false){
    const main = document.getElementById('main-area');
    if(main) main.scrollIntoView({behavior:'smooth',block:'start'});
  }
}

function _initView(){
  let v = 'vigilar';
  try { v = localStorage.getItem('ops-view') || 'vigilar'; } catch(_){}
  setView(v, {scroll:false});
}

// ── COMMAND PALETTE ────────────────────────────────────────
// Built fresh on open so it can reference current presets / state.
function _buildOpsActions(){
  const A = [];
  const push = (id,label,hint,run)=>A.push({id,label,hint,run});
  // Navigation
  push('view-vigilar','Ir a Vigilar','Vista de monitoreo',()=>setView('vigilar'));
  push('view-configurar','Ir a Configurar','Presets y config',()=>setView('configurar'));
  push('view-verificar','Ir a Verificar','OTS, AWS, manual',()=>setView('verificar'));
  push('view-cerrar','Ir a Cerrar elección','Cierre electoral',()=>setView('cerrar'));
  // Operations
  push('start','Iniciar monitoreo','Arranca el pipeline',()=>doIniciar());
  push('finish','Finalizar ciclo','Detiene el monitoreo',()=>openFinalizeModal());
  push('emergency','Parada de emergencia','Kill switch',()=>openEmergencyModal());
  push('wizard','Asistente de arranque','Preparar elección paso a paso',()=>openSetupWizard());
  push('autosave','Alternar auto-guardar','ON/OFF commits a GitHub',()=>toggleAutoApply());
  if(typeof autoApply==='function') push('apply','Guardar cambios ahora','Commit de config a GitHub',()=>autoApply());
  // Presets
  try {
    [...FACTORY_PRESETS, ...(customPresets||[])].forEach(p=>{
      push('preset-'+p.id, 'Preset: '+p.name, p.desc||'', ()=>{ setView('configurar',{scroll:false}); loadPreset(p.id); });
    });
  } catch(_){}
  // AWS
  if(typeof exportAwsReceipt==='function') push('aws-receipt','AWS: exportar recibo','Proyección de costos',()=>exportAwsReceipt());
  if(typeof exportGrantDocument==='function') push('aws-grant','AWS: solicitud de grant','Documento para AWS Activate / Imagine Grant',()=>exportGrantDocument());
  if(typeof verifyAwsReadiness==='function') push('aws-ready','AWS: verificar preparación','Chequeo sin gasto',()=>{ setView('verificar',{scroll:false}); scrollTo('s-aws'); verifyAwsReadiness(); });
  // Misc
  if(typeof toggleOpsLang==='function') push('lang','Cambiar idioma','ES / EN',()=>toggleOpsLang());
  push('help','Ver atajos de teclado','',()=>openKbdHelp());
  return A;
}

let _cmdActions = [];
let _cmdSel = 0;

function openCmdPalette(){
  const ov = document.getElementById('cmd-palette');
  if(!ov) return;
  _cmdActions = _buildOpsActions();
  _cmdSel = 0;
  ov.style.display = 'flex';
  const inp = document.getElementById('cmd-input');
  inp.value = '';
  _renderCmdList('');
  inp.focus();
}
function closeCmdPalette(){
  const ov = document.getElementById('cmd-palette');
  if(ov) ov.style.display = 'none';
}
function _cmdFilter(q){
  q = (q||'').toLowerCase().trim();
  if(!q) return _cmdActions;
  return _cmdActions.filter(a=>(a.label+' '+a.hint).toLowerCase().includes(q));
}
function _renderCmdList(q){
  const list = document.getElementById('cmd-list');
  if(!list) return;
  const items = _cmdFilter(q);
  if(_cmdSel >= items.length) _cmdSel = Math.max(0, items.length-1);
  list.innerHTML = items.map((a,i)=>
    '<div class="cmd-item'+(i===_cmdSel?' sel':'')+'" data-i="'+i+'" onmousedown="_cmdRun('+i+')">'+
    '<span class="cmd-item-label">'+a.label+'</span>'+
    (a.hint?'<span class="cmd-item-hint">'+a.hint+'</span>':'')+'</div>'
  ).join('') || '<div class="cmd-empty">Sin resultados</div>';
}
function _cmdRun(i){
  const items = _cmdFilter(document.getElementById('cmd-input').value);
  const a = items[i];
  closeCmdPalette();
  if(a && typeof a.run==='function'){ try { a.run(); } catch(e){ console.warn('cmd',a.id,e); } }
}
function _cmdKey(e){
  const items = _cmdFilter(document.getElementById('cmd-input').value);
  if(e.key==='ArrowDown'){ e.preventDefault(); _cmdSel=Math.min(_cmdSel+1, items.length-1); _renderCmdList(document.getElementById('cmd-input').value); }
  else if(e.key==='ArrowUp'){ e.preventDefault(); _cmdSel=Math.max(_cmdSel-1, 0); _renderCmdList(document.getElementById('cmd-input').value); }
  else if(e.key==='Enter'){ e.preventDefault(); _cmdRun(_cmdSel); }
  else if(e.key==='Escape'){ e.preventDefault(); closeCmdPalette(); }
}

// ── KEYBOARD SHORTCUTS ─────────────────────────────────────
function openKbdHelp(){ const o=document.getElementById('kbd-help'); if(o) o.style.display='flex'; }
function closeKbdHelp(){ const o=document.getElementById('kbd-help'); if(o) o.style.display='none'; }

function _isTyping(el){
  if(!el) return false;
  const t = el.tagName;
  return t==='INPUT' || t==='TEXTAREA' || t==='SELECT' || el.isContentEditable;
}

document.addEventListener('keydown', function(e){
  // Ctrl/Cmd+K always opens the palette, even from a field
  if((e.ctrlKey||e.metaKey) && (e.key==='k'||e.key==='K')){
    e.preventDefault(); openCmdPalette(); return;
  }
  // Palette has its own handler
  const palette = document.getElementById('cmd-palette');
  if(palette && palette.style.display==='flex'){ _cmdKey(e); return; }
  if(e.key==='Escape'){
    closeCmdPalette(); closeKbdHelp();
    document.querySelectorAll('.ovl-dismiss[data-open="1"]').forEach(o=>{o.style.display='none';o.dataset.open='0';});
    return;
  }
  if(_isTyping(document.activeElement)) return;       // don't hijack typing
  if(e.ctrlKey||e.metaKey||e.altKey) return;
  switch(e.key){
    case '1': setView('vigilar'); break;
    case '2': setView('configurar'); break;
    case '3': setView('verificar'); break;
    case '4': setView('cerrar'); break;
    case 's': case 'S': doIniciar(); break;
    case 'f': case 'F': openFinalizeModal(); break;
    case 'e': case 'E': openEmergencyModal(); break;
    case '?': openKbdHelp(); break;
  }
});

// ── SETUP WIZARD ───────────────────────────────────────────
let _wizStep = 1;
const _WIZ_TOTAL = 4;

function openSetupWizard(){
  _wizStep = 1;
  const o = document.getElementById('setup-wizard');
  if(!o) return;
  o.style.display = 'flex';
  _renderWizStep();
}
function closeSetupWizard(){ const o=document.getElementById('setup-wizard'); if(o) o.style.display='none'; }
function wizNext(){ if(_wizStep<_WIZ_TOTAL){ _wizStep++; _renderWizStep(); } }
function wizPrev(){ if(_wizStep>1){ _wizStep--; _renderWizStep(); } }
function wizFinish(){ closeSetupWizard(); setView('vigilar',{scroll:false}); try { doIniciar(); } catch(e){ console.warn('wizFinish',e); } }

function _renderWizStep(){
  for(let i=1;i<=_WIZ_TOTAL;i++){
    const p = document.getElementById('wiz-step-'+i);
    if(p) p.style.display = (i===_wizStep)?'block':'none';
  }
  const dots = document.getElementById('wiz-dots');
  if(dots){
    let h='';
    for(let i=1;i<=_WIZ_TOTAL;i++) h+='<span class="wiz-dot'+(i===_wizStep?' on':'')+'"></span>';
    dots.innerHTML=h;
  }
  const prev = document.getElementById('wiz-prev');
  const next = document.getElementById('wiz-next');
  const fin  = document.getElementById('wiz-finish');
  if(prev) prev.style.display = _wizStep>1 ? 'inline-flex':'none';
  if(next) next.style.display = _wizStep<_WIZ_TOTAL ? 'inline-flex':'none';
  if(fin)  fin.style.display  = _wizStep===_WIZ_TOTAL ? 'inline-flex':'none';
  _wizPopulate();
}

function _wizPopulate(){
  // Country
  const cc = document.getElementById('wiz-current-country');
  if(cc){
    const name = (document.getElementById('ms-country')?.textContent||'').trim();
    cc.textContent = (name && name!=='—') ? name : ((typeof ACTIVE_COUNTRY_CODE!=='undefined' && ACTIVE_COUNTRY_CODE) || '—');
  }
  // URL
  const cu = document.getElementById('wiz-current-url');
  if(cu){
    const u = (document.getElementById('inp-main-url')||{}).value;
    cu.textContent = u || '(sin URL configurada — configúrala antes de iniciar)';
    cu.style.color = u ? '' : 'var(--warn)';
  }
  // Presets
  const grid = document.getElementById('wiz-preset-grid');
  if(grid && !grid.dataset.built){
    try {
      grid.innerHTML = FACTORY_PRESETS.map(p=>
        '<div class="wiz-preset" data-id="'+p.id+'" onclick="_wizPickPreset(\''+p.id+'\')">'+
        '<div class="wiz-preset-name">'+p.name+'</div>'+
        '<div class="wiz-preset-desc">'+(p.desc||'')+'</div></div>'
      ).join('');
      grid.dataset.built = '1';
    } catch(_){}
  }
  // Summary
  const sm = document.getElementById('wiz-summary');
  if(sm){
    const country = (document.getElementById('ms-country')?.textContent||'—').trim();
    const url = (document.getElementById('inp-main-url')||{}).value || '—';
    const preset = (typeof activePresetId!=='undefined' && activePresetId) || '(ninguno)';
    sm.innerHTML = 'País: <strong>'+country+'</strong><br>URL: <strong>'+url+'</strong><br>Preset: <strong>'+preset+'</strong>';
  }
}

function _wizPickPreset(id){
  try { loadPreset(id); } catch(_){}
  document.querySelectorAll('#wiz-preset-grid .wiz-preset').forEach(el=>{
    el.classList.toggle('sel', el.dataset.id===id);
  });
}

// Offer the wizard on first run if no country/URL configured yet.
function _maybeOfferWizard(){
  try {
    const u = (document.getElementById('inp-main-url')||{}).value;
    const seen = localStorage.getItem('ops-wizard-seen');
    if(!u && !seen){ localStorage.setItem('ops-wizard-seen','1'); openSetupWizard(); }
  } catch(_){}
}

// ── CEILING FEEDBACK (config sin fricción) ─────────────────
// Shown when a security ceiling clamps a slider, instead of a silent clamp.
let _ceilingToastTimer = null;
function _ceilingFeedback(key, requested, clamped){
  let el = document.getElementById('ceiling-toast');
  if(!el){
    el = document.createElement('div');
    el.id = 'ceiling-toast';
    document.body.appendChild(el);
  }
  const labels = { rph:'solicitudes/hora', interval:'intervalo (min)' };
  el.innerHTML = '🔒 <strong>'+(labels[key]||key)+'</strong> limitado a <strong>'+clamped+
    '</strong> (pediste '+requested+'). Desbloquea los límites en Configurar → Presets para subir.';
  el.classList.add('show');
  clearTimeout(_ceilingToastTimer);
  _ceilingToastTimer = setTimeout(()=>el.classList.remove('show'), 4200);
}

// ── INIT ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function(){
  _initView();
  // input listener for palette
  const inp = document.getElementById('cmd-input');
  if(inp) inp.addEventListener('input', ()=>{ _cmdSel=0; _renderCmdList(inp.value); });
});
