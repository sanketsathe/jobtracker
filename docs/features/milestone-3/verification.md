# Milestone 3 Verification

## Acceptance Checklist
| Criteria | Status | Notes |
| --- | --- | --- |
| `/leads/` route is owner-scoped and lists leads with SSR filters (`q`, `source`, `work_mode`, `scam`, `has_app`, `archived` defaulting to active) | PASS | Filters applied in `LeadListView.get_queryset` with owner constraint and archived default; order `-discovered_at, -updated_at`. |
| `has_app` implemented with `Exists` annotation to avoid N+1 | PASS | Uses `Application` subquery with `OuterRef("pk")`; template reads annotated flag only. |
| Lead quick drawer/full editor use existing overlay pattern and close via ESC/outside click; mobile uses modal | PASS | `app.js` handles popover/modal selection and close interactions; `.app-row` rows reused. |
| Conversion endpoint owner-scoped, idempotent, and copies lead fields to Application | PASS | `LeadConvertView` wraps in transaction, unique constraint on `Application(job, owner)`, copies `job_url`, `location_text`, `source`, status wishlist. |
| Redirect after convert opens application drawer | PASS | Redirects to `/applications/?selected=<id>` which is honored by template and JS. |
| Non-JS usability for triage/conversion | PASS | Added `<noscript>` link from leads table to full editor, forms submit with redirects. |
| Ownership leakage prevented (404 for non-owners on lead endpoints) | PASS | Lead views use owner-scoped queryset + `get_object_or_404`; tests cover 404s. |
| Archived default hidden unless filtered; notes/archiving fields present | PASS | `is_archived` default filter plus fields in forms; badges show state. |
| `selected=<id>` SSR/JS open behavior covered by tests | PASS | New test asserts list highlights selected row; JS already opens drawer via `app.js` `selected` param handling. |

## Commands Run
- `python3 manage.py check` – OK.
- `python3 manage.py migrate` – OK (no migrations).
- `python3 manage.py test tracker --keepdb --noinput` – OK (42 tests).
- `make test-fast` – OK (42 tests, keepdb).
- `USE_SQLITE_FOR_TESTS=1 make test` – OK (42 tests, sqlite).
- `FEATURE=milestone-3 make screenshot` – OK; screenshots in `docs/evidence/2026-01-06/milestone-3/`.
- `make test-docker-autoports` – OK; auto-picked free ports (example: DB_PORT=54714 REDIS_PORT=54715) and cleaned containers after run.

## Milestone 2 Regression Check
- Application drawer still honors `selected` query param and opens from `/applications/?selected=<id>`; no regressions observed.

## Security / Ownership
- Lead quick/edit/patch/convert are owner-scoped and return 404 for non-owners (per tests in `tracker/tests.py`).

## Performance Notes
- `has_app` uses `Exists` annotation; lead list template only reads annotated flags so no additional queries during render observed.

## Docker Test Status
- Default ports can collide with local services. Compose now allows overriding ports; redis host port defaults to 6380. For dockerised tests, set free ports (e.g., `DB_PORT=55432 REDIS_PORT=6382 COMPOSE_PROJECT_NAME=jobtracker3 AUTO_DOCKER=1 make test`). If existing compose metadata causes errors, rerun with a fresh project name or `make docker-doctor`.
