#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 006_test_unit.sh -- Run backend unit tests from repo root
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ROOT_DIR="$SCRIPT_DIR"
VENV_PY="$ROOT_DIR/.venv/bin/python"
BACKEND_DIR="$ROOT_DIR/backend"

if [ ! -f "$VENV_PY" ]; then
    echo "[ERROR] Virtual environment not found at $VENV_PY"
    echo "        Run 001_env.sh and install dependencies first."
    exit 1
fi

if [ ! -f "$BACKEND_DIR/pytest.ini" ]; then
    echo "[ERROR] Could not find backend pytest config at $BACKEND_DIR/pytest.ini"
    exit 1
fi

export PYTHONUTF8=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

echo ""
echo "=== Running Unit Tests ==="
cd "$BACKEND_DIR"
"$VENV_PY" -m pytest tests/unit/ -q -p pytest_asyncio.plugin -p anyio.pytest_plugin -p pytest_cov --cov=app.security.input_sanitizer --cov=app.services.persona_manager --cov=app.services.state_machine --cov-report=term-missing --cov-fail-under=100

echo "[PASS] Unit tests completed successfully."
