#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# 000_init.sh  --  One-time git initialisation for VoxOra
# Update name/email below before running.
# ============================================================
git config --global user.name 'SHAN Konduru'
git config --global user.email 'ShanKonduru@gmail.com'

git init
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/ShanKonduru/VoxOra.git

echo ""
echo "Git repository initialised."
echo "Remote set to: https://github.com/ShanKonduru/VoxOra.git"
echo ""
echo "Next step:  ./001_env.sh  then  source 002_activate.sh"
