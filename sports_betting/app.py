"""
Sports Betting Analysis App - powered by SofaScore data.
"""

import os
from flask import Flask, render_template, jsonify, request
from datetime import date, timedelta
import sofascore_api as sf
import analysis_engine as ae
import demo_data

app = Flask(__name__)
DEMO_MODE = os.environ.get("DEMO_MODE", "0") == "1"


# ──────────────────────────────────────────────
# HTML Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", demo_mode=DEMO_MODE)


@app.route("/match/<int:event_id>")
def match_detail(event_id):
    return render_template("match.html", event_id=event_id, demo_mode=DEMO_MODE)


# ──────────────────────────────────────────────
# JSON API
# ──────────────────────────────────────────────

@app.route("/api/live")
def api_live():
    sport = request.args.get("sport", "football")
    if DEMO_MODE:
        return jsonify([sf.parse_event_summary(e) for e in demo_data.DEMO_LIVE_EVENTS])
    events = sf.get_live_events(sport)
    return jsonify([sf.parse_event_summary(e) for e in events])


@app.route("/api/scheduled")
def api_scheduled():
    sport = request.args.get("sport", "football")
    day_offset = int(request.args.get("day", 0))
    d = date.today() + timedelta(days=day_offset)
    if DEMO_MODE:
        return jsonify([sf.parse_event_summary(e) for e in demo_data.DEMO_SCHEDULED_EVENTS])
    events = sf.get_scheduled_events(sport, d.strftime("%Y-%m-%d"))
    return jsonify([sf.parse_event_summary(e) for e in events])


@app.route("/api/picks")
def api_picks():
    """
    Main endpoint: analyze today's matches and return top 3-4 picks.
    """
    sport     = request.args.get("sport", "football")
    day_offset = int(request.args.get("day", 0))

    if DEMO_MODE:
        return jsonify(_demo_picks())

    d = date.today() + timedelta(days=day_offset)
    events = sf.get_scheduled_events(sport, d.strftime("%Y-%m-%d"))
    result = ae.get_daily_picks(events)
    return jsonify(result)


@app.route("/api/match/<int:event_id>")
def api_match(event_id):
    if DEMO_MODE:
        base = demo_data.DEMO_MATCH_DETAIL.get(
            event_id,
            demo_data.DEMO_MATCH_DETAIL[10001]
        )
        base = dict(base)
        base["summary"] = dict(base["summary"])
        base["summary"]["id"] = event_id

        # Build betting analysis from demo forms
        event_stub = _find_demo_event(event_id)
        if event_stub:
            home_id = event_stub["homeTeam"]["id"]
            away_id = event_stub["awayTeam"]["id"]
            hf = demo_data.DEMO_TEAM_FORMS.get(home_id)
            af = demo_data.DEMO_TEAM_FORMS.get(away_id)
            h2h = demo_data.DEMO_H2H.get(event_id, {"over25_rate": 0.5, "btts_rate": 0.5, "count": 0})
            if hf and af:
                base["betting"] = {
                    "over25":  ae.analyze_over25(hf, af, h2h),
                    "btts":    ae.analyze_btts(hf, af, h2h),
                    "over15":  ae.analyze_over15(hf, af, h2h),
                    "x12":     ae.analyze_1x2(hf, af, h2h, base["summary"]["home_team"], base["summary"]["away_team"]),
                    "home_form": ae.form_summary(hf),
                    "away_form": ae.form_summary(af),
                }
        return jsonify(base)

    detail = sf.get_event_details(event_id)
    if not detail or "event" not in detail:
        return jsonify({"error": "Match introuvable"}), 404

    event    = detail["event"]
    summary  = sf.parse_event_summary(event)
    raw_stats = sf.get_event_statistics(event_id)
    stats    = sf.parse_statistics(raw_stats)
    incidents = sf.get_event_incidents(event_id) or []
    h2h_raw  = sf.get_h2h(event_id) or {}

    home_id  = event.get("homeTeam", {}).get("id")
    away_id  = event.get("awayTeam", {}).get("id")
    home_form = ae.get_team_form(home_id) if home_id else None
    away_form = ae.get_team_form(away_id) if away_id else None
    h2h_stats = ae.get_h2h_stats(event_id)

    betting = {}
    if home_form and away_form:
        betting = {
            "over25":     ae.analyze_over25(home_form, away_form, h2h_stats),
            "btts":       ae.analyze_btts(home_form, away_form, h2h_stats),
            "over15":     ae.analyze_over15(home_form, away_form, h2h_stats),
            "x12":        ae.analyze_1x2(home_form, away_form, h2h_stats,
                                          summary["home_team"], summary["away_team"]),
            "home_form":  ae.form_summary(home_form),
            "away_form":  ae.form_summary(away_form),
        }

    return jsonify({
        "summary":    summary,
        "statistics": stats,
        "incidents":  incidents,
        "h2h":        h2h_raw,
        "betting":    betting,
    })


@app.route("/api/match/<int:event_id>/lineups")
def api_lineups(event_id):
    if DEMO_MODE:
        return jsonify(_demo_lineups(event_id))
    data = sf.get_event_lineups(event_id) or {}
    return jsonify(data)


# ──────────────────────────────────────────────
# Demo helpers
# ──────────────────────────────────────────────

def _find_demo_event(event_id):
    all_events = demo_data.DEMO_SCHEDULED_EVENTS + demo_data.DEMO_LIVE_EVENTS
    return next((e for e in all_events if e["id"] == event_id), None)


def _demo_picks():
    import analysis_engine as ae
    picks = []
    for event in demo_data.DEMO_SCHEDULED_EVENTS:
        eid     = event["id"]
        home_id = event["homeTeam"]["id"]
        away_id = event["awayTeam"]["id"]
        hf = demo_data.DEMO_TEAM_FORMS.get(home_id)
        af = demo_data.DEMO_TEAM_FORMS.get(away_id)
        if not hf or not af:
            continue
        h2h   = demo_data.DEMO_H2H.get(eid, {"over25_rate": 0.5, "btts_rate": 0.5, "count": 0})
        ev_sum = sf.parse_event_summary(event)

        for bet in [
            ae.analyze_over25(hf, af, h2h),
            ae.analyze_btts(hf, af, h2h),
            ae.analyze_over15(hf, af, h2h),
        ] + ae.analyze_1x2(hf, af, h2h, ev_sum["home_team"], ev_sum["away_team"])[:1]:
            if bet["confidence"] >= ae.MIN_CONFIDENCE:
                bet.update({
                    "match_id":   eid,
                    "home_team":  ev_sum["home_team"],
                    "away_team":  ev_sum["away_team"],
                    "home_logo":  ev_sum["home_logo"],
                    "away_logo":  ev_sum["away_logo"],
                    "tournament": ev_sum["tournament"],
                    "start_ts":   ev_sum["start_timestamp"],
                    "home_form":  ae.form_summary(hf),
                    "away_form":  ae.form_summary(af),
                })
                picks.append(bet)

    picks.sort(key=lambda x: x["confidence"], reverse=True)
    # Deduplicate: one bet per match max (best one)
    seen, selected = set(), []
    for p in picks:
        if p["match_id"] not in seen:
            seen.add(p["match_id"])
            selected.append(p)
        if len(selected) >= ae.MAX_DAILY_PICKS:
            break

    return {
        "picks": selected,
        "total_matches_analyzed": len(demo_data.DEMO_SCHEDULED_EVENTS),
    }


def _demo_lineups(event_id):
    return {
        "home": {
            "name": "Paris Saint-Germain", "formation": "4-3-3",
            "players": [
                {"player": {"name": "Donnarumma",  "jerseyNumber": "99"}, "position": "G"},
                {"player": {"name": "Hakimi",       "jerseyNumber": "2"},  "position": "D"},
                {"player": {"name": "Marquinhos",   "jerseyNumber": "5"},  "position": "D"},
                {"player": {"name": "Beraldo",      "jerseyNumber": "34"}, "position": "D"},
                {"player": {"name": "Nuno Mendes",  "jerseyNumber": "25"}, "position": "D"},
                {"player": {"name": "Vitinha",      "jerseyNumber": "17"}, "position": "M"},
                {"player": {"name": "F. Ruiz",      "jerseyNumber": "8"},  "position": "M"},
                {"player": {"name": "Zaire-Emery",  "jerseyNumber": "33"}, "position": "M"},
                {"player": {"name": "Dembélé",      "jerseyNumber": "10"}, "position": "A"},
                {"player": {"name": "Mbappé",       "jerseyNumber": "7"},  "position": "A"},
                {"player": {"name": "Barcola",      "jerseyNumber": "29"}, "position": "A"},
                {"player": {"name": "Kolo Muani",   "jerseyNumber": "23"}, "position": "A",  "substitute": True},
                {"player": {"name": "Safonov",      "jerseyNumber": "16"}, "position": "G",  "substitute": True},
            ],
        },
        "away": {
            "name": "Marseille", "formation": "4-2-3-1",
            "players": [
                {"player": {"name": "Rulli",        "jerseyNumber": "1"},  "position": "G"},
                {"player": {"name": "Clauss",        "jerseyNumber": "13"}, "position": "D"},
                {"player": {"name": "Mbemba",        "jerseyNumber": "99"}, "position": "D"},
                {"player": {"name": "Brassier",      "jerseyNumber": "4"},  "position": "D"},
                {"player": {"name": "Murillo",       "jerseyNumber": "22"}, "position": "D"},
                {"player": {"name": "Kondogbia",     "jerseyNumber": "6"},  "position": "M"},
                {"player": {"name": "Guendouzi",     "jerseyNumber": "8"},  "position": "M"},
                {"player": {"name": "Harit",         "jerseyNumber": "7"},  "position": "M"},
                {"player": {"name": "Sarr",          "jerseyNumber": "11"}, "position": "M"},
                {"player": {"name": "Luis Henrique", "jerseyNumber": "19"}, "position": "A"},
                {"player": {"name": "Aubameyang",    "jerseyNumber": "10"}, "position": "A"},
            ],
        },
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
