// ══════════════════════════════════════════════════════════
// ops-aws.js — AWS cost PROJECTION meter + receipt + opt-in
// connection readiness for VIGIL.
//
// IMPORTANT — Zero Cost mandate:
//   VIGIL runs for free on GitHub Pages + GitHub Actions. There is
//   no live AWS integration and this module never makes paid calls.
//   The meter is an ESTIMATE of what the observed workload WOULD cost
//   on AWS, produced as an artifact for grant/credit applications
//   (AWS Activate, AWS Imagine Grant, AWS Credits for Nonprofits).
// ══════════════════════════════════════════════════════════

// Public on-demand AWS rate card (us-east-1, approximate). Dated so the
// receipt can disclose exactly which prices were used.
const AWS_RATES = {
  as_of: '2026-01-01',
  region: 'us-east-1',
  lambda_req:        0.0000002,    // $ per request
  lambda_gb_sec:     0.0000166667, // $ per GB-second
  s3_gb_month:       0.023,        // $ per GB-month (Standard)
  s3_put_per_1k:     0.005,        // $ per 1,000 PUT requests
  s3_get_per_1k:     0.0004,       // $ per 1,000 GET requests
  data_transfer_gb:  0.09,         // $ per GB egress (first tier)
  cloudwatch_gb:     0.50,         // $ per GB logs ingested
  eventbridge_per_m: 1.00,         // $ per 1M scheduled events
};

// Assumptions for translating a GitHub-hosted workload into AWS units.
const AWS_ASSUMPTIONS = {
  lambda_mem_gb:        0.512,  // memory per scrape invocation
  lambda_sec_per_cycle: 3.0,    // compute seconds per capture cycle
  kb_per_snapshot:      40,     // stored JSON size per snapshot
  kb_per_request:       12,     // egress per fetch
  log_kb_per_cycle:     8,      // CloudWatch logs per cycle
};

function _awsCfg(){
  let c = { enabled:false, region:AWS_RATES.region, profile:'serverless' };
  try { const s = JSON.parse(localStorage.getItem('ops-aws-config')||'null'); if(s) c = Object.assign(c, s); } catch(_){}
  return c;
}
function _saveAwsCfg(c){ try { localStorage.setItem('ops-aws-config', JSON.stringify(c)); } catch(_){} }

// Derive workload metrics from data the panel already has loaded.
function _awsMetrics(){
  const snap = (typeof snapshotData!=='undefined' && snapshotData) || {};
  const chainLen = snap.chain?.chain_length || 0;
  const start = snap.coverage?.monitoring_since || snap.generated_at || null;
  const now = Date.now();
  const startMs = start ? new Date(start).getTime() : now;
  const hours = Math.max(0, (now - startMs)/3600000);
  // Polling interval (min) from config, fallback 5
  let interval = 5;
  try { interval = +(localConfig?.watchdog?.interval_minutes ?? currentConfig?.watchdog?.interval_minutes ?? 5) || 5; } catch(_){}
  // Number of endpoints (national + departments)
  let endpoints = 1;
  try {
    const deps = snap.departments ? Object.keys(snap.departments).length : 0;
    endpoints = Math.max(1, deps + 1);
  } catch(_){}
  // Cycles: prefer real chain length; else estimate from uptime/interval
  const estCycles = interval>0 ? Math.floor((hours*60)/interval) : 0;
  const cycles = chainLen > 0 ? chainLen : estCycles;
  const requests = cycles * endpoints;
  return { hours, interval, endpoints, cycles, requests, chainLen, start };
}

function computeAwsProjection(){
  const m = _awsMetrics();
  const R = AWS_RATES, K = AWS_ASSUMPTIONS;
  const li = [];
  const add = (service, detail, qty, unit, rate)=>{
    const cost = qty*rate;
    li.push({ service, detail, qty, unit, rate, cost });
  };
  // Lambda
  add('Lambda', 'Invocaciones (ciclos × endpoints)', m.requests, 'req', R.lambda_req);
  const gbSec = m.cycles * K.lambda_sec_per_cycle * K.lambda_mem_gb;
  add('Lambda', 'Cómputo (GB-segundo)', +gbSec.toFixed(2), 'GB-s', R.lambda_gb_sec);
  // S3 storage (GB-month, prorated by uptime fraction of a month)
  const storeGb = (m.cycles * K.kb_per_snapshot) / (1024*1024);
  const monthFrac = Math.max(m.hours/720, 0.0001);
  add('S3', 'Almacenamiento snapshots', +(storeGb*monthFrac).toFixed(6), 'GB-mes', R.s3_gb_month);
  add('S3', 'PUT (escritura snapshots)', m.cycles, 'req', R.s3_put_per_1k/1000);
  // Data transfer
  const egressGb = (m.requests * K.kb_per_request) / (1024*1024);
  add('Transferencia', 'Egress de datos', +egressGb.toFixed(6), 'GB', R.data_transfer_gb);
  // CloudWatch
  const logGb = (m.cycles * K.log_kb_per_cycle) / (1024*1024);
  add('CloudWatch', 'Logs ingeridos', +logGb.toFixed(6), 'GB', R.cloudwatch_gb);
  // EventBridge scheduler
  add('EventBridge', 'Eventos programados', m.cycles, 'ev', R.eventbridge_per_m/1000000);
  const total = li.reduce((s,x)=>s+x.cost, 0);
  return { lineItems: li, total, metrics: m, rates: R };
}

function _fmtUsd(n){ return '$' + (n||0).toLocaleString('en-US',{minimumFractionDigits:4, maximumFractionDigits:4}); }
function _fmtUsd2(n){ return '$' + (n||0).toLocaleString('en-US',{minimumFractionDigits:2, maximumFractionDigits:2}); }

function renderAwsMeter(){
  const totalEl = document.getElementById('aws-total');
  const body = document.getElementById('aws-breakdown');
  if(!totalEl && !body) return;
  const p = computeAwsProjection();
  if(totalEl) totalEl.textContent = _fmtUsd2(p.total);
  const periodEl = document.getElementById('aws-period');
  if(periodEl){
    const m = p.metrics;
    periodEl.textContent = `${m.cycles} ciclos · ${m.endpoints} endpoints · ${m.hours.toFixed(1)} h`;
  }
  if(body){
    body.innerHTML = p.lineItems.map(x=>
      '<tr><td>'+x.service+'</td><td style="color:var(--muted)">'+x.detail+'</td>'+
      '<td style="text-align:right">'+x.qty+' '+x.unit+'</td>'+
      '<td style="text-align:right">'+_fmtUsd2(x.cost)+'</td></tr>'
    ).join('');
  }
}

// "Mini recibo" — itemized projection, downloadable.
function exportAwsReceipt(){
  const p = computeAwsProjection();
  const m = p.metrics;
  const now = new Date().toISOString();
  const country = (typeof ACTIVE_COUNTRY_CODE!=='undefined' && ACTIVE_COUNTRY_CODE) || '—';
  const pad = (s,n)=>String(s).padEnd(n).slice(0,n);
  const lines = [
    '═══════════════════════════════════════════════════════════════',
    '  VIGIL — PROYECCIÓN DE COSTOS AWS (RECIBO ESTIMADO)',
    '  AWS Cost Projection — Estimated Receipt',
    '═══════════════════════════════════════════════════════════════',
    '',
    'Generado:        ' + now,
    'País / Election: ' + country,
    'Período:         ' + (m.start || '—') + '  →  ' + now,
    'Workload:        ' + m.cycles + ' ciclos · ' + m.endpoints + ' endpoints · ' + m.hours.toFixed(1) + ' h',
    'Región AWS:      ' + p.rates.region,
    'Tarifas (as_of): ' + p.rates.as_of,
    '',
    '── LÍNEAS ───────────────────────────────────────────────────',
    pad('Servicio',12)+pad('Detalle',32)+pad('Cantidad',14)+'Subtotal',
    '─────────────────────────────────────────────────────────────',
    ...p.lineItems.map(x=>
      pad(x.service,12)+pad(x.detail,32)+pad(x.qty+' '+x.unit,14)+_fmtUsd(x.cost)
    ),
    '─────────────────────────────────────────────────────────────',
    pad('',58)+'TOTAL: '+_fmtUsd2(p.total),
    '',
    '── NOTA ─────────────────────────────────────────────────────',
    'Proyección ESTIMADA para fines de solicitud de créditos/grant',
    '(AWS Activate · AWS Imagine Grant · AWS Credits for Nonprofits).',
    'VIGIL opera actualmente SIN COSTO en GitHub Pages + Actions.',
    'Este documento NO representa facturación real de AWS.',
    '',
    'Estimated projection for AWS credit/grant applications only.',
    'VIGIL currently runs at ZERO COST on GitHub. Not a real AWS bill.',
    '═══════════════════════════════════════════════════════════════',
  ];
  const text = lines.join('\n');
  const blob = new Blob([text], {type:'text/plain;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `VIGIL-AWS-Receipt-${now.slice(0,10)}.txt`;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Opt-in connection: stores intent + validates format. No paid calls.
function toggleAwsConnection(){
  const c = _awsCfg();
  c.enabled = !c.enabled;
  c.region = (document.getElementById('aws-region')?.value || c.region || AWS_RATES.region).trim();
  c.profile = document.getElementById('aws-profile')?.value || c.profile;
  _saveAwsCfg(c);
  _renderAwsConnUI();
}
function verifyAwsReadiness(){
  const c = _awsCfg();
  c.region = (document.getElementById('aws-region')?.value || c.region || '').trim();
  c.profile = document.getElementById('aws-profile')?.value || c.profile;
  _saveAwsCfg(c);
  const out = document.getElementById('aws-ready-out');
  if(!out) return;
  const regionOk = /^[a-z]{2}-[a-z]+-\d$/.test(c.region);
  const checks = [
    ['Región con formato válido', regionOk, c.region||'(vacía)'],
    ['Perfil de servicios definido', !!c.profile, c.profile||'(ninguno)'],
    ['Sin gasto activo (Zero Cost)', true, 'VIGIL no realiza llamadas facturables'],
    ['Recibo de proyección disponible', true, 'exportable para el grant'],
  ];
  out.innerHTML = checks.map(([label, ok, val])=>
    '<div class="aws-check"><span class="aws-check-dot '+(ok?'ok':'bad')+'"></span>'+
    '<span>'+label+'</span><span style="color:var(--muted);margin-left:auto">'+val+'</span></div>'
  ).join('') +
  '<div style="margin-top:8px;font-size:11px;color:var(--muted)">'+
  (regionOk?'Listo para conectar AWS si un grant aporta créditos. VIGIL permanece gratis hasta entonces.'
          :'Corrige la región (ej. us-east-1) para completar la preparación.')+'</div>';
}

function _renderAwsConnUI(){
  const c = _awsCfg();
  const t = document.getElementById('aws-enable-val');
  if(t){ t.textContent = c.enabled?'ON':'OFF'; t.className = 'aws-toggle-val '+(c.enabled?'on':'off'); }
  const r = document.getElementById('aws-region'); if(r && !r.value) r.value = c.region||'';
  const pf = document.getElementById('aws-profile'); if(pf) pf.value = c.profile||'serverless';
  const panel = document.getElementById('aws-conn-fields');
  if(panel) panel.style.opacity = c.enabled? '1':'0.55';
}

function initAwsPanel(){
  _renderAwsConnUI();
  renderAwsMeter();
}
