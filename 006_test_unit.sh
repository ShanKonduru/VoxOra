#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 006_test_unit.sh  --  Run unit tests only, with coverage
# ============================================================

if [ ! -f ".venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Run 001_env.sh and source 002_activate.sh first."
    exit 1
fi

export PYTHONUTF8=1
cd backend
python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing
cd ..
