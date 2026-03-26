"""
Core betting analysis engine.
Fetches last N matches per team, computes stats,
and generates ranked daily betting picks.
"""

import math
from typing import Optional
import sofascore_api as sf


# ─────────────────────────────────────────────────────────
# 1. Team form fetcher
# ─────────────────────────────────────────────────────────

def get_team_form(team_id: int, n: int = 8) -> Optional[dict]:
    """
    Fetch last N completed matches for a team from SofaScore
    and return aggregated betting statistics.
    """
    data = sf._get(f"/team/{team_id}/events/last/0")
    if not data or "events" not in data:
        return None

    events = [
        e for e in data["events"]
        if e.get("status", {}).get("type") == "finished"
    ][:n]

    if not events:
        return None

    return _compute_form_stats(team_id, events)


def _compute_form_stats(team_id: int, events: list) -> dict:
    scored_list, conceded_list, total_list = [], [], []
    btts_list, results, over15_list, over25_list, over35_list = [], [], [], [], []

    for e in events:
        is_home = e.get("homeTeam", {}).get("id") == team_id
        hs = int(e.get("homeScore", {}).get("current") or 0)
        as_ = int(e.get("awayScore", {}).get("current") or 0)

        scored = hs if is_home else as_
        conceded = as_ if is_home else hs
        total = hs + as_

        scored_list.append(scored)
        conceded_list.append(conceded)
        total_list.append(total)
        btts_list.append(1 if hs > 0 and as_ > 0 else 0)
        over15_list.append(1 if total >= 2 else 0)
        over25_list.append(1 if total >= 3 else 0)
        over35_list.append(1 if total >= 4 else 0)

        if scored > conceded:
            results.append("W")
        elif scored < conceded:
            results.append("L")
        else:
            results.append("D")

    n = len(events)
    return {
        "avg_scored":          round(sum(scored_list) / n, 2),
        "avg_conceded":        round(sum(conceded_list) / n, 2),
        "avg_total":           round(sum(total_list) / n, 2),
        "over15_rate":         round(sum(over15_list) / n, 3),
        "over25_rate":         round(sum(over25_list) / n, 3),
        "over35_rate":         round(sum(over35_list) / n, 3),
        "btts_rate":           round(sum(btts_list) / n, 3),
        "win_rate":            round(sum(1 for r in results if r == "W") / n, 3),
        "draw_rate":           round(sum(1 for r in results if r == "D") / n, 3),
        "loss_rate":           round(sum(1 for r in results if r == "L") / n, 3),
        "clean_sheet_rate":    round(sum(1 for g in conceded_list if g == 0) / n, 3),
        "fail_to_score_rate":  round(sum(1 for g in scored_list if g == 0) / n, 3),
        "form_str":            results[:5],
        "goals_scored_list":   scored_list,
        "goals_conceded_list": conceded_list,
        "matches_analyzed":    n,
    }


# ─────────────────────────────────────────────────────────
# 2. H2H stats
# ─────────────────────────────────────────────────────────

def get_h2h_stats(event_id: int, n: int = 6) -> dict:
    raw = sf.get_h2h(event_id) or {}
    events = (raw.get("events") or raw.get("teamDuel", {}).get("events") or [])[:n]

    if not events:
        return {"over25_rate": 0.5, "btts_rate": 0.5, "count": 0}

    totals = []
    btts_count = 0
    for e in events:
        hs = int(e.get("homeScore", {}).get("current") or 0)
        as_ = int(e.get("awayScore", {}).get("current") or 0)
        totals.append(hs + as_)
        if hs > 0 and as_ > 0:
            btts_count += 1

    n_actual = len(events)
    return {
        "over25_rate":   round(sum(1 for t in totals if t >= 3) / n_actual, 3),
        "btts_rate":     round(btts_count / n_actual, 3),
        "avg_total":     round(sum(totals) / n_actual, 2),
        "count":         n_actual,
    }


# ─────────────────────────────────────────────────────────
# 3. Poisson helpers
# ─────────────────────────────────────────────────────────

def _poisson_prob(lam: float, k: int) -> float:
    if lam <= 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_over(lam: float, threshold: float) -> float:
    """P(total goals > threshold) with Poisson(lambda)."""
    k_max = int(threshold)
    prob_le = sum(_poisson_prob(lam, k) for k in range(k_max + 1))
    return max(0.0, min(1.0, 1.0 - prob_le))


def poisson_btts(lam_home: float, lam_away: float) -> float:
    """P(home >= 1) * P(away >= 1)."""
    p_home_scores = 1 - _poisson_prob(lam_home, 0)
    p_away_scores = 1 - _poisson_prob(lam_away, 0)
    return p_home_scores * p_away_scores


# ─────────────────────────────────────────────────────────
# 4. Market analyzers
# ─────────────────────────────────────────────────────────

def _form_badge(form: list) -> str:
    icons = {"W": "✅", "D": "🟡", "L": "❌"}
    return " ".join(icons.get(r, "?") for r in form)


def analyze_over25(home: dict, away: dict, h2h: dict) -> dict:
    lam_home = (home["avg_scored"] + away["avg_conceded"]) / 2
    lam_away = (away["avg_scored"] + home["avg_conceded"]) / 2
    lam_total = lam_home + lam_away

    p_poisson = poisson_over(lam_total, 2)
    p_hist    = (home["over25_rate"] + away["over25_rate"]) / 2
    p_h2h     = h2h.get("over25_rate", p_hist)
    h2h_w     = 0.15 if h2h.get("count", 0) >= 3 else 0.0
    hist_w    = 0.35 - h2h_w / 2
    pois_w    = 0.65 - h2h_w / 2

    prob = pois_w * p_poisson + hist_w * p_hist + h2h_w * p_h2h

    factors = [
        f"Buts attendus dans le match : **{lam_total:.2f}**",
        f"Buts/match dom. (marqués {home['avg_scored']:.1f} / encaissés {away['avg_conceded']:.1f})",
        f"Buts/match ext. (marqués {away['avg_scored']:.1f} / encaissés {home['avg_conceded']:.1f})",
        f"Taux Over 2.5 dom. : {home['over25_rate']*100:.0f}% | ext. : {away['over25_rate']*100:.0f}%",
    ]
    if h2h.get("count", 0) >= 3:
        factors.append(f"H2H Over 2.5 : {h2h['over25_rate']*100:.0f}% sur {h2h['count']} matchs")

    return {
        "market":      "Plus de 2.5 buts",
        "market_key":  "over25",
        "icon":        "⚽",
        "prob":        round(prob, 4),
        "confidence":  round(prob * 100, 1),
        "exp_goals":   round(lam_total, 2),
        "lam_home":    round(lam_home, 2),
        "lam_away":    round(lam_away, 2),
        "factors":     factors,
    }


def analyze_over15(home: dict, away: dict, h2h: dict) -> dict:
    lam_home = (home["avg_scored"] + away["avg_conceded"]) / 2
    lam_away = (away["avg_scored"] + home["avg_conceded"]) / 2
    lam_total = lam_home + lam_away

    p_poisson = poisson_over(lam_total, 1)
    p_hist    = (home["over15_rate"] + away["over15_rate"]) / 2

    prob = 0.65 * p_poisson + 0.35 * p_hist

    return {
        "market":      "Plus de 1.5 buts",
        "market_key":  "over15",
        "icon":        "🎯",
        "prob":        round(prob, 4),
        "confidence":  round(prob * 100, 1),
        "exp_goals":   round(lam_total, 2),
        "lam_home":    round(lam_home, 2),
        "lam_away":    round(lam_away, 2),
        "factors": [
            f"Buts attendus : **{lam_total:.2f}**",
            f"Taux Over 1.5 dom. : {home['over15_rate']*100:.0f}% | ext. : {away['over15_rate']*100:.0f}%",
        ],
    }


def analyze_btts(home: dict, away: dict, h2h: dict) -> dict:
    lam_home = (home["avg_scored"] + away["avg_conceded"]) / 2
    lam_away = (away["avg_scored"] + home["avg_conceded"]) / 2

    p_poisson = poisson_btts(lam_home, lam_away)
    p_hist    = (home["btts_rate"] + away["btts_rate"]) / 2
    # Penalty: if a team fails to score often → reduce
    fts_penalty = (home["fail_to_score_rate"] + away["fail_to_score_rate"]) / 2
    p_adjusted  = p_hist * (1 - fts_penalty * 0.3)

    p_h2h  = h2h.get("btts_rate", p_hist)
    h2h_w  = 0.15 if h2h.get("count", 0) >= 3 else 0.0
    prob   = (0.45 - h2h_w / 2) * p_poisson + (0.40 - h2h_w / 2) * p_adjusted + h2h_w * p_h2h

    factors = [
        f"Taux BTTS dom. : {home['btts_rate']*100:.0f}% | ext. : {away['btts_rate']*100:.0f}%",
        f"Dom. marque en moy. {home['avg_scored']:.1f} bt/m · ext. {away['avg_scored']:.1f} bt/m",
        f"Taux sans marquer dom. : {home['fail_to_score_rate']*100:.0f}% | ext. : {away['fail_to_score_rate']*100:.0f}%",
    ]
    if h2h.get("count", 0) >= 3:
        factors.append(f"H2H BTTS : {h2h['btts_rate']*100:.0f}% sur {h2h['count']} matchs")

    return {
        "market":     "Les deux équipes marquent",
        "market_key": "btts",
        "icon":       "🤝",
        "prob":       round(prob, 4),
        "confidence": round(prob * 100, 1),
        "factors":    factors,
    }


def analyze_1x2(home: dict, away: dict, h2h: dict, home_name: str, away_name: str) -> list:
    """Returns list of (1, X, 2) bet dicts ranked by prob."""
    # Form score: W=3, D=1, L=0
    def form_pts(form): return sum({"W": 3, "D": 1, "L": 0}.get(r, 0) for r in form)

    home_pts = form_pts(home["form_str"])
    away_pts = form_pts(away["form_str"])
    max_pts  = max(home_pts + away_pts, 1)

    home_form_score = home_pts / max_pts
    away_form_score = away_pts / max_pts

    # Combine win rate + form
    p_home_win = home["win_rate"] * 0.5 + home_form_score * 0.3 + (1 - away["win_rate"]) * 0.2
    p_away_win = away["win_rate"] * 0.5 + away_form_score * 0.3 + (1 - home["win_rate"]) * 0.2
    p_draw     = (home["draw_rate"] + away["draw_rate"]) / 2

    # Normalize
    total = p_home_win + p_away_win + p_draw
    p_home_win /= total
    p_away_win /= total
    p_draw     /= total

    picks = []
    for label, market_key, prob, icon, team_name in [
        (f"Victoire {home_name}", "home_win", p_home_win, "🏠", home_name),
        ("Match Nul",             "draw",      p_draw,     "🤝", "Nul"),
        (f"Victoire {away_name}", "away_win",  p_away_win, "✈️", away_name),
    ]:
        picks.append({
            "market":     label,
            "market_key": market_key,
            "icon":       icon,
            "prob":       round(prob, 4),
            "confidence": round(prob * 100, 1),
            "factors": [
                f"Win rate dom. : {home['win_rate']*100:.0f}% | ext. : {away['win_rate']*100:.0f}%",
                f"Forme dom. : {_form_badge(home['form_str'])} | ext. : {_form_badge(away['form_str'])}",
            ],
        })
    return sorted(picks, key=lambda x: x["prob"], reverse=True)


def analyze_double_chance(home: dict, away: dict, home_name: str, away_name: str) -> list:
    """1X and X2 double chance markets."""
    p_h_draw  = home["win_rate"] + home["draw_rate"]
    p_a_draw  = away["win_rate"] + away["draw_rate"]
    results = []
    for label, mkey, prob in [
        (f"1X — {home_name} ou Nul", "dc_1x", p_h_draw),
        (f"X2 — {away_name} ou Nul", "dc_x2", p_a_draw),
    ]:
        results.append({
            "market":     label,
            "market_key": mkey,
            "icon":       "🔀",
            "prob":       round(min(prob, 0.97), 4),
            "confidence": round(min(prob * 100, 97), 1),
            "factors": [
                f"Win/Draw rate dom. : {p_h_draw*100:.0f}%",
                f"Win/Draw rate ext. : {p_a_draw*100:.0f}%",
            ],
        })
    return results


# ─────────────────────────────────────────────────────────
# 5. Per-match full analysis
# ─────────────────────────────────────────────────────────

MIN_CONFIDENCE = 65.0   # only keep bets above this threshold
DEDUP_BUFFER   = 5.0    # don't show two bets within X% confidence of each other

def analyze_match(event: dict, home_form: dict, away_form: dict, h2h: dict) -> dict:
    """
    Given pre-fetched form data, run all markets and return ranked candidates.
    """
    summary = sf.parse_event_summary(event)
    candidates = []

    # Over/Under
    for bet in [
        analyze_over25(home_form, away_form, h2h),
        analyze_over15(home_form, away_form, h2h),
        analyze_btts(home_form, away_form, h2h),
    ]:
        if bet["confidence"] >= MIN_CONFIDENCE:
            bet["match_id"]   = summary["id"]
            bet["home_team"]  = summary["home_team"]
            bet["away_team"]  = summary["away_team"]
            bet["home_logo"]  = summary["home_logo"]
            bet["away_logo"]  = summary["away_logo"]
            bet["tournament"] = summary["tournament"]
            bet["start_ts"]   = summary["start_timestamp"]
            candidates.append(bet)

    # 1X2 – only take best pick
    x12_picks = analyze_1x2(home_form, away_form, h2h,
                             summary["home_team"], summary["away_team"])
    best_1x2 = next((p for p in x12_picks if p["confidence"] >= MIN_CONFIDENCE), None)
    if best_1x2:
        best_1x2.update({
            "match_id":   summary["id"],
            "home_team":  summary["home_team"],
            "away_team":  summary["away_team"],
            "home_logo":  summary["home_logo"],
            "away_logo":  summary["away_logo"],
            "tournament": summary["tournament"],
            "start_ts":   summary["start_timestamp"],
        })
        candidates.append(best_1x2)

    return {"summary": summary, "candidates": candidates,
            "home_form": home_form, "away_form": away_form}


# ─────────────────────────────────────────────────────────
# 6. Daily picks selector
# ─────────────────────────────────────────────────────────

MAX_DAILY_PICKS = 4


def get_daily_picks(events: list) -> dict:
    """
    Process all today's events, fetch team forms concurrently,
    and return top MAX_DAILY_PICKS picks ranked by confidence.
    """
    all_candidates = []
    match_analyses = []

    for event in events[:30]:   # limit API calls
        status = event.get("status", {}).get("type", "")
        if status not in ("notstarted", "inprogress"):
            continue

        home_id = event.get("homeTeam", {}).get("id")
        away_id = event.get("awayTeam", {}).get("id")
        if not home_id or not away_id:
            continue

        home_form = get_team_form(home_id)
        away_form = get_team_form(away_id)

        if not home_form or not away_form:
            continue

        h2h = get_h2h_stats(event.get("id", 0))
        result = analyze_match(event, home_form, away_form, h2h)
        match_analyses.append(result)
        all_candidates.extend(result["candidates"])

    # Rank by confidence
    all_candidates.sort(key=lambda x: x["confidence"], reverse=True)

    # Deduplicate: avoid same match appearing twice with same market type
    selected = []
    seen_match_markets = set()
    for bet in all_candidates:
        key = (bet["match_id"], bet["market_key"])
        if key not in seen_match_markets:
            seen_match_markets.add(key)
            selected.append(bet)
        if len(selected) >= MAX_DAILY_PICKS:
            break

    return {
        "picks":    selected,
        "analyses": match_analyses,
        "total_matches_analyzed": len(match_analyses),
    }


# ─────────────────────────────────────────────────────────
# 7. Form summary for display
# ─────────────────────────────────────────────────────────

def form_summary(form: dict) -> dict:
    """Return display-ready stats for a team."""
    return {
        "avg_scored":       form["avg_scored"],
        "avg_conceded":     form["avg_conceded"],
        "over25_rate_pct":  round(form["over25_rate"] * 100),
        "btts_rate_pct":    round(form["btts_rate"] * 100),
        "win_rate_pct":     round(form["win_rate"] * 100),
        "form_str":         form["form_str"],
        "matches":          form["matches_analyzed"],
        "clean_sheet_pct":  round(form["clean_sheet_rate"] * 100),
        "fts_pct":          round(form["fail_to_score_rate"] * 100),
    }
