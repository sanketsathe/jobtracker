# Evidence Log

## Commands run
- `./.venv/bin/python manage.py check`
- `make test-fast`
- `USE_SQLITE_FOR_TESTS=1 ./.venv/bin/python manage.py test tracker`
- `USE_SQLITE_FOR_TESTS=1 make test`
- `FEATURE=milestone-2 make screenshot`

## Test results
- `make test-fast` ✅
- `USE_SQLITE_FOR_TESTS=1 ./.venv/bin/python manage.py test tracker` ✅
- `USE_SQLITE_FOR_TESTS=1 make test` ✅

## Screenshots
- `docs/evidence/2026-01-06/milestone-2/01-login.png`
- `docs/evidence/2026-01-06/milestone-2/02-dashboard.png`
- `docs/evidence/2026-01-06/milestone-2/03-new-application.png`

## Links
- `docs/ui-layout.md`
- `docs/ui-modern.md`
- `docs/api.md`
- `docs/reminders.md`
- `docs/milestone-2.md`
- `docs/pwa.md`

## Notes
- Screenshot run initially failed until `scripts/e2e/smoke_screenshots.py` was updated to detect the avatar menu.

## Run 2026-01-06 01:21

- Command: FEATURE=milestone-2 make screenshot
- Output: docs/evidence/2026-01-06/milestone-2/
- Screenshots:
  - docs/evidence/2026-01-06/milestone-2/01-login.png
  - docs/evidence/2026-01-06/milestone-2/02-dashboard.png
  - docs/evidence/2026-01-06/milestone-2/03-new-application.png

## Run 2026-01-06 09:39

- Command: FEATURE=milestone-2 make screenshot
- Output: docs/evidence/2026-01-06/milestone-2/
- Screenshots:
  - docs/evidence/2026-01-06/milestone-2/01-login.png
  - docs/evidence/2026-01-06/milestone-2/02-dashboard.png
  - docs/evidence/2026-01-06/milestone-2/03-new-application.png
