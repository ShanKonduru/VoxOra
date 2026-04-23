@echo off
REM ============================================================
REM 003_setup.bat  --  Install backend Python + frontend Node deps
REM Run after 002_activate.bat.
REM ============================================================

echo === Upgrading pip ===
python.exe -m pip install --upgrade pip

echo.
echo === Installing backend Python dependencies (dev) ===
pip install -r backend\requirements-dev.txt

echo.
echo === Installing frontend Node dependencies ===
cd frontend
call npm ci
cd ..

echo.
echo === Setup complete ===
echo.
echo Next steps:
echo   1. Copy .env.example to .env and fill in POSTGRES_PASSWORD and OPENAI_API_KEY
echo   2. 004_run.bat        -- start the full stack via Docker Compose
echo   3. 005_run_test.bat   -- lint + test the backend
