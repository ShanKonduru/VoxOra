@echo off
REM ============================================================
REM 007_test_integration.bat  --  Run integration tests only
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
echo === Running Integration Tests ===
python -m pytest tests/integration/ -v --cov=app --cov-report=term-missing
cd ..
