"""
Sports Betting Analysis App - powered by SofaScore data.
"""

import os
from flask import Flask, render_template, jsonify, request
from datetime import date, timedelta
import sofascore_api as sf
import demo_data

app = Flask(__name__)

# Set DEMO_MODE=1 to use local demo data (no internet required)
DEMO_MODE = os.environ.get("DEMO_MODE", "0") == "1"


# ──────────────────────────────────────────────
# Routes HTML
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", demo_mode=DEMO_MODE)


@app.route("/match/<int:event_id>")
def match_detail(event_id):
    return render_template("match.html", event_id=event_id, demo_mode=DEMO_MODE)


# ──────────────────────────────────────────────
# API JSON (consommé par le frontend JS)
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


@app.route("/api/match/<int:event_id>")
def api_match(event_id):
    if DEMO_MODE:
        demo = demo_data.DEMO_MATCH_12345678
        demo["summary"]["id"] = event_id
        return jsonify(demo)

    detail = sf.get_event_details(event_id)
    if not detail or "event" not in detail:
        return jsonify({"error": "Match introuvable"}), 404

    event = detail["event"]
    summary = sf.parse_event_summary(event)

    raw_stats = sf.get_event_statistics(event_id)
    stats = sf.parse_statistics(raw_stats)

    incidents = sf.get_event_incidents(event_id) or []
    h2h = sf.get_h2h(event_id) or {}
    odds_raw = sf.get_event_odds(event_id) or {}
    betting = sf.compute_betting_score(stats, odds_raw)

    return jsonify({
        "summary": summary,
        "statistics": stats,
        "incidents": incidents,
        "h2h": h2h,
        "odds": odds_raw,
        "betting": betting,
    })


@app.route("/api/match/<int:event_id>/lineups")
def api_lineups(event_id):
    if DEMO_MODE:
        return jsonify({
            "home": {
                "name": "Paris Saint-Germain",
                "formation": "4-3-3",
                "players": [
                    {"player": {"name": "Donnarumma", "jerseyNumber": "99"}, "position": "G"},
                    {"player": {"name": "Hakimi", "jerseyNumber": "2"}, "position": "D"},
                    {"player": {"name": "Marquinhos", "jerseyNumber": "5"}, "position": "D"},
                    {"player": {"name": "Beraldo", "jerseyNumber": "34"}, "position": "D"},
                    {"player": {"name": "Nuno Mendes", "jerseyNumber": "25"}, "position": "D"},
                    {"player": {"name": "Vitinha", "jerseyNumber": "17"}, "position": "M"},
                    {"player": {"name": "Ruiz", "jerseyNumber": "8"}, "position": "M"},
                    {"player": {"name": "Zaire-Emery", "jerseyNumber": "33"}, "position": "M"},
                    {"player": {"name": "Dembélé", "jerseyNumber": "10"}, "position": "A"},
                    {"player": {"name": "Mbappé", "jerseyNumber": "7"}, "position": "A"},
                    {"player": {"name": "Barcola", "jerseyNumber": "29"}, "position": "A"},
                    {"player": {"name": "Kolo Muani", "jerseyNumber": "23"}, "position": "A", "substitute": True},
                    {"player": {"name": "Safonov", "jerseyNumber": "16"}, "position": "G", "substitute": True},
                ],
            },
            "away": {
                "name": "Marseille",
                "formation": "4-2-3-1",
                "players": [
                    {"player": {"name": "Rulli", "jerseyNumber": "1"}, "position": "G"},
                    {"player": {"name": "Clauss", "jerseyNumber": "13"}, "position": "D"},
                    {"player": {"name": "Mbemba", "jerseyNumber": "99"}, "position": "D"},
                    {"player": {"name": "Brassier", "jerseyNumber": "4"}, "position": "D"},
                    {"player": {"name": "Murillo", "jerseyNumber": "22"}, "position": "D"},
                    {"player": {"name": "Kondogbia", "jerseyNumber": "6"}, "position": "M"},
                    {"player": {"name": "Guendouzi", "jerseyNumber": "8"}, "position": "M"},
                    {"player": {"name": "Harit", "jerseyNumber": "7"}, "position": "M"},
                    {"player": {"name": "Sarr", "jerseyNumber": "11"}, "position": "M"},
                    {"player": {"name": "Luis Henrique", "jerseyNumber": "19"}, "position": "A"},
                    {"player": {"name": "Aubameyang", "jerseyNumber": "10"}, "position": "A"},
                ],
            },
        })

    data = sf.get_event_lineups(event_id) or {}
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
