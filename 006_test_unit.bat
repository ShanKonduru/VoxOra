@echo off
setlocal
REM ============================================================
REM 006_test_unit.bat -- Run backend unit tests from repo root
REM ============================================================

set "ROOT_DIR=%~dp0"
set "VENV_PY=%ROOT_DIR%.venv\Scripts\python.exe"
set "BACKEND_DIR=%ROOT_DIR%backend"

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment not found at "%VENV_PY%"
    echo         Run 001_env.bat and install dependencies first.
    exit /b 1
)

if not exist "%BACKEND_DIR%\pytest.ini" (
    echo [ERROR] Could not find backend pytest config at "%BACKEND_DIR%\pytest.ini"
    exit /b 1
)

set "PYTHONUTF8=1"
set "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1"

pushd "%BACKEND_DIR%"
echo === Running Unit Tests ===
"%VENV_PY%" -m pytest tests\unit\ -q -p pytest_asyncio.plugin -p anyio.pytest_plugin -p pytest_cov --cov=app.security.input_sanitizer --cov=app.services.persona_manager --cov=app.services.state_machine --cov-report=term-missing --cov-fail-under=100
set "EXIT_CODE=%ERRORLEVEL%"
popd

if not "%EXIT_CODE%"=="0" (
    echo [FAIL] Unit tests failed with exit code %EXIT_CODE%.
    exit /b %EXIT_CODE%
)

echo [PASS] Unit tests completed successfully.
exit /b 0
