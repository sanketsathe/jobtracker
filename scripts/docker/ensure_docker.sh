#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI not found. Install Docker Desktop (macOS) or your Docker engine."
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
    echo "Docker is running."
    exit 0
fi

os_name="$(uname -s)"
if [ "$os_name" = "Darwin" ]; then
    "$SCRIPT_DIR/macos_start_docker.sh"
    exit $?
fi

echo "Docker is not running, and auto-start is only supported on macOS."
echo "Start Docker and retry."
exit 1
