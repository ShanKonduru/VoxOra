#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 007_test_integration.sh  --  Run integration tests only
# ============================================================

if [ ! -f ".venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Run 001_env.sh and source 002_activate.sh first."
    exit 1
fi

export PYTHONUTF8=1
cd backend
python -m pytest tests/integration/ -v --cov=app --cov-report=term-missing
cd ..
