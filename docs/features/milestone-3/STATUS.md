# Milestone 3 Status

## DONE
- `/leads/` inbox owner-scoped with SSR filters, `has_app` annotation, and archived default hidden.
- Conversion flow idempotent via unique constraint and transaction; redirect opens `/applications/?selected=<id>` drawer.
- Non-JS fallback link added on leads table to reach the full editor/conversion form.
- Test coverage run: `python3 manage.py check`, `python3 manage.py migrate`, `python3 manage.py test tracker --keepdb --noinput`, `make test-fast`, `USE_SQLITE_FOR_TESTS=1 make test`, `FEATURE=milestone-3 make screenshot`, `make test-docker-autoports`.
- `selected` query param behavior covered by tests; drawer auto-opens as before.
- Dockerised test path simplified: `make test-docker-autoports` picks free ports/project name, waits for Postgres readiness, runs tests, and tears down containers.

## PENDING
- None; rerun commands below if environment changes.

## How to Reproduce / Verify
- Core filters/ownership: visit `/leads/?q=foo&has_app=1&archived=1` while logged in; non-owner access to `/leads/<id>/quick/` returns 404.
- Application drawer highlighting: `/applications/?selected=<id>` shows selected row; JS opens quick drawer.
- Docker test run: `make test-docker-autoports` (auto-picks free ports and unique compose project).

## Next Steps
- None. Re-run verification commands if further changes occur.
