#!/bin/zsh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TASK_CACHE="${TMPDIR:-/tmp}/offshore-energy-uv-cache"

cd "$PROJECT_DIR"
export UV_CACHE_DIR="$TASK_CACHE"

uv sync

if [[ ! -f data/processed/model_metrics.json || ! -f models/forecasting_v2.joblib ]]; then
  uv run python bootstrap.py --skip-download
fi

uv run streamlit run app.py
