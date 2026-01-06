# Milestone 3 Epics

This plan breaks the milestone into epics with stories, tasks, and acceptance criteria.

## Epic 1: Navigation + Route
Stories:
- Add Leads to authenticated navigation.
- Provide `/leads/` inbox route.

Tasks:
- Update sidebar nav.
- Add Lead list view and URL route.

Acceptance criteria:
- Authenticated users can open `/leads/`.
- Sidebar includes Leads between Applications and Profile.

## Epic 2: Leads Inbox List + Filters
Stories:
- SSR list of JobLead owned by the user.
- Querystring filters for search, source, work mode, scam, conversion, archive.

Tasks:
- Implement Lead list template with table layout + mobile cards.
- Add `has_app` annotation via `Exists`.
- Apply filters and default ordering.

Acceptance criteria:
- Filters work without JS and are bookmarkable.
- `has_app` uses annotation to avoid N+1.
- Default order is `-discovered_at`, then `-updated_at`.

## Epic 3: Lead Quick Drawer + Full Editor
Stories:
- Quick drawer reuses existing overlay patterns.
- Full editor modal for deep edits.

Tasks:
- Add `/leads/<id>/quick/` and `/leads/<id>/edit/` partials.
- Add patch endpoint for autosave.
- Ensure ESC/outside click closes drawer.

Acceptance criteria:
- Quick drawer opens from list rows.
- Maximize opens full editor modal.
- Fields autosave with existing UI states.

## Epic 4: Convert Lead -> Application
Stories:
- Convert leads safely, idempotently, and redirect to applications.

Tasks:
- Add POST `/leads/<id>/convert/` endpoint.
- Enforce owner scoping + unique constraint.
- Return JSON for AJAX, redirect for normal POST.

Acceptance criteria:
- Converting twice does not create duplicates.
- Non-owners receive 404.
- Redirect highlights the resulting application.

## Epic 5: Data Model Enhancements
Stories:
- Notes and archiving fields keep the inbox clean.
- Backfill missing lead owners.

Tasks:
- Add JobLead notes + archive fields.
- Backfill JobLead owners from related applications or fallback user.

Acceptance criteria:
- Missing owners are backfilled safely.
- Archived filter works with default to active leads.

## Epic 6: Tests + Docs + Evidence
Stories:
- Coverage for ownership, conversion, filters.
- Evidence captured for UI changes.

Tasks:
- Add tests for ownership, idempotency, and filters.
- Update docs (spec, test plan, milestone summary).
- Capture Playwright screenshots and log evidence.

Acceptance criteria:
- `python manage.py test tracker` passes.
- Evidence log links latest screenshots and commands.
