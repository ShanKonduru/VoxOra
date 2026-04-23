@echo off
REM ============================================================
REM 007_test_integration.bat  --  Run integration tests only
REM ============================================================

if not defined VIRTUAL_ENV (
    call .venv\Scripts\activate.bat
)

set PYTHONUTF8=1
cd backend
python -m pytest tests/integration/ -v --cov=app --cov-report=term-missing
cd ..
