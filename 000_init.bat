@echo off
REM ============================================================
REM 000_init.bat  --  One-time git initialisation for VoxOra
REM Update name/email below before running.
REM ============================================================
git config --global user.name "SHAN Konduru"
git config --global user.email "ShanKonduru@gmail.com"

git init
git remote remove origin 2>nul
git remote add origin https://github.com/ShanKonduru/VoxOra.git

echo.
echo Git repository initialised.
echo Remote set to: https://github.com/ShanKonduru/VoxOra.git
echo.
echo Next step:  001_env.bat  (create Python venv + check Node)
