#!/usr/bin/env bash
# ============================================================
# 002_activate.sh  --  Activate the Python virtual environment
# Must be *sourced*, not executed:
#   source 002_activate.sh   OR   . 002_activate.sh
# ============================================================
if [ ! -f ".venv/bin/activate" ]; then
    echo "[ERROR] .venv not found. Run 001_env.sh first."
    return 1 2>/dev/null || exit 1
fi
source .venv/bin/activate
echo "Virtual environment activated.  Run 'deactivate' or source 008_deactivate.sh to exit."
