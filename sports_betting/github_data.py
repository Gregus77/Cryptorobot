"""
Real football data fetched from openfootball GitHub JSON files.
No API key required. Works in any environment.
Sources: https://github.com/openfootball/football.json
"""

import json
import math
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache

BASE = "https://raw.githubusercontent.com/openfootball/football.json/master"

SEASONS = ["2025-26", "2024-25", "2023-24"]

LEAGUES = {
    "Premier League":  ("en.1.json", "England",     "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "La Liga":         ("es.1.json", "Espagne",      "🇪🇸"),
    "Bundesliga":      ("de.1.json", "Allemagne",    "🇩🇪"),
    "Serie A":         ("it.1.json", "Italie",       "🇮🇹"),
    "Ligue 1":         ("fr.1.json", "France",       "🇫🇷"),
    "Liga Portugal":   ("pt.1.json", "Portugal",     "🇵🇹"),
    "Eredivisie":      ("nl.1.json", "Pays-Bas",     "🇳🇱"),
}

# ─── HTTP fetch ──────────────────────────────────────────
def _fetch(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BetScore/1.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read())
    except Exception:
        return None


# ─── Load season data ─────────────────────────────────────
@lru_cache(maxsize=32)
def _load_league(season: str, fname: str) -> list:
    data = _fetch(f"{BASE}/{season}/{fname}")
    if not data:
        return []
    return data.get("matches", [])


def load_all_matches(seasons=None) -> list:
    """Return all matches across leagues and seasons."""
    if seasons is None:
        seasons = SEASONS
    all_matches = []
    for league, (fname, country, flag) in LEAGUES.items():
        for season in seasons:
            for m in _load_league(season, fname):
                all_matches.append({
                    "league":   league,
                    "country":  country,
                    "flag":     flag,
                    "season":   season,
                    "date":     str(m.get("date", "")),
                    "time":     m.get("time", ""),
                    "home":     m["team1"],
                    "away":     m["team2"],
                    "score":    m.get("score", {}).get("ft"),   # [home, away] or None
                    "round":    m.get("round", ""),
                })
    return all_matches


# ─── Team form builder ───────────────────────────────────
def build_team_stats(all_matches: list, n: int = 10) -> dict:
    """
    Build stats dict: team_name → {avg_sc, avg_co, o25, o15, btts, fts, wr, form, n}
    Uses the last N finished matches per team.
    """
    raw = defaultdict(lambda: {"scored": [], "conceded": [], "results": []})

    # Sort by date so we take the LAST n
    finished = sorted(
        [m for m in all_matches if m["score"] is not None and len(m["score"]) == 2],
        key=lambda x: x["date"]
    )

    for m in finished:
        h, a = m["score"]
        t1, t2 = m["home"], m["away"]
        raw[t1]["scored"].append(h);   raw[t1]["conceded"].append(a)
        raw[t1]["results"].append("W" if h > a else "D" if h == a else "L")
        raw[t2]["scored"].append(a);   raw[t2]["conceded"].append(h)
        raw[t2]["results"].append("W" if a > h else "D" if a == h else "L")

    stats = {}
    for team, d in raw.items():
        sc  = d["scored"][-n:]
        co  = d["conceded"][-n:]
        res = d["results"][-n:]
        nn  = len(sc)
        if nn < 3:
            continue
        stats[team] = {
            "avg_sc":  round(sum(sc) / nn, 2),
            "avg_co":  round(sum(co) / nn, 2),
            "avg_tot": round((sum(sc) + sum(co)) / nn, 2),
            "o15":     round(sum(1 for x, y in zip(sc, co) if x + y >= 2) / nn, 3),
            "o25":     round(sum(1 for x, y in zip(sc, co) if x + y >= 3) / nn, 3),
            "o35":     round(sum(1 for x, y in zip(sc, co) if x + y >= 4) / nn, 3),
            "btts":    round(sum(1 for x, y in zip(sc, co) if x > 0 and y > 0) / nn, 3),
            "fts":     round(sum(1 for x in sc if x == 0) / nn, 3),
            "cs":      round(sum(1 for y in co if y == 0) / nn, 3),
            "wr":      round(sum(1 for r in res if r == "W") / nn, 3),
            "dr":      round(sum(1 for r in res if r == "D") / nn, 3),
            "lr":      round(sum(1 for r in res if r == "L") / nn, 3),
            "form":    res[-5:],
            "sc_list": sc[-8:],
            "co_list": co[-8:],
            "n":       nn,
        }
    return stats


# ─── Poisson helpers ─────────────────────────────────────
def _poisson(lam: float, k: int) -> float:
    if lam <= 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_over(lam: float, threshold: float) -> float:
    prob_le = sum(_poisson(lam, k) for k in range(int(threshold) + 1))
    return round(max(0.0, min(1.0, 1.0 - prob_le)) * 100, 1)


# ─── Match analyser ──────────────────────────────────────
def analyse_match(hf: dict, af: dict) -> dict:
    """
    Returns over15/25/35 and BTTS probabilities based on
    Poisson model + historical rates blended.
    """
    lh = (hf["avg_sc"] + af["avg_co"]) / 2
    la = (af["avg_sc"] + hf["avg_co"]) / 2
    lt = lh + la

    # Over 2.5
    p_o25_p = poisson_over(lt, 2) / 100
    p_o25_h = (hf["o25"] + af["o25"]) / 2
    p_o25   = round((0.55 * p_o25_p + 0.45 * p_o25_h) * 100, 1)

    # Over 1.5
    p_o15_p = poisson_over(lt, 1) / 100
    p_o15_h = (hf["o15"] + af["o15"]) / 2
    p_o15   = round((0.60 * p_o15_p + 0.40 * p_o15_h) * 100, 1)

    # Over 3.5
    p_o35_p = poisson_over(lt, 3) / 100
    p_o35_h = (hf["o35"] + af["o35"]) / 2
    p_o35   = round((0.55 * p_o35_p + 0.45 * p_o35_h) * 100, 1)

    # BTTS
    ph_sc    = 1 - _poisson(lh, 0)
    pa_sc    = 1 - _poisson(la, 0)
    p_btts_p = ph_sc * pa_sc
    p_btts_h = ((hf["btts"] + af["btts"]) / 2) * (1 - (hf["fts"] + af["fts"]) / 2 * 0.35)
    p_btts   = round((0.45 * p_btts_p + 0.55 * p_btts_h) * 100, 1)

    # Composite "value" score (combined signal strength)
    value = round((p_o25 * 0.4 + p_btts * 0.35 + p_o15 * 0.25), 1)

    return {
        "lam":    round(lt, 2),
        "lam_h":  round(lh, 2),
        "lam_a":  round(la, 2),
        "over15": p_o15,
        "over25": p_o25,
        "over35": p_o35,
        "btts":   p_btts,
        "value":  value,
    }


# ─── Daily picks for a specific date ─────────────────────
def get_picks_for_date(target_date: str, all_matches: list, team_stats: dict,
                       min_confidence: float = 62.0, max_picks: int = 4) -> dict:
    """
    Find upcoming matches on target_date, run analysis,
    return top picks ranked by confidence.
    """
    day_matches = [
        m for m in all_matches
        if m["date"] == target_date and m["score"] is None
    ]

    candidates = []
    for m in day_matches:
        hf = team_stats.get(m["home"])
        af = team_stats.get(m["away"])
        if not hf or not af:
            continue

        res = analyse_match(hf, af)

        # Generate individual bet candidates
        bets = []
        if res["over25"] >= min_confidence:
            bets.append({
                "market":     "Plus de 2.5 buts",
                "market_key": "over25",
                "icon":       "⚽",
                "confidence": res["over25"],
                "exp_goals":  res["lam"],
            })
        if res["btts"] >= min_confidence:
            bets.append({
                "market":     "Les deux équipes marquent (BTTS)",
                "market_key": "btts",
                "icon":       "🤝",
                "confidence": res["btts"],
                "exp_goals":  res["lam"],
            })
        if res["over15"] >= min_confidence:
            bets.append({
                "market":     "Plus de 1.5 buts",
                "market_key": "over15",
                "icon":       "🎯",
                "confidence": res["over15"],
                "exp_goals":  res["lam"],
            })
        if res["over35"] >= min_confidence:
            bets.append({
                "market":     "Plus de 3.5 buts",
                "market_key": "over35",
                "icon":       "🔥",
                "confidence": res["over35"],
                "exp_goals":  res["lam"],
            })

        for bet in bets:
            bet.update({
                "match_id":   hash(f"{m['home']}{m['away']}{m['date']}") & 0x7FFFFFFF,
                "home_team":  m["home"],
                "away_team":  m["away"],
                "home_logo":  f"/static/img/team-default.svg",
                "away_logo":  f"/static/img/team-default.svg",
                "tournament": m["league"],
                "flag":       m.get("flag", ""),
                "start_ts":   _date_to_ts(m["date"], m.get("time", "15:00")),
                "round":      m["round"],
                "home_form":  _form_summary(hf, m["home"]),
                "away_form":  _form_summary(af, m["away"]),
                "analysis":   res,
                "factors":    _build_factors(hf, af, res, m["home"], m["away"]),
            })
            candidates.append(bet)

    # Sort by confidence, deduplicate (1 bet per match)
    candidates.sort(key=lambda x: x["confidence"], reverse=True)
    seen, picks = set(), []
    for bet in candidates:
        mid = (bet["home_team"], bet["away_team"])
        if mid not in seen:
            seen.add(mid)
            picks.append(bet)
        if len(picks) >= max_picks:
            break

    return {
        "picks":                  picks,
        "total_matches_analyzed": len(day_matches),
        "date":                   target_date,
        "source":                 "openfootball/github",
    }


def _build_factors(hf, af, res, home, away):
    fb_h = "".join({"W": "✅", "D": "🟡", "L": "❌"}.get(r, "?") for r in hf["form"])
    fb_a = "".join({"W": "✅", "D": "🟡", "L": "❌"}.get(r, "?") for r in af["form"])
    return [
        f"**{home}** : {hf['avg_sc']:.1f} buts/m marqués · {hf['avg_co']:.1f} encaissés · forme {fb_h}",
        f"**{away}** : {af['avg_sc']:.1f} buts/m marqués · {af['avg_co']:.1f} encaissés · forme {fb_a}",
        f"Buts attendus λ = **{res['lam']}** (dom {res['lam_h']} + ext {res['lam_a']})",
        f"Taux Over 2.5 historique dom. : {round(hf['o25']*100)}% · ext. : {round(af['o25']*100)}%",
        f"Taux BTTS dom. : {round(hf['btts']*100)}% · ext. : {round(af['btts']*100)}%",
    ]


def _form_summary(f: dict, name: str) -> dict:
    return {
        "name":             name,
        "avg_scored":       f["avg_sc"],
        "avg_conceded":     f["avg_co"],
        "over25_rate_pct":  round(f["o25"] * 100),
        "btts_rate_pct":    round(f["btts"] * 100),
        "win_rate_pct":     round(f["wr"] * 100),
        "clean_sheet_pct":  round(f["cs"] * 100),
        "fts_pct":          round(f["fts"] * 100),
        "form_str":         f["form"],
        "matches":          f["n"],
    }


def _date_to_ts(date_str: str, time_str: str = "15:00") -> int:
    import datetime as dt
    try:
        h, m = map(int, time_str.split(":"))
        d = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=h, minute=m, tzinfo=dt.timezone.utc)
        return int(d.timestamp())
    except Exception:
        return 0


# ─── Convenience: get best upcoming date ─────────────────
def get_best_upcoming_date(all_matches: list) -> str:
    """Return nearest future date with upcoming matches."""
    today = date.today().isoformat()
    upcoming_dates = sorted(set(
        m["date"] for m in all_matches
        if m["score"] is None and m["date"] >= today
    ))
    return upcoming_dates[0] if upcoming_dates else today


def get_upcoming_dates(all_matches: list, n: int = 5) -> list:
    today = date.today().isoformat()
    return sorted(set(
        m["date"] for m in all_matches
        if m["score"] is None and m["date"] >= today
    ))[:n]


# ─── Quick test ──────────────────────────────────────────
if __name__ == "__main__":
    print("Loading match data from GitHub...")
    all_m = load_all_matches()
    print(f"  {len(all_m)} matches loaded")

    stats = build_team_stats(all_m)
    print(f"  {len(stats)} teams with stats")

    best_date = get_best_upcoming_date(all_m)
    print(f"  Best upcoming date: {best_date}")

    result = get_picks_for_date(best_date, all_m, stats)
    print(f"\n=== PICKS FOR {best_date} ===")
    for i, p in enumerate(result["picks"], 1):
        print(f"#{i} [{p['confidence']}%] {p['market']}")
        print(f"    {p['home_team']} vs {p['away_team']} [{p['tournament']}]")
        print(f"    λ={p['analysis']['lam']}  BTTS={p['analysis']['btts']}%  O2.5={p['analysis']['over25']}%")
