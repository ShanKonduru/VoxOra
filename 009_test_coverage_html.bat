@echo off
REM ============================================================
REM 009_test_coverage_html.bat  --  Full test suite + HTML report
REM Opens htmlcov\index.html after run
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
echo === Running All Tests with HTML Coverage ===
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html -q
cd ..

echo.
echo === HTML report generated at: backend\htmlcov\index.html ===
start "" "backend\htmlcov\index.html"
