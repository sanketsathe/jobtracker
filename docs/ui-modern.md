# UI Modernization Guide

This document captures the layout system, visual tokens, and interaction patterns for Milestone 2.

## Design tokens
Defined in `tracker/static/tracker/app.css`:
- Colors: `--bg`, `--surface`, `--text`, `--muted`, `--border`, `--accent`, `--shadow`
- Radii: `--radius`, `--radius-sm`
- Spacing: `--space-*` (aliases `--s-*`)
- Controls: `--control-h`, `--pad`

Density + theme:
- `html[data-density="compact"]` adjusts spacing and control height.
- `html[data-theme="light|dark"]` sets explicit theme.
- `html[data-reduce-motion="true"]` disables animations.

## Layout
- Auth layout: `templates/layout/base_auth.html` (centered auth card).
- App layout: `templates/layout/base_app.html` (sidebar + top bar + content).
- Sidebar shows global nav only (Applications + Profile).
- Applications uses a single page with `view=list|board|followups`.

## View switcher + filters
- Segmented view switcher sits above the filter bar.
- Filter bar uses SSR querystrings (`search`, `status`, `due`, `sort`).
- Saved view pills provide quick presets.
- Quick Add uses `<details>` for progressive disclosure.

## Popover + modal patterns
Overlay root:
- `#overlay-root` hosts popovers, modals, and toasts.

Quick edit popover:
- Desktop: anchored popover near the row.
- Mobile: rendered as bottom sheet.
- Autosaves status, follow-up date, and next action.

Full editor modal:
- Desktop: centered modal sheet.
- Mobile: full-screen modal.
- Includes all fields + follow-up history.

## A11y + keyboard
- ESC closes popover or modal.
- Popover does not trap focus.
- Full editor modal traps focus and restores focus on close.
- Menu uses `aria-haspopup`, `aria-expanded`, and outside click to close.

## Mobile behavior
- Sidebar becomes off-canvas via hamburger.
- List view becomes card layout.
- Quick edit uses a sheet on touch devices.
