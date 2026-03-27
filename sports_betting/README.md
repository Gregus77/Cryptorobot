# BetScore — Paris Sportifs & Analyse SofaScore

Site web d'analyse de paris sportifs basé sur les données SofaScore en temps réel.

## Fonctionnalités

- **Matchs en direct** avec auto-refresh (30s)
- **Matchs programmés** par sport et par jour
- **Statistiques détaillées** (possession, tirs, corners, xG, attaques dangereuses...)
- **Analyse betting** avec scoring algorithmique (1X2)
- **Confrontations directes** (H2H)
- **Compositions d'équipe**
- **Incidents** (buts, cartons, remplacements)
- **Multi-sport** : Football, Basket, Tennis, Hockey
- **Thème sombre/clair**

## Installation

```bash
cd sports_betting
pip install -r requirements.txt
python app.py
```

Ouvrir : http://localhost:5000

## Structure

```
sports_betting/
├── app.py              # Serveur Flask
├── sofascore_api.py    # Intégration API SofaScore
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html      # Dashboard
│   └── match.html      # Détail du match
└── static/
    ├── css/style.css
    ├── js/
    │   ├── theme.js
    │   ├── index.js
    │   └── match.js
    └── img/
```

## Avertissement

Ce site utilise l'API publique non-officielle de SofaScore à des fins éducatives.
Le pari sportif comporte des risques financiers importants.
