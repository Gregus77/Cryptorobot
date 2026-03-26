"""
SofaScore API integration module.
Uses SofaScore's unofficial public API to fetch match data.
"""

import requests
import json
from datetime import datetime, date, timedelta
from typing import Optional

BASE_URL = "https://api.sofascore.com/api/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
}

SPORT_MAP = {
    "football": "football",
    "basketball": "basketball",
    "tennis": "tennis",
    "hockey": "ice-hockey",
    "baseball": "baseball",
    "volleyball": "volleyball",
}


def _get(endpoint: str, params: dict = None) -> Optional[dict]:
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def get_live_events(sport: str = "football") -> list:
    data = _get(f"/sport/{sport}/events/live")
    if data and "events" in data:
        return data["events"]
    return []


def get_scheduled_events(sport: str = "football", date_str: str = None) -> list:
    if not date_str:
        date_str = date.today().strftime("%Y-%m-%d")
    data = _get(f"/sport/{sport}/scheduled-events/{date_str}")
    if data and "events" in data:
        return data["events"]
    return []


def get_event_details(event_id: int) -> Optional[dict]:
    return _get(f"/event/{event_id}")


def get_event_statistics(event_id: int) -> list:
    data = _get(f"/event/{event_id}/statistics")
    if data and "statistics" in data:
        return data["statistics"]
    return []


def get_event_odds(event_id: int) -> Optional[dict]:
    return _get(f"/event/{event_id}/odds/1/all")


def get_event_lineups(event_id: int) -> Optional[dict]:
    return _get(f"/event/{event_id}/lineups")


def get_event_incidents(event_id: int) -> Optional[dict]:
    data = _get(f"/event/{event_id}/incidents")
    if data and "incidents" in data:
        return data["incidents"]
    return []


def get_h2h(event_id: int) -> Optional[dict]:
    return _get(f"/event/{event_id}/h2h/events")


def get_team_form(team_id: int, event_id: int) -> Optional[dict]:
    return _get(f"/team/{team_id}/events/last/0")


def get_team_info(team_id: int) -> Optional[dict]:
    return _get(f"/team/{team_id}")


def get_tournament_standings(tournament_id: int, season_id: int) -> Optional[dict]:
    return _get(f"/unique-tournament/{tournament_id}/season/{season_id}/standings/total")


def parse_event_summary(event: dict) -> dict:
    """Extract key info from a raw event dict."""
    home = event.get("homeTeam", {})
    away = event.get("awayTeam", {})
    score = event.get("homeScore", {})
    status = event.get("status", {})
    tournament = event.get("tournament", {})

    home_score = score.get("current", "-")
    away_score = event.get("awayScore", {}).get("current", "-")

    return {
        "id": event.get("id"),
        "home_team": home.get("name", "?"),
        "home_team_id": home.get("id"),
        "home_logo": f"https://api.sofascore.com/api/v1/team/{home.get('id')}/image",
        "away_team": away.get("name", "?"),
        "away_team_id": away.get("id"),
        "away_logo": f"https://api.sofascore.com/api/v1/team/{away.get('id')}/image",
        "home_score": home_score,
        "away_score": away_score,
        "status_type": status.get("type", "notstarted"),
        "status_desc": status.get("description", ""),
        "minute": event.get("time", {}).get("currentPeriodStartTimestamp"),
        "start_timestamp": event.get("startTimestamp"),
        "tournament": tournament.get("name", ""),
        "tournament_id": tournament.get("uniqueTournament", {}).get("id"),
        "category": tournament.get("category", {}).get("name", ""),
        "country_flag": tournament.get("category", {}).get("alpha2", ""),
        "slug": event.get("slug", ""),
        "round": event.get("roundInfo", {}).get("round"),
    }


def parse_statistics(raw_stats: list) -> dict:
    """Flatten statistics into a dict keyed by stat name."""
    result = {}
    for period in raw_stats:
        period_name = period.get("period", "ALL")
        if period_name not in ("ALL", "1ST", "2ND"):
            continue
        for group in period.get("groups", []):
            for item in group.get("statisticsItems", []):
                key = item.get("key", "").replace(" ", "_").lower()
                result[f"{period_name}_{key}"] = {
                    "name": item.get("name"),
                    "home": item.get("home"),
                    "away": item.get("away"),
                    "home_value": item.get("homeValue"),
                    "away_value": item.get("awayValue"),
                    "render_type": item.get("renderType"),
                }
    return result


def compute_betting_score(stats: dict, odds: dict = None) -> dict:
    """
    Compute a simple betting signal score [0-100] for home/draw/away
    based on SofaScore match statistics.
    """
    home_score = 50
    away_score = 50

    def stat_val(key_suffix: str):
        full_key = f"ALL_{key_suffix}"
        s = stats.get(full_key)
        if not s:
            return None, None
        try:
            h = float(str(s.get("home_value", 0) or 0).replace("%", ""))
            a = float(str(s.get("away_value", 0) or 0).replace("%", ""))
            return h, a
        except (ValueError, TypeError):
            return None, None

    weights = {
        "ball_possession": 1.5,
        "total_shots": 2.0,
        "shots_on_goal": 3.0,
        "big_chances": 4.0,
        "expected_goals": 3.5,
        "corner_kicks": 1.0,
        "fouls": -0.5,
        "attacks": 1.0,
        "dangerous_attacks": 2.0,
        "free_kicks": 0.5,
        "goalkeeper_saves": 0.5,
    }

    adjustments_home = 0
    adjustments_away = 0

    for key, weight in weights.items():
        h, a = stat_val(key)
        if h is None:
            continue
        total = h + a
        if total == 0:
            continue
        diff = (h - a) / total * 100
        adjustments_home += diff * weight
        adjustments_away -= diff * weight

    home_score = min(max(50 + adjustments_home, 0), 100)
    away_score = min(max(50 + adjustments_away, 0), 100)

    draw_score = 100 - abs(home_score - away_score)
    draw_score = max(draw_score * 0.6, 5)

    total = home_score + away_score + draw_score
    home_pct = round(home_score / total * 100, 1)
    away_pct = round(away_score / total * 100, 1)
    draw_pct = round(draw_score / total * 100, 1)

    if home_pct >= 45:
        signal = "DOMICILE"
        confidence = home_pct
    elif away_pct >= 45:
        signal = "EXTERIEUR"
        confidence = away_pct
    else:
        signal = "NUL"
        confidence = draw_pct

    return {
        "home_pct": home_pct,
        "draw_pct": draw_pct,
        "away_pct": away_pct,
        "signal": signal,
        "confidence": confidence,
    }
