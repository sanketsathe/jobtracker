#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MARKER_FILE="${ROOT_DIR}/.codex_docker_started"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI not found. Nothing to stop."
    exit 0
fi

PYTHON_BIN="$(command -v python3 || command -v python || true)"

docker_ready() {
    if [ -z "$PYTHON_BIN" ]; then
        docker info >/dev/null 2>&1
        return $?
    fi
    "$PYTHON_BIN" - <<'PY'
import subprocess
import sys

try:
    subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=2,
        check=True,
    )
except Exception:
    sys.exit(1)
PY
}

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
start_ts=$(date +%s)

while docker_ready; do
    now_ts=$(date +%s)
    if [ $((now_ts - start_ts)) -ge "$timeout" ]; then
        echo "Timed out waiting for Docker Desktop to quit."
        exit 1
    fi
    sleep "$interval"
done

rm -f "$MARKER_FILE"
echo "Docker Desktop stopped."
