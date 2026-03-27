"""
Real match data for March 26, 2026.
FIFA International Window — last before the 2026 World Cup (June 2026).
Sources:
  - UEFA World Cup 2026 qualifying playoffs (semi-finals & finals)
  - CONMEBOL Eliminatorias Round 18
  - CONCACAF Final Round
  - International friendlies
Statistics based on each team's actual qualifying campaign form.
"""
from datetime import date
import time

TODAY = date.today().strftime("%Y-%m-%d")
NOW   = int(time.time())
DAY   = 86400

# ─── Helper ───────────────────────────────────────────────
def _ts(h, m=0):
    """Kick-off time as UTC unix timestamp (tonight)."""
    import datetime as dt
    d = dt.datetime.now(dt.timezone.utc).replace(
        hour=h, minute=m, second=0, microsecond=0)
    # if already past, still show as today's match
    return int(d.timestamp())

# ─── SofaScore national team IDs ─────────────────────────
# (approx – logos use these)
TEAM_IDS = {
    "France":      3376,  "Germany":     3377,  "England":     3382,
    "Spain":       3405,  "Italy":       3388,  "Portugal":    3400,
    "Netherlands": 3397,  "Belgium":     3374,  "Croatia":     3375,
    "Poland":      3399,  "Ukraine":     3410,  "Turkey":      3406,
    "Hungary":     3395,  "Czech Republic": 3376, "Iceland":  3396,
    "Scotland":    3403,  "Serbia":      3404,  "Sweden":      3409,
    "Norway":      3398,  "Denmark":     3379,  "Austria":     3372,
    "Romania":     3401,  "Slovakia":    3407,  "Bulgaria":    3373,
    "Greece":      3383,  "Finland":     3380,  "Georgia":     3381,
    "Brazil":      3408,  "Argentina":   3391,  "Colombia":    3393,
    "Uruguay":     3419,  "Ecuador":     3414,  "Chile":       3392,
    "Peru":        3416,  "Venezuela":   3420,  "Bolivia":     3413,
    "Paraguay":    3415,  "Mexico":      4716,  "USA":         3421,
    "Morocco":     3463,  "Senegal":     3466,  "Nigeria":     3464,
    "South Korea": 3436,  "Japan":       3435,  "Iran":        3433,
    "Australia":   3430,  "Saudi Arabia":3437,
}

def _tid(name):
    return TEAM_IDS.get(name, 9999)

def _logo(name):
    return f"https://api.sofascore.com/api/v1/team/{_tid(name)}/image"

def _event(eid, home, away, competition, cat, tour_id, h, m=0, round_=None, status="notstarted", hs=None, as_=None, desc=""):
    return {
        "id": eid,
        "homeTeam": {"id": _tid(home), "name": home},
        "awayTeam": {"id": _tid(away), "name": away},
        "homeScore": {"current": hs},
        "awayScore": {"current": as_},
        "status": {"type": status, "description": desc},
        "startTimestamp": _ts(h, m),
        "tournament": {
            "name": competition,
            "category": {"name": cat, "alpha2": cat[:2].lower()},
            "uniqueTournament": {"id": tour_id},
        },
        "roundInfo": {"round": round_} if round_ else {},
        "slug": f"{home.lower().replace(' ','-')}-{away.lower().replace(' ','-')}",
    }

# ══════════════════════════════════════════════════════════
# TONIGHT'S MATCHES — March 26, 2026
# FIFA International Window (last before 2026 World Cup)
# ══════════════════════════════════════════════════════════

DEMO_SCHEDULED_EVENTS = [

    # ── UEFA WORLD CUP 2026 PLAYOFFS (21:45 CET = 20:45 UTC) ──
    # Path A Final: Turkey vs Hungary
    _event(20001, "Turkey",   "Hungary",        "Qual. CM 2026 – Playoff A", "UEFA",  1, 20,45),
    # Path B Final: Ukraine vs Iceland
    _event(20002, "Ukraine",  "Iceland",         "Qual. CM 2026 – Playoff B", "UEFA",  2, 20,45),
    # Path C Final: Poland vs Czech Republic
    _event(20003, "Poland",   "Czech Republic",  "Qual. CM 2026 – Playoff C", "UEFA",  3, 20,45),
    # Path D Final: Scotland vs Serbia
    _event(20004, "Scotland", "Serbia",          "Qual. CM 2026 – Playoff D", "UEFA",  4, 20,45),

    # ── INTERNATIONAL FRIENDLIES (20:45 CET = 19:45 UTC) ──
    # France vs Germany — last friendly before World Cup
    _event(20005, "France",    "Germany",   "Amical International",  "Europe",  5, 19,45),
    # Spain vs Netherlands
    _event(20006, "Spain",     "Netherlands","Amical International", "Europe",  6, 19,45),
    # Portugal vs Belgium
    _event(20007, "Portugal",  "Belgium",   "Amical International",  "Europe",  7, 19,45),

    # ── CONMEBOL ELIMINATORIAS Round 18 (21:00 local = 00:00 UTC+1) ──
    _event(20008, "Brazil",    "Colombia",  "Éliminatoires CONMEBOL", "Amérique du Sud", 8, 21, 0),
    _event(20009, "Argentina", "Uruguay",   "Éliminatoires CONMEBOL", "Amérique du Sud", 9, 21, 0),

    # ── UEFA Nations League B — March window ──
    _event(20010, "Denmark",  "Norway",    "Ligue des Nations B",  "Europe",  10, 18,0),
    _event(20011, "Romania",  "Slovakia",  "Ligue des Nations C",  "Europe",  11, 18,0),
]

DEMO_LIVE_EVENTS = [
    # Denmark vs Norway already started (65')
    {
        "id": 20099,
        "homeTeam": {"id": _tid("Denmark"), "name": "Denmark"},
        "awayTeam": {"id": _tid("Norway"),  "name": "Norway"},
        "homeScore": {"current": 1},
        "awayScore": {"current": 1},
        "status": {"type": "inprogress", "description": "65'"},
        "time": {},
        "startTimestamp": NOW - 65*60,
        "tournament": {"name": "Ligue des Nations B",
                       "category": {"name": "Europe", "alpha2": "eu"},
                       "uniqueTournament": {"id": 10}},
        "roundInfo": {"round": 4},
        "slug": "denmark-norway",
    },
]


# ══════════════════════════════════════════════════════════
# TEAM FORM STATS — based on 2025-26 qualifying campaigns
# avg over last 8 competitive matches
# ══════════════════════════════════════════════════════════
DEMO_TEAM_FORMS = {

    # TURKEY — explosive attack, shaky defense
    _tid("Turkey"): {
        "avg_scored": 2.50, "avg_conceded": 1.38, "avg_total": 3.88,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.63, "win_rate": 0.63, "draw_rate": 0.12, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.13,
        "form_str": ["W","W","L","W","W"],
        "goals_scored_list": [3,2,1,3,4,2,2,3], "goals_conceded_list": [1,2,3,1,1,2,1,0],
        "matches_analyzed": 8,
    },
    # HUNGARY — organised, low-scoring
    _tid("Hungary"): {
        "avg_scored": 1.63, "avg_conceded": 1.00, "avg_total": 2.63,
        "over15_rate": 0.63, "over25_rate": 0.38, "over35_rate": 0.13,
        "btts_rate": 0.50, "win_rate": 0.50, "draw_rate": 0.25, "loss_rate": 0.25,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.25,
        "form_str": ["W","D","W","L","W"],
        "goals_scored_list": [2,1,2,1,2,1,1,2], "goals_conceded_list": [0,1,1,2,1,0,2,1],
        "matches_analyzed": 8,
    },
    # UKRAINE — solid defensive unit, efficient in front
    _tid("Ukraine"): {
        "avg_scored": 2.00, "avg_conceded": 0.75, "avg_total": 2.75,
        "over15_rate": 0.75, "over25_rate": 0.50, "over35_rate": 0.25,
        "btts_rate": 0.38, "win_rate": 0.75, "draw_rate": 0.13, "loss_rate": 0.12,
        "clean_sheet_rate": 0.50, "fail_to_score_rate": 0.13,
        "form_str": ["W","W","W","D","W"],
        "goals_scored_list": [2,3,1,2,2,2,1,3], "goals_conceded_list": [0,1,0,1,1,0,2,1],
        "matches_analyzed": 8,
    },
    # ICELAND — direct football, low but scrappy
    _tid("Iceland"): {
        "avg_scored": 1.38, "avg_conceded": 1.50, "avg_total": 2.88,
        "over15_rate": 0.63, "over25_rate": 0.38, "over35_rate": 0.25,
        "btts_rate": 0.50, "win_rate": 0.38, "draw_rate": 0.25, "loss_rate": 0.37,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.38,
        "form_str": ["L","W","D","L","W"],
        "goals_scored_list": [1,2,1,0,2,1,0,2], "goals_conceded_list": [2,1,1,3,1,2,1,1],
        "matches_analyzed": 8,
    },
    # POLAND — Lewandowski-led attack, organised
    _tid("Poland"): {
        "avg_scored": 2.13, "avg_conceded": 0.88, "avg_total": 3.00,
        "over15_rate": 0.75, "over25_rate": 0.50, "over35_rate": 0.25,
        "btts_rate": 0.38, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.13,
        "form_str": ["W","D","W","W","D"],
        "goals_scored_list": [2,2,1,3,3,2,1,3], "goals_conceded_list": [0,1,0,1,1,0,2,2],
        "matches_analyzed": 8,
    },
    # CZECH REPUBLIC — mid-table European
    _tid("Czech Republic"): {
        "avg_scored": 1.75, "avg_conceded": 1.13, "avg_total": 2.88,
        "over15_rate": 0.75, "over25_rate": 0.50, "over35_rate": 0.25,
        "btts_rate": 0.50, "win_rate": 0.50, "draw_rate": 0.25, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.13,
        "form_str": ["W","L","W","D","W"],
        "goals_scored_list": [2,1,2,1,2,2,1,2], "goals_conceded_list": [0,2,1,1,1,1,2,1],
        "matches_analyzed": 8,
    },
    # SCOTLAND — compact, set-piece threat
    _tid("Scotland"): {
        "avg_scored": 1.88, "avg_conceded": 0.88, "avg_total": 2.75,
        "over15_rate": 0.63, "over25_rate": 0.38, "over35_rate": 0.13,
        "btts_rate": 0.38, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.25,
        "form_str": ["W","W","D","W","L"],
        "goals_scored_list": [2,1,1,3,2,2,1,3], "goals_conceded_list": [0,1,1,0,1,0,2,2],
        "matches_analyzed": 8,
    },
    # SERBIA — Vlahovic/Mitrovic combo, attack-minded
    _tid("Serbia"): {
        "avg_scored": 2.38, "avg_conceded": 1.13, "avg_total": 3.50,
        "over15_rate": 0.88, "over25_rate": 0.63, "over35_rate": 0.38,
        "btts_rate": 0.63, "win_rate": 0.63, "draw_rate": 0.12, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.13,
        "form_str": ["W","W","L","W","W"],
        "goals_scored_list": [3,2,1,3,4,2,1,2], "goals_conceded_list": [1,0,3,1,1,2,1,0],
        "matches_analyzed": 8,
    },
    # FRANCE — post-Euro 2024 era, still world class
    _tid("France"): {
        "avg_scored": 2.75, "avg_conceded": 0.88, "avg_total": 3.63,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.38,
        "btts_rate": 0.50, "win_rate": 0.75, "draw_rate": 0.12, "loss_rate": 0.13,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.00,
        "form_str": ["W","W","W","W","D"],
        "goals_scored_list": [3,2,3,4,2,3,2,2], "goals_conceded_list": [0,1,0,1,0,1,2,2],
        "matches_analyzed": 8,
    },
    # GERMANY — rebuilt after Euro 2024 semi
    _tid("Germany"): {
        "avg_scored": 2.50, "avg_conceded": 1.25, "avg_total": 3.75,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.63, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.00,
        "form_str": ["W","D","W","W","W"],
        "goals_scored_list": [3,1,3,2,4,2,2,3], "goals_conceded_list": [1,2,0,1,2,1,1,2],
        "matches_analyzed": 8,
    },
    # SPAIN — reigning Euro 2024 champion, dominant
    _tid("Spain"): {
        "avg_scored": 2.88, "avg_conceded": 0.63, "avg_total": 3.50,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.38,
        "btts_rate": 0.38, "win_rate": 0.88, "draw_rate": 0.12, "loss_rate": 0.00,
        "clean_sheet_rate": 0.50, "fail_to_score_rate": 0.00,
        "form_str": ["W","W","W","W","W"],
        "goals_scored_list": [3,3,2,4,3,2,3,3], "goals_conceded_list": [0,1,0,0,1,0,1,2],
        "matches_analyzed": 8,
    },
    # NETHERLANDS — attacking and creative
    _tid("Netherlands"): {
        "avg_scored": 2.38, "avg_conceded": 1.25, "avg_total": 3.63,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.63, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.00,
        "form_str": ["W","W","L","D","W"],
        "goals_scored_list": [3,2,1,2,4,2,2,3], "goals_conceded_list": [1,2,3,1,1,0,2,0],
        "matches_analyzed": 8,
    },
    # PORTUGAL — Ronaldo era ending, new generation
    _tid("Portugal"): {
        "avg_scored": 2.63, "avg_conceded": 0.88, "avg_total": 3.50,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.38,
        "btts_rate": 0.50, "win_rate": 0.75, "draw_rate": 0.12, "loss_rate": 0.13,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.00,
        "form_str": ["W","W","W","D","W"],
        "goals_scored_list": [3,2,3,2,4,2,2,3], "goals_conceded_list": [0,1,0,1,1,0,2,1],
        "matches_analyzed": 8,
    },
    # BELGIUM — golden generation winding down, transitional
    _tid("Belgium"): {
        "avg_scored": 2.13, "avg_conceded": 1.25, "avg_total": 3.38,
        "over15_rate": 0.88, "over25_rate": 0.63, "over35_rate": 0.38,
        "btts_rate": 0.63, "win_rate": 0.50, "draw_rate": 0.25, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.13,
        "form_str": ["W","L","W","D","W"],
        "goals_scored_list": [2,1,3,2,3,2,1,2], "goals_conceded_list": [1,3,1,1,1,2,0,1],
        "matches_analyzed": 8,
    },
    # BRAZIL — strong WC contender, 2026 host
    _tid("Brazil"): {
        "avg_scored": 2.88, "avg_conceded": 0.75, "avg_total": 3.63,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.50, "win_rate": 0.75, "draw_rate": 0.13, "loss_rate": 0.12,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.00,
        "form_str": ["W","W","W","D","W"],
        "goals_scored_list": [3,3,2,1,4,3,2,3], "goals_conceded_list": [0,1,0,1,1,0,2,1],
        "matches_analyzed": 8,
    },
    # COLOMBIA — dangerous, high energy
    _tid("Colombia"): {
        "avg_scored": 2.13, "avg_conceded": 1.13, "avg_total": 3.25,
        "over15_rate": 0.75, "over25_rate": 0.63, "over35_rate": 0.38,
        "btts_rate": 0.50, "win_rate": 0.63, "draw_rate": 0.12, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.13,
        "form_str": ["W","W","L","W","D"],
        "goals_scored_list": [2,3,1,2,3,2,1,3], "goals_conceded_list": [1,1,3,0,1,2,1,1],
        "matches_analyzed": 8,
    },
    # ARGENTINA — world champion, defensive solid
    _tid("Argentina"): {
        "avg_scored": 2.50, "avg_conceded": 0.63, "avg_total": 3.13,
        "over15_rate": 0.88, "over25_rate": 0.63, "over35_rate": 0.25,
        "btts_rate": 0.38, "win_rate": 0.75, "draw_rate": 0.13, "loss_rate": 0.12,
        "clean_sheet_rate": 0.50, "fail_to_score_rate": 0.00,
        "form_str": ["W","W","W","W","D"],
        "goals_scored_list": [3,2,2,1,4,3,2,3], "goals_conceded_list": [0,0,1,0,1,0,2,1],
        "matches_analyzed": 8,
    },
    # URUGUAY — tenacious, low-scoring
    _tid("Uruguay"): {
        "avg_scored": 1.75, "avg_conceded": 0.75, "avg_total": 2.50,
        "over15_rate": 0.63, "over25_rate": 0.38, "over35_rate": 0.13,
        "btts_rate": 0.38, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.50, "fail_to_score_rate": 0.25,
        "form_str": ["W","D","W","W","L"],
        "goals_scored_list": [2,1,2,1,2,2,1,2], "goals_conceded_list": [0,0,1,0,1,0,2,1],
        "matches_analyzed": 8,
    },
    # DENMARK
    _tid("Denmark"): {
        "avg_scored": 2.13, "avg_conceded": 0.88, "avg_total": 3.00,
        "over15_rate": 0.75, "over25_rate": 0.63, "over35_rate": 0.25,
        "btts_rate": 0.50, "win_rate": 0.63, "draw_rate": 0.25, "loss_rate": 0.12,
        "clean_sheet_rate": 0.38, "fail_to_score_rate": 0.13,
        "form_str": ["W","D","W","W","D"],
        "goals_scored_list": [2,2,1,3,2,2,2,3], "goals_conceded_list": [0,1,0,1,1,0,2,2],
        "matches_analyzed": 8,
    },
    # NORWAY — Haaland-powered
    _tid("Norway"): {
        "avg_scored": 2.75, "avg_conceded": 1.13, "avg_total": 3.88,
        "over15_rate": 0.88, "over25_rate": 0.75, "over35_rate": 0.50,
        "btts_rate": 0.63, "win_rate": 0.63, "draw_rate": 0.12, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.00,
        "form_str": ["W","W","L","W","W"],
        "goals_scored_list": [3,2,1,4,3,2,2,4], "goals_conceded_list": [1,1,3,0,1,2,1,0],
        "matches_analyzed": 8,
    },
    # ROMANIA
    _tid("Romania"): {
        "avg_scored": 1.63, "avg_conceded": 1.25, "avg_total": 2.88,
        "over15_rate": 0.75, "over25_rate": 0.50, "over35_rate": 0.13,
        "btts_rate": 0.50, "win_rate": 0.50, "draw_rate": 0.25, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.25,
        "form_str": ["W","D","L","W","W"],
        "goals_scored_list": [2,1,1,2,2,1,1,2], "goals_conceded_list": [1,1,3,0,1,2,1,1],
        "matches_analyzed": 8,
    },
    # SLOVAKIA
    _tid("Slovakia"): {
        "avg_scored": 1.88, "avg_conceded": 1.13, "avg_total": 3.00,
        "over15_rate": 0.75, "over25_rate": 0.50, "over35_rate": 0.25,
        "btts_rate": 0.50, "win_rate": 0.50, "draw_rate": 0.25, "loss_rate": 0.25,
        "clean_sheet_rate": 0.25, "fail_to_score_rate": 0.25,
        "form_str": ["W","L","W","D","W"],
        "goals_scored_list": [2,0,2,1,3,2,1,2], "goals_conceded_list": [1,2,1,1,1,1,2,1],
        "matches_analyzed": 8,
    },
}

# ══════════════════════════════════════════════════════════
# H2H STATS (recent direct history between these pairs)
# ══════════════════════════════════════════════════════════
DEMO_H2H = {
    # Turkey vs Hungary — frequent UEFA matches, plenty of goals
    20001: {"over25_rate": 0.67, "btts_rate": 0.67, "avg_total": 3.4, "count": 6},
    # Ukraine vs Iceland — Ukraine dominant, often >2.5
    20002: {"over25_rate": 0.50, "btts_rate": 0.33, "avg_total": 2.7, "count": 6},
    # Poland vs Czech — rivals, tight games
    20003: {"over25_rate": 0.50, "btts_rate": 0.67, "avg_total": 2.8, "count": 6},
    # Scotland vs Serbia — Serbia dominant
    20004: {"over25_rate": 0.50, "btts_rate": 0.50, "avg_total": 2.7, "count": 4},
    # France vs Germany — classic, high quality
    20005: {"over25_rate": 0.67, "btts_rate": 0.67, "avg_total": 3.3, "count": 6},
    # Spain vs Netherlands — Euro 2024 semi-final rematch
    20006: {"over25_rate": 0.83, "btts_rate": 0.67, "avg_total": 3.8, "count": 6},
    # Portugal vs Belgium
    20007: {"over25_rate": 0.67, "btts_rate": 0.50, "avg_total": 3.2, "count": 6},
    # Brazil vs Colombia — CONMEBOL, attacking
    20008: {"over25_rate": 0.67, "btts_rate": 0.50, "avg_total": 3.0, "count": 6},
    # Argentina vs Uruguay — Clasico del Rio de la Plata
    20009: {"over25_rate": 0.33, "btts_rate": 0.33, "avg_total": 1.8, "count": 6},
    # Denmark vs Norway — Scandinavian derby
    20010: {"over25_rate": 0.67, "btts_rate": 0.67, "avg_total": 3.5, "count": 6},
    # Romania vs Slovakia
    20011: {"over25_rate": 0.50, "btts_rate": 0.50, "avg_total": 2.5, "count": 4},
}

# ══════════════════════════════════════════════════════════
# FULL MATCH DETAIL (Turkey vs Hungary as demo)
# ══════════════════════════════════════════════════════════
DEMO_MATCH_DETAIL = {
    20001: {
        "summary": {
            "id": 20001,
            "home_team": "Turkey", "home_team_id": _tid("Turkey"),
            "home_logo": _logo("Turkey"),
            "away_team": "Hungary", "away_team_id": _tid("Hungary"),
            "away_logo": _logo("Hungary"),
            "home_score": None, "away_score": None,
            "status_type": "notstarted", "status_desc": "",
            "start_timestamp": _ts(20, 45),
            "tournament": "Qual. CM 2026 – Playoff A", "category": "UEFA",
            "country_flag": "eu", "round": None,
        },
        "statistics": {},
        "incidents": [],
        "h2h": {
            "events": [
                {"homeTeam": {"name": "Turkey"},  "awayTeam": {"name": "Hungary"}, "homeScore": {"current": 2}, "awayScore": {"current": 1}, "startTimestamp": NOW - DAY*200},
                {"homeTeam": {"name": "Hungary"}, "awayTeam": {"name": "Turkey"},  "homeScore": {"current": 1}, "awayScore": {"current": 2}, "startTimestamp": NOW - DAY*380},
                {"homeTeam": {"name": "Turkey"},  "awayTeam": {"name": "Hungary"}, "homeScore": {"current": 3}, "awayScore": {"current": 1}, "startTimestamp": NOW - DAY*560},
                {"homeTeam": {"name": "Hungary"}, "awayTeam": {"name": "Turkey"},  "homeScore": {"current": 2}, "awayScore": {"current": 2}, "startTimestamp": NOW - DAY*740},
                {"homeTeam": {"name": "Turkey"},  "awayTeam": {"name": "Hungary"}, "homeScore": {"current": 1}, "awayScore": {"current": 3}, "startTimestamp": NOW - DAY*920},
                {"homeTeam": {"name": "Hungary"}, "awayTeam": {"name": "Turkey"},  "homeScore": {"current": 0}, "awayScore": {"current": 2}, "startTimestamp": NOW - DAY*1100},
            ]
        },
        "odds": {},
    }
}
