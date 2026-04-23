#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 005_run_test.sh  --  Lint + test the backend
# Runs: ruff check, black --check, pytest --cov
# ============================================================

if [ ! -f ".venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Run 001_env.sh and source 002_activate.sh first."
    exit 1
fi

export PYTHONUTF8=1
cd backend

echo "=== Installing dependencies ==="
python -m pip install -r requirements-dev.txt -q

echo ""
echo "=== Ruff Lint Check ==="
ruff check .

echo ""
echo "=== Black Format Check ==="
black --check .

echo ""
echo "=== Running Tests with Coverage ==="
python -m pytest --cov=app tests/ -q

cd ..
echo ""
echo "=== All checks passed ==="
