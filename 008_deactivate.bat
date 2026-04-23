@echo off
REM ============================================================
REM 008_deactivate.bat  --  Deactivate the Python virtual environment
REM ============================================================
if not defined VIRTUAL_ENV (
    echo [INFO] No virtual environment is currently active.
    exit /b 0
)
deactivate
echo Virtual environment deactivated.
