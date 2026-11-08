// ── Pestañas y estado general ───────────────────────────────────────────────
//
// ESPAÑOL
// Dos cosas viven aquí, y comparten una idea: una sola fuente de verdad.
//
// `goTab()` muestra una de las cuatro pestañas. Antes el panel era una página
// de 2.400 líneas con diez secciones al mismo nivel, de 11 px, y había que
// recorrerla entera para encontrar cualquier cosa.
//
// `computeOverallState()` decide el estado del sistema. Antes lo decidían
// tres sitios distintos: el encabezado decía «NORMAL / INACTIVO», las
// tarjetas decían «CERRADO / NORMAL / PENDIENTE» y a la vez podía aparecer un
// error. Tres respuestas a la misma pregunta, en la misma pantalla, y ninguna
// forma de saber cuál era la buena. Ahora hay una función y todo lee de ella.
//
// ENGLISH
// Two things live here, sharing one idea: a single source of truth.
//
// `goTab()` shows one of four tabs; the panel used to be one 2,400-line page
// with ten same-level sections at 11px.
//
// `computeOverallState()` decides the system state. Three places used to
// decide it, and they contradicted each other on the same screen, with no way
// to tell which was right.

const OPS_TABS = ['inicio', 'evidencia', 'red', 'avanzado'];
const OPS_TAB_DEFAULT = 'inicio';

function _opsTabFromHash() {
  const h = (location.hash || '').replace(/^#/, '');
  return OPS_TABS.includes(h) ? h : OPS_TAB_DEFAULT;
}

function goTab(tab) {
  if (!OPS_TABS.includes(tab)) tab = OPS_TAB_DEFAULT;
  document.querySelectorAll('[data-tab]').forEach(function (el) {
    el.hidden = el.getAttribute('data-tab') !== tab;
  });
  document.querySelectorAll('[data-tab-btn]').forEach(function (btn) {
    const on = btn.getAttribute('data-tab-btn') === tab;
    btn.classList.toggle('active', on);
    // `aria-current` y no `aria-selected`: estos botones no son un
    // `role="tab"` dentro de un `tablist`, son navegación.
    // English: aria-current, not aria-selected -- these are navigation, not
    // ARIA tabs inside a tablist.
    if (on) btn.setAttribute('aria-current', 'page');
    else btn.removeAttribute('aria-current');
  });
  if (location.hash !== '#' + tab) {
    history.replaceState(null, '', '#' + tab);
  }
  window.OPS_TAB = tab;
  // Volver arriba al cambiar de pestaña: quedarse a media altura de la
  // anterior desorienta.
  // English: scroll to top on tab change; landing mid-page disorients.
  const main = document.getElementById('main-area');
  if (main) main.scrollTop = 0;
  window.scrollTo(0, 0);
}
window.goTab = goTab;

function initOpsTabs() {
  goTab(_opsTabFromHash());
  window.addEventListener('hashchange', function () { goTab(_opsTabFromHash()); });
}
window.initOpsTabs = initOpsTabs;

// ── El estado general, en un solo sitio ─────────────────────────────────────
//
// Devuelve {level, headline, detail, action} y nada más decide el estado.
//   'ok'   — verde: capturando y con datos recientes
//   'idle' — gris: pausado, o sin nodo encendido
//   'bad'  — rojo: hay un problema concreto, con una frase que lo nombra
//
// El gris no es un estado menor. La mayor parte del tiempo, y durante años
// entre elecciones, este panel estará legítimamente en gris. Pintarlo de rojo
// enseñaría a ignorar los rojos.
function computeOverallState() {
  const L = (window.OPS_LANG === 'en') ? 'en' : 'es';
  const say = function (es, en) { return L === 'en' ? en : es; };

  if (opsIsPages()) {
    return {
      level: 'idle',
      headline: say('Tu nodo no está encendido', 'Your node is not running'),
      detail: say(
        'Este panel está publicado sin servidor. Enciende tu nodo para capturar datos.',
        'This panel is published without a server. Start your node to capture data.'),
      action: 'node',
    };
  }

  const st = window._opsPipelineState || {};
  if (st.error) {
    return {
      level: 'bad',
      headline: say('Problema: ', 'Problem: ') + st.error,
      detail: '',
      action: 'help',
    };
  }
  if (!st.running) {
    return {
      level: 'idle',
      headline: say('Pausado', 'Paused'),
      detail: say('No se está capturando nada ahora mismo.',
                  'Nothing is being captured right now.'),
      action: null,
    };
  }

  const mins = typeof st.lastMinutes === 'number' ? st.lastMinutes : null;
  const src = st.source || say('la fuente configurada', 'the configured source');

  // Un nodo que dice estar capturando pero cuyo ultimo dato es de hace horas
  // no esta bien, aunque el proceso siga vivo. Es justo el caso que un panel
  // honesto tiene que señalar.
  // English: a node that says it is capturing but whose last datum is hours
  // old is not fine, even if the process is alive.
  if (mins !== null && mins > 180) {
    return {
      level: 'bad',
      headline: say('Problema: sin datos nuevos desde hace ' + mins + ' min',
                    'Problem: no new data for ' + mins + ' min'),
      detail: say('El proceso sigue activo, pero la fuente no está respondiendo.',
                  'The process is alive, but the source is not responding.'),
      action: 'help',
    };
  }

  return {
    level: 'ok',
    headline: say('Todo bien. Vigilando ' + src, 'All good. Watching ' + src),
    detail: mins === null
      ? say('Sin capturas todavía en esta sesión.', 'No captures yet this session.')
      : say('Último dato hace ' + mins + ' min.', 'Last data ' + mins + ' min ago.'),
    action: null,
  };
}
window.computeOverallState = computeOverallState;

function renderOverallState() {
  const s = computeOverallState();
  const box = document.getElementById('hero-state');
  const head = document.getElementById('hero-headline');
  const det = document.getElementById('hero-detail');
  const act = document.getElementById('hero-action');
  if (!box || !head) return s;

  box.classList.remove('is-ok', 'is-idle', 'is-bad');
  box.classList.add('is-' + s.level);
  head.textContent = s.headline;
  if (det) det.textContent = s.detail || '';
  if (act) act.style.display = s.action ? '' : 'none';

  // El boton dice lo que va a hacer, no en que estado estamos. Un boton
  // "Iniciar" mientras ya se esta capturando invita a pulsarlo dos veces.
  // English: the button says what it will do, not what state we are in. An
  // "Start" button while already capturing invites pressing it twice.
  const toggle = document.getElementById('hero-toggle');
  if (toggle) {
    const running = !!(window._opsPipelineState || {}).running;
    toggle.textContent = running
      ? (window.OPS_LANG === 'en' ? 'Pause' : 'Pausar')
      : (window.OPS_LANG === 'en' ? 'Start' : 'Iniciar');
    // Sin nodo no hay nada que iniciar: el boton se deshabilita en vez de
    // fallar al pulsarlo. English: with no node there is nothing to start.
    toggle.disabled = opsIsPages();
  }

  box.dataset.opsResolved = '1';
  return s;
}
window.renderOverallState = renderOverallState;

function openHeroHelp() {
  const s = computeOverallState();
  if (s.action === 'node') {
    window.open('https://github.com/VectisDev/Vigil/wiki/Instalaci%C3%B3n-%E2%80%94-Setup',
                '_blank', 'noopener');
    return;
  }
  goTab('avanzado');
}
window.openHeroHelp = openHeroHelp;

function heroToggleCapture() {
  const st = window._opsPipelineState || {};
  if (st.running) { if (typeof doDetener === 'function') return doDetener(); }
  if (typeof doIniciar === 'function') return doIniciar();
}
window.heroToggleCapture = heroToggleCapture;

// El enlace publico es el panel de solo lectura, no esta pagina de operacion.
// English: the public link is the read-only panel, not this operations page.
function sharePublicLink() {
  const url = new URL('../', location.href).href;
  const btn = document.getElementById('hero-share');
  const done = function (msg) {
    if (!btn) return;
    const prev = btn.innerHTML;
    btn.textContent = msg;
    setTimeout(function () { btn.innerHTML = prev; }, 2500);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(
      function () { done(window.OPS_LANG === 'en' ? 'Link copied' : 'Enlace copiado'); },
      function () { window.open(url, '_blank', 'noopener'); });
  } else {
    window.open(url, '_blank', 'noopener');
  }
}
window.sharePublicLink = sharePublicLink;

// ── Barra superior: nombre del nodo, reloj de Honduras, guía ───────────────

function _opsNodeName() {
  try {
    const parts = location.pathname.split('/').filter(Boolean);
    const isProject = /\.github\.io$/i.test(location.hostname) && parts.length >= 2;
    const repo = isProject ? parts[0] : (window.REPO_NAME || 'VIGIL');
    const owner = location.hostname.split('.')[0];
    return isProject ? owner + '/' + repo : repo;
  } catch (e) { return 'VIGIL'; }
}

// Honduras no usa horario de verano, asi que America/Tegucigalpa es estable
// todo el año. Se nombra la zona en vez de restar seis horas a mano: una
// resta a mano es un error esperando a que alguien cambie de pais.
// English: Honduras observes no DST, so America/Tegucigalpa is stable all
// year. Naming the zone beats subtracting six hours by hand.
function _opsStartClock() {
  const el = document.getElementById('hdr-clock-val');
  if (!el) return;
  const fmt = new Intl.DateTimeFormat('es-HN', {
    timeZone: 'America/Tegucigalpa', hour: '2-digit', minute: '2-digit', hour12: false,
  });
  const tick = function () { try { el.textContent = fmt.format(new Date()); } catch (e) {} };
  tick();
  setInterval(tick, 20000);
}

function initOpsTopbar() {
  const n = document.getElementById('hdr-node');
  if (n) {
    const name = _opsNodeName();
    // Fuera de un sitio de proyecto el nombre coincide con la marca que ya
    // esta a la izquierda; repetirlo no informa de nada.
    // English: off a project site the name equals the brand already shown to
    // the left; repeating it informs nobody.
    if (name && name.toLowerCase() !== 'vigil') n.textContent = name;
    else n.hidden = true;
  }
  _opsStartClock();
}
window.initOpsTopbar = initOpsTopbar;

function toggleOpsGuide() {
  const panel = document.getElementById('ops-guide');
  const btn = document.getElementById('btn-help');
  if (!panel) return;
  const open = panel.hasAttribute('hidden');
  if (open) panel.removeAttribute('hidden'); else panel.setAttribute('hidden', '');
  if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  if (open) { const c = panel.querySelector('button, a'); if (c) c.focus(); }
}
window.toggleOpsGuide = toggleOpsGuide;
