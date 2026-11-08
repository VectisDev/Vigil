/* Tema de toda la página: un solo fondo, claro u oscuro.
   La preferencia guardada gana; si no hay, se usa la del sistema. */
(function () {
  var KEY = 'vigil-theme';

  function systemTheme() {
    try {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } catch (e) {
      return 'light';
    }
  }

  function savedTheme() {
    try {
      var v = localStorage.getItem(KEY);
      return v === 'light' || v === 'dark' ? v : null;
    } catch (e) {
      return null;
    }
  }

  function applyIcons(theme) {
    var links = document.querySelectorAll('link[rel="icon"]');
    for (var i = 0; i < links.length; i++) {
      var light = links[i].getAttribute('data-icon-light');
      var dark = links[i].getAttribute('data-icon-dark');
      if (light && dark) links[i].setAttribute('href', theme === 'dark' ? dark : light);
    }
    var logos = document.querySelectorAll('[data-logo-light][data-logo-dark]');
    for (var j = 0; j < logos.length; j++) {
      logos[j].setAttribute('src', theme === 'dark' ? logos[j].getAttribute('data-logo-dark') : logos[j].getAttribute('data-logo-light'));
    }
  }

  function label(theme) {
    return theme === 'dark' ? 'Día' : 'Noche';
  }

  function paintToggle(theme) {
    var buttons = document.querySelectorAll('#theme-toggle, .theme-toggle');
    var next = theme === 'dark' ? 'light' : 'dark';
    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
      btn.setAttribute('aria-label', next === 'dark' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro');
      if (btn.getAttribute('data-theme-text') === '1') btn.textContent = label(theme);
    }
  }

  function apply(theme, persist) {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;
    applyIcons(theme);
    paintToggle(theme);
    if (persist) {
      try { localStorage.setItem(KEY, theme); } catch (e) {}
    }
  }

  var initial = savedTheme() || systemTheme();
  apply(initial, false);

  window.vigilSetTheme = function (theme) { apply(theme, true); };
  window.vigilToggleTheme = function () {
    var cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    apply(cur === 'dark' ? 'light' : 'dark', true);
  };

  function ensureToggle() {
    if (document.getElementById('theme-toggle') || document.querySelector('.theme-toggle')) return;
    var host = document.querySelector('nav, header, #vigil-titlebar, .hdr, .bar');
    if (!host) host = document.body;
    if (!host) return;
    var btn = document.createElement('button');
    btn.id = 'theme-toggle';
    btn.type = 'button';
    btn.className = 'theme-toggle';
    btn.setAttribute('data-theme-text', '1');
    host.appendChild(btn);
  }

  function bind() {
    ensureToggle();
    var buttons = document.querySelectorAll('#theme-toggle, .theme-toggle');
    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      if (btn.getAttribute('data-theme-bound') === '1') continue;
      btn.setAttribute('data-theme-bound', '1');
      var already = btn.getAttribute('onclick') || '';
      if (already.indexOf('toggleTheme') === -1 && already.indexOf('vigilToggleTheme') === -1) {
        btn.addEventListener('click', function () { window.vigilToggleTheme(); });
      }
    }
    paintToggle(document.documentElement.getAttribute('data-theme') || initial);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind);
  else bind();
})();
