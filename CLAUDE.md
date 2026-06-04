# CLAUDE.md — Centinel Project Context

## What this is

Electoral monitoring system for Honduras. `web/` is a GitHub Pages static site.
No build step, no bundler — everything is served as-is.

---

## File map — web/ops/ panel

| File | Lines | Content |
|---|---|---|
| `web/ops/index.html` | ~1537 | HTML shell, GLOBALS/DEPARTMENTS/PRESETS constants, AUTH IIFE, `initAll()` |
| `web/ops/ops.css` | ~536 | All styles — SpaceX design system |
| `web/ops/js/ops-core.js` | ~564 | `loadConfig`, `loadSnapshot`, sensor cards, map, sliders |
| `web/ops/js/ops-panel.js` | ~927 | `markDirty`, `autoApply`, `setMode`, tabs, presets, `writeChanges`, OTS, logs |
| `web/ops/js/ops-monitor.js` | ~1333 | Downloads, country selector, swarm, election, lab |

Load order: `ops-core.js` → `ops-panel.js` → `ops-monitor.js` → inline script in index.html.
All files are global scope (`<script src>`), not ES modules. `onclick=` handlers in HTML work directly.

---

## SpaceX design system (ops.css)

### CSS variables
```
--bg:#080b0f         main background
--panel:#0d1117      card/sidebar background
--panel2:#131920     secondary surface
--border:#1e2530     borders
--fg:#e7e9ec         foreground text
--muted:#8b929c      secondary text
--accent:#6ea8fe     blue highlight
--ok:#57c08d         green / nominal
--bad:#df6b86        red / critical
--warn:#d4b066       amber / warning
--purple:#b08cf0     purple / research
--mono: ui-monospace/SF Mono/Menlo/Consolas
```

### SpaceX visual rules
- `border-radius: 2px` on interactive elements (buttons, cards) — NOT 8px
- `text-transform: uppercase; letter-spacing: .08em` on labels and titles
- Glow shadows with color variables: `box-shadow: 0 0 10px var(--accent-glow)`
- Monospace font (`var(--mono)`) for data values, badges, status text
- `.section-title` class: 12px, uppercase, 700 weight, letter-spacing .08em

### Key CSS classes already in ops.css
- **Badges:** `.badge .badge-ok .badge-warn .badge-bad .badge-neutral`
- **Tables:** `.data-table` (with `th`, `td`, `input` inside)
- **Toggles:** `.toggle .toggle-slider` (checkbox toggle)
- **Tabs:** `.tabs` + `.tab-pane .tab-pane.active` — `showTab(id)` activates
- **Sections:** `.ctrl-section` (panel with border-radius:12px), `.ctrl-row`
- **Terminals:** `.terminal .terminal-hdr .log-pre .log-table`
- **Presets:** `.presets-grid .preset-card`
- **Cards:** `.stat-card .sc-label .sc-val`
- **Sidebar:** `.soz-autosave .soz-autosave-val .soz-autosave-label`
- **Glow animations:** `badge-ok/bad/warn` have `box-shadow` glow, `.ms-val.nominal/alerta/critico`
- **Info box:** `.info-box` (blue tinted box)
- **Details/summary:** styled with `▶/▼` chevrons in `details summary::before`

### Adding new styles
Add to `ops.css` at the relevant section. SpaceX block is at the bottom (after `/* ── SPACEX REDESIGN ── */`).
Add new files to `CRITICAL_FILES` in `scripts/heal_web.py`.

---

## Auto-save / dirty state (ops-panel.js)

- `markDirty()` → sets `isDirty=true`, starts 1.5s debounce timer → `autoApply()`
- `_autoApplyEnabled` (localStorage `centinel-autosave`) — kill-switch
- When OFF: `#btn-apply-now` shows (manual apply button)
- At end of `initAll()`: timer is cancelled and `isDirty=false` to prevent PAT modal on load

---

## Modo Fácil / Modo Completo

- `setMode('easy'|'full')` in ops-panel.js controls `#advanced-config` visibility
- `#advanced-config`: 5-tab config panel (Endpoints, Captura, Alertas, Red, Reglas)
- Tabs activated via `showTab('t-endpoints'|'t-capture'|'t-alerts'|'t-network'|'t-rules')`

---

## Dev diary conventions

- Location: `docs/dev-diary/`
- Naming: `dev-diary-YYYYMMDD-CamelCaseTitle-01.md`
- Voice: first-person, project owner narrating (not AI translating). No "implementamos" from AI perspective.
- Header format: `# YYYYMMDD — Title` then date line, then narrative.
- No legacy folder — all entries at flat level in `docs/dev-diary/`

---

## Git workflow

- Feature branches from `main`, prefix `vectisdev/<slug>-<id>`
- Push to BOTH `origin claude/<branch>` AND `origin vectisdev/<branch>` (stop hook checks against `vectisdev/` ref)
- Create dual PRs: one → `main`, one → `dev-v15` (current dev branch)
- Conventional commits: `fix:`, `feat:`, `chore:`, `docs:`, `security:`
- Include session URL at end of commit message

---

## heal_web.py

`scripts/heal_web.py` restores critical files via `git checkout HEAD`.
When adding new files to `web/ops/`, add them to `CRITICAL_FILES` list in that script.
