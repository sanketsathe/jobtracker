.PHONY: check test test-fast test-clean playwright-install screenshot archive-evidence docs-check docker-start docker-stop docker-up docker-down docker-ensure clean-test-db

PYTHON ?= $(if $(wildcard ./.venv/bin/python),./.venv/bin/python,python3)
COMPOSE_FILE ?= docker-compose.yml
DOCKER_OK ?= $(shell docker info >/dev/null 2>&1 && echo 1 || echo 0)
DAYS ?= 60
TEST_ARGS ?= --noinput
PG_SERVICE ?= $(shell awk '\
	/^services:/ { in_services = 1; next } \
	in_services && match($$0, /^[[:space:]]{2}([A-Za-z0-9_-]+):[[:space:]]*$$/, m) { \
		svc = m[1]; services[svc] = 1; current = svc; next } \
	in_services && match($$0, /^[[:space:]]{4}image:[[:space:]]*postgres/, m) { \
		if (!postgres_service) postgres_service = current } \
	END { \
		if ("db" in services) { print "db"; exit } \
		if ("postgres" in services) { print "postgres"; exit } \
		if (postgres_service) { print postgres_service; exit } \
	}' $(COMPOSE_FILE))
PG_USER ?= $(shell awk -v svc="$(PG_SERVICE)" '\
	/^services:/ { in_services = 1; next } \
	in_services && match($$0, /^[[:space:]]{2}([A-Za-z0-9_-]+):[[:space:]]*$$/, m) { current = m[1]; next } \
	current == svc && match($$0, /^[[:space:]]{6}POSTGRES_USER:[[:space:]]*(.+)$$/, m) { \
		user = m[1]; gsub(/"/, "", user); print user; found = 1; exit } \
	current == svc && match($$0, /^[[:space:]]{6}-[[:space:]]*POSTGRES_USER=([^[:space:]]+)/, m) { \
		user = m[1]; gsub(/"/, "", user); print user; found = 1; exit } \
	END { if (!found) print "jobtracker" }' $(COMPOSE_FILE))
PG_ADMIN_DB ?= postgres

check:
	$(PYTHON) manage.py check

test:
	@set -e; \
	EXIT_CODE=0; \
	if [ "$(AUTO_DOCKER)" = "1" ]; then \
		$(MAKE) docker-up; \
	fi; \
	if [ "$(CLEAN_TEST_DB)" = "1" ]; then \
		$(MAKE) clean-test-db; \
	fi; \
	$(PYTHON) manage.py test $(TEST_ARGS) || EXIT_CODE=$$?; \
	if [ "$(AUTO_DOCKER_QUIT)" = "1" ]; then \
		$(MAKE) docker-stop || true; \
	fi; \
	exit $$EXIT_CODE

test-fast:
	@if [ "$(DOCKER_OK)" = "1" ]; then \
		$(PYTHON) manage.py test tracker --keepdb; \
	else \
		echo "Docker not running; falling back to SQLite (USE_SQLITE_FOR_TESTS=1)."; \
		USE_SQLITE_FOR_TESTS=1 $(PYTHON) manage.py test tracker --keepdb; \
	fi

test-clean:
	@if [ -z "$(PG_SERVICE)" ]; then \
		echo "Unable to detect Postgres service in $(COMPOSE_FILE). Set PG_SERVICE=<name> and retry."; \
		exit 1; \
	fi
	@docker compose exec -T $(PG_SERVICE) psql -U $(PG_USER) -d $(PG_ADMIN_DB) -v ON_ERROR_STOP=1 \
		-c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='test_jobtracker' AND pid <> pg_backend_pid();" \
		-c "DROP DATABASE IF EXISTS test_jobtracker;" || true

playwright-install:
	$(PYTHON) -m playwright install chromium

screenshot:
	@if [ -z "$(FEATURE)" ]; then \
		echo "Usage: FEATURE=<slug> make screenshot"; \
		exit 1; \
	fi
	@set -e; \
	EXIT_CODE=0; \
	NEED_DOCKER=0; \
	if [ -n "$(DJANGO_SETTINGS_MODULE)" ] && [ "$(DJANGO_SETTINGS_MODULE)" != "config.settings_e2e" ]; then \
		NEED_DOCKER=1; \
	fi; \
	if [ "$(AUTO_DOCKER)" = "1" ] && [ "$$NEED_DOCKER" = "1" ]; then \
		$(MAKE) docker-up; \
	fi; \
	$(PYTHON) scripts/e2e/smoke_screenshots.py --feature "$(FEATURE)" || EXIT_CODE=$$?; \
	if [ "$(AUTO_DOCKER_QUIT)" = "1" ]; then \
		$(MAKE) docker-stop || true; \
	fi; \
	exit $$EXIT_CODE

archive-evidence:
	$(PYTHON) scripts/archive/archive_evidence.py --days $(DAYS)

docs-check:
	@test -f docs/PROCESS/Definition_of_Done.md
	@test -f docs/PROCESS/Codex_Delivery_Protocol.md
	@test -f docs/PROCESS/Evidence_Standards.md
	@test -f docs/adr/TEMPLATE.md
	@test -f docs/features/_template/spec.md

docker-start:
	@scripts/docker/ensure_docker.sh

docker-ensure: docker-start

docker-up: docker-start
	@docker compose up -d
	@docker compose ps

docker-down:
	@docker compose down

docker-stop:
	@scripts/docker/macos_stop_docker.sh

clean-test-db:
	@scripts/infra/clean_test_db.sh
