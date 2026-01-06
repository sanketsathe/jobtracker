# Evidence Log

## Commands run
- `python3 manage.py check`
- `make test-fast`
- `python3 manage.py test tracker --keepdb --noinput`
- `AUTO_DOCKER=1 make test` (failed)
- `USE_SQLITE_FOR_TESTS=1 make test`
- `FEATURE=milestone-3 make screenshot`

## Test results
- `make test-fast` ✅
- `python3 manage.py test tracker --keepdb --noinput` ✅
- `AUTO_DOCKER=1 make test` ❌ (Redis port 6379 already allocated)
- `USE_SQLITE_FOR_TESTS=1 make test` ✅

## Screenshots
- `docs/evidence/2026-01-06/milestone-3/01-login.png`
- `docs/evidence/2026-01-06/milestone-3/02-dashboard.png`
- `docs/evidence/2026-01-06/milestone-3/03-leads.png`

## Links
- `docs/milestone-3.md`
- `docs/features/milestone-3/spec.md`
- `docs/features/milestone-3/test-plan.md`

## Notes
- `python3 manage.py test tracker` prompted for an existing test DB; reran with `--keepdb --noinput`.
- Docker compose failed due to port 6379 in use; tests were rerun with SQLite.

## Run 2026-01-06 11:35

- Command: FEATURE=milestone-3 make screenshot
- Output: docs/evidence/2026-01-06/milestone-3/
- Screenshots:
  - docs/evidence/2026-01-06/milestone-3/01-login.png
  - docs/evidence/2026-01-06/milestone-3/02-dashboard.png
  - docs/evidence/2026-01-06/milestone-3/03-leads.png

## Run 2026-01-06 21:09

- Command: FEATURE=milestone-3 make screenshot
- Output: docs/evidence/2026-01-06/milestone-3/
- Screenshots:
  - docs/evidence/2026-01-06/milestone-3/01-login.png
  - docs/evidence/2026-01-06/milestone-3/02-dashboard.png
  - docs/evidence/2026-01-06/milestone-3/03-leads.png

## Run 2026-01-06 21:57

- Command: FEATURE=milestone-3 make screenshot
- Output: docs/evidence/2026-01-06/milestone-3/
- Screenshots:
  - docs/evidence/2026-01-06/milestone-3/01-login.png
  - docs/evidence/2026-01-06/milestone-3/02-dashboard.png
  - docs/evidence/2026-01-06/milestone-3/03-leads.png
