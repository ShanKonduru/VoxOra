@echo off
REM ============================================================
REM 005_run_test.bat  --  Lint + test the backend
REM Runs: ruff check, black --check, pytest --cov
REM ============================================================

REM Activate venv if not already active
if not defined VIRTUAL_ENV (
    call .venv\Scripts\activate.bat
)

set PYTHONUTF8=1
cd backend

echo === Ruff Lint Check ===
ruff check .
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Ruff found issues. Fix them and re-run.
    cd ..
    exit /b 1
)

echo.
echo === Black Format Check ===
black --check .
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Formatting issues found. Run:  cd backend ^&^& black .
    cd ..
    exit /b 1
)

echo.
echo === Running Tests with Coverage ===
python -m pytest --cov=app tests/ -q

cd ..
echo.
echo === All checks passed ===
