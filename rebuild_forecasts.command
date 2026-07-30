#!/bin/zsh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TASK_CACHE="${TMPDIR:-/tmp}/offshore-energy-uv-cache"

cd "$PROJECT_DIR"
export UV_CACHE_DIR="$TASK_CACHE"

uv sync
uv run python bootstrap.py --skip-download
uv run pytest -q

echo ""
echo "Forecasting Model v2 rebuilt and tested successfully."
