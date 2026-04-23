@echo off
REM ============================================================
REM 006_test_unit.bat  --  Run unit tests only, with coverage
REM ============================================================

if not defined VIRTUAL_ENV (
    call .venv\Scripts\activate.bat
)

set PYTHONUTF8=1
cd backend
python -m pytest tests/unit/ -v --cov=app --cov-report=term-missing
cd ..
