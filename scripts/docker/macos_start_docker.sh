#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MARKER_FILE="${ROOT_DIR}/.codex_docker_started"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI not found. Install Docker Desktop first."
    exit 1
fi

if docker info >/dev/null 2>&1; then
    echo "Docker already running."
    exit 0
fi

echo "Starting Docker Desktop..."
open -a Docker

timeout=120
interval=2
elapsed=0

while ! docker info >/dev/null 2>&1; do
    if [ "$elapsed" -ge "$timeout" ]; then
        echo "Timed out waiting for Docker Desktop. Start it manually and retry."
        exit 1
    fi
    sleep "$interval"
    elapsed=$((elapsed + interval))
done

touch "$MARKER_FILE"
echo "Docker ready."
