---
name: ops-visual
description: Use this agent for visual/CSS changes to web/ops/. It knows the SpaceX design system, existing CSS classes, and file structure so the main context doesn't need to re-read ops.css before every edit.
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

### SpaceX visual rules — ALWAYS follow these
- `border-radius: 2px` on interactive elements — not 8px, not 6px
- `text-transform: uppercase; letter-spacing: .08em` on labels
- Monospace font (`var(--mono)`) for data values, counters, status text
- Glow on important status: `box-shadow: 0 0 10px var(--X-glow)`
- `.section-title` is 12px uppercase 700 — match this for section headers
- New CSS sections go into `ops.css` at the bottom SpaceX block

### Existing classes (don't recreate these)
- `.badge .badge-ok .badge-warn .badge-bad .badge-neutral` — status pills
- `.data-table` — styled table
- `.toggle .toggle-slider` — checkbox toggle
- `.tabs` + `.tab-pane .tab-pane.active` — tab system
- `.ctrl-section` — content panel with border, padding, border-radius:12px
- `.ctrl-row` — form row (label + control)
- `.hdr-btn .hdr-btn.primary` — header buttons (border-radius:2px in SpaceX block)
- `.info-box` — blue-tinted info box
- `.terminal .terminal-hdr .log-pre` — terminal blocks
- `.val-badge` — monospace value badge
- `details summary` — styled with ▶/▼ in ::before

## File locations

- HTML: `web/ops/index.html` — HTML shell only, no business logic CSS
- CSS: `web/ops/ops.css` — ALL styles go here
- New files: add to `CRITICAL_FILES` in `scripts/heal_web.py`

## Rules

1. Read `ops.css` once at the start — the design system above covers variables and classes but not every existing line
2. Remove inline styles (`style="background:var(--bg);..."`) — extract to CSS classes
3. Replace native `<details>/<summary>` with styled divs when appearance matters — native browser widget ignores our CSS
4. Never use `border-radius` > 2px on buttons, never > 12px on panels
5. All interactive elements need a `transition:.15s` or similar
