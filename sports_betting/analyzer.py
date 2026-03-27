"""
Analyseur statistique pour paris sportifs.
Calcule : forme, buts, BTTS, Over/Under, H2H, score moyen.
"""

from sofascore_api import (
    get_team_last_events,
    get_event_h2h,
    extract_match_info,
)


def _parse_goals(event: dict, team_id: int) -> tuple:
    """
    Retourne (buts_marqués, buts_encaissés) pour l'équipe dans un match terminé.
    Retourne None si match non terminé ou données manquantes.
    """
    home = event.get("homeTeam", {})
    away = event.get("awayTeam", {})
    home_score = event.get("homeScore", {})
    away_score = event.get("awayScore", {})
    status = event.get("status", {}).get("type", "")

    if status not in ("finished", "ended", "afterextratime", "afterpenalties"):
        return None

    hg = home_score.get("current", home_score.get("display"))
    ag = away_score.get("current", away_score.get("display"))

    if hg is None or ag is None:
        return None

    hg, ag = int(hg), int(ag)

    if home.get("id") == team_id:
        return hg, ag
    elif away.get("id") == team_id:
        return ag, hg
    return None


def get_team_form(team_id: int, n: int = 10) -> dict:
    """
    Analyse les N derniers matchs d'une équipe.
    Retourne des statistiques de forme.
    """
    events = get_team_last_events(team_id, page=0)
    results = []

    for event in events:
        parsed = _parse_goals(event, team_id)
        if parsed is None:
            continue
        gf, ga = parsed
        if gf > ga:
            result = "W"
        elif gf == ga:
            result = "D"
        else:
            result = "L"
        results.append({
            "result": result,
            "goals_for": gf,
            "goals_against": ga,
            "total_goals": gf + ga,
            "btts": gf > 0 and ga > 0,
            "clean_sheet": ga == 0,
            "failed_to_score": gf == 0,
        })
        if len(results) >= n:
            break

    if not results:
        return {
            "matches": 0,
            "wins": 0, "draws": 0, "losses": 0,
            "win_rate": 0.0,
            "avg_goals_for": 0.0,
            "avg_goals_against": 0.0,
            "avg_total_goals": 0.0,
            "btts_rate": 0.0,
            "clean_sheet_rate": 0.0,
            "failed_to_score_rate": 0.0,
            "over_1_5_rate": 0.0,
            "over_2_5_rate": 0.0,
            "over_3_5_rate": 0.0,
            "form_string": "",
        }

    n_matches = len(results)
    wins = sum(1 for r in results if r["result"] == "W")
    draws = sum(1 for r in results if r["result"] == "D")
    losses = sum(1 for r in results if r["result"] == "L")
    form_str = "".join(r["result"] for r in results)

    return {
        "matches": n_matches,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": round(wins / n_matches, 3),
        "avg_goals_for": round(sum(r["goals_for"] for r in results) / n_matches, 2),
        "avg_goals_against": round(sum(r["goals_against"] for r in results) / n_matches, 2),
        "avg_total_goals": round(sum(r["total_goals"] for r in results) / n_matches, 2),
        "btts_rate": round(sum(1 for r in results if r["btts"]) / n_matches, 3),
        "clean_sheet_rate": round(sum(1 for r in results if r["clean_sheet"]) / n_matches, 3),
        "failed_to_score_rate": round(sum(1 for r in results if r["failed_to_score"]) / n_matches, 3),
        "over_1_5_rate": round(sum(1 for r in results if r["total_goals"] > 1) / n_matches, 3),
        "over_2_5_rate": round(sum(1 for r in results if r["total_goals"] > 2) / n_matches, 3),
        "over_3_5_rate": round(sum(1 for r in results if r["total_goals"] > 3) / n_matches, 3),
        "form_string": form_str,
    }


def get_h2h_stats(event_id: int, home_team_id: int) -> dict:
    """
    Analyse les confrontations directes pour un match donné.
    """
    data = get_event_h2h(event_id)
    if not data:
        return {}

    all_events = []
    for key in ("teamDuel", "managerDuel"):
        section = data.get(key, {})
        for sub in ("homeTeamDuelEvents", "awayTeamDuelEvents"):
            all_events.extend(section.get(sub, []))

    # Déduplique par event_id
    seen = set()
    unique = []
    for e in all_events:
        eid = e.get("id")
        if eid and eid not in seen:
            seen.add(eid)
            unique.append(e)

    results = []
    for event in unique:
        home = event.get("homeTeam", {})
        away = event.get("awayTeam", {})
        home_score = event.get("homeScore", {})
        away_score = event.get("awayScore", {})
        status = event.get("status", {}).get("type", "")

        if status not in ("finished", "ended", "afterextratime", "afterpenalties"):
            continue

        hg = home_score.get("current", home_score.get("display"))
        ag = away_score.get("current", away_score.get("display"))
        if hg is None or ag is None:
            continue

        hg, ag = int(hg), int(ag)
        total = hg + ag
        winner = event.get("winnerCode")

        # Perspective équipe domicile du match analysé
        if home.get("id") == home_team_id:
            gf, ga = hg, ag
        else:
            gf, ga = ag, hg

        results.append({
            "goals_home_team": gf,
            "goals_away_team": ga,
            "total_goals": total,
            "btts": hg > 0 and ag > 0,
            "winner_is_home_team": (winner == 1 and home.get("id") == home_team_id)
                                   or (winner == 2 and away.get("id") == home_team_id),
        })

    if not results:
        return {"h2h_matches": 0}

    n = len(results)
    home_wins = sum(1 for r in results if r["winner_is_home_team"])

    return {
        "h2h_matches": n,
        "home_team_wins": home_wins,
        "home_team_win_rate": round(home_wins / n, 3),
        "avg_total_goals": round(sum(r["total_goals"] for r in results) / n, 2),
        "btts_rate": round(sum(1 for r in results if r["btts"]) / n, 3),
        "over_2_5_rate": round(sum(1 for r in results if r["total_goals"] > 2) / n, 3),
        "over_3_5_rate": round(sum(1 for r in results if r["total_goals"] > 3) / n, 3),
        "avg_goals_home_team": round(sum(r["goals_home_team"] for r in results) / n, 2),
        "avg_goals_away_team": round(sum(r["goals_away_team"] for r in results) / n, 2),
    }


def analyze_match(event: dict) -> dict:
    """
    Analyse complète d'un match: forme des deux équipes + H2H.
    """
    info = extract_match_info(event)
    home_id = info["home_team_id"]
    away_id = info["away_team_id"]
    event_id = info["event_id"]

    home_form = get_team_form(home_id, n=10) if home_id else {}
    away_form = get_team_form(away_id, n=10) if away_id else {}
    h2h = get_h2h_stats(event_id, home_id) if event_id else {}

    return {
        "match_info": info,
        "home_form": home_form,
        "away_form": away_form,
        "h2h": h2h,
    }
