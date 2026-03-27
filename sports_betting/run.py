"""
Script principal - Analyse Paris Sportifs via SofaScore
========================================================

Usage:
    # Analyser les matchs de football d'aujourd'hui (top ligues)
    python run.py

    # Analyser les matchs des 3 prochains jours
    python run.py --days 3

    # Filtrer par ligue (ex: "Premier League", "Ligue 1", "Champions")
    python run.py --league "Ligue 1"

    # Analyser uniquement les matchs avec confiance FORT ou MOYEN
    python run.py --min-confidence moyen

    # Exporter les résultats en JSON
    python run.py --output results.json
"""

import sys
import json
import time
import argparse
from datetime import datetime

sys.path.insert(0, ".")

from sofascore_api import get_multi_day_events, get_scheduled_events
from recommender import generate_recommendations


# Ligues populaires à filtrer en priorité
TOP_LEAGUES = [
    "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
    "Champions League", "Europa League", "Conference League",
    "Eredivisie", "Primeira Liga", "Super Lig",
]


def format_confidence_bar(confidence: float) -> str:
    filled = int(confidence * 10)
    return "[" + "█" * filled + "░" * (10 - filled) + f"] {confidence*100:.0f}%"


def print_match_report(rec: dict, show_all: bool = False):
    """Affiche le rapport d'un match dans le terminal."""
    print("\n" + "=" * 65)
    print(f"  {rec['match']}")
    print(f"  {rec['date']}  |  {rec['tournament']}")
    print("=" * 65)

    # Forme des équipes
    hf = rec["home_form_summary"]
    af = rec["away_form_summary"]
    if hf["matches"] > 0:
        print(f"\n  FORME  {hf['team'][:25]:25s} ({hf['matches']} matchs): {hf['form']}")
        print(f"         Buts +{hf['avg_goals_for']:.1f} / -{hf['avg_goals_against']:.1f} par match")
    if af["matches"] > 0:
        print(f"         {af['team'][:25]:25s} ({af['matches']} matchs): {af['form']}")
        print(f"         Buts +{af['avg_goals_for']:.1f} / -{af['avg_goals_against']:.1f} par match")

    h2h = rec["h2h_summary"]
    if h2h["matches"] > 0:
        print(f"\n  H2H  {h2h['matches']} matchs | Moy buts: {h2h['avg_goals']:.1f} | BTTS: {h2h['btts_rate']*100:.0f}%")

    print("\n  ── PARIS CONSEILLES ──────────────────────────────────")

    # Résultat
    r = rec["result"]
    print(f"\n  1X2  {r['bet']}")
    print(f"       {format_confidence_bar(r['confidence'])}  [{r['label']}]")
    print(f"       Dom:{r.get('home_prob',0)*100:.0f}% / Nul:{r.get('draw_prob',0)*100:.0f}% / Ext:{r.get('away_prob',0)*100:.0f}%")
    if r["reason"]:
        print(f"       -> {r['reason']}")

    # BTTS
    b = rec["btts"]
    print(f"\n  BTTS {b['bet']}")
    print(f"       {format_confidence_bar(b['confidence'])}  [{b['label']}]")
    if b["reason"]:
        print(f"       -> {b['reason']}")

    # Over/Under
    for line_key, label in [("over_2_5", "O/U 2.5"), ("over_1_5", "O/U 1.5"), ("over_3_5", "O/U 3.5")]:
        ou = rec[line_key]
        exp = f" (xG≈{ou['expected_goals']})" if ou.get("expected_goals") else ""
        print(f"\n  {label}  {ou['bet']}{exp}")
        print(f"       {format_confidence_bar(ou['confidence'])}  [{ou['label']}]")
        if ou["reason"]:
            print(f"       -> {ou['reason']}")

    print()


def filter_events(events: list, league_filter: str = None) -> list:
    """Filtre les événements par ligue."""
    if not league_filter:
        return events
    league_lower = league_filter.lower()
    return [
        e for e in events
        if league_lower in e.get("tournament", {}).get("name", "").lower()
        or league_lower in e.get("tournament", {}).get("category", {}).get("name", "").lower()
    ]


def filter_by_status(events: list) -> list:
    """Ne garde que les matchs non commencés."""
    allowed = {"notstarted", "scheduled", "postponed"}
    return [
        e for e in events
        if e.get("status", {}).get("type", "").lower() in allowed
        or e.get("status", {}).get("description", "").lower() in {"not started", "scheduled"}
    ]


def run(days: int = 1, league_filter: str = None, min_confidence: str = "faible",
        max_matches: int = 20, output_file: str = None):
    """
    Analyse principale.
    """
    print(f"\n{'='*65}")
    print(f"  ANALYSE PARIS SPORTIFS - SofaScore")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}")
    print(f"  Jours analysés : {days}")
    print(f"  Filtre ligue   : {league_filter or 'Toutes'}")
    print(f"  Confiance min  : {min_confidence.upper()}")

    # Récupération des matchs
    print("\n  Récupération des matchs...")
    if days == 1:
        events = get_scheduled_events("football")
    else:
        events = get_multi_day_events("football", days_ahead=days)

    print(f"  {len(events)} matchs trouvés.")

    # Filtre ligues
    events = filter_events(events, league_filter)
    print(f"  {len(events)} matchs après filtre ligue.")

    # Garde uniquement les matchs à venir
    events = filter_by_status(events)
    print(f"  {len(events)} matchs à venir.")

    if not events:
        print("\n  Aucun match à analyser.")
        return

    # Limite pour ne pas surcharger l'API
    events = events[:max_matches]

    confidence_order = {"FORT": 3, "MOYEN": 2, "FAIBLE": 1, "TRES_FAIBLE": 0, "INSUFFISANT": -1}
    min_conf_level = confidence_order.get(min_confidence.upper(), 0)

    all_results = []
    print(f"\n  Analyse de {len(events)} matchs...\n")

    for i, event in enumerate(events, 1):
        home = event.get("homeTeam", {}).get("name", "?")
        away = event.get("awayTeam", {}).get("name", "?")
        print(f"  [{i}/{len(events)}] {home} vs {away}...", end=" ", flush=True)

        try:
            rec = generate_recommendations(event)
            all_results.append(rec)

            # Vérifie si au moins une reco dépasse le seuil
            best_conf_label = max(
                [rec["result"]["label"], rec["btts"]["label"],
                 rec["over_2_5"]["label"]],
                key=lambda x: confidence_order.get(x, -1)
            )
            if confidence_order.get(best_conf_label, -1) >= min_conf_level:
                print("OK")
                print_match_report(rec)
            else:
                print(f"(confiance trop faible: {best_conf_label})")

        except Exception as e:
            print(f"ERREUR: {e}")

        time.sleep(0.5)  # Respecte le rate limit SofaScore

    # Export JSON si demandé
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n  Résultats exportés: {output_file}")

    # Résumé final: meilleures opportunités
    print("\n" + "=" * 65)
    print("  TOP PARIS (confiance FORT uniquement)")
    print("=" * 65)

    strong_bets = []
    for rec in all_results:
        for bet_type, bet_data in [
            ("1X2", rec["result"]),
            ("BTTS", rec["btts"]),
            ("O/U 2.5", rec["over_2_5"]),
        ]:
            if bet_data.get("label") == "FORT":
                strong_bets.append({
                    "match": rec["match"],
                    "date": rec["date"],
                    "type": bet_type,
                    "bet": bet_data["bet"],
                    "confidence": bet_data["confidence"],
                })

    if strong_bets:
        strong_bets.sort(key=lambda x: x["confidence"], reverse=True)
        for sb in strong_bets:
            print(f"  {sb['date']}  {sb['match'][:35]:35s}")
            print(f"           [{sb['type']}] {sb['bet']} - {sb['confidence']*100:.0f}%")
    else:
        print("  Aucun pari avec confiance FORT trouvé.")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyse de paris sportifs via SofaScore"
    )
    parser.add_argument("--days", type=int, default=1,
                        help="Nombre de jours à analyser (défaut: 1)")
    parser.add_argument("--league", type=str, default=None,
                        help="Filtre par nom de ligue (ex: 'Ligue 1')")
    parser.add_argument("--min-confidence", type=str, default="faible",
                        choices=["fort", "moyen", "faible"],
                        help="Niveau minimum de confiance (défaut: faible)")
    parser.add_argument("--max-matches", type=int, default=20,
                        help="Nombre max de matchs à analyser (défaut: 20)")
    parser.add_argument("--output", type=str, default=None,
                        help="Fichier JSON de sortie (optionnel)")

    args = parser.parse_args()

    run(
        days=args.days,
        league_filter=args.league,
        min_confidence=args.min_confidence,
        max_matches=args.max_matches,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
