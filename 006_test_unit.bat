@echo off
REM ============================================================
REM 006_test_unit.bat  --  Run unit tests only, with coverage
REM ============================================================

if not defined VIRTUAL_ENV (
    call .venv\Scripts\activate.bat
)

set PYTHONUTF8=1
cd backend

echo === Installing dependencies ===
python -m pip install -r requirements-dev.txt -q
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] pip install failed.
    cd ..
    exit /b 1
)

echo.
echo === Running Unit Tests ===
python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing
cd ..
