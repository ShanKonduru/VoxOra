@echo off
REM ============================================================
REM 002_activate.bat  --  Activate the Python virtual environment
REM ============================================================
if not exist .venv\Scripts\activate.bat (
    echo [ERROR] .venv not found. Run 001_env.bat first.
    exit /b 1
)
call .venv\Scripts\activate.bat
echo Virtual environment activated.  Run 008_deactivate.bat to exit.
