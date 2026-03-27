"""
Moteur de recommandations pour paris sportifs.
Génère des conseils basés sur les stats de forme, H2H et buts.

Types de paris analysés:
  - Résultat (1X2)
  - BTTS (Les deux équipes marquent)
  - Over/Under 1.5 / 2.5 / 3.5 buts
  - Vainqueur probable
"""

from analyzer import analyze_match


# Seuils de confiance (entre 0 et 1)
CONFIDENCE_THRESHOLDS = {
    "fort": 0.70,
    "moyen": 0.55,
    "faible": 0.45,
}


def _confidence_label(score: float) -> str:
    if score >= CONFIDENCE_THRESHOLDS["fort"]:
        return "FORT"
    elif score >= CONFIDENCE_THRESHOLDS["moyen"]:
        return "MOYEN"
    elif score >= CONFIDENCE_THRESHOLDS["faible"]:
        return "FAIBLE"
    return "TRES_FAIBLE"


def _weighted_avg(values: list, weights: list) -> float:
    total_w = sum(weights)
    if total_w == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / total_w


def recommend_btts(home_form: dict, away_form: dict, h2h: dict) -> dict:
    """
    Recommande BTTS (Both Teams To Score).
    Score de confiance basé sur la forme offensive/défensive + H2H.
    """
    scores = []
    weights = []

    # Forme domicile: taux BTTS
    if home_form.get("matches", 0) >= 3:
        scores.append(home_form["btts_rate"])
        weights.append(2)
        # Capacité offensive de l'équipe à domicile
        if home_form["avg_goals_for"] > 0 and home_form["failed_to_score_rate"] < 0.3:
            scores.append(0.75)
            weights.append(1)
        # Fragilité défensive adversaire (domicile encaisse)
        if home_form["avg_goals_against"] > 1.0:
            scores.append(0.72)
            weights.append(1)

    # Forme extérieur: taux BTTS
    if away_form.get("matches", 0) >= 3:
        scores.append(away_form["btts_rate"])
        weights.append(2)
        if away_form["avg_goals_for"] > 0 and away_form["failed_to_score_rate"] < 0.4:
            scores.append(0.70)
            weights.append(1)

    # H2H BTTS
    if h2h.get("h2h_matches", 0) >= 3:
        scores.append(h2h["btts_rate"])
        weights.append(3)

    if not scores:
        return {"bet": "BTTS Oui", "confidence": 0.0, "label": "INSUFFISANT", "reason": "Données insuffisantes"}

    confidence = _weighted_avg(scores, weights)
    label = _confidence_label(confidence)

    bet = "BTTS Oui" if confidence >= 0.5 else "BTTS Non"
    if confidence < 0.5:
        confidence = 1 - confidence

    reasons = []
    if home_form.get("matches", 0) >= 3:
        reasons.append(f"Domicile BTTS: {home_form['btts_rate']*100:.0f}%")
    if away_form.get("matches", 0) >= 3:
        reasons.append(f"Extérieur BTTS: {away_form['btts_rate']*100:.0f}%")
    if h2h.get("h2h_matches", 0) >= 3:
        reasons.append(f"H2H BTTS: {h2h['btts_rate']*100:.0f}%")

    return {
        "bet": bet,
        "confidence": round(confidence, 3),
        "label": label,
        "reason": " | ".join(reasons),
    }


def recommend_over_under(home_form: dict, away_form: dict, h2h: dict, line: float = 2.5) -> dict:
    """
    Recommande Over/Under pour une ligne donnée (1.5, 2.5, 3.5).
    """
    key = f"over_{str(line).replace('.', '_')}_rate"

    scores = []
    weights = []

    expected_goals = 0.0
    expected_count = 0

    if home_form.get("matches", 0) >= 3:
        home_rate = home_form.get(key, 0)
        scores.append(home_rate)
        weights.append(2)
        expected_goals += home_form.get("avg_total_goals", 0)
        expected_count += 1

    if away_form.get("matches", 0) >= 3:
        away_rate = away_form.get(key, 0)
        scores.append(away_rate)
        weights.append(2)
        expected_goals += away_form.get("avg_total_goals", 0)
        expected_count += 1

    if h2h.get("h2h_matches", 0) >= 3:
        h2h_rate = h2h.get("over_2_5_rate" if line == 2.5 else f"over_{str(line).replace('.','_')}_rate", 0)
        scores.append(h2h_rate)
        weights.append(3)
        expected_goals += h2h.get("avg_total_goals", 0)
        expected_count += 1

    if not scores:
        return {
            "bet": f"Over {line}",
            "confidence": 0.0,
            "label": "INSUFFISANT",
            "reason": "Données insuffisantes",
            "expected_goals": None,
        }

    confidence = _weighted_avg(scores, weights)
    avg_expected = round(expected_goals / expected_count, 2) if expected_count > 0 else None

    label = _confidence_label(confidence)
    bet = f"Over {line}" if confidence >= 0.5 else f"Under {line}"
    if confidence < 0.5:
        confidence = 1 - confidence

    reasons = []
    if home_form.get("matches", 0) >= 3:
        reasons.append(f"Dom moy buts: {home_form.get('avg_total_goals', 0):.1f}")
    if away_form.get("matches", 0) >= 3:
        reasons.append(f"Ext moy buts: {away_form.get('avg_total_goals', 0):.1f}")
    if h2h.get("h2h_matches", 0) >= 3:
        reasons.append(f"H2H moy buts: {h2h.get('avg_total_goals', 0):.1f}")

    return {
        "bet": bet,
        "confidence": round(confidence, 3),
        "label": label,
        "reason": " | ".join(reasons),
        "expected_goals": avg_expected,
    }


def recommend_result(home_form: dict, away_form: dict, h2h: dict, home_name: str, away_name: str) -> dict:
    """
    Recommande le résultat 1X2.
    Score basé sur win rate, goals, H2H.
    """
    home_score = 0.0
    away_score = 0.0
    draw_score = 0.0

    # Forme: win rate
    if home_form.get("matches", 0) >= 3:
        home_score += home_form["win_rate"] * 3
        draw_score += home_form["draws"] / home_form["matches"] * 1.5
        # Avantage domicile classique
        home_score += 0.10

    if away_form.get("matches", 0) >= 3:
        away_score += away_form["win_rate"] * 3
        draw_score += away_form["draws"] / away_form["matches"] * 1.5

    # Forme offensive vs défensive
    if home_form.get("matches", 0) >= 3 and away_form.get("matches", 0) >= 3:
        # Domicile attaque forte + défense away faible
        if home_form["avg_goals_for"] > away_form["avg_goals_against"]:
            home_score += 0.3
        if away_form["avg_goals_for"] > home_form["avg_goals_against"]:
            away_score += 0.3

    # H2H win rate
    if h2h.get("h2h_matches", 0) >= 3:
        home_score += h2h["home_team_win_rate"] * 2
        away_score += (1 - h2h["home_team_win_rate"]) * 2

    total = home_score + away_score + draw_score
    if total == 0:
        return {
            "bet": "1X2",
            "confidence": 0.0,
            "label": "INSUFFISANT",
            "reason": "Données insuffisantes",
            "winner": "?",
        }

    home_prob = home_score / total
    away_prob = away_score / total
    draw_prob = draw_score / total

    if home_prob >= away_prob and home_prob >= draw_prob:
        winner = home_name
        bet = "1 (Victoire domicile)"
        confidence = home_prob
    elif away_prob >= home_prob and away_prob >= draw_prob:
        winner = away_name
        bet = "2 (Victoire extérieur)"
        confidence = away_prob
    else:
        winner = "Nul"
        bet = "X (Match nul)"
        confidence = draw_prob

    label = _confidence_label(confidence)
    reasons = []
    if home_form.get("matches", 0) >= 3:
        reasons.append(f"Dom win%: {home_form['win_rate']*100:.0f}%")
    if away_form.get("matches", 0) >= 3:
        reasons.append(f"Ext win%: {away_form['win_rate']*100:.0f}%")
    if h2h.get("h2h_matches", 0) >= 3:
        reasons.append(f"H2H dom win%: {h2h['home_team_win_rate']*100:.0f}%")

    return {
        "bet": bet,
        "confidence": round(confidence, 3),
        "label": label,
        "reason": " | ".join(reasons),
        "winner": winner,
        "home_prob": round(home_prob, 3),
        "draw_prob": round(draw_prob, 3),
        "away_prob": round(away_prob, 3),
    }


def generate_recommendations(event: dict) -> dict:
    """
    Point d'entrée principal.
    Génère toutes les recommandations pour un match.
    """
    analysis = analyze_match(event)
    info = analysis["match_info"]
    home_form = analysis["home_form"]
    away_form = analysis["away_form"]
    h2h = analysis["h2h"]

    home_name = info["home_team"]
    away_name = info["away_team"]

    recs = {
        "match": f"{home_name} vs {away_name}",
        "date": info["match_date"],
        "tournament": f"{info['category']} - {info['tournament']}",
        "result": recommend_result(home_form, away_form, h2h, home_name, away_name),
        "btts": recommend_btts(home_form, away_form, h2h),
        "over_1_5": recommend_over_under(home_form, away_form, h2h, line=1.5),
        "over_2_5": recommend_over_under(home_form, away_form, h2h, line=2.5),
        "over_3_5": recommend_over_under(home_form, away_form, h2h, line=3.5),
        "home_form_summary": {
            "team": home_name,
            "matches": home_form.get("matches", 0),
            "form": home_form.get("form_string", ""),
            "avg_goals_for": home_form.get("avg_goals_for", 0),
            "avg_goals_against": home_form.get("avg_goals_against", 0),
        },
        "away_form_summary": {
            "team": away_name,
            "matches": away_form.get("matches", 0),
            "form": away_form.get("form_string", ""),
            "avg_goals_for": away_form.get("avg_goals_for", 0),
            "avg_goals_against": away_form.get("avg_goals_against", 0),
        },
        "h2h_summary": {
            "matches": h2h.get("h2h_matches", 0),
            "avg_goals": h2h.get("avg_total_goals", 0),
            "btts_rate": h2h.get("btts_rate", 0),
        },
    }
    return recs
