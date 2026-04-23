@echo off
REM ============================================================
REM 004_run.bat  --  Start the full VoxOra stack (Docker Compose)
REM Starts: PostgreSQL 16, Redis 7, FastAPI backend, React frontend
REM
REM LOCAL DEV (without Docker):
REM   Terminal 1:  cd backend  &&  uvicorn app.main:app --reload
REM   Terminal 2:  cd frontend &&  npm run dev
REM ============================================================

if not exist .env (
    echo [ERROR] .env file not found.
    echo Copy .env.example to .env and fill in POSTGRES_PASSWORD and OPENAI_API_KEY.
    exit /b 1
)

echo === Starting VoxOra via Docker Compose ===
echo Press Ctrl+C to stop all services.
echo.
docker compose up --build
