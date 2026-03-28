"""
Simulation Monte Carlo — Strategie Paris Sportifs (1 mois)
===========================================================
Simule 30 jours de paris en appliquant notre strategie
SANS connaitre les resultats a l'avance.

Donnees reelles utilisees (saison 2025/26) :
- Premier League : 2.93 buts/match en moyenne → Over 2.5 ≈ 58%
- Bundesliga     : 2.44 buts/match            → Over 2.5 ≈ 47%
- Ligue 1        : 2.60 buts/match            → Over 2.5 ≈ 51%
- Serie A        : 2.72 buts/match            → Over 2.5 ≈ 53%
- La Liga        : 2.58 buts/match            → Over 2.5 ≈ 50%
- Amicaux inter. : 2.80 buts/match            → Over 2.5 ≈ 55%
- BTTS rate moyen top 5 ligues               ≈ 52%
"""

import random
import json
from datetime import datetime, timedelta

random.seed(42)  # reproductible

# ─── Parametres de la strategie ─────────────────────────────────────────────

BANKROLL_INITIALE = 200.0   # euros
MISE_PAR_PARI     = 0.04    # 4% de la bankroll courante (Kelly conservateur)
JOURS_SIMULATION  = 30
PARIS_PAR_JOUR    = 2       # On vise 2 paris selectifs par jour

# Seuil minimal de confiance pour parier (notre algo exige > 60%)
SEUIL_CONFIANCE   = 0.60

# ─── Donnees reelles des ligues (saison 2025/26) ─────────────────────────────

LIGUES = [
    # (nom, over_2_5_rate_reel, btts_rate_reel, cote_over_2_5, cote_btts)
    ("Premier League",    0.58, 0.54, 1.75, 1.80),
    ("Bundesliga",        0.47, 0.51, 1.90, 1.85),
    ("Ligue 1",           0.51, 0.49, 1.85, 1.87),
    ("Serie A",           0.53, 0.52, 1.82, 1.83),
    ("La Liga",           0.50, 0.48, 1.87, 1.88),
    ("Champions League",  0.62, 0.57, 1.68, 1.72),
    ("Amicaux Inter.",    0.55, 0.53, 1.69, 1.81),
]

# Equipes offensives connues → notre algo detecte Over 2.5 FORT
MATCHS_FORT = [
    ("Bayern Munich", "Dortmund",      "Bundesliga",     0.71, 0.65, 1.65, 1.75),
    ("Man City",      "Arsenal",       "Premier League", 0.68, 0.62, 1.68, 1.78),
    ("PSG",           "Marseille",     "Ligue 1",        0.66, 0.60, 1.70, 1.80),
    ("Real Madrid",   "Atletico",      "La Liga",        0.63, 0.58, 1.72, 1.82),
    ("Napoli",        "Inter Milan",   "Serie A",        0.65, 0.61, 1.70, 1.79),
    ("Liverpool",     "Chelsea",       "Premier League", 0.70, 0.64, 1.66, 1.76),
    ("France",        "Colombie",      "Amicaux Inter.", 0.76, 0.68, 1.69, 1.81),
    ("Argentina",     "Mauritanie",    "Amicaux Inter.", 0.72, 0.55, 1.60, 2.00),
    ("Leipzig",       "Leverkusen",    "Bundesliga",     0.67, 0.63, 1.68, 1.77),
    ("Barcelona",     "Sevilla",       "La Liga",        0.64, 0.59, 1.71, 1.81),
    ("Man United",    "Tottenham",     "Premier League", 0.62, 0.58, 1.73, 1.83),
    ("Lyon",          "Monaco",        "Ligue 1",        0.61, 0.57, 1.74, 1.84),
    ("Juventus",      "Milan",         "Serie A",        0.60, 0.56, 1.75, 1.85),
    ("Dortmund",      "Gladbach",      "Bundesliga",     0.65, 0.60, 1.69, 1.79),
    ("Atletico",      "Villarreal",    "La Liga",        0.58, 0.53, 1.78, 1.88),
    ("Ajax",          "PSV",           "Eredivisie",     0.73, 0.66, 1.63, 1.74),
    ("Porto",         "Benfica",       "Liga Portugal",  0.61, 0.57, 1.73, 1.83),
    ("Celtic",        "Rangers",       "Premiership",    0.63, 0.59, 1.71, 1.82),
    ("Inter Milan",   "Atalanta",      "Serie A",        0.66, 0.62, 1.69, 1.79),
    ("Stuttgart",     "Bayern Munich", "Bundesliga",     0.68, 0.63, 1.67, 1.77),
]

# ─── Generateur de journee de paris ─────────────────────────────────────────

def generer_journee(jour: int):
    """
    Simule une journee : selectionne 2 matchs 'de qualite'
    selon notre strategie (confiance > 60%).
    """
    paris_jour = []
    pool = random.sample(MATCHS_FORT, min(6, len(MATCHS_FORT)))

    for match in pool:
        home, away, ligue, over_rate, btts_rate, cote_over, cote_btts = match

        # Notre algo calcule la confiance AVANT le match
        # (base sur la forme, H2H etc.) — on simule ici avec un bruit realiste
        confiance_estimee_over = over_rate + random.uniform(-0.08, 0.08)
        confiance_estimee_btts = btts_rate + random.uniform(-0.08, 0.08)

        # On choisit le meilleur type de pari
        if confiance_estimee_over >= SEUIL_CONFIANCE:
            pari = {
                "jour": jour,
                "match": f"{home} vs {away}",
                "ligue": ligue,
                "type": "Over 2.5",
                "confiance_algo": round(confiance_estimee_over, 3),
                "cote": cote_over,
                "proba_reelle": over_rate,  # ce qu'on ne connait PAS a l'avance
            }
            paris_jour.append(pari)
            if len(paris_jour) >= PARIS_PAR_JOUR:
                break

        elif confiance_estimee_btts >= SEUIL_CONFIANCE:
            pari = {
                "jour": jour,
                "match": f"{home} vs {away}",
                "ligue": ligue,
                "type": "BTTS Oui",
                "confiance_algo": round(confiance_estimee_btts, 3),
                "cote": cote_btts,
                "proba_reelle": btts_rate,
            }
            paris_jour.append(pari)
            if len(paris_jour) >= PARIS_PAR_JOUR:
                break

    return paris_jour


def simuler_resultat(pari: dict) -> bool:
    """
    Determine si le pari est gagnant selon la probabilite reelle du marche.
    On ne connait PAS ce resultat a l'avance.
    """
    return random.random() < pari["proba_reelle"]


# ─── Simulation principale ────────────────────────────────────────────────────

def run_simulation(n_runs: int = 1000):
    """
    Lance N simulations Monte Carlo independantes sur 30 jours.
    Retourne les statistiques agregees.
    """
    resultats_tous = []

    for run in range(n_runs):
        random.seed(run * 7 + 13)  # seed differente pour chaque run
        bankroll = BANKROLL_INITIALE
        historique = []
        total_paris = 0
        total_gagnes = 0
        jours_sans_pari = 0

        for jour in range(1, JOURS_SIMULATION + 1):
            paris = generer_journee(jour)

            if not paris:
                jours_sans_pari += 1
                continue

            for pari in paris:
                mise = round(bankroll * MISE_PAR_PARI, 2)
                if mise < 1.0 or bankroll < 10:
                    break

                gagne = simuler_resultat(pari)
                total_paris += 1

                if gagne:
                    profit = round(mise * (pari["cote"] - 1), 2)
                    bankroll = round(bankroll + profit, 2)
                    total_gagnes += 1
                else:
                    bankroll = round(bankroll - mise, 2)

                historique.append({
                    "jour": jour,
                    "match": pari["match"],
                    "type": pari["type"],
                    "cote": pari["cote"],
                    "mise": mise,
                    "gagne": gagne,
                    "bankroll": bankroll,
                })

        roi = (bankroll - BANKROLL_INITIALE) / BANKROLL_INITIALE * 100
        resultats_tous.append({
            "bankroll_finale": bankroll,
            "roi": round(roi, 2),
            "total_paris": total_paris,
            "total_gagnes": total_gagnes,
            "win_rate": round(total_gagnes / total_paris, 3) if total_paris > 0 else 0,
            "historique": historique if run == 0 else [],  # sauver seulement run 0
        })

    return resultats_tous


# ─── Affichage ────────────────────────────────────────────────────────────────

def afficher_rapport(resultats: list):
    bankrolls = [r["bankroll_finale"] for r in resultats]
    rois       = [r["roi"] for r in resultats]
    win_rates  = [r["win_rate"] for r in resultats]
    paris_tot  = [r["total_paris"] for r in resultats]

    positifs   = sum(1 for r in rois if r > 0)
    negatifs   = sum(1 for r in rois if r <= 0)

    print("\n" + "=" * 65)
    print("  SIMULATION MONTE CARLO — 1 MOIS DE PARIS")
    print(f"  {len(resultats)} simulations independantes | Bankroll: {BANKROLL_INITIALE}€")
    print(f"  Mise: {int(MISE_PAR_PARI*100)}% par pari | Seuil confiance: {int(SEUIL_CONFIANCE*100)}%")
    print("=" * 65)

    print(f"\n  ── RESULTATS AGREGÉS ({len(resultats)} simulations) ──────────────")
    print(f"  Bankroll finale moyenne  : {sum(bankrolls)/len(bankrolls):.2f}€")
    print(f"  Bankroll finale mediane  : {sorted(bankrolls)[len(bankrolls)//2]:.2f}€")
    print(f"  Meilleur scenario        : +{max(bankrolls)-BANKROLL_INITIALE:.2f}€  ({max(rois):.1f}%)")
    print(f"  Pire scenario            : {min(bankrolls)-BANKROLL_INITIALE:.2f}€  ({min(rois):.1f}%)")
    print(f"  ROI moyen                : {sum(rois)/len(rois):.2f}%")
    print(f"  Simulations beneficiaires: {positifs}/{len(resultats)}  ({positifs/len(resultats)*100:.1f}%)")
    print(f"  Simulations deficitaires : {negatifs}/{len(resultats)}  ({negatifs/len(resultats)*100:.1f}%)")
    print(f"  Win rate moyen           : {sum(win_rates)/len(win_rates)*100:.1f}%")
    print(f"  Nombre de paris/mois moy : {sum(paris_tot)/len(paris_tot):.0f}")

    # Distribution des ROI
    print(f"\n  ── DISTRIBUTION DES ROI ───────────────────────────────")
    buckets = [
        ("< -20%",  lambda r: r < -20),
        ("-20 à -10%", lambda r: -20 <= r < -10),
        ("-10 à  0%",  lambda r: -10 <= r < 0),
        ("  0 à +10%", lambda r: 0 <= r < 10),
        ("+10 à +20%", lambda r: 10 <= r < 20),
        ("+20 à +30%", lambda r: 20 <= r < 30),
        (">  +30%",    lambda r: r >= 30),
    ]
    for label, cond in buckets:
        count = sum(1 for r in rois if cond(r))
        bar = "█" * (count // 10)
        print(f"  {label:15s}: {count:4d}  {bar}")

    # Detail du premier run (exemple concret)
    run0 = resultats[0]
    histo = run0["historique"]
    print(f"\n  ── EXEMPLE CONCRET (simulation #1) ────────────────────")
    print(f"  {'Jour':>4} | {'Match':<35} | {'Type':<10} | {'Cote':>5} | {'Mise':>6} | {'Res':>5} | {'Bankroll':>9}")
    print("  " + "-" * 84)
    for p in histo[:20]:
        res = "✓ WIN" if p["gagne"] else "✗ LOSE"
        print(f"  J{p['jour']:02d}  | {p['match']:<35} | {p['type']:<10} | {p['cote']:>5.2f} | {p['mise']:>5.2f}€ | {res:>5} | {p['bankroll']:>8.2f}€")
    if len(histo) > 20:
        print(f"  ... ({len(histo)-20} paris supplementaires)")
    print(f"\n  Bankroll finale (run #1): {run0['bankroll_finale']:.2f}€  |  ROI: {run0['roi']:.1f}%")
    print(f"  Paris: {run0['total_gagnes']}/{run0['total_paris']} gagnes  |  Win rate: {run0['win_rate']*100:.1f}%")

    # Percentiles
    sorted_rois = sorted(rois)
    n = len(sorted_rois)
    print(f"\n  ── PERCENTILES ROI ──────────────────────────────────")
    print(f"  P10 (pire  10%): {sorted_rois[n//10]:.1f}%")
    print(f"  P25            : {sorted_rois[n//4]:.1f}%")
    print(f"  P50 (mediane)  : {sorted_rois[n//2]:.1f}%")
    print(f"  P75            : {sorted_rois[3*n//4]:.1f}%")
    print(f"  P90 (meilleur 10%): {sorted_rois[9*n//10]:.1f}%")

    print(f"\n  ── CONCLUSION ────────────────────────────────────────")
    roi_moyen = sum(rois)/len(rois)
    if roi_moyen > 5:
        verdict = "STRATEGIE RENTABLE - Edge statistique positif"
    elif roi_moyen > 0:
        verdict = "STRATEGIE LEGEREMENT POSITIVE - A affiner"
    elif roi_moyen > -5:
        verdict = "STRATEGIE EQUILIBREE - Proche du seuil de rentabilite"
    else:
        verdict = "STRATEGIE DEFICITAIRE - Revoir les criteres de selection"
    print(f"  {verdict}")
    print(f"  ROI moyen sur 1 mois : {roi_moyen:.2f}%")
    print(f"  Gain/Perte moyen     : {(sum(bankrolls)/len(bankrolls)) - BANKROLL_INITIALE:.2f}€ sur {BANKROLL_INITIALE}€")
    print()


if __name__ == "__main__":
    print("  Lancement de la simulation (1000 runs x 30 jours)...")
    resultats = run_simulation(n_runs=1000)
    afficher_rapport(resultats)

    # Export JSON
    export = {
        "config": {
            "bankroll_initiale": BANKROLL_INITIALE,
            "mise_pct": MISE_PAR_PARI,
            "jours": JOURS_SIMULATION,
            "seuil_confiance": SEUIL_CONFIANCE,
        },
        "stats": {
            "roi_moyen": round(sum(r["roi"] for r in resultats) / len(resultats), 2),
            "bankroll_moyenne": round(sum(r["bankroll_finale"] for r in resultats) / len(resultats), 2),
            "win_rate_moyen": round(sum(r["win_rate"] for r in resultats) / len(resultats), 3),
            "pct_simulations_positives": round(sum(1 for r in resultats if r["roi"] > 0) / len(resultats) * 100, 1),
        }
    }
    with open("simulation_results.json", "w") as f:
        json.dump(export, f, indent=2)
    print("  Resultats exportes: simulation_results.json")
