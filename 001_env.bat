@echo off
REM ============================================================
REM 001_env.bat  --  Create Python venv + verify Node.js
REM Run once after cloning the repo.
REM ============================================================

echo === Creating Python virtual environment at .venv ===
python -m venv .venv
echo Virtual environment created.

echo.
echo === Checking Node.js ===
node --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f %%v in ('node --version') do echo Node.js %%v found.
) else (
    echo [WARNING] Node.js not found. Install from https://nodejs.org
)

echo.
echo Done. Next steps:
echo   1. 002_activate.bat    (activate the venv)
echo   2. 003_setup.bat       (install Python + Node dependencies)
