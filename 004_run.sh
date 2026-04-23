#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 004_run.sh  --  Start the full VoxOra stack (Docker Compose)
# Starts: PostgreSQL 16, Redis 7, FastAPI backend, React frontend
#
# LOCAL DEV (without Docker):
#   Terminal 1:  cd backend  &&  uvicorn app.main:app --reload
#   Terminal 2:  cd frontend &&  npm run dev
# ============================================================

if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found."
    echo "Copy .env.example to .env and fill in POSTGRES_PASSWORD and OPENAI_API_KEY."
    exit 1
fi

echo "=== Starting VoxOra via Docker Compose ==="
echo "Press Ctrl+C to stop all services."
echo ""
docker compose up --build
