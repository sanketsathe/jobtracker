#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MARKER_FILE="${ROOT_DIR}/.codex_docker_started"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI not found. Nothing to stop."
    exit 0
fi

echo "Bringing compose stack down (best effort)..."
(
    cd "$ROOT_DIR"
    docker compose down
) || true

if [ "${AUTO_DOCKER_QUIT:-}" != "1" ]; then
    echo "AUTO_DOCKER_QUIT not set; leaving Docker Desktop running."
    exit 0
fi

if [ ! -f "$MARKER_FILE" ]; then
    echo "Marker file not found; Docker Desktop was not started by this workflow."
    exit 0
fi

echo "Stopping Docker Desktop..."
if ! osascript -e 'quit app "Docker"' >/dev/null 2>&1; then
    echo "osascript quit failed; falling back to pkill."
    pkill -f "Docker Desktop" >/dev/null 2>&1 || true
fi

timeout=60
interval=2
elapsed=0

while docker info >/dev/null 2>&1; do
    if [ "$elapsed" -ge "$timeout" ]; then
        echo "Timed out waiting for Docker Desktop to quit."
        exit 1
    fi
    sleep "$interval"
    elapsed=$((elapsed + interval))
done

rm -f "$MARKER_FILE"
echo "Docker Desktop stopped."
