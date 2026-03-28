@echo off
title BetSmart - Lancement
color 0A
cls

echo.
echo  ==========================================
echo    BETSMART - Paris Sportifs
echo  ==========================================
echo.

:: ── Cherche Python ──────────────────────────
set PYTHON=
for %%P in (python python3 py) do (
    if not defined PYTHON (
        %%P --version >nul 2>&1 && set PYTHON=%%P
    )
)

if not defined PYTHON (
    color 0C
    echo  [ERREUR] Python n'est pas installe sur ce PC.
    echo.
    echo  Voici quoi faire :
    echo  1. Va sur https://www.python.org/downloads/
    echo  2. Clique sur "Download Python" (gros bouton jaune)
    echo  3. Lance l'installeur
    echo  4. IMPORTANT : coche la case "Add Python to PATH"
    echo  5. Clique Installer
    echo  6. Relance ce fichier .bat
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

echo  [OK] Python trouve !
%PYTHON% --version
echo.

:: ── Installe Flask ───────────────────────────
echo  Installation des modules necessaires...
echo  (ca peut prendre 30 secondes la premiere fois)
echo.
%PYTHON% -m pip install flask requests --quiet --ignore-installed
if errorlevel 1 (
    %PYTHON% -m pip install flask requests --ignore-installed
)
echo  [OK] Modules installes !
echo.

:: ── Lance le serveur ─────────────────────────
echo  ==========================================
echo   Le site va s'ouvrir dans ton navigateur
echo   Adresse : http://localhost:5000
echo  ==========================================
echo.
echo  Ne ferme PAS cette fenetre pendant que
echo  tu utilises le site.
echo  Pour arreter : appuie sur Ctrl+C
echo.

:: Ouvre le navigateur apres 3 secondes
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"

:: Lance le serveur
%PYTHON% app.py

echo.
echo  Le serveur s'est arrete.
pause
