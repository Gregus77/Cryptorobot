@echo off
:: ─────────────────────────────────────────────
::  BetSmart — Script de lancement (Windows)
:: ─────────────────────────────────────────────

cd /d "%~dp0"

echo.
echo   BetSmart Dashboard
echo   ------------------

:: Vérifie Python
python --version >nul 2>&1
if errorlevel 1 (
  echo   ERREUR : Python non trouve.
  echo   Installe Python : https://www.python.org/downloads/
  echo   Coche bien "Add Python to PATH" a l'installation !
  pause
  exit /b 1
)

:: Installe les dépendances
echo   Installation des dependances...
python -m pip install flask requests --quiet --ignore-installed

echo.
echo   Lancement du serveur...
echo   Ouvre ton navigateur sur : http://localhost:5000
echo   Arret : Ctrl+C
echo.

python app.py
pause
