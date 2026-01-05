# Evidence Log

## Commands run
- `DJANGO_SETTINGS_MODULE=config.settings AUTO_DOCKER=1 AUTO_DOCKER_QUIT=1 FEATURE=smoke-pg make screenshot`

## Test results
- Screenshot run succeeded against Postgres via Docker Compose.

## Screenshots
- `docs/evidence/2026-01-05/smoke-pg/01-login.png`
- `docs/evidence/2026-01-05/smoke-pg/02-dashboard.png`
- `docs/evidence/2026-01-05/smoke-pg/03-new-application.png`

## Links
- `docs/evidence/2026-01-05/smoke-pg/server.log`

## Notes
- Docker Desktop was already running; AUTO_DOCKER_QUIT did not quit without marker.

## Run 2026-01-05 10:26

- Command: FEATURE=smoke-pg make screenshot
- Output: docs/evidence/2026-01-05/smoke-pg/
- Screenshots:
  - docs/evidence/2026-01-05/smoke-pg/01-login.png
  - docs/evidence/2026-01-05/smoke-pg/02-dashboard.png
  - docs/evidence/2026-01-05/smoke-pg/03-new-application.png
