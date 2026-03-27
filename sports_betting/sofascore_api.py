"""
SofaScore API wrapper
Fetches matches, team stats, H2H data from SofaScore's public API.
"""

import requests
import time
from datetime import datetime, timedelta

BASE_URL = "https://api.sofascore.com/api/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://www.sofascore.com/",
}

SPORTS = {
    "football": "football",
    "basketball": "basketball",
    "tennis": "tennis",
    "hockey": "american-football",
}


def _get(url: str, params: dict = None, retries: int = 3) -> dict:
    """Safe GET request with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                time.sleep(2 ** attempt)
            else:
                return {}
        except requests.RequestException as e:
            print(f"[API] Erreur requête ({attempt+1}/{retries}): {e}")
            time.sleep(1)
    return {}


def get_scheduled_events(sport: str = "football", date: str = None) -> list:
    """
    Retourne les matchs programmés pour une date donnée (format YYYY-MM-DD).
    Par défaut: aujourd'hui.
    """
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/sport/{sport}/scheduled-events/{date}"
    data = _get(url)
    return data.get("events", [])


def get_live_events(sport: str = "football") -> list:
    """Retourne les matchs en direct."""
    url = f"{BASE_URL}/sport/{sport}/events/live"
    data = _get(url)
    return data.get("events", [])


def get_team_last_events(team_id: int, page: int = 0) -> list:
    """Retourne les derniers matchs d'une équipe."""
    url = f"{BASE_URL}/team/{team_id}/events/last/{page}"
    data = _get(url)
    return data.get("events", [])


def get_team_next_events(team_id: int, page: int = 0) -> list:
    """Retourne les prochains matchs d'une équipe."""
    url = f"{BASE_URL}/team/{team_id}/events/next/{page}"
    data = _get(url)
    return data.get("events", [])


def get_event_h2h(event_id: int) -> dict:
    """Retourne les confrontations directes pour un match."""
    url = f"{BASE_URL}/event/{event_id}/h2h"
    return _get(url)


def get_event_statistics(event_id: int) -> dict:
    """Retourne les statistiques détaillées d'un match."""
    url = f"{BASE_URL}/event/{event_id}/statistics"
    return _get(url)


def get_team_statistics(team_id: int, tournament_id: int, season_id: int) -> dict:
    """Retourne les statistiques d'une équipe pour une saison."""
    url = f"{BASE_URL}/team/{team_id}/tournament/{tournament_id}/season/{season_id}/statistics/overall"
    return _get(url)


def get_tournament_standings(tournament_id: int, season_id: int) -> dict:
    """Retourne le classement d'un tournoi."""
    url = f"{BASE_URL}/tournament/{tournament_id}/season/{season_id}/standings/total"
    return _get(url)


def get_top_tournaments(sport: str = "football") -> list:
    """Retourne les principaux tournois."""
    url = f"{BASE_URL}/sport/{sport}/tournaments/top"
    data = _get(url)
    return data.get("tournaments", [])


def get_multi_day_events(sport: str = "football", days_ahead: int = 3) -> list:
    """
    Récupère tous les matchs sur plusieurs jours à venir.
    Retourne une liste d'événements avec leur date.
    """
    all_events = []
    today = datetime.utcnow()
    for i in range(days_ahead):
        date_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        events = get_scheduled_events(sport, date_str)
        for e in events:
            e["_fetch_date"] = date_str
        all_events.extend(events)
        time.sleep(0.3)
    return all_events


def extract_match_info(event: dict) -> dict:
    """Extrait les infos essentielles d'un événement SofaScore."""
    home = event.get("homeTeam", {})
    away = event.get("awayTeam", {})
    score = event.get("homeScore", {})
    score_away = event.get("awayScore", {})
    tournament = event.get("tournament", {})
    start_ts = event.get("startTimestamp", 0)

    home_goals = score.get("current", score.get("display", None))
    away_goals = score_away.get("current", score_away.get("display", None))

    return {
        "event_id": event.get("id"),
        "match_date": datetime.utcfromtimestamp(start_ts).strftime("%Y-%m-%d %H:%M") if start_ts else "?",
        "home_team": home.get("name", "?"),
        "home_team_id": home.get("id"),
        "away_team": away.get("name", "?"),
        "away_team_id": away.get("id"),
        "tournament": tournament.get("name", "?"),
        "category": tournament.get("category", {}).get("name", "?"),
        "status": event.get("status", {}).get("description", "?"),
        "home_goals": home_goals,
        "away_goals": away_goals,
        "winner_code": event.get("winnerCode"),  # 1=home, 2=away, 3=draw
    }
