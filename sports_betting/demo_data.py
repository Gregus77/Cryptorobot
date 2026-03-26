"""
Rich demo data for development/testing without internet access.
Simulates realistic SofaScore API responses + pre-computed analysis.
"""
from datetime import date, datetime
import time

TODAY = date.today().strftime("%Y-%m-%d")
NOW = int(time.time())
DAY = 86400


# ─── Raw event stubs (as SofaScore returns them) ──────────
def _event(id_, home_name, home_id, away_name, away_id,
           tournament, cat, tour_id, offset_h=2, round_=None):
    return {
        "id": id_,
        "homeTeam": {"id": home_id, "name": home_name},
        "awayTeam": {"id": away_id, "name": away_name},
        "homeScore": {"current": None},
        "awayScore": {"current": None},
        "status": {"type": "notstarted", "description": ""},
        "startTimestamp": NOW + offset_h * 3600,
        "tournament": {
            "name": tournament,
            "category": {"name": cat, "alpha2": cat[:2].lower()},
            "uniqueTournament": {"id": tour_id},
        },
        "roundInfo": {"round": round_} if round_ else {},
        "slug": f"{home_name.lower().replace(' ', '-')}-{away_name.lower().replace(' ', '-')}",
    }


DEMO_SCHEDULED_EVENTS = [
    _event(10001, "Paris Saint-Germain", 2697,  "Marseille",       2721,  "Ligue 1",      "France",   34, 2,  28),
    _event(10002, "Real Madrid",         2817,  "FC Barcelona",    2829,  "La Liga",      "Espagne",  8,  3,  30),
    _event(10003, "Manchester City",     2692,  "Arsenal",         2087,  "Premier League","Angleterre",17, 4, 31),
    _event(10004, "Bayern Munich",       2833,  "Borussia Dortmund",2837, "Bundesliga",   "Allemagne",35, 5,  27),
    _event(10005, "Juventus",            2942,  "Inter Milan",     2943,  "Serie A",      "Italie",   23, 6,  31),
    _event(10006, "Ajax",                2692,  "Feyenoord",       3321,  "Eredivisie",   "Pays-Bas", 37, 7,  22),
    _event(10007, "Porto",               5529,  "Benfica",         7172,  "Liga Portugal","Portugal", 238,8,  25),
]

DEMO_LIVE_EVENTS = [
    {
        "id": 10099,
        "homeTeam": {"id": 2697, "name": "Lyon"},
        "awayTeam": {"id": 2721, "name": "Lens"},
        "homeScore": {"current": 1},
        "awayScore": {"current": 2},
        "status": {"type": "inprogress", "description": "71'"},
        "time": {},
        "startTimestamp": NOW - 71 * 60,
        "tournament": {"name": "Ligue 1", "category": {"name": "France", "alpha2": "fr"}, "uniqueTournament": {"id": 34}},
        "roundInfo": {"round": 28},
        "slug": "lyon-lens",
    },
]


# ─── Team form stats (pre-computed, realistic) ────────────
# Key: team_id
DEMO_TEAM_FORMS = {
    # PSG — prolific attack, leaky-ish defense
    2697: {
        "avg_scored": 2.88, "avg_conceded": 1.12, "avg_total": 4.00,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.63, "win_rate": 0.75, "draw_rate": 0.12, "loss_rate": 0.13,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.00,
        "form_str": ["W", "W", "W", "D", "W"], "goals_scored_list": [3,4,2,1,3,4,2,3],
        "goals_conceded_list": [1,0,2,1,1,2,1,0], "matches_analyzed": 8,
    },
    # Marseille — attacking but concedes a lot
    2721: {
        "avg_scored": 2.25, "avg_conceded": 1.75, "avg_total": 4.00,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.63,
        "btts_rate": 0.75, "win_rate": 0.50, "draw_rate": 0.25, "loss_rate": 0.25,
        "clean_sheet_rate": 0.13, "fail_to_score_rate": 0.13,
        "form_str": ["W", "L", "W", "D", "W"], "goals_scored_list": [2,3,1,2,3,2,1,3],
        "goals_conceded_list": [1,2,2,1,2,3,1,1], "matches_analyzed": 8,
    },
    # Real Madrid — dominant
    2817: {
        "avg_scored": 2.75, "avg_conceded": 0.75, "avg_total": 3.50,
        "over15_rate": 0.88, "over25_rate": 0.63, "over35_rate": 0.38,
        "btts_rate": 0.50, "win_rate": 0.88, "draw_rate": 0.12, "loss_rate": 0.00,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.00,
        "form_str": ["W", "W", "W", "W", "D"], "goals_scored_list": [3,2,4,2,3,2,3,2],
        "goals_conceded_list": [0,1,0,2,0,1,0,1], "matches_analyzed": 8,
    },
    # Barcelona — high scoring
    2829: {
        "avg_scored": 2.50, "avg_conceded": 1.25, "avg_total": 3.75,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.63, "win_rate": 0.75, "draw_rate": 0.12, "loss_rate": 0.13,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.00,
        "form_str": ["W", "W", "L", "W", "W"], "goals_scored_list": [3,2,1,3,4,2,2,3],
        "goals_conceded_list": [0,2,3,1,0,1,2,1], "matches_analyzed": 8,
    },
    # Man City — clinical
    2692: {
        "avg_scored": 2.63, "avg_conceded": 0.88, "avg_total": 3.50,
        "over15_rate": 0.88, "over25_rate": 0.63, "over35_rate": 0.38,
        "btts_rate": 0.50, "win_rate": 0.75, "draw_rate": 0.13, "loss_rate": 0.12,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.00,
        "form_str": ["W", "W", "D", "W", "W"], "goals_scored_list": [3,2,2,3,4,2,2,3],
        "goals_conceded_list": [0,1,1,0,1,0,2,1], "matches_analyzed": 8,
    },
    # Arsenal — solid
    2087: {
        "avg_scored": 2.13, "avg_conceded": 0.88, "avg_total": 3.00,
        "over15_rate": 0.88, "over25_rate": 0.63, "over35_rate": 0.25,
        "btts_rate": 0.50, "win_rate": 0.75, "draw_rate": 0.13, "loss_rate": 0.12,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.13,
        "form_str": ["W", "W", "W", "D", "W"], "goals_scored_list": [2,3,1,2,3,2,1,2],
        "goals_conceded_list": [0,1,0,1,0,2,1,1], "matches_analyzed": 8,
    },
    # Bayern Munich
    2833: {
        "avg_scored": 3.13, "avg_conceded": 1.25, "avg_total": 4.38,
        "over15_rate": 1.00, "over25_rate": 0.88, "over35_rate": 0.63,
        "btts_rate": 0.75, "win_rate": 0.88, "draw_rate": 0.00, "loss_rate": 0.12,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.00,
        "form_str": ["W", "W", "W", "W", "L"], "goals_scored_list": [4,3,3,2,5,3,2,3],
        "goals_conceded_list": [1,0,2,1,0,3,1,0], "matches_analyzed": 8,
    },
    # BVB — unstable defense
    2837: {
        "avg_scored": 2.38, "avg_conceded": 1.88, "avg_total": 4.25,
        "over15_rate": 1.00, "over25_rate": 0.88, "over35_rate": 0.63,
        "btts_rate": 0.75, "win_rate": 0.50, "draw_rate": 0.13, "loss_rate": 0.37,
        "clean_sheet_rate": 0.13, "fail_to_score_rate": 0.13,
        "form_str": ["L", "W", "L", "W", "D"], "goals_scored_list": [2,3,1,3,4,1,2,2],
        "goals_conceded_list": [2,1,3,2,1,4,1,2], "matches_analyzed": 8,
    },
    # Juventus
    2942: {
        "avg_scored": 1.50, "avg_conceded": 0.75, "avg_total": 2.25,
        "over15_rate": 0.50, "over25_rate": 0.25, "over35_rate": 0.13,
        "btts_rate": 0.38, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.50, "fail_to_score_rate": 0.25,
        "form_str": ["W", "D", "W", "W", "D"], "goals_scored_list": [2,1,1,2,1,2,1,2],
        "goals_conceded_list": [0,0,1,0,1,0,2,1], "matches_analyzed": 8,
    },
    # Inter Milan
    2943: {
        "avg_scored": 2.00, "avg_conceded": 0.88, "avg_total": 2.88,
        "over15_rate": 0.75, "over25_rate": 0.50, "over35_rate": 0.25,
        "btts_rate": 0.50, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.13,
        "form_str": ["W", "W", "D", "W", "L"], "goals_scored_list": [2,2,1,3,2,1,2,2],
        "goals_conceded_list": [0,1,1,0,2,1,0,1], "matches_analyzed": 8,
    },
    # Ajax & Feyenoord
    3321: {
        "avg_scored": 2.50, "avg_conceded": 1.38, "avg_total": 3.88,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.63, "win_rate": 0.63, "draw_rate": 0.12, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.13,
        "form_str": ["W", "W", "L", "W", "W"], "goals_scored_list": [3,2,1,4,2,3,2,2],
        "goals_conceded_list": [1,2,3,0,1,2,1,1], "matches_analyzed": 8,
    },
    # Porto & Benfica
    5529: {
        "avg_scored": 2.25, "avg_conceded": 1.13, "avg_total": 3.38,
        "over15_rate": 0.88, "over25_rate": 0.63, "over35_rate": 0.38,
        "btts_rate": 0.50, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.00,
        "form_str": ["W", "D", "W", "W", "D"], "goals_scored_list": [2,2,1,3,3,2,2,2],
        "goals_conceded_list": [1,1,2,0,1,2,1,1], "matches_analyzed": 8,
    },
    7172: {
        "avg_scored": 2.63, "avg_conceded": 1.25, "avg_total": 3.88,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.63, "win_rate": 0.75, "draw_rate": 0.13, "loss_rate": 0.12,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.00,
        "form_str": ["W", "W", "W", "D", "L"], "goals_scored_list": [3,2,3,2,4,2,2,3],
        "goals_conceded_list": [1,0,2,1,1,2,1,2], "matches_analyzed": 8,
    },
}


# ─── H2H stubs ────────────────────────────────────────────
DEMO_H2H = {
    10001: {"over25_rate": 0.80, "btts_rate": 0.70, "avg_total": 3.8, "count": 5},
    10002: {"over25_rate": 0.67, "btts_rate": 0.50, "avg_total": 3.2, "count": 6},
    10003: {"over25_rate": 0.67, "btts_rate": 0.50, "avg_total": 3.0, "count": 6},
    10004: {"over25_rate": 0.83, "btts_rate": 0.83, "avg_total": 4.5, "count": 6},
    10005: {"over25_rate": 0.40, "btts_rate": 0.40, "avg_total": 2.2, "count": 5},
    10006: {"over25_rate": 0.67, "btts_rate": 0.67, "avg_total": 3.6, "count": 6},
    10007: {"over25_rate": 0.67, "btts_rate": 0.50, "avg_total": 3.0, "count": 6},
}


# ─── Full match detail for match page ────────────────────
DEMO_MATCH_DETAIL = {
    10001: {
        "summary": {
            "id": 10001,
            "home_team": "Paris Saint-Germain", "home_team_id": 2697,
            "home_logo": "https://api.sofascore.com/api/v1/team/2697/image",
            "away_team": "Marseille",            "away_team_id": 2721,
            "away_logo": "https://api.sofascore.com/api/v1/team/2721/image",
            "home_score": None, "away_score": None,
            "status_type": "notstarted", "status_desc": "",
            "start_timestamp": NOW + 2 * 3600,
            "tournament": "Ligue 1", "category": "France", "country_flag": "fr", "round": 28,
        },
        "statistics": {},
        "incidents": [],
        "h2h": {
            "events": [
                {"homeTeam": {"name": "PSG"}, "awayTeam": {"name": "Marseille"}, "homeScore": {"current": 3}, "awayScore": {"current": 2}, "startTimestamp": NOW - DAY * 200},
                {"homeTeam": {"name": "Marseille"}, "awayTeam": {"name": "PSG"}, "homeScore": {"current": 2}, "awayScore": {"current": 3}, "startTimestamp": NOW - DAY * 380},
                {"homeTeam": {"name": "PSG"}, "awayTeam": {"name": "Marseille"}, "homeScore": {"current": 4}, "awayScore": {"current": 0}, "startTimestamp": NOW - DAY * 560},
                {"homeTeam": {"name": "Marseille"}, "awayTeam": {"name": "PSG"}, "homeScore": {"current": 1}, "awayScore": {"current": 2}, "startTimestamp": NOW - DAY * 740},
                {"homeTeam": {"name": "PSG"}, "awayTeam": {"name": "Marseille"}, "homeScore": {"current": 2}, "awayScore": {"current": 2}, "startTimestamp": NOW - DAY * 920},
            ]
        },
        "odds": {},
    }
}
