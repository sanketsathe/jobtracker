# Milestone 2 Epics

This plan breaks the milestone into epics with stories, tasks, and acceptance criteria.

## Epic 1: Layout + Navigation
Stories:
- Split authenticated and auth layouts.
- Global sidebar only includes Applications and Profile.
- Top bar adds avatar menu and quick profile panel.

Tasks:
- Create `base_app.html` and `base_auth.html`.
- Fix login layout and auth redirects.
- Add avatar menu with profile quick panel + settings link.

Acceptance criteria:
- Login page renders without sidebar/topbar.
- Sidebar only includes Applications + Profile.
- Avatar menu opens/closes with ESC and outside click.

## Epic 2: Applications Single Page Views
Stories:
- `/applications/` hosts list, board, and follow-ups.
- Filters and saved views are SSR-first querystrings.

Tasks:
- Add view switcher and filter bar in list template.
- Move board + followups content into `/applications/`.
- Redirect legacy `/board/` and `/followups/` routes.

Acceptance criteria:
- List/Board/Follow-ups switcher stays in one page.
- Filters apply via querystring and are bookmarkable.
- Mobile list renders as cards.

## Epic 3: Quick Edit Popover + Full Editor
Stories:
- Quick edit popover for fast status/next action updates.
- Full-screen modal editor for deep edits and follow-ups.

Tasks:
- Add `/applications/<id>/quick/` and `/applications/<id>/edit/` partials.
- Implement overlay portal with popover + modal.
- Wire autosave + undo toast + error states.

Acceptance criteria:
- Clicking a row opens a popover (sheet on mobile).
- Maximize opens full editor with follow-up list.
- Autosave works with clear status/error states.

## Epic 4: Status Workflow + Undo
Stories:
- Pipeline stages enforce terminal status rules.
- Undo toast for status change and follow-up clears.

Tasks:
- Validate status transitions in PATCH.
- Add undo toast with rollback call.

Acceptance criteria:
- Terminal -> non-terminal blocked for non-staff.
- Staff can override with `force=true`.
- Undo restores previous value within timeout.

## Epic 5: Follow-up Tracking
Stories:
- Primary next action + follow-up date are first-class.
- Follow-up history list supports completion.

Tasks:
- Follow-up create/update endpoints.
- Follow-up view shows today/overdue/week.

Acceptance criteria:
- Due sections render accurately.
- Follow-up create/complete works from modal.

## Epic 6: Board View
Stories:
- Kanban columns grouped by status.
- Drag/drop updates status with fallback select.

Tasks:
- Render status columns in `/applications/?view=board`.
- Add drag/drop + select fallback.

Acceptance criteria:
- Drag/drop persists status changes.
- Select fallback works without JS.

## Epic 7: Profile + Settings
Stories:
- Profile covers identity, targets, and contact details.
- Settings include theme, density, and reminder prefs.

Tasks:
- Add `UserProfile` settings fields.
- Update profile view with `tab=profile|settings`.

Acceptance criteria:
- Settings persist and reflect in layout.
- Reminder toggle available in avatar menu.

## Epic 8: Reminders + PWA
Stories:
- In-app reminders show due today/overdue.
- Email digest command sends daily reminders.
- PWA manifest + icons for install prompt.

Tasks:
- Update reminder command docs and tests.
- Add `manifest.webmanifest` and icons.

Acceptance criteria:
- Digest sends one email per user.
- Manifest and icons are linked in layouts.

## Epic 9: Tests + Evidence
Stories:
- Coverage for ownership, filters, popovers, board, reminders.
- Evidence captured for UI changes.

Tasks:
- Update/extend Django tests.
- Run checks/tests and capture Playwright screenshots.

Acceptance criteria:
- `python manage.py test tracker` passes.
- Evidence log links latest screenshots and commands.
