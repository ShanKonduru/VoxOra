#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 003_setup.sh  --  Install backend Python + frontend Node deps
# Run after sourcing 002_activate.sh.
# ============================================================

PYTHON=".venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "[ERROR] Virtual environment not found. Run 001_env.sh and source 002_activate.sh first."
    exit 1
fi

echo "=== Upgrading pip ==="
"$PYTHON" -m pip install --upgrade pip

echo ""
echo "=== Installing backend Python dependencies (dev) ==="
"$PYTHON" -m pip install -r backend/requirements-dev.txt

echo ""
echo "=== Installing frontend Node dependencies ==="
cd frontend
npm ci
cd ..

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill in POSTGRES_PASSWORD and OPENAI_API_KEY"
echo "  2. ./004_run.sh        -- start the full stack via Docker Compose"
echo "  3. ./005_run_test.sh   -- lint + test the backend"
