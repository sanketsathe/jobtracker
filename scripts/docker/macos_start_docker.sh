#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MARKER_FILE="${ROOT_DIR}/.codex_docker_started"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI not found. Install Docker Desktop first."
    exit 1
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

if docker_ready; then
    echo "Docker already running."
    exit 0
fi

echo "Starting Docker Desktop..."
if ! open -a Docker >/dev/null 2>&1; then
    if ! open -a "Docker Desktop" >/dev/null 2>&1; then
        echo "Unable to launch Docker Desktop. Start it manually and retry."
        exit 1
    fi
fi

timeout=120
interval=2
start_ts=$(date +%s)

while ! docker_ready; do
    now_ts=$(date +%s)
    if [ $((now_ts - start_ts)) -ge "$timeout" ]; then
        echo "Timed out waiting for Docker Desktop. Start it manually and retry."
        exit 1
    fi
    sleep "$interval"
done

touch "$MARKER_FILE"
echo "Docker ready."
