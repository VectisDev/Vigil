// ══════════════════════════════════════════════════════════
// vigil-log.js — VIGIL Evidence Log (VELE)
//
// Structured logging compliant with:
//   RFC 5424  — Syslog severity + structured data
//   ISO 27037 — Digital evidence chain of custody
//   ISO 27042 — Evidence integrity verification
//   ISO 27043 — Investigation process support
//   FRE 902(14) — US self-authenticating digital records
//
// Every log entry is: timestamped (UTC), identified (source),
// classified (severity + event type), hashed (SHA-256),
// and chained (prev hash) for tamper detection.
// ══════════════════════════════════════════════════════════

const VELE = (function(){
  'use strict';

  const VERSION = 1;
  const VIGIL_VERSION = '2.1.0';
  const STORAGE_KEY = 'vigil-evidence-log';
  const MAX_ENTRIES = 500;

  // RFC 5424 severity levels (0-7, we use the string names)
  const SEV = ['EMERGENCY','ALERT','CRITICAL','ERROR','WARNING','NOTICE','INFO','DEBUG'];
  const SEV_SET = new Set(SEV);

  // Event type registry — every loggable action has a canonical ID
  const EVT = {
    SESSION_START:      'SESSION_START',
    SESSION_END:        'SESSION_END',
    MONITORING_START:   'MONITORING_START',
    MONITORING_STOP:    'MONITORING_STOP',
    CONFIG_CHANGE:      'CONFIG_CHANGE',
    CONFIG_COMMIT:      'CONFIG_COMMIT',
    PRESET_LOAD:        'PRESET_LOAD',
    COUNTRY_CHANGE:     'COUNTRY_CHANGE',
    CEILING_UNLOCK:     'CEILING_UNLOCK',
    CEILING_LOCK:       'CEILING_LOCK',
    EMERGENCY_STOP:     'EMERGENCY_STOP',
    ELECTION_FINALIZE:  'ELECTION_FINALIZE',
    SNAPSHOT_LOAD:      'SNAPSHOT_LOAD',
    ANOMALY_DETECTED:   'ANOMALY_DETECTED',
    ATTACK_DETECTED:    'ATTACK_DETECTED',
    SWARM_CONNECT:      'SWARM_CONNECT',
    SWARM_DISCONNECT:   'SWARM_DISCONNECT',
    OTS_ANCHOR:         'OTS_ANCHOR',
    OTS_VERIFY:         'OTS_VERIFY',
    EXPORT_REPORT:      'EXPORT_REPORT',
    EXPORT_RECEIPT:     'EXPORT_RECEIPT',
    DATA_PURGE:         'DATA_PURGE',
    AWS_MIRROR_ON:      'AWS_MIRROR_ON',
    AWS_MIRROR_OFF:     'AWS_MIRROR_OFF',
    VIEW_CHANGE:        'VIEW_CHANGE',
    LANG_CHANGE:        'LANG_CHANGE',
    AUTH_ATTEMPT:       'AUTH_ATTEMPT',
    SYSTEM_ERROR:       'SYSTEM_ERROR',
    USER_ACTION:        'USER_ACTION'
  };

  let _prevHash = null;
  let _page = 'unknown';

  // ── SHA-256 (Web Crypto API) ─────────────────────────────
  async function sha256(str){
    const buf = new TextEncoder().encode(str);
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash)).map(b=>b.toString(16).padStart(2,'0')).join('');
  }

  // ── UUID-like event ID ───────────────────────────────────
  function eid(){
    if(crypto.randomUUID) return 'evt_'+crypto.randomUUID().replace(/-/g,'').slice(0,16);
    const a = new Uint8Array(8);
    crypto.getRandomValues(a);
    return 'evt_'+Array.from(a).map(b=>b.toString(16).padStart(2,'0')).join('');
  }

  // ── Source context (ISO 27037) ───────────────────────────
  function _src(){
    return {
      seed: (typeof getCurrentSeedId==='function'?getCurrentSeedId():null) || sessionStorage.getItem('centinel_seed_id') || null,
      role: (typeof getCurrentRole==='function'?getCurrentRole():null) || sessionStorage.getItem('centinel_role') || null,
      fp:   sessionStorage.getItem('centinel_fp') || null
    };
  }

  function _sys(){
    return {
      vele: VERSION,
      vigil: VIGIL_VERSION,
      page: _page,
      ua: navigator.userAgent.slice(0,120)
    };
  }

  // ── Core log function ────────────────────────────────────
  async function log(severity, msgid, data, opts){
    if(!SEV_SET.has(severity)) severity = 'INFO';
    if(!msgid) msgid = 'USER_ACTION';
    opts = opts || {};

    const payload = {
      v: VERSION,
      ts: new Date().toISOString(),
      severity: severity,
      msgid: msgid,
      eid: eid(),
      src: _src(),
      sys: _sys(),
      data: data || {},
      detail: opts.detail || null,
      git_sha: opts.git_sha || null,
      ots_ref: opts.ots_ref || null
    };

    // ISO 27042: integrity hash of the data payload
    const dataStr = JSON.stringify(payload.data);
    payload.hash = 'sha256:' + await sha256(dataStr);

    // Chain link (ISO 27043: investigation continuity)
    payload.prev = _prevHash;
    const entryStr = JSON.stringify(payload);
    _prevHash = 'sha256:' + await sha256(entryStr);

    // Persist
    _store(payload);

    // Legacy bridge: also write to old auditLog format for backward compat
    if(typeof _renderSessionLog === 'function'){
      try { _renderSessionLog(); } catch(_){}
    }

    return payload;
  }

  // ── Storage ──────────────────────────────────────────────
  function _store(entry){
    try{
      const raw = localStorage.getItem(STORAGE_KEY);
      const arr = raw ? JSON.parse(raw) : [];
      arr.push(entry);
      while(arr.length > MAX_ENTRIES) arr.shift();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
    }catch(_){}
  }

  function getAll(){
    try{
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    }catch(_){ return []; }
  }

  function clear(){
    localStorage.removeItem(STORAGE_KEY);
    _prevHash = null;
  }

  // ── Chain verification (ISO 27042) ───────────────────────
  async function verifyChain(){
    const entries = getAll();
    if(!entries.length) return {valid:true, entries:0, errors:[]};
    const errors = [];
    let prev = null;

    for(let i=0; i<entries.length; i++){
      const e = entries[i];

      // Verify data hash
      const dataHash = 'sha256:' + await sha256(JSON.stringify(e.data));
      if(dataHash !== e.hash){
        errors.push({index:i, eid:e.eid, error:'data_hash_mismatch', expected:e.hash, got:dataHash});
      }

      // Verify chain link
      if(e.prev !== prev){
        errors.push({index:i, eid:e.eid, error:'chain_break', expected:e.prev, got:prev});
      }

      // Compute this entry's hash for next link
      prev = 'sha256:' + await sha256(JSON.stringify(e));
    }

    _prevHash = prev;
    return {valid: errors.length===0, entries: entries.length, errors: errors};
  }

  // ── Export for court / observation missions ──────────────
  function exportForensic(){
    const entries = getAll();
    const header = [
      'VIGIL EVIDENCE LOG (VELE) — FORENSIC EXPORT',
      'Format: RFC 5424 + ISO 27037/27042/27043',
      'Exported: ' + new Date().toISOString(),
      'Entries: ' + entries.length,
      'Schema version: ' + VERSION,
      'VIGIL version: ' + VIGIL_VERSION,
      '',
      'DISCLAIMER: This log is a digital record generated by VIGIL electoral',
      'monitoring software. Each entry is SHA-256 hashed and chained for',
      'tamper detection. For court admissibility, this export should be',
      'accompanied by the corresponding expert affidavit (peritaje informatico)',
      'or FRE 902(14) certification as applicable.',
      '',
      '═'.repeat(72),
      ''
    ].join('\n');

    const body = entries.map((e,i) => {
      return [
        `ENTRY ${i+1}/${entries.length}`,
        `  Event ID:    ${e.eid}`,
        `  Timestamp:   ${e.ts}`,
        `  Severity:    ${e.severity}`,
        `  Event Type:  ${e.msgid}`,
        `  Operator:    ${e.src?.seed || 'N/A'} (${e.src?.role || 'N/A'})`,
        `  Fingerprint: ${e.src?.fp || 'N/A'}`,
        `  Page:        ${e.sys?.page || 'N/A'}`,
        `  VIGIL:       v${e.sys?.vigil || 'N/A'}`,
        `  Data:        ${JSON.stringify(e.data)}`,
        `  Detail:      ${e.detail || '—'}`,
        `  Data Hash:   ${e.hash}`,
        `  Prev Hash:   ${e.prev || 'GENESIS'}`,
        `  Git SHA:     ${e.git_sha || '—'}`,
        `  OTS Ref:     ${e.ots_ref || '—'}`,
        '─'.repeat(72)
      ].join('\n');
    }).join('\n');

    return header + body;
  }

  function downloadExport(filename){
    const content = exportForensic();
    const blob = new Blob([content], {type:'text/plain;charset=utf-8'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename || `vigil-evidence-log-${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ── Convenience methods ──────────────────────────────────
  function emergency(msgid, data, opts){ return log('EMERGENCY', msgid, data, opts); }
  function alert(msgid, data, opts){ return log('ALERT', msgid, data, opts); }
  function critical(msgid, data, opts){ return log('CRITICAL', msgid, data, opts); }
  function error(msgid, data, opts){ return log('ERROR', msgid, data, opts); }
  function warning(msgid, data, opts){ return log('WARNING', msgid, data, opts); }
  function notice(msgid, data, opts){ return log('NOTICE', msgid, data, opts); }
  function info(msgid, data, opts){ return log('INFO', msgid, data, opts); }
  function debug(msgid, data, opts){ return log('DEBUG', msgid, data, opts); }

  // ── Init ─────────────────────────────────────────────────
  function init(page){
    _page = page || 'unknown';
    // Restore chain state from last stored entry
    const entries = getAll();
    if(entries.length){
      const last = entries[entries.length-1];
      sha256(JSON.stringify(last)).then(h=>{ _prevHash = 'sha256:'+h; });
    }
  }

  return {
    VERSION, EVT, SEV,
    init, log,
    emergency, alert, critical, error, warning, notice, info, debug,
    getAll, clear, verifyChain,
    exportForensic, downloadExport,
    sha256
  };
})();
