#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 001_env.sh  --  Create Python venv + verify Node.js
# Run once after cloning the repo.
# ============================================================

echo "=== Creating Python virtual environment at .venv ==="
python3 -m venv .venv
echo "Virtual environment created at .venv/"

echo ""
echo "=== Checking Node.js ==="
if command -v node &>/dev/null; then
    echo "Node.js $(node --version) found."
else
    echo "[WARNING] Node.js not found. Install from https://nodejs.org"
fi

echo ""
echo "Done. Next steps:"
echo "  1. source 002_activate.sh    (activate the venv)"
echo "  2. ./003_setup.sh            (install Python + Node dependencies)"
