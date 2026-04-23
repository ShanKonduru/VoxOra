#!/usr/bin/env bash
set -euo pipefail

PYTHON=".venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "[ERROR] Virtual environment not found. Run 001_env.sh first."
    exit 1
fi

echo "Upgrading pip..."
"$PYTHON" -m pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
"$PYTHON" -m pip install -r requirements.txt

echo "Done. All packages installed."
