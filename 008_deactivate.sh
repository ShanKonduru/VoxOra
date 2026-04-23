#!/usr/bin/env bash
# ============================================================
# 008_deactivate.sh  --  Deactivate the Python virtual environment
# Must be *sourced*, not executed:
#   source 008_deactivate.sh   OR   . 008_deactivate.sh
# ============================================================
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "[INFO] No virtual environment is currently active."
    return 0 2>/dev/null || exit 0
fi
deactivate
echo "Virtual environment deactivated."
