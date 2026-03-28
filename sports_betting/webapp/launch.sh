#!/bin/bash
# ─────────────────────────────────────────────
#  BetSmart — Script de lancement automatique
# ─────────────────────────────────────────────

cd "$(dirname "$0")"   # se place dans le bon dossier

echo ""
echo "  ⚡ BetSmart Dashboard"
echo "  ─────────────────────"

# 1. Vérifie Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "  ❌ Python non trouvé."
  echo "     Installe Python 3 : https://www.python.org/downloads/"
  exit 1
fi

PYTHON=$(command -v python3 || command -v python)
echo "  ✅ Python : $($PYTHON --version)"

# 2. Installe les dépendances si besoin
echo "  📦 Vérification des dépendances..."
$PYTHON -c "import flask" 2>/dev/null || {
  echo "  → Installation de flask..."
  $PYTHON -m pip install flask requests --quiet --ignore-installed
}
$PYTHON -c "import requests" 2>/dev/null || {
  $PYTHON -m pip install requests --quiet
}
echo "  ✅ Dépendances OK"

# 3. Lance le serveur
echo ""
echo "  🚀 Lancement du serveur..."
echo "  → Ouvre ton navigateur sur : http://localhost:5000"
echo "  → Arrêt : Ctrl+C"
echo ""

$PYTHON app.py
