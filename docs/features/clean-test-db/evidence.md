# Evidence Log

## Commands run
- `AUTO_DOCKER=1 AUTO_DOCKER_QUIT=1 make test` (failed; see log)
- `COMPOSE_PROJECT_NAME=jobtracker2 AUTO_DOCKER=1 AUTO_DOCKER_QUIT=1 make test`
- `CLEAN_TEST_DB=1 COMPOSE_PROJECT_NAME=jobtracker2 AUTO_DOCKER=1 AUTO_DOCKER_QUIT=1 make test`
- `AUTO_DOCKER=1 make docker-up` (auto-ran docker-doctor after "No such container")
- `docker compose -p jobtracker ps`
- `./.venv/bin/python manage.py check`
- `USE_SQLITE_FOR_TESTS=1 ./.venv/bin/python manage.py test tracker`

## Test results
- Default compose project fails with `No such container` during `docker compose up -d` (Docker Desktop metadata issue).
- Tests pass against Postgres using alternate compose project.
- CLEAN_TEST_DB run drops test DB before tests; no "already exists" warning.
- `make docker-up` still reported `No such container` after docker-doctor; services appeared as Up via `docker compose -p jobtracker ps`.
- Django checks passed; tracker tests passed with SQLite fallback.

## Screenshots
- N/A (no UI changes)

## Links
- `docs/evidence/2026-01-05/clean-test-db/test-default.log`
- `docs/evidence/2026-01-05/clean-test-db/test-default-workaround.log`
- `docs/evidence/2026-01-05/clean-test-db/test-clean-success.log`

## Notes
- Docker Desktop is running but default project containers appear corrupted; Docker reports "No such container" for IDs listed in `docker ps -a`.
- Docker Desktop restart attempts timed out, so `make docker-down`, Postgres migrations, and runserver smoke test could not be re-verified after the restart.
