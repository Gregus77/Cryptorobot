
# PROMPT COMPLET — Crée-moi un site web professionnel de paris sportifs

## CONTEXTE
Je veux un site web complet de conseils de paris sportifs, beau, moderne, qui donne envie de l'utiliser tous les jours et qui pourrait être vendu comme un service premium. Le site analyse les matchs de football via l'API publique de SofaScore et donne des recommandations de paris basées sur des statistiques réelles.

---

## STACK TECHNIQUE
- **Backend** : Python + Flask
- **Frontend** : HTML5 / CSS3 / JavaScript vanilla (pas de React, on veut simple)
- **Graphiques** : Chart.js (CDN)
- **Icônes** : pas de librairie externe, utilise des emojis et du SVG inline
- **Base de données** : JSON local (pas de SQL, pas de serveur distant)
- **Démarrage** : `python app.py` → ouvre http://localhost:5000

---

## STRUCTURE DES FICHIERS

```
betsmart/
├── app.py                    ← serveur Flask principal
├── launch.bat                ← double-clic pour lancer sur Windows
├── launch.sh                 ← lancer sur Linux/Mac
├── data/
│   └── bankroll_history.json ← historique sauvegardé localement
├── templates/
│   └── index.html            ← page principale (tout en une page)
└── static/
    └── css/
        └── style.css         ← styles séparés
```

---

## FONCTIONNALITÉS OBLIGATOIRES

### 1. PAGE PRINCIPALE — Dashboard
- Header fixe avec logo ⚡ BetSmart, date/heure en direct, bouton refresh
- Design **dark mode** professionnel (fond #0d1117, cartes #1c2333, accents bleu/vert/violet)
- Totalement responsive (mobile + desktop)

### 2. SECTION BANKROLL & PROJECTION
- Input pour entrer sa bankroll (en €)
- Boutons de durée : 1 mois / 3 mois / 6 mois / 12 mois
- Graphique Chart.js avec 3 courbes :
  - P90 en vert (meilleur scénario 10%)
  - P50 en bleu (scénario médian)
  - P10 en rouge (pire scénario 10%)
  - Ligne pointillée = bankroll initiale
- 3 stats sous le graphe : Gain médian estimé / ROI moyen / % de simulations rentables
- La simulation Monte Carlo utilise : 500 runs, mise 4% de bankroll, win rate 63.5%, cote moyenne 1.72

### 3. BARRE DE KPIs (5 métriques)
- Win Rate global : 63.5%
- ROI mensuel moyen : +35%
- Cote moyenne : 1.72
- Paris par mois : ~60
- % simulations rentables : 86.9%

### 4. MATCHS DU JOUR — CŒUR DU SITE
Récupération via SofaScore API (https://api.sofascore.com/api/v1) :
- Endpoint : `/sport/football/scheduled-events/YYYY-MM-DD`
- Headers User-Agent obligatoires pour éviter le blocage
- `session.trust_env = False` pour bypasser les proxies
- Si SofaScore inaccessible → utiliser des données de démo réalistes
- Badge "🟢 LIVE SofaScore" ou "🟡 Démo"

**Pour chaque match affiché :**
- Nom des équipes + heure du match
- Ligue avec drapeau emoji
- Type de pari recommandé : Over 2.5 / BTTS Oui / Victoire domicile
- Barre de confiance animée (couleur selon niveau)
- Cote estimée
- Taux Over 2.5 de la ligue
- Buts par match moyen (xGoals)
- Badge FORT (vert) / MOYEN (orange) / FAIBLE (gris)

**Statistiques réelles des ligues 2025/26 à utiliser :**
```
Champions League : over25=62%, btts=57%, avg=3.10 buts/match
Premier League   : over25=58%, btts=54%, avg=2.93
Bundesliga       : over25=55%, btts=53%, avg=2.75
Serie A          : over25=53%, btts=52%, avg=2.72
Ligue 1          : over25=51%, btts=49%, avg=2.60
La Liga          : over25=50%, btts=48%, avg=2.58
```

### 5. SUIVI DE BANKROLL PERSONNEL
- L'utilisateur entre sa bankroll de départ (sauvegardée en JSON local)
- Bouton "+ Ajouter un pari" → modal avec : match, type de pari, cote, mise, résultat (gagné/perdu)
- Historique des paris sous forme de tableau
- Courbe d'évolution personnelle de la bankroll (Chart.js)
- Statistiques personnelles calculées : win rate réel, ROI réel, série en cours, meilleur/pire pari

### 6. TOP PARIS DU MOMENT (section résumé)
- Tableau récapitulatif des 3 meilleurs paris du jour
- Format : Match | Type | Cote | Confiance | Raison statistique
- Mis en avant visuellement (fond dégradé, étoiles)

### 7. STATS PAR LIGUE
- Barre horizontale par ligue avec % Over 2.5 et buts/match
- Classement des ligues les plus rentables pour cette stratégie

---

## FONCTIONNALITÉS "PREMIUM" — Pour rendre le site vendable

### A. SYSTÈME DE SCORE DE CONFIANCE
Algorithme de notation sur 100 :
- Forme domicile (10 derniers matchs) : +0 à +30 points
- Forme extérieur : +0 à +25 points
- H2H (confrontations directes) : +0 à +20 points
- Stats de la ligue (Over 2.5 %) : +0 à +15 points
- Facteur cote (meilleure valeur) : +0 à +10 points
Score ≥ 70 = FORT, 55-69 = MOYEN, 45-54 = FAIBLE, < 45 = ignoré

### B. SIMULATEUR DE GAINS
- Input : mise souhaitée en €
- Calcul automatique du gain potentiel selon la cote
- Affichage : "Si tu mises 20€ sur ce pari → gain potentiel : 13.40€"
- Mise conseillée calculée automatiquement : 4% de la bankroll saisie

### C. ALERTES VISUELLES
- Badge "🔥 EN FEU" si une équipe a 5+ victoires consécutives
- Badge "⚡ VALEUR" si la cote est > 1.80 avec confiance FORT
- Badge "📈 TENDANCE" si Over 2.5 dans les 8 derniers matchs

### D. CALENDRIER DE LA SEMAINE
- Onglets : Aujourd'hui / Demain / Cette semaine
- Filtre par ligue (Champions, PL, Bundesliga, Ligue 1, etc.)
- Filtre par type de pari (Over 2.5 / BTTS / 1X2)

### E. SECTION "POURQUOI CETTE STRATÉGIE"
Bloc pédagogique avec :
- Explication Over 2.5 (50% des matchs top ligues)
- Explication gestion de bankroll (mise fixe 4%)
- Règle d'or : ne jamais parier sur moins de 60% de confiance
- Avertissement responsabilité (obligatoire légalement)

### F. SECTION SOCIALE / CONFIANCE
- Compteur animé : "⚡ 1,247 paris analysés ce mois"
- Taux de réussite affiché : "63.5% de succès sur les 30 derniers jours"
- Témoignages fictifs mais réalistes (3-4 avis)
- Note étoiles 4.8/5

---

## DESIGN DÉTAILLÉ

### Palette de couleurs
```css
--bg: #0d1117;
--surface: #161b22;
--card: #1c2333;
--border: #30363d;
--accent: #58a6ff;       /* bleu principal */
--green: #3fb950;        /* gains, FORT */
--orange: #d29922;       /* MOYEN */
--red: #f85149;          /* pertes, risque */
--purple: #bc8cff;       /* accents */
--text: #e6edf3;
--muted: #8b949e;
```

### Effets visuels
- Cards avec `box-shadow: 0 4px 24px rgba(0,0,0,.45)`
- Hover sur les matchs : `transform: translateX(4px)` + bordure gauche colorée
- Barres de confiance animées en CSS
- Gradient sur les boutons CTA
- Badge FORT avec glow vert : `box-shadow: 0 0 12px rgba(63,185,80,.3)`
- Skeleton loading pendant le chargement des matchs
- Smooth scroll entre les sections

### Navigation
- Header sticky avec blur background
- 4 sections via scroll ou onglets : Dashboard / Mes Paris / Statistiques / Stratégie
- Sur mobile : bottom nav bar avec icônes

---

## API ROUTES FLASK

```
GET /                          → page principale
GET /api/matches               → matchs du jour + recommandations
GET /api/projection?bankroll=X&months=Y  → simulation Monte Carlo
GET /api/stats                 → stats globales stratégie
POST /api/bet                  → ajouter un pari à l'historique
GET /api/history               → historique des paris
DELETE /api/bet/<id>           → supprimer un pari
```

### Format réponse /api/matches
```json
{
  "matches": [
    {
      "match": "Bayern Munich vs Borussia Dortmund",
      "league": "🇩🇪 Bundesliga",
      "date": "20:30",
      "bet": "Over 2.5",
      "confidence": 0.74,
      "cote": 1.65,
      "label": "FORT",
      "over25": 71.0,
      "btts": 65.0,
      "avg_goals": 2.75,
      "badge": "🔥 EN FEU"
    }
  ],
  "date": "28/03/2026 18:00",
  "source": "sofascore",
  "total": 8
}
```

### Format réponse /api/projection
```json
{
  "labels": ["28 Mar", "4 Avr", ...],
  "p10": [200, 185, ...],
  "p50": [200, 218, ...],
  "p90": [200, 240, ...],
  "roi_moyen": 35.2,
  "pct_positif": 86.9,
  "bankroll_init": 200,
  "bankroll_p50_final": 365.0,
  "gain_median": 165.0
}
```

### POST /api/bet (body JSON)
```json
{
  "match": "PSG vs Marseille",
  "type": "Over 2.5",
  "cote": 1.72,
  "mise": 8.0,
  "result": "win"
}
```

---

## SAUVEGARDE LOCALE (data/bankroll_history.json)
```json
{
  "bankroll_initiale": 200.0,
  "bankroll_courante": 247.50,
  "bets": [
    {
      "id": "uuid",
      "date": "2026-03-28",
      "match": "Bayern vs Dortmund",
      "type": "Over 2.5",
      "cote": 1.65,
      "mise": 8.0,
      "result": "win",
      "profit": 5.20,
      "bankroll_after": 207.20
    }
  ]
}
```

---

## DONNÉES DE DÉMO (si SofaScore inaccessible)
Utilise ces matchs réalistes pour le mode démo :
```python
DEMO_MATCHES = [
    ("Bayern Munich", "Borussia Dortmund", "Bundesliga",    0.74, 0.65, 1.65, "🔥 EN FEU"),
    ("Man City",      "Arsenal",           "Premier League",0.70, 0.62, 1.68, "⚡ VALEUR"),
    ("PSG",           "Marseille",         "Ligue 1",       0.66, 0.60, 1.80, "🔥 EN FEU"),
    ("Real Madrid",   "Atletico Madrid",   "La Liga",       0.64, 0.58, 1.72, ""),
    ("Napoli",        "Inter Milan",       "Serie A",       0.62, 0.61, 1.79, "⚡ VALEUR"),
    ("Liverpool",     "Chelsea",           "Premier League",0.68, 0.64, 1.66, "📈 TENDANCE"),
    ("Ajax",          "PSV",               "Eredivisie",    0.72, 0.66, 1.63, "🔥 EN FEU"),
    ("Barcelona",     "Sevilla",           "La Liga",       0.61, 0.59, 1.71, ""),
]
```

---

## TEXTES MARKETING (section "Pourquoi BetSmart")

**Titre principal :** "La stratégie statistique qui transforme tes paris"

**3 arguments clés :**
1. 🎯 "Basé sur 10 000+ matchs analysés — pas sur des intuitions"
2. 📈 "63.5% de réussite sur les paris Over 2.5 en top 5 ligues"
3. 🛡️ "Gestion de bankroll intégrée — ne perds jamais plus que prévu"

**Disclaimer légal à inclure (obligatoire) :**
"⚠️ Les paris sportifs comportent des risques. Ne pariez que ce que vous pouvez vous permettre de perdre. BetSmart est un outil d'aide à la décision, pas une garantie de gains. 18+ uniquement. Jouez responsable : joueurs-info-service.fr"

---

## INSTRUCTIONS FINALES

1. Crée tous les fichiers listés dans la structure
2. Le site doit fonctionner avec `python app.py` puis http://localhost:5000
3. Crée `launch.bat` pour Windows (installe auto les dépendances + ouvre le navigateur)
4. Utilise uniquement : flask, requests (pas d'autres libs externes)
5. Le frontend doit être en un seul fichier HTML (templates/index.html)
6. Toutes les fonctionnalités doivent marcher SANS connexion internet (mode démo)
7. La sauvegarde des paris se fait dans data/bankroll_history.json
8. Ajoute des commentaires en français dans le code
9. Le site doit être joli, professionnel, donner envie de l'utiliser chaque jour
10. Mobile-first : doit être utilisable depuis un téléphone

Lance-toi et crée le site complet, fichier par fichier.
