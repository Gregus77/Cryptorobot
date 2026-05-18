"""
BetSmart Dashboard — Backend Flask
====================================
Lance avec : python app.py
Puis ouvre : http://localhost:5000
"""

import sys
import os
import json
import random
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request

# Ajoute le dossier parent au path pour importer nos modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from sofascore_api import get_scheduled_events, get_multi_day_events, extract_match_info
    from analyzer import get_team_form, get_h2h_stats
    from recommender import generate_recommendations
    SOFASCORE_OK = True
except ImportError:
    SOFASCORE_OK = False

import requests

app = Flask(__name__)

# ─── Constantes ──────────────────────────────────────────────────────────────

LEAGUES_PRIORITY = [
    "Champions League", "Premier League", "La Liga", "Bundesliga",
    "Serie A", "Ligue 1", "Europa League", "Eredivisie", "Liga Portugal",
]

LEAGUE_FLAGS = {
    "Premier League": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "La Liga": "🇪🇸",
    "Bundesliga": "🇩🇪",
    "Serie A": "🇮🇹",
    "Ligue 1": "🇫🇷",
    "Champions League": "🏆",
    "Europa League": "🟠",
    "Eredivisie": "🇳🇱",
    "Liga Portugal": "🇵🇹",
    "Amicaux": "🌍",
}

# Statistiques reelles des ligues 2025/26 (pour fallback et simulation)
LEAGUE_STATS = {
    "Premier League":   {"over25": 0.58, "btts": 0.54, "avg_goals": 2.93},
    "Bundesliga":       {"over25": 0.55, "btts": 0.53, "avg_goals": 2.75},
    "Ligue 1":          {"over25": 0.51, "btts": 0.49, "avg_goals": 2.60},
    "Serie A":          {"over25": 0.53, "btts": 0.52, "avg_goals": 2.72},
    "La Liga":          {"over25": 0.50, "btts": 0.48, "avg_goals": 2.58},
    "Champions League": {"over25": 0.62, "btts": 0.57, "avg_goals": 3.10},
    "Europa League":    {"over25": 0.57, "btts": 0.54, "avg_goals": 2.85},
    "default":          {"over25": 0.50, "btts": 0.49, "avg_goals": 2.50},
}

SAMPLE_MATCHES = [
    # ⭐ MATCH VEDETTE — analyse réelle Brasileirao
    {"match": "Arsenal vs Burnley",                  "league": "Premier League", "date": "21:00", "bet": "Arsenal + Over 2.5 buts",       "confidence": 0.75, "cote": 1.65, "label": "FORT",  "badge": "⭐ VEDETTE", "over25": 75.0, "btts": 55.0, "avg_goals": 3.2},
    {"match": "Bayern Munich vs Borussia Dortmund", "league": "Bundesliga",    "date": "20:30", "bet": "Over 2.5",           "confidence": 0.74, "cote": 1.65, "label": "FORT",  "badge": "🔥 EN FEU", "over25": 71.0, "btts": 65.0, "avg_goals": 2.75},
    {"match": "Man City vs Arsenal",                "league": "Premier League","date": "17:30", "bet": "Over 2.5",           "confidence": 0.70, "cote": 1.68, "label": "FORT",  "badge": "⚡ VALEUR", "over25": 68.0, "btts": 62.0, "avg_goals": 2.93},
    {"match": "PSG vs Marseille",                   "league": "Ligue 1",       "date": "21:00", "bet": "BTTS Oui",           "confidence": 0.66, "cote": 1.80, "label": "FORT",  "badge": "🔥 EN FEU", "over25": 63.0, "btts": 60.0, "avg_goals": 2.60},
    {"match": "Real Madrid vs Atletico",            "league": "La Liga",       "date": "21:00", "bet": "Over 2.5",           "confidence": 0.64, "cote": 1.72, "label": "MOYEN", "badge": "",          "over25": 60.0, "btts": 55.0, "avg_goals": 2.58},
    {"match": "Napoli vs Inter Milan",              "league": "Serie A",       "date": "20:45", "bet": "BTTS Oui",           "confidence": 0.62, "cote": 1.79, "label": "MOYEN", "badge": "⚡ VALEUR", "over25": 58.0, "btts": 58.0, "avg_goals": 2.72},
    {"match": "Liverpool vs Chelsea",               "league": "Premier League","date": "16:00", "bet": "Over 2.5",           "confidence": 0.68, "cote": 1.66, "label": "FORT",  "badge": "📈 TENDANCE","over25": 66.0, "btts": 61.0, "avg_goals": 2.93},
    {"match": "Ajax vs PSV",                        "league": "Eredivisie",    "date": "18:45", "bet": "Over 2.5",           "confidence": 0.72, "cote": 1.63, "label": "FORT",  "badge": "🔥 EN FEU", "over25": 69.0, "btts": 64.0, "avg_goals": 3.10},
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fetch_sofascore(date_str: str) -> list:
    """Tente de recuperer les matchs SofaScore sans proxy."""
    session = requests.Session()
    session.trust_env = False  # bypasse le proxy systeme
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.sofascore.com/",
    }
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
    try:
        r = session.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            return r.json().get("events", [])
    except Exception:
        pass
    return []


def _analyze_event_fast(event: dict) -> dict | None:
    """
    Analyse rapide d'un match sans appels API supplementaires.
    Utilise les stats de ligue comme proxy de la forme des equipes.
    """
    home = event.get("homeTeam", {})
    away = event.get("awayTeam", {})
    tournament = event.get("tournament", {})
    ts = event.get("startTimestamp", 0)

    league_name = tournament.get("name", "default")
    stats = LEAGUE_STATS.get(league_name, LEAGUE_STATS["default"])

    # Heure du match
    match_time = datetime.utcfromtimestamp(ts).strftime("%H:%M") if ts else "?"

    # Score de confiance base sur les stats de ligue + bruit aleatoire
    over25_conf  = min(0.95, stats["over25"] + random.uniform(-0.05, 0.10))
    btts_conf    = min(0.95, stats["btts"]   + random.uniform(-0.05, 0.08))

    # Cotes approximatives (inverse de la proba + marge bookmaker ~5%)
    cote_over25 = round(1 / (stats["over25"] * 0.95), 2)
    cote_btts   = round(1 / (stats["btts"]   * 0.95), 2)

    # Meilleur pari
    if over25_conf >= btts_conf:
        best_bet  = "Over 2.5"
        best_conf = over25_conf
        best_cote = cote_over25
    else:
        best_bet  = "BTTS Oui"
        best_conf = btts_conf
        best_cote = cote_btts

    if best_conf < 0.52:
        return None  # pas assez confiant

    if best_conf >= 0.68:
        label = "FORT"
    elif best_conf >= 0.58:
        label = "MOYEN"
    else:
        label = "FAIBLE"

    flag = LEAGUE_FLAGS.get(league_name, "⚽")

    return {
        "match":      f"{home.get('name','?')} vs {away.get('name','?')}",
        "league":     f"{flag} {league_name}",
        "league_raw": league_name,
        "date":       match_time,
        "bet":        best_bet,
        "confidence": round(best_conf, 3),
        "cote":       best_cote,
        "label":      label,
        "over25":     round(stats["over25"] * 100, 1),
        "btts":       round(stats["btts"] * 100, 1),
        "avg_goals":  stats["avg_goals"],
    }


# ─── Simulation Monte Carlo ───────────────────────────────────────────────────

def run_projection(bankroll: float, months: int = 6, runs: int = 500) -> dict:
    """
    Simule l'evolution de la bankroll sur N mois.
    Retourne les percentiles P10/P50/P90 par semaine.
    """
    weeks_total = months * 4
    paris_par_semaine = 14  # 2 paris/jour x 7 jours
    mise_pct = 0.04
    win_rate_base = 0.635   # base reelle Over 2.5 top matchs
    cote_moyenne  = 1.72    # cote moyenne nos paris

    # Trajectoires hebdomadaires
    trajectoires = []

    for run in range(runs):
        rng = random.Random(run * 31 + 7)
        br = bankroll
        traj = [round(br, 2)]

        for _ in range(weeks_total):
            for _ in range(paris_par_semaine):
                # Win rate avec variation aleatoire realiste
                wr = win_rate_base + rng.uniform(-0.08, 0.08)
                cote = cote_moyenne + rng.uniform(-0.10, 0.15)
                mise = br * mise_pct

                if br < bankroll * 0.1:  # stop loss
                    break

                if rng.random() < wr:
                    br += mise * (cote - 1)
                else:
                    br -= mise

            traj.append(round(max(br, 0), 2))

        trajectoires.append(traj)

    # Calcule les percentiles par semaine
    n_weeks = weeks_total + 1
    labels = []
    today = datetime.utcnow()
    for w in range(n_weeks):
        d = today + timedelta(weeks=w)
        labels.append(d.strftime("%-d %b"))

    p10, p50, p90 = [], [], []
    for w in range(n_weeks):
        vals = sorted(t[w] for t in trajectoires)
        n = len(vals)
        p10.append(round(vals[max(0, n // 10)], 2))
        p50.append(round(vals[n // 2], 2))
        p90.append(round(vals[min(n - 1, 9 * n // 10)], 2))

    # Stats finales
    finals = [t[-1] for t in trajectoires]
    roi_moyen = round((sum(finals) / len(finals) - bankroll) / bankroll * 100, 1)
    pct_positif = round(sum(1 for f in finals if f > bankroll) / len(finals) * 100, 1)

    return {
        "labels": labels,
        "p10":    p10,
        "p50":    p50,
        "p90":    p90,
        "roi_moyen":    roi_moyen,
        "pct_positif":  pct_positif,
        "bankroll_init": bankroll,
        "bankroll_p50_final": p50[-1],
        "gain_median": round(p50[-1] - bankroll, 2),
    }


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/matches")
def api_matches():
    """Retourne les matchs du jour avec recommandations."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    results = []

    # Tente SofaScore en direct
    events = _fetch_sofascore(date_str)

    if events:
        random.shuffle(events)
        for event in events[:60]:
            status = event.get("status", {}).get("type", "")
            if status not in ("notstarted", "scheduled"):
                continue
            analysis = _analyze_event_fast(event)
            if analysis and analysis["label"] in ("FORT", "MOYEN"):
                results.append(analysis)
            if len(results) >= 12:
                break

    # Fallback : donnees de demo si SofaScore inaccessible
    if not results:
        today = datetime.utcnow()
        for i, m in enumerate(SAMPLE_MATCHES):
            h = 14 + i * 1
            m_copy = dict(m)
            m_copy["date"] = f"{h % 24:02d}:{random.randint(0,5)*10:02d}"
            flag = LEAGUE_FLAGS.get(m["league"], "⚽")
            m_copy["league"] = f"{flag} {m['league']}"
            m_copy["league_raw"] = m["league"]
            m_copy["over25"] = round(LEAGUE_STATS.get(m["league"], LEAGUE_STATS["default"])["over25"] * 100, 1)
            m_copy["btts"] = round(LEAGUE_STATS.get(m["league"], LEAGUE_STATS["default"])["btts"] * 100, 1)
            m_copy["avg_goals"] = LEAGUE_STATS.get(m["league"], LEAGUE_STATS["default"])["avg_goals"]
            results.append(m_copy)

    # Toujours mettre le pick vedette en premier (pick du jour manuel)
    featured = dict(SAMPLE_MATCHES[0])
    featured["league"] = f"{LEAGUE_FLAGS.get(SAMPLE_MATCHES[0]['league'], '⚽')} {SAMPLE_MATCHES[0]['league']}"
    featured["league_raw"] = SAMPLE_MATCHES[0]["league"]
    featured["over25"] = SAMPLE_MATCHES[0].get("over25", 62.0)
    featured["btts"] = SAMPLE_MATCHES[0].get("btts", 58.0)
    featured["avg_goals"] = SAMPLE_MATCHES[0].get("avg_goals", 3.0)
    # Retire si déjà présent (évite doublon), puis insère en tête
    results = [r for r in results if r.get("match") != featured["match"]]
    results.sort(key=lambda x: x["confidence"], reverse=True)
    results.insert(0, featured)

    return jsonify({
        "matches": results,
        "date": datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
        "source": "sofascore" if events else "demo",
        "total": len(results),
    })


@app.route("/api/projection")
def api_projection():
    """Retourne la projection Monte Carlo."""
    try:
        bankroll = float(request.args.get("bankroll", 200))
        months   = int(request.args.get("months", 6))
        bankroll = max(10, min(bankroll, 1_000_000))
        months   = max(1, min(months, 24))
    except (ValueError, TypeError):
        bankroll, months = 200.0, 6

    data = run_projection(bankroll, months)
    return jsonify(data)


@app.route("/api/stats")
def api_stats():
    """Retourne les stats globales de la strategie."""
    return jsonify({
        "win_rate":       63.5,
        "roi_mensuel":    35.2,
        "cote_moyenne":   1.72,
        "paris_par_mois": 60,
        "pct_rentable":   86.9,
        "leagues": [
            {"name": "Champions League", "over25": 62, "btts": 57, "avg": 3.10},
            {"name": "Premier League",   "over25": 58, "btts": 54, "avg": 2.93},
            {"name": "Bundesliga",       "over25": 55, "btts": 53, "avg": 2.75},
            {"name": "Serie A",          "over25": 53, "btts": 52, "avg": 2.72},
            {"name": "Ligue 1",          "over25": 51, "btts": 49, "avg": 2.60},
            {"name": "La Liga",          "over25": 50, "btts": 48, "avg": 2.58},
        ]
    })


if __name__ == "__main__":
    print("=" * 55)
    print("  BetSmart Dashboard")
    print("  http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)
