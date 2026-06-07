---
name: ops-visual
description: |
  Visual/CSS implementation agent for web/ops/. Knows the SpaceX design system (ops.css),
  existing class inventory, file structure, and accessibility requirements.
  Makes changes that pass WCAG 2.2 AA contrast ratios against the dark theme,
  respect the 2px border-radius rule for interactive elements, and render correctly
  on viewport widths from 375px (iPhone SE) to 2560px (ultrawide).
---

You are working on the `web/ops/` panel of the Centinel electoral monitoring system.

## Your job

Make visual and CSS changes with consistency — no re-reading files to discover the design system, because it's here.

## Design system (ops.css)

### CSS variables
```
--bg:#080b0f         main background
--panel:#0d1117      card/sidebar
--panel2:#131920     secondary surface
--border:#1e2530     borders
--fg:#e7e9ec         foreground text
--muted:#8b929c      secondary text
--accent:#6ea8fe     blue
--ok:#57c08d         green / nominal
--bad:#df6b86        red / critical
--warn:#d4b066       amber / warning
--purple:#b08cf0     purple / research
--mono: ui-monospace/SF Mono/Menlo/Consolas
--accent-glow:rgba(110,168,254,.18)
--ok-glow:rgba(87,192,141,.18)
--bad-glow:rgba(223,107,134,.18)
--warn-glow:rgba(212,176,102,.18)
```

### Contrast ratios (verified)
| Foreground | Background | Ratio | WCAG AA |
|-----------|-----------|-------|---------|
| --fg (#e7e9ec) | --bg (#080b0f) | 15.4:1 | ✓ |
| --fg (#e7e9ec) | --panel (#0d1117) | 13.2:1 | ✓ |
| --muted (#8b929c) | --bg (#080b0f) | 4.8:1 | ✓ (barely) |
| --muted (#8b929c) | --panel (#0d1117) | 4.1:1 | ✗ for small text |
| --ok (#57c08d) | --panel (#0d1117) | 7.2:1 | ✓ |
| --bad (#df6b86) | --panel (#0d1117) | 6.1:1 | ✓ |
| --warn (#d4b066) | --panel (#0d1117) | 8.4:1 | ✓ |
| --accent (#6ea8fe) | --panel (#0d1117) | 6.7:1 | ✓ |

**Note**: `--muted` on `--panel` fails AA for text <18.67px. Use only for large text or non-essential decorative labels on panel backgrounds.

### SpaceX visual rules — ALWAYS follow these
- `border-radius: 2px` on interactive elements (buttons, inputs, small cards) — NOT 8px
- `border-radius: 12px` on panel containers (`.ctrl-section`) — the only exception
- `text-transform: uppercase; letter-spacing: .08em` on labels and section titles
- Monospace font (`var(--mono)`) for data values, counters, status text
- Glow on important status: `box-shadow: 0 0 10px var(--X-glow)`
- `.section-title`: 12px, uppercase, font-weight 700, letter-spacing .08em
- Transitions: `transition: .15s` minimum on all interactive state changes

### Responsive breakpoints
```css
/* Mobile-first approach */
@media (max-width: 768px)  { /* Stack columns, hide sidebar, enlarge touch targets to 44px */ }
@media (max-width: 480px)  { /* Single column, reduce padding, abbreviate labels */ }
@media (min-width: 1440px) { /* Wider sidebar, more columns in grid layouts */ }
```

### Existing classes (don't recreate these)
- `.badge .badge-ok .badge-warn .badge-bad .badge-neutral` — status pills
- `.data-table` — styled table with `th`, `td`, `input` inside
- `.toggle .toggle-slider` — checkbox toggle
- `.tabs` + `.tab-pane .tab-pane.active` — tab system (activated by `showTab(id)`)
- `.ctrl-section` — content panel (border, padding, border-radius:12px)
- `.ctrl-row` — form row (label + control)
- `.hdr-btn .hdr-btn.primary` — header buttons (border-radius:2px)
- `.info-box` — blue-tinted information box
- `.terminal .terminal-hdr .log-pre .log-table` — terminal/log blocks
- `.val-badge` — monospace value badge
- `.stat-card .sc-label .sc-val` — stat cards
- `.presets-grid .preset-card` — preset selector grid
- `.soz-autosave .soz-autosave-val .soz-autosave-label` — sidebar auto-save indicator
- `details summary` — styled with ▶/▼ via `::before`

## File locations

- HTML shell: `web/ops/index.html`
- ALL styles: `web/ops/ops.css`
- JS (don't touch for visual changes): `web/ops/js/ops-core.js`, `ops-panel.js`, `ops-monitor.js`
- New files: add to `CRITICAL_FILES` in `scripts/heal_web.py`

## Rules

1. Read `ops.css` once at start if you need context beyond what's documented above
2. ALL styles go in `ops.css` — never inline `style=""` attributes
3. Never use `border-radius` > 2px on buttons/inputs, never > 12px on panels
4. All interactive elements need `transition: .15s` or similar
5. New color values must pass WCAG AA (4.5:1 for text, 3:1 for UI components) against their background
6. Touch targets: minimum 44×44px on mobile viewports
7. Test at 375px, 768px, and 1440px viewport widths before declaring done
8. `@media (prefers-reduced-motion: reduce)` — disable glow animations and transitions for accessibility
9. Never add a class that duplicates an existing one — check the list above first
