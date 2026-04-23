#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 009_test_coverage_html.sh  --  Full test suite + HTML report
# Opens htmlcov/index.html after run (requires a browser)
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
echo "=== Running All Tests with HTML Coverage ==="
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html -q
cd ..

echo ""
echo "=== HTML report generated at: backend/htmlcov/index.html ==="
# open in default browser (Linux/macOS)
if command -v xdg-open &>/dev/null; then
    xdg-open backend/htmlcov/index.html
elif command -v open &>/dev/null; then
    open backend/htmlcov/index.html
fi
