#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker CLI not found. Install Docker Desktop (macOS) or your Docker engine."
    exit 1
fi

if docker info >/dev/null 2>&1; then
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
