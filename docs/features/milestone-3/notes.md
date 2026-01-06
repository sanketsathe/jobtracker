# Work Notes

## Log
- Added Leads inbox list with SSR filters and annotations.
- Implemented lead quick drawer, full editor, and conversion endpoint.
- Extended JobLead model with notes/archiving and added Application unique constraint.
- Added a non-JS fallback link from the leads table and made the Redis compose port configurable to avoid local conflicts during dockerised tests.
- Added `make test-docker-autoports` to pick free ports/unique project names for dockerised test runs and tear down afterward.

## DoD
- Feature spec exists: `docs/features/milestone-3/spec.md`
- Acceptance criteria verified: automated tests + Playwright smoke
- Scope/non-goals documented: `docs/features/milestone-3/spec.md`
- `python manage.py check`: done
- `make test-fast`: done
- `make test`: done via SQLite; docker compose failed (port 6379 in use)
- Migrations created and applied: created; applied in `config.settings_e2e` during screenshots
- Evidence captured: done
- Evidence log updated: done
- Manual smoke: N/A (Playwright smoke via `make screenshot`)
- Commit hygiene: N/A (no commit requested)

## Open questions
- None.
