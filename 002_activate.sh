#!/usr/bin/env bash
# NOTE: This script must be *sourced*, not executed, so activation
# takes effect in your current shell session:
#   source 002_activate.sh   OR   . 002_activate.sh
source .venv/bin/activate
echo "Virtual environment activated. Run 'deactivate' or 008_deactivate.sh to exit."
