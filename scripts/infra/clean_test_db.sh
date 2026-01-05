#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-jobtracker}"
COMPOSE=(docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE")
PG_SERVICE="${PG_SERVICE:-}"
PG_USER="${PG_USER:-jobtracker}"
PG_ADMIN_DB="${PG_ADMIN_DB:-postgres}"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI not found; skipping test DB cleanup."
    exit 0
fi

if ! docker info >/dev/null 2>&1; then
    echo "Docker not running; skipping test DB cleanup."
    exit 0
fi

if [ -z "$PG_SERVICE" ]; then
    PG_SERVICE=$(awk '
        /^services:/ { in_services = 1; next }
        in_services && $0 ~ /^[[:space:]][[:space:]][A-Za-z0-9_-]+:[[:space:]]*$/ {
            line = $0
            sub(/^[[:space:]][[:space:]]/, "", line)
            sub(/:[[:space:]]*$/, "", line)
            svc = line
            services[svc] = 1
            current = svc
            next
        }
        in_services && $0 ~ /^[[:space:]][[:space:]][[:space:]][[:space:]]image:[[:space:]]*postgres/ {
            if (!postgres_service) postgres_service = current
        }
        END {
            if ("db" in services) { print "db"; exit }
            if ("postgres" in services) { print "postgres"; exit }
            if (postgres_service) { print postgres_service; exit }
        }' "$COMPOSE_FILE")
fi

if [ -z "$PG_SERVICE" ]; then
    echo "Unable to detect Postgres service in $COMPOSE_FILE; skipping test DB cleanup."
    exit 0
fi

if ! "${COMPOSE[@]}" ps --services --status running | grep -q "^${PG_SERVICE}$"; then
    echo "Postgres service '$PG_SERVICE' not running; skipping test DB cleanup."
    exit 0
fi

DB_NAME="${DB_NAME:-jobtracker}"
TEST_DB_NAME="${TEST_DB_NAME:-test_${DB_NAME}}"

if [ -n "${TEST_DB:-}" ]; then
    TEST_DB_NAME="$TEST_DB"
fi

if [ -n "${DJANGO_TEST_DATABASE_NAME:-}" ]; then
    TEST_DB_NAME="$DJANGO_TEST_DATABASE_NAME"
fi

echo "Cleaning test database '${TEST_DB_NAME}' on service '${PG_SERVICE}'..."
(
    cd "$ROOT_DIR"
    "${COMPOSE[@]}" exec -T "$PG_SERVICE" psql -U "$PG_USER" -d "$PG_ADMIN_DB" -v ON_ERROR_STOP=1 \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${TEST_DB_NAME}' AND pid <> pg_backend_pid();" \
        -c "DROP DATABASE IF EXISTS \"${TEST_DB_NAME}\";"
)

echo "Test database cleanup complete."
