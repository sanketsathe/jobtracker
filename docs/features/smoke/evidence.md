# Evidence Log

## Commands run
- `./.venv/bin/python -m pip install -r requirements-dev.txt`
- `./.venv/bin/python -m playwright install chromium`
- `FEATURE=smoke make screenshot`

## Test results
- Screenshot run succeeded using SQLite settings.

## Screenshots
- `docs/evidence/2026-01-05/smoke/01-login.png`
- `docs/evidence/2026-01-05/smoke/02-dashboard.png`
- `docs/evidence/2026-01-05/smoke/03-new-application.png`

## Links
- `docs/evidence/2026-01-05/smoke/server.log`

## Notes
- Uses `config.settings_e2e` and does not require Docker.

## Run 2026-01-05 10:25

- Command: FEATURE=smoke make screenshot
- Output: docs/evidence/2026-01-05/smoke/
- Screenshots:
  - docs/evidence/2026-01-05/smoke/01-login.png
  - docs/evidence/2026-01-05/smoke/02-dashboard.png
  - docs/evidence/2026-01-05/smoke/03-new-application.png
