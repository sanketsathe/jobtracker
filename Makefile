.PHONY: check test test-fast test-clean

PYTHON ?= $(if $(wildcard ./.venv/bin/python),./.venv/bin/python,python3)
COMPOSE_FILE ?= docker-compose.yml
DOCKER_OK ?= $(shell docker info >/dev/null 2>&1 && echo 1 || echo 0)
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
	$(PYTHON) manage.py test

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
