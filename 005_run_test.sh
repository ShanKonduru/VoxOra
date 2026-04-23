#!/usr/bin/env bash
set -euo pipefail

PYTHON=".venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "[ERROR] Virtual environment not found. Run 001_env.sh and 003_setup.sh first."
    exit 1
fi

export PYTHONUTF8=1
echo "Running tests..."
"$PYTHON" -m pytest tests/ -v
