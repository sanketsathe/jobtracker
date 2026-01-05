# Evidence Log

## Commands run
- `AUTO_DOCKER=1 AUTO_DOCKER_QUIT=1 make test` (failed; see log)
- `COMPOSE_PROJECT_NAME=jobtracker2 AUTO_DOCKER=1 AUTO_DOCKER_QUIT=1 make test`
- `CLEAN_TEST_DB=1 COMPOSE_PROJECT_NAME=jobtracker2 AUTO_DOCKER=1 AUTO_DOCKER_QUIT=1 make test`

## Test results
- Default compose project fails with `No such container` during `docker compose up -d` (Docker Desktop metadata issue).
- Tests pass against Postgres using alternate compose project.
- CLEAN_TEST_DB run drops test DB before tests; no "already exists" warning.

## Screenshots
- N/A (no UI changes)

## Links
- `docs/evidence/2026-01-05/clean-test-db/test-default.log`
- `docs/evidence/2026-01-05/clean-test-db/test-default-workaround.log`
- `docs/evidence/2026-01-05/clean-test-db/test-clean-success.log`

## Notes
- Docker Desktop is running but default project containers appear corrupted; Docker reports "No such container" for IDs listed in `docker ps -a`.
