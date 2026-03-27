"""
BetScore — Sports Betting Analysis
Data sources (in priority order):
  1. GitHub openfootball JSON (always available, no API key)
  2. SofaScore unofficial API (if reachable)
  3. Demo data (DEMO_MODE=1 or all sources unreachable)
"""

import os
import threading
from flask import Flask, render_template, jsonify, request
from datetime import date, timedelta
import sofascore_api as sf
import analysis_engine as ae
import demo_data
import github_data as gd

app = Flask(__name__)
DEMO_MODE = os.environ.get("DEMO_MODE", "0") == "1"

# ── Pre-load GitHub data once at startup (cached in memory) ──
_gh_cache = {"matches": None, "stats": None, "loaded": False}
_gh_lock  = threading.Lock()


def _ensure_gh_loaded():
    global _gh_cache
    if _gh_cache["loaded"]:
        return
    with _gh_lock:
        if _gh_cache["loaded"]:
            return
        try:
            all_m = gd.load_all_matches()
            stats = gd.build_team_stats(all_m)
            _gh_cache = {"matches": all_m, "stats": stats, "loaded": True}
        except Exception as e:
            app.logger.warning(f"GitHub data load failed: {e}")
            _gh_cache["loaded"] = True   # don't retry on every request


def _gh_matches():
    _ensure_gh_loaded()
    return _gh_cache["matches"] or []


def _gh_stats():
    _ensure_gh_loaded()
    return _gh_cache["stats"] or {}


# Start loading in background at startup
threading.Thread(target=_ensure_gh_loaded, daemon=True).start()


# ──────────────────────────────────────────────────────────
# HTML routes
# ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/match/<path:event_id>")
def match_detail(event_id):
    return render_template("match.html", event_id=event_id)


# ──────────────────────────────────────────────────────────
# /api/picks  — Main endpoint: top 3-4 bets of the day
# ──────────────────────────────────────────────────────────

@app.route("/api/picks")
def api_picks():
    day_offset  = int(request.args.get("day", 0))
    target_date = (date.today() + timedelta(days=day_offset)).isoformat()

    # ── 1. Try GitHub openfootball data ───────────────────
    all_m  = _gh_matches()
    stats  = _gh_stats()
    if all_m and stats:
        result = gd.get_picks_for_date(target_date, all_m, stats,
                                       min_confidence=60.0, max_picks=4)
        if result["picks"]:
            return jsonify(result)

        # If no matches on that specific date, find nearest future date
        upcoming = gd.get_upcoming_dates(all_m, 10)
        for d in upcoming:
            result = gd.get_picks_for_date(d, all_m, stats,
                                           min_confidence=60.0, max_picks=4)
            if result["picks"]:
                result["note"] = f"Prochain jour avec matchs : {d} (pause internationale aujourd'hui)"
                return jsonify(result)

    # ── 2. Try SofaScore API ─────────────────────────────
    if not DEMO_MODE:
        sport  = request.args.get("sport", "football")
        events = sf.get_scheduled_events(sport, target_date)
        if events:
            res = ae.get_daily_picks(events)
            if res.get("picks"):
                return jsonify(res)

    # ── 3. Fall back to demo data ────────────────────────
    return jsonify(_demo_picks())


# ──────────────────────────────────────────────────────────
# /api/scheduled  — All matches for a given day
# ──────────────────────────────────────────────────────────

@app.route("/api/scheduled")
def api_scheduled():
    day_offset  = int(request.args.get("day", 0))
    target_date = (date.today() + timedelta(days=day_offset)).isoformat()

    all_m = _gh_matches()
    if all_m:
        day = [m for m in all_m if m["date"] == target_date and m["score"] is None]
        if not day:
            # During international break → show nearest upcoming
            upcoming = gd.get_upcoming_dates(all_m, 5)
            if upcoming:
                next_date = upcoming[0]
                day = [m for m in all_m if m["date"] == next_date and m["score"] is None]
        return jsonify([_match_to_summary(m) for m in sorted(day, key=lambda x: x.get("time",""))])

    # Fallback
    if DEMO_MODE:
        return jsonify([sf.parse_event_summary(e) for e in demo_data.DEMO_SCHEDULED_EVENTS])
    sport  = request.args.get("sport", "football")
    events = sf.get_scheduled_events(sport, target_date)
    return jsonify([sf.parse_event_summary(e) for e in events])


# ──────────────────────────────────────────────────────────
# /api/live  — Live matches
# ──────────────────────────────────────────────────────────

@app.route("/api/live")
def api_live():
    if DEMO_MODE:
        return jsonify([sf.parse_event_summary(e) for e in demo_data.DEMO_LIVE_EVENTS])
    sport  = request.args.get("sport", "football")
    events = sf.get_live_events(sport)
    return jsonify([sf.parse_event_summary(e) for e in events])


# ──────────────────────────────────────────────────────────
# /api/match/<id>  — Match detail + betting analysis
# ──────────────────────────────────────────────────────────

@app.route("/api/match/<path:event_id>")
def api_match(event_id):
    all_m = _gh_matches()
    stats = _gh_stats()

    # event_id can be "Home_Away_date" format or numeric
    # Try to find match in GitHub data by encoded id
    match = None
    if all_m:
        for m in all_m:
            mid = str(gd._date_to_ts(m["date"], m.get("time","15:00")) & 0x7FFFFFFF)
            slug = _make_slug(m["home"], m["away"])
            if str(event_id) in (mid, slug):
                match = m
                break

    if match:
        hf = stats.get(match["home"])
        af = stats.get(match["away"])
        res = gd.analyse_match(hf, af) if hf and af else {}
        betting = {}
        if hf and af:
            betting = {
                "over25":     {"market": "Plus de 2.5 buts",  "confidence": res["over25"], "exp_goals": res["lam"], "factors": gd._build_factors(hf,af,res,match["home"],match["away"])},
                "over15":     {"market": "Plus de 1.5 buts",  "confidence": res["over15"], "exp_goals": res["lam"], "factors": []},
                "btts":       {"market": "Les deux équipes marquent", "confidence": res["btts"], "factors": []},
                "x12":        _x12(hf, af, match["home"], match["away"]),
                "home_form":  gd._form_summary(hf, match["home"]),
                "away_form":  gd._form_summary(af, match["away"]),
            }
        summary = {
            "id":            event_id,
            "home_team":     match["home"],
            "away_team":     match["away"],
            "home_logo":     "/static/img/team-default.svg",
            "away_logo":     "/static/img/team-default.svg",
            "home_score":    None,
            "away_score":    None,
            "status_type":   "notstarted",
            "status_desc":   "",
            "start_timestamp": gd._date_to_ts(match["date"], match.get("time","15:00")),
            "tournament":    match["league"],
            "category":      match["country"],
            "round":         match["round"],
        }
        return jsonify({"summary": summary, "statistics": {}, "incidents": [],
                        "h2h": {}, "betting": betting})

    # Fallback to SofaScore or demo
    if DEMO_MODE:
        base = demo_data.DEMO_MATCH_DETAIL.get(
            int(event_id) if str(event_id).isdigit() else 20001,
            demo_data.DEMO_MATCH_DETAIL[20001])
        base = dict(base); base["summary"] = dict(base["summary"])
        base["summary"]["id"] = event_id
        event_stub = next((e for e in demo_data.DEMO_SCHEDULED_EVENTS
                           if e["id"] == int(event_id)), None) if str(event_id).isdigit() else None
        if event_stub:
            hid = event_stub["homeTeam"]["id"]; aid = event_stub["awayTeam"]["id"]
            hf2 = demo_data.DEMO_TEAM_FORMS.get(hid); af2 = demo_data.DEMO_TEAM_FORMS.get(aid)
            h2h = demo_data.DEMO_H2H.get(int(event_id), {"over25_rate":0.5,"btts_rate":0.5,"count":0})
            if hf2 and af2:
                base["betting"] = {
                    "over25":     ae.analyze_over25(hf2,af2,h2h),
                    "btts":       ae.analyze_btts(hf2,af2,h2h),
                    "over15":     ae.analyze_over15(hf2,af2,h2h),
                    "x12":        ae.analyze_1x2(hf2,af2,h2h,base["summary"]["home_team"],base["summary"]["away_team"]),
                    "home_form":  ae.form_summary(hf2),
                    "away_form":  ae.form_summary(af2),
                }
        return jsonify(base)

    try:
        eid = int(event_id)
    except ValueError:
        return jsonify({"error": "Match introuvable"}), 404

    detail = sf.get_event_details(eid)
    if not detail or "event" not in detail:
        return jsonify({"error": "Match introuvable"}), 404
    event    = detail["event"]
    summary  = sf.parse_event_summary(event)
    raw_stats = sf.get_event_statistics(eid)
    stats2   = sf.parse_statistics(raw_stats)
    incidents = sf.get_event_incidents(eid) or []
    h2h_raw  = sf.get_h2h(eid) or {}
    h2h_s    = ae.get_h2h_stats(eid)
    hid      = event.get("homeTeam",{}).get("id")
    aid      = event.get("awayTeam",{}).get("id")
    hf3      = ae.get_team_form(hid) if hid else None
    af3      = ae.get_team_form(aid) if aid else None
    betting  = {}
    if hf3 and af3:
        betting = {
            "over25":     ae.analyze_over25(hf3,af3,h2h_s),
            "btts":       ae.analyze_btts(hf3,af3,h2h_s),
            "over15":     ae.analyze_over15(hf3,af3,h2h_s),
            "x12":        ae.analyze_1x2(hf3,af3,h2h_s,summary["home_team"],summary["away_team"]),
            "home_form":  ae.form_summary(hf3),
            "away_form":  ae.form_summary(af3),
        }
    return jsonify({"summary": summary, "statistics": stats2,
                    "incidents": incidents, "h2h": h2h_raw, "betting": betting})


@app.route("/api/match/<path:event_id>/lineups")
def api_lineups(event_id):
    if DEMO_MODE:
        return jsonify(_demo_lineups())
    try:
        data = sf.get_event_lineups(int(event_id)) or {}
    except Exception:
        data = {}
    return jsonify(data)


# ──────────────────────────────────────────────────────────
# /api/upcoming  — List of dates with matches
# ──────────────────────────────────────────────────────────

@app.route("/api/upcoming")
def api_upcoming():
    all_m = _gh_matches()
    if not all_m:
        return jsonify([])
    dates = gd.get_upcoming_dates(all_m, 10)
    return jsonify(dates)


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _match_to_summary(m: dict) -> dict:
    ts  = gd._date_to_ts(m["date"], m.get("time","15:00"))
    mid = str(ts & 0x7FFFFFFF)
    return {
        "id":            mid,
        "home_team":     m["home"],
        "home_team_id":  None,
        "home_logo":     "/static/img/team-default.svg",
        "away_team":     m["away"],
        "away_team_id":  None,
        "away_logo":     "/static/img/team-default.svg",
        "home_score":    None,
        "away_score":    None,
        "status_type":   "notstarted",
        "status_desc":   "",
        "start_timestamp": ts,
        "tournament":    m["league"],
        "category":      m.get("country",""),
        "country_flag":  m.get("flag",""),
        "round":         m.get("round",""),
        "slug":          _make_slug(m["home"], m["away"]),
    }


def _make_slug(home, away):
    return home.lower().replace(" ","-") + "_" + away.lower().replace(" ","-")


def _x12(hf, af, home, away):
    def fp(form): return sum({"W":3,"D":1,"L":0}.get(r,0) for r in form)
    hp = fp(hf["form"]); ap = fp(af["form"])
    mx = max(hp+ap,1)
    pw = hf["wr"]*0.5 + hp/mx*0.3 + (1-af["wr"])*0.2
    aw = af["wr"]*0.5 + ap/mx*0.3 + (1-hf["wr"])*0.2
    dw = (hf["dr"]+af["dr"])/2
    t  = pw+aw+dw
    pw /= t; aw /= t; dw /= t
    return [
        {"market": f"Victoire {home}", "market_key":"home_win", "icon":"🏠", "prob":round(pw,3), "confidence":round(pw*100,1), "factors":[]},
        {"market": "Match Nul",        "market_key":"draw",     "icon":"🤝", "prob":round(dw,3), "confidence":round(dw*100,1), "factors":[]},
        {"market": f"Victoire {away}", "market_key":"away_win", "icon":"✈️", "prob":round(aw,3), "confidence":round(aw*100,1), "factors":[]},
    ]


def _demo_picks():
    picks = []
    for event in demo_data.DEMO_SCHEDULED_EVENTS:
        eid = event["id"]
        hf  = demo_data.DEMO_TEAM_FORMS.get(event["homeTeam"]["id"])
        af  = demo_data.DEMO_TEAM_FORMS.get(event["awayTeam"]["id"])
        if not hf or not af: continue
        h2h = demo_data.DEMO_H2H.get(eid, {"over25_rate":0.5,"btts_rate":0.5,"count":0})
        ev  = sf.parse_event_summary(event)
        for bet in [ae.analyze_over25(hf,af,h2h), ae.analyze_btts(hf,af,h2h),
                    ae.analyze_over15(hf,af,h2h)]:
            if bet["confidence"] >= ae.MIN_CONFIDENCE:
                bet.update({"match_id":eid,"home_team":ev["home_team"],"away_team":ev["away_team"],
                             "home_logo":ev["home_logo"],"away_logo":ev["away_logo"],
                             "tournament":ev["tournament"],"start_ts":ev["start_timestamp"],
                             "home_form":ae.form_summary(hf),"away_form":ae.form_summary(af)})
                picks.append(bet)
    picks.sort(key=lambda x: x["confidence"], reverse=True)
    seen, sel = set(), []
    for p in picks:
        if p["match_id"] not in seen:
            seen.add(p["match_id"]); sel.append(p)
        if len(sel) >= ae.MAX_DAILY_PICKS: break
    return {"picks": sel, "total_matches_analyzed": len(demo_data.DEMO_SCHEDULED_EVENTS), "source":"demo"}


def _demo_lineups():
    return {
        "home": {"name":"Équipe Domicile","formation":"4-3-3",
                 "players":[{"player":{"name":"Joueur "+str(i),"jerseyNumber":str(i)},"position":p}
                             for i,p in enumerate([" G","D","D","D","D","M","M","M","A","A","A"],1)]},
        "away": {"name":"Équipe Extérieure","formation":"4-4-2",
                 "players":[{"player":{"name":"Joueur "+str(i),"jerseyNumber":str(i)},"position":p}
                             for i,p in enumerate([" G","D","D","D","D","M","M","M","M","A","A"],1)]},
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
