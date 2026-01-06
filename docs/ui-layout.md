# UI Layout

This doc summarizes the global layout and the primary navigation/filtering patterns.

## Global shell
- Auth layout uses `base_auth.html` with a centered card (no sidebar/topbar).
- App layout uses `base_app.html` with a left sidebar and top bar.
- Top bar holds the hamburger, brand, and avatar menu.

## Sidebar navigation
- Items: Applications, Profile.
- Desktop: fixed sidebar with optional collapsed mode.
- Mobile: off-canvas drawer controlled by hamburger.

## Applications page
- Single page with view switcher (`list` | `board` | `followups`).
- Filter bar uses SSR querystrings.
- Saved view pills map to presets:
  - All: `/applications/?view=list`
  - Follow-ups Due: `/applications/?view=list&due=today`
  - Overdue: `/applications/?view=list&due=overdue`
  - This Week: `/applications/?view=list&due=week`
  - Interviews: `/applications/?view=list&status=INTERVIEW`

## Quick edit + full editor
- Row click opens a quick edit popover (sheet on mobile).
- Popover can maximize into full editor modal.
- Autosave runs on debounce with a compact status indicator.
