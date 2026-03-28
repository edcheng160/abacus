"""
Japan F1 Grand Prix Prediction Model — 2026 Season
Suzuka International Racing Course | March 29, 2026

Data sources:
  - Race results: Australia R1 + China R2 (actual 2026 results)
  - Practice data: FP1 + FP2 from Suzuka (March 27, 2026)
"""

import math
import random
from typing import Optional


# ---------------------------------------------------------------------------
# ACTUAL 2026 RACE RESULTS (used to compute form scores)
# Points: 25-18-15-12-10-8-6-4-2-1, DNF/DNS = 0
# ---------------------------------------------------------------------------

RACE_RESULTS_2026 = {
    "Australia": {
        "race": {
            "George Russell":    {"pos": 1,  "grid": 1,  "points": 25, "status": "Finished"},
            "Kimi Antonelli":    {"pos": 2,  "grid": 2,  "points": 18, "status": "Finished"},
            "Charles Leclerc":   {"pos": 3,  "grid": 4,  "points": 15, "status": "Finished"},
            "Lewis Hamilton":    {"pos": 4,  "grid": 7,  "points": 12, "status": "Finished"},
            "Lando Norris":      {"pos": 5,  "grid": 6,  "points": 10, "status": "Finished"},
            "Max Verstappen":    {"pos": 6,  "grid": 20, "points":  8, "status": "Finished"},  # +FL bonus included
            "Oliver Bearman":    {"pos": 7,  "grid": 12, "points":  6, "status": "Finished"},
            "Arvid Lindblad":    {"pos": 8,  "grid": 9,  "points":  4, "status": "Finished"},
            "Gabriel Bortoleto": {"pos": 9,  "grid": 10, "points":  2, "status": "Finished"},
            "Pierre Gasly":      {"pos": 10, "grid": 14, "points":  1, "status": "Finished"},
            "Esteban Ocon":      {"pos": 11, "grid": 13, "points":  0, "status": "Finished"},
            "Alex Albon":        {"pos": 12, "grid": 15, "points":  0, "status": "Finished"},
            "Liam Lawson":       {"pos": 13, "grid": 8,  "points":  0, "status": "Finished"},
            "Franco Colapinto":  {"pos": 14, "grid": 16, "points":  0, "status": "Finished"},
            "Carlos Sainz":      {"pos": 15, "grid": 21, "points":  0, "status": "Finished"},
            "Sergio Perez":      {"pos": 16, "grid": 18, "points":  0, "status": "Finished"},
            "Lance Stroll":      {"pos": 17, "grid": 22, "points":  0, "status": "DNF"},
            "Fernando Alonso":   {"pos": 18, "grid": 17, "points":  0, "status": "DNF"},
            "Valtteri Bottas":   {"pos": 19, "grid": 19, "points":  0, "status": "DNF"},
            "Isack Hadjar":      {"pos": 20, "grid": 3,  "points":  0, "status": "DNF"},
            "Oscar Piastri":     {"pos": 21, "grid": 5,  "points":  0, "status": "DNS"},
            "Nico Hulkenberg":   {"pos": 22, "grid": 11, "points":  0, "status": "DNS"},
        }
    },
    "China": {
        "sprint": {
            "George Russell":    {"pos": 1, "points": 8},
            "Charles Leclerc":   {"pos": 2, "points": 7},
            "Lewis Hamilton":    {"pos": 3, "points": 6},
            "Lando Norris":      {"pos": 4, "points": 5},
            "Kimi Antonelli":    {"pos": 5, "points": 4},  # 10s penalty already served
            "Oscar Piastri":     {"pos": 6, "points": 3},
            "Liam Lawson":       {"pos": 7, "points": 2},
            "Oliver Bearman":    {"pos": 8, "points": 1},
            "Max Verstappen":    {"pos": 9, "points": 0},
        },
        "race": {
            "Kimi Antonelli":    {"pos": 1,  "grid": 1,  "points": 25, "status": "Finished"},
            "George Russell":    {"pos": 2,  "grid": 2,  "points": 18, "status": "Finished"},
            "Lewis Hamilton":    {"pos": 3,  "grid": 3,  "points": 15, "status": "Finished"},
            "Charles Leclerc":   {"pos": 4,  "grid": 4,  "points": 12, "status": "Finished"},
            "Oliver Bearman":    {"pos": 5,  "grid": 10, "points": 10, "status": "Finished"},
            "Pierre Gasly":      {"pos": 6,  "grid": 7,  "points":  8, "status": "Finished"},
            "Liam Lawson":       {"pos": 7,  "grid": 14, "points":  6, "status": "Finished"},
            "Isack Hadjar":      {"pos": 8,  "grid": 9,  "points":  4, "status": "Finished"},
            "Carlos Sainz":      {"pos": 9,  "grid": 17, "points":  2, "status": "Finished"},
            "Franco Colapinto":  {"pos": 10, "grid": 12, "points":  1, "status": "Finished"},
            "Nico Hulkenberg":   {"pos": 11, "grid": 11, "points":  0, "status": "Finished"},
            "Arvid Lindblad":    {"pos": 12, "grid": 15, "points":  0, "status": "Finished"},
            "Valtteri Bottas":   {"pos": 13, "grid": 20, "points":  0, "status": "Finished"},
            "Esteban Ocon":      {"pos": 14, "grid": 13, "points":  0, "status": "Finished"},  # 10s penalty
            "Sergio Perez":      {"pos": 15, "grid": 22, "points":  0, "status": "Finished"},
            "Max Verstappen":    {"pos": 16, "grid": 8,  "points":  0, "status": "DNF"},
            "Fernando Alonso":   {"pos": 17, "grid": 19, "points":  0, "status": "DNF"},
            "Lance Stroll":      {"pos": 18, "grid": 21, "points":  0, "status": "DNF"},
            "Lando Norris":      {"pos": 19, "grid": 6,  "points":  0, "status": "DNS"},
            "Oscar Piastri":     {"pos": 20, "grid": 5,  "points":  0, "status": "DNS"},
            "Gabriel Bortoleto": {"pos": 21, "grid": 16, "points":  0, "status": "DNS"},
            "Alex Albon":        {"pos": 22, "grid": 18, "points":  0, "status": "DNS"},
        }
    }
}

# Actual 2026 championship standings after Round 2
STANDINGS_2026 = {
    "George Russell":    51,
    "Kimi Antonelli":    47,
    "Charles Leclerc":   34,
    "Lewis Hamilton":    33,
    "Oliver Bearman":    17,
    "Lando Norris":      15,
    "Pierre Gasly":       9,
    "Max Verstappen":     8,
    "Liam Lawson":        8,
    "Arvid Lindblad":     4,
    "Isack Hadjar":       4,
    "Oscar Piastri":      3,
    "Carlos Sainz":       2,
    "Gabriel Bortoleto":  2,
    "Franco Colapinto":   1,
    "Esteban Ocon":       0,
    "Nico Hulkenberg":    0,
    "Alex Albon":         0,
    "Valtteri Bottas":    0,
    "Sergio Perez":       0,
    "Fernando Alonso":    0,
    "Lance Stroll":       0,
}

# ---------------------------------------------------------------------------
# 2026 DRIVER LINEUP
# Base ratings updated from pre-season expectations + 2026 early evidence
# ---------------------------------------------------------------------------
DRIVERS_2026 = [
    # Mercedes — dominant car, both drivers performing
    {
        "name": "George Russell",
        "team": "Mercedes",
        "number": 63,
        "skill": 90,
        "suzuka_affinity": 78,
        "wet_weather": 85,
        "consistency": 91,
        "overtaking": 80,
    },
    {
        "name": "Kimi Antonelli",
        "team": "Mercedes",
        "number": 12,
        "skill": 86,
        "suzuka_affinity": 62,   # limited Suzuka history
        "wet_weather": 76,
        "consistency": 82,
        "overtaking": 80,
    },
    # Ferrari — strong second, Hamilton in fine form
    {
        "name": "Lewis Hamilton",
        "team": "Ferrari",
        "number": 44,
        "skill": 91,
        "suzuka_affinity": 88,   # 4 Suzuka wins (2015-18)
        "wet_weather": 90,
        "consistency": 86,
        "overtaking": 83,
    },
    {
        "name": "Charles Leclerc",
        "team": "Ferrari",
        "number": 16,
        "skill": 89,
        "suzuka_affinity": 76,
        "wet_weather": 82,
        "consistency": 81,
        "overtaking": 80,
    },
    # McLaren — fast car but catastrophic reliability in 2026 so far
    {
        "name": "Lando Norris",
        "team": "McLaren",
        "number": 4,
        "skill": 91,             # reigning world champion
        "suzuka_affinity": 79,
        "wet_weather": 83,
        "consistency": 78,       # penalised by car unreliability
        "overtaking": 85,
    },
    {
        "name": "Oscar Piastri",
        "team": "McLaren",
        "number": 81,
        "skill": 86,
        "suzuka_affinity": 70,
        "wet_weather": 79,
        "consistency": 75,       # penalised by car unreliability
        "overtaking": 79,
    },
    # Red Bull — Verstappen driving brilliantly but car is struggling
    {
        "name": "Max Verstappen",
        "team": "Red Bull Racing",
        "number": 1,
        "skill": 97,
        "suzuka_affinity": 92,   # 3 Suzuka wins (2022-24)
        "wet_weather": 93,
        "consistency": 88,       # car DNF risk hurts
        "overtaking": 92,
    },
    {
        "name": "Isack Hadjar",
        "team": "Red Bull Racing",
        "number": 6,
        "skill": 78,
        "suzuka_affinity": 62,
        "wet_weather": 70,
        "consistency": 72,
        "overtaking": 74,
    },
    # Racing Bulls
    {
        "name": "Liam Lawson",
        "team": "Racing Bulls",
        "number": 30,
        "skill": 80,
        "suzuka_affinity": 65,
        "wet_weather": 74,
        "consistency": 76,
        "overtaking": 76,
    },
    {
        "name": "Arvid Lindblad",
        "team": "Racing Bulls",
        "number": 58,
        "skill": 75,             # impressive debut P8 Australia
        "suzuka_affinity": 55,
        "wet_weather": 68,
        "consistency": 68,
        "overtaking": 72,
    },
    # Haas — surprisingly strong in 2026
    {
        "name": "Oliver Bearman",
        "team": "Haas",
        "number": 87,
        "skill": 81,             # P7 Australia, P5 China — upgraded
        "suzuka_affinity": 62,
        "wet_weather": 72,
        "consistency": 76,
        "overtaking": 74,
    },
    {
        "name": "Esteban Ocon",
        "team": "Haas",
        "number": 31,
        "skill": 77,
        "suzuka_affinity": 68,
        "wet_weather": 74,
        "consistency": 73,
        "overtaking": 71,
    },
    # Alpine
    {
        "name": "Pierre Gasly",
        "team": "Alpine",
        "number": 10,
        "skill": 79,
        "suzuka_affinity": 70,
        "wet_weather": 76,
        "consistency": 75,
        "overtaking": 74,
    },
    {
        "name": "Franco Colapinto",
        "team": "Alpine",
        "number": 43,
        "skill": 76,
        "suzuka_affinity": 58,
        "wet_weather": 70,
        "consistency": 70,
        "overtaking": 73,
    },
    # Audi (formerly Sauber)
    {
        "name": "Nico Hulkenberg",
        "team": "Audi",
        "number": 27,
        "skill": 77,
        "suzuka_affinity": 66,
        "wet_weather": 75,
        "consistency": 72,
        "overtaking": 71,
    },
    {
        "name": "Gabriel Bortoleto",
        "team": "Audi",
        "number": 5,
        "skill": 76,
        "suzuka_affinity": 60,
        "wet_weather": 70,
        "consistency": 68,       # reliability issues so far
        "overtaking": 74,
    },
    # Williams
    {
        "name": "Alex Albon",
        "team": "Williams",
        "number": 23,
        "skill": 79,
        "suzuka_affinity": 67,
        "wet_weather": 76,
        "consistency": 70,       # hydraulics DNS China
        "overtaking": 73,
    },
    {
        "name": "Carlos Sainz",
        "team": "Williams",
        "number": 55,
        "skill": 85,
        "suzuka_affinity": 73,
        "wet_weather": 81,
        "consistency": 82,
        "overtaking": 77,
    },
    # Aston Martin — scoreless both races, both cars DNF/DNF
    {
        "name": "Fernando Alonso",
        "team": "Aston Martin",
        "number": 14,
        "skill": 87,
        "suzuka_affinity": 80,   # 2006 Suzuka winner
        "wet_weather": 88,
        "consistency": 72,       # car failures drag this down
        "overtaking": 86,
    },
    {
        "name": "Lance Stroll",
        "team": "Aston Martin",
        "number": 18,
        "skill": 72,
        "suzuka_affinity": 58,
        "wet_weather": 68,
        "consistency": 62,       # DNF both races
        "overtaking": 65,
    },
    # Cadillac (new 11th team)
    {
        "name": "Sergio Perez",
        "team": "Cadillac",
        "number": 11,
        "skill": 76,
        "suzuka_affinity": 70,
        "wet_weather": 72,
        "consistency": 70,
        "overtaking": 72,
    },
    {
        "name": "Valtteri Bottas",
        "team": "Cadillac",
        "number": 77,
        "skill": 74,
        "suzuka_affinity": 72,
        "wet_weather": 75,
        "consistency": 68,
        "overtaking": 68,
    },
]

# ---------------------------------------------------------------------------
# 2026 TEAM CAR RATINGS — base from Australia+China, refined by Suzuka FP2
# FP2 order: McLaren > Mercedes > Ferrari >> Audi ~ Williams ~ Haas > RB ...
# ---------------------------------------------------------------------------
TEAM_CAR_2026 = {
    "Mercedes":       {"pace": 96, "reliability": 94, "tire_management": 93, "downforce": 94},
    "Ferrari":        {"pace": 90, "reliability": 88, "tire_management": 89, "downforce": 90},
    "McLaren":        {"pace": 95, "reliability": 62, "tire_management": 91, "downforce": 92},  # fastest at Suzuka, still unreliable
    "Red Bull Racing":{"pace": 83, "reliability": 74, "tire_management": 86, "downforce": 87},  # understeer at Suzuka, FP2 P10
    "Haas":           {"pace": 82, "reliability": 84, "tire_management": 80, "downforce": 79},
    "Racing Bulls":   {"pace": 80, "reliability": 80, "tire_management": 79, "downforce": 80},  # Lindblad gearbox issues
    "Alpine":         {"pace": 79, "reliability": 83, "tire_management": 78, "downforce": 77},
    "Audi":           {"pace": 79, "reliability": 76, "tire_management": 76, "downforce": 75},  # Hulkenberg P7 FP2
    "Williams":       {"pace": 79, "reliability": 78, "tire_management": 78, "downforce": 77},  # Albon P8 FP2
    "Aston Martin":   {"pace": 72, "reliability": 68, "tire_management": 71, "downforce": 71},  # 3.5s+ off pace
    "Cadillac":       {"pace": 67, "reliability": 72, "tire_management": 66, "downforce": 65},
}

# ---------------------------------------------------------------------------
# JAPAN FP1 — Friday March 27 | Fastest: Russell 1:31.666
# Gaps in seconds. None = no representative time set.
# ---------------------------------------------------------------------------
FP1_GAPS: dict[str, float | None] = {
    "George Russell":    0.000,
    "Kimi Antonelli":    0.026,
    "Lando Norris":      0.132,
    "Oscar Piastri":     0.199,
    "Charles Leclerc":   0.289,
    "Lewis Hamilton":    0.374,
    "Max Verstappen":    None,   # sandbagging — only long runs, ignore
    "Liam Lawson":       0.863,
    "Esteban Ocon":      0.935,
    "Arvid Lindblad":    0.999,
    "Gabriel Bortoleto": 1.093,
    "Nico Hulkenberg":   1.132,
    "Isack Hadjar":      1.137,
    "Oliver Bearman":    1.234,
    "Pierre Gasly":      1.312,
    "Franco Colapinto":  1.695,
    "Carlos Sainz":      1.717,
    "Alex Albon":        2.031,
    "Sergio Perez":      2.555,
    "Valtteri Bottas":   2.824,
    "Lance Stroll":      3.628,
    "Fernando Alonso":   None,   # Crawford drove (mandatory rookie sub — Alonso at birth of child)
}

# ---------------------------------------------------------------------------
# JAPAN FP2 — Friday March 27 | Fastest: Piastri 1:30.133
# Most representative session for qualifying pace (track rubbered in, soft tyres)
# ---------------------------------------------------------------------------
FP2_GAPS: dict[str, float | None] = {
    "Oscar Piastri":     0.000,
    "Kimi Antonelli":    0.092,
    "George Russell":    0.205,
    "Lando Norris":      0.516,
    "Charles Leclerc":   0.713,
    "Lewis Hamilton":    0.847,
    "Nico Hulkenberg":   1.308,
    "Alex Albon":        1.363,
    "Oliver Bearman":    1.365,
    "Max Verstappen":    1.376,
    "Esteban Ocon":      1.399,
    "Liam Lawson":       1.457,
    "Carlos Sainz":      1.475,
    "Pierre Gasly":      1.601,
    "Isack Hadjar":      1.626,
    "Gabriel Bortoleto": 1.800,
    "Franco Colapinto":  2.305,
    "Valtteri Bottas":   2.482,
    "Fernando Alonso":   3.463,
    "Sergio Perez":      3.556,
    "Lance Stroll":      3.818,
    "Arvid Lindblad":    None,   # gearbox failure — no time set
}

# ---------------------------------------------------------------------------
# JAPAN FP3 — Saturday March 28 | Fastest: Antonelli 1:29.362
# Mercedes showed clear step — first driver under 1:30 all weekend.
# FIA reduced qualifying energy recharge limit 9.0→8.0 MJ (super clipping fix).
# ---------------------------------------------------------------------------
FP3_GAPS: dict[str, float | None] = {
    "Kimi Antonelli":    0.000,
    "George Russell":    0.254,
    "Charles Leclerc":   0.867,
    "Oscar Piastri":     1.002,
    "Lewis Hamilton":    1.021,
    "Lando Norris":      1.238,   # battery change — only ~22 min of session
    "Nico Hulkenberg":   1.296,
    "Max Verstappen":    1.548,
    "Gabriel Bortoleto": 1.638,
    "Pierre Gasly":      1.720,
    "Isack Hadjar":      1.732,
    "Liam Lawson":       1.735,
    "Arvid Lindblad":    1.926,
    "Esteban Ocon":      1.964,
    "Oliver Bearman":    2.196,
    "Alex Albon":        2.371,
    "Franco Colapinto":  2.397,
    "Carlos Sainz":      2.467,
    "Valtteri Bottas":   3.141,
    "Sergio Perez":      3.178,
    "Lance Stroll":      4.123,
    "Fernando Alonso":   4.167,
}

# Notable incidents across all practice sessions
PRACTICE_INCIDENTS = [
    # FP3
    "FP3: Antonelli (Mercedes) broke 1:30 barrier — clear Mercedes step vs FP1/FP2",
    "FP3: Norris battery change — only 22 min on track (P6), 3rd McLaren reliability issue",
    "FP3: Hulkenberg P7, Bortoleto P9 — both Audis sandwiching Verstappen (P8)",
    "FP3: Verstappen P8 (+1.548s) — Red Bull understeer unresolved heading into qualifying",
    "FP3: Piastri under investigation for impeding Hulkenberg at 130R",
    "FP3: FIA cut qualifying energy recharge limit 9.0→8.0 MJ to stop 'super clipping'",
    # FP2
    "FP2: Norris hydraulics scare (garage 23min) — McLaren reliability repeated concern",
    "FP2: Albon P8 — Williams strong; contact with Perez in FP1 under investigation",
    "FP2: Colapinto under investigation for impeding Verstappen on timed lap",
    "FP2: Hamilton radio — 'no confidence in the car' during long runs",
    # FP1
    "FP1: Alonso missed session — Crawford subbed (birth of child); Alonso returned FP2",
    "FP1: Lindblad gearbox failure FP2 — limited data, grid position risk",
]


def _gap_to_adjustment(gap: float | None, scale: float = 4.0) -> float:
    """
    Convert a lap time gap (seconds behind fastest) to a score adjustment.
    0.0s gap → +8.0 | 2.0s → 0.0 | 4.0s → -8.0 | None → 0.0 (neutral)
    """
    if gap is None:
        return 0.0
    return max(-10.0, 8.0 - gap * scale)


def _compute_practice_scores() -> dict[str, float]:
    """
    Weighted average of FP1/FP2/FP3 pace adjustments.
    FP3 weight 3.0 — closest to qualifying, rubbered track, full soft-tyre effort.
    FP2 weight 2.0 — representative soft-tyre runs.
    FP1 weight 1.0 — early session, green track, less representative.
    Returns adjustment in the same -10..+8 range as gap_to_adjustment.
    """
    scores: dict[str, float] = {}
    for driver in DRIVERS_2026:
        name = driver["name"]
        fp1_adj = _gap_to_adjustment(FP1_GAPS.get(name))
        fp2_adj = _gap_to_adjustment(FP2_GAPS.get(name))
        fp3_adj = _gap_to_adjustment(FP3_GAPS.get(name))
        fp1_has = FP1_GAPS.get(name) is not None
        fp2_has = FP2_GAPS.get(name) is not None
        fp3_has = FP3_GAPS.get(name) is not None

        total_w = (1.0 * fp1_has) + (2.0 * fp2_has) + (3.0 * fp3_has)
        if total_w == 0:
            scores[name] = 0.0
            continue

        weighted = (1.0 * fp1_adj * fp1_has +
                    2.0 * fp2_adj * fp2_has +
                    3.0 * fp3_adj * fp3_has) / total_w
        scores[name] = round(weighted, 2)

    return scores



PRACTICE_SCORES = _compute_practice_scores()

# ---------------------------------------------------------------------------
# FORM SCORE: points-per-race vs field average, weighted recent > older
# Weight: China race=3, China sprint=1.5, Australia race=2
# ---------------------------------------------------------------------------
def _compute_form_scores() -> dict[str, float]:
    """
    Returns a form adjustment per driver (-8 to +8 range) based on
    actual 2026 results vs expected finishing position.
    """
    weights = {"aus_race": 2.0, "chn_sprint": 1.5, "chn_race": 3.0}
    total_w = sum(weights.values())
    max_points = {"aus_race": 25, "chn_sprint": 8, "chn_race": 25}

    scores: dict[str, float] = {}
    for driver in DRIVERS_2026:
        name = driver["name"]
        aus = RACE_RESULTS_2026["Australia"]["race"].get(name, {})
        chn_s = RACE_RESULTS_2026["China"]["sprint"].get(name, {})
        chn_r = RACE_RESULTS_2026["China"]["race"].get(name, {})

        aus_pts = aus.get("points", 0)
        chn_s_pts = chn_s.get("points", 0)
        chn_r_pts = chn_r.get("points", 0)

        # Normalise each session 0-1
        norm = (
            weights["aus_race"]   * (aus_pts   / max_points["aus_race"]) +
            weights["chn_sprint"] * (chn_s_pts / max_points["chn_sprint"]) +
            weights["chn_race"]   * (chn_r_pts / max_points["chn_race"])
        ) / total_w

        # Also penalise DNS/DNFs
        dnf_count = sum(
            1 for r in [aus, chn_r]
            if r.get("status", "") in ("DNF", "DNS")
        )

        # Scale to -8..+8 adjustment on base score
        form = (norm * 16) - 2 - (dnf_count * 1.5)
        scores[name] = round(form, 2)

    return scores

FORM_SCORES = _compute_form_scores()

# ---------------------------------------------------------------------------
# SUZUKA CIRCUIT CHARACTERISTICS
# ---------------------------------------------------------------------------
SUZUKA_FACTORS = {
    "circuit_type": "technical",
    "lap_length_km": 5.807,
    "race_laps": 53,
    "drs_zones": 1,
    "overtaking_difficulty": 0.85,
    "tire_degradation": "medium",
    "weather_variability": 0.25,
    "pole_to_win_rate": 0.55,
}


def _weighted_score(driver: dict, car: dict, grid_pos: int,
                    weather: str, safety_car_prob: float,
                    form_weight: float = 0.15,
                    practice_weight: float = 0.15) -> float:
    """
    Composite performance score blending base ratings + 2026 form + practice pace.
    """
    driver_score = (
        0.35 * driver["skill"] +
        0.25 * driver["suzuka_affinity"] +
        0.20 * driver["consistency"] +
        0.10 * driver["overtaking"] +
        0.10 * driver["wet_weather"]
    )

    car_score = (
        0.40 * car["pace"] +
        0.25 * car["tire_management"] +
        0.20 * car["downforce"] +
        0.15 * car["reliability"]
    )

    base = 0.60 * driver_score + 0.40 * car_score

    # Blend in recent championship form
    form = FORM_SCORES.get(driver["name"], 0.0)
    # Blend in Suzuka practice pace (most circuit-specific signal)
    practice = PRACTICE_SCORES.get(driver["name"], 0.0)
    combined = base + form_weight * form * 10 + practice_weight * practice * 10

    # Grid position adjustment (Suzuka: very hard to overtake)
    od = SUZUKA_FACTORS["overtaking_difficulty"]
    if grid_pos == 1:
        grid_bonus = 8.0
    elif grid_pos == 2:
        grid_bonus = 5.0
    elif grid_pos <= 5:
        grid_bonus = (6 - grid_pos) * 1.5
    elif grid_pos <= 10:
        grid_bonus = -(grid_pos - 5) * 1.2 * od
    else:
        grid_bonus = -(grid_pos - 5) * 2.0 * od

    # Weather modifier
    if weather == "wet":
        combined += (driver["wet_weather"] - 75) * 0.15
    elif weather == "mixed":
        combined += (driver["wet_weather"] - 75) * 0.07

    # Safety car bunching effect
    sc_eq = safety_car_prob * 5.0 * (1 - (grid_pos / 22))

    score = combined + grid_bonus + sc_eq
    score += random.gauss(0, 2.5)
    return score


def simulate_race(
    qualifying_order: Optional[list[str]] = None,
    weather: str = "dry",
    safety_car_probability: float = 0.35,
    seed: Optional[int] = None,
) -> list[dict]:
    """
    Simulate the Japan GP and return a predicted finishing order.

    Args:
        qualifying_order: Grid order (P1 first). If None, predicted from pace.
        weather: 'dry', 'wet', or 'mixed'
        safety_car_probability: 0.0-1.0
        seed: For reproducibility

    Returns:
        List of result dicts sorted P1..P22.
    """
    if seed is not None:
        random.seed(seed)

    driver_map = {d["name"]: d for d in DRIVERS_2026}

    if qualifying_order is None:
        predicted_quali = sorted(
            DRIVERS_2026,
            key=lambda d: (
                0.50 * TEAM_CAR_2026[d["team"]]["pace"] +
                0.30 * d["skill"] +
                0.20 * d["suzuka_affinity"] +
                random.gauss(0, 1.5)
            ),
            reverse=True,
        )
        qualifying_order = [d["name"] for d in predicted_quali]

    results = []
    for grid_pos, name in enumerate(qualifying_order, start=1):
        if name not in driver_map:
            continue
        driver = driver_map[name]
        car = TEAM_CAR_2026[driver["team"]]
        score = _weighted_score(driver, car, grid_pos, weather, safety_car_probability)

        # Reliability-based DNF (McLaren and Aston Martin notably poor)
        reliability = car["reliability"] / 100.0
        dnf = random.random() > reliability * 0.97
        results.append({
            "name": name,
            "team": driver["team"],
            "number": driver["number"],
            "grid": grid_pos,
            "score": score,
            "dnf": dnf,
            "form": FORM_SCORES.get(name, 0.0),
            "champ_pts": STANDINGS_2026.get(name, 0),
        })

    finishers = sorted([r for r in results if not r["dnf"]], key=lambda x: x["score"], reverse=True)
    dnfs = [r for r in results if r["dnf"]]
    random.shuffle(dnfs)

    final = finishers + dnfs
    for pos, entry in enumerate(final, start=1):
        entry["position"] = pos
        entry["status"] = "DNF" if entry["dnf"] else f"P{pos}"

    return final


def run_monte_carlo(
    n_simulations: int = 10000,
    qualifying_order: Optional[list[str]] = None,
    weather: str = "dry",
    safety_car_probability: float = 0.35,
) -> dict:
    """Run N simulations and return win/podium/points probabilities."""
    win_counts: dict[str, int] = {d["name"]: 0 for d in DRIVERS_2026}
    podium_counts: dict[str, int] = {d["name"]: 0 for d in DRIVERS_2026}
    points_counts: dict[str, int] = {d["name"]: 0 for d in DRIVERS_2026}
    finish_totals: dict[str, int] = {d["name"]: 0 for d in DRIVERS_2026}
    dnf_counts: dict[str, int] = {d["name"]: 0 for d in DRIVERS_2026}

    for _ in range(n_simulations):
        result = simulate_race(
            qualifying_order=qualifying_order,
            weather=weather,
            safety_car_probability=safety_car_probability,
        )
        for entry in result:
            name = entry["name"]
            pos = entry["position"]
            if entry["dnf"]:
                dnf_counts[name] += 1
                finish_totals[name] += 22
            else:
                finish_totals[name] += pos
                if pos == 1:
                    win_counts[name] += 1
                if pos <= 3:
                    podium_counts[name] += 1
                if pos <= 10:
                    points_counts[name] += 1

    stats = {}
    for driver in DRIVERS_2026:
        name = driver["name"]
        stats[name] = {
            "team": driver["team"],
            "number": driver["number"],
            "win_pct": round(100 * win_counts[name] / n_simulations, 1),
            "podium_pct": round(100 * podium_counts[name] / n_simulations, 1),
            "points_pct": round(100 * points_counts[name] / n_simulations, 1),
            "avg_finish": round(finish_totals[name] / n_simulations, 2),
            "dnf_pct": round(100 * dnf_counts[name] / n_simulations, 1),
            "champ_pts": STANDINGS_2026.get(name, 0),
            "form": FORM_SCORES.get(name, 0.0),
        }

    return stats


def predict_qualifying() -> list[dict]:
    """
    Predict qualifying order for Japan 2026.
    FP3 is weighted highest (3x) — closest session to Q1/Q2/Q3 conditions.
    Combined practice score dominates (55%); car pace and driver skill fill the rest.
    """
    random.seed(42)
    scores = []
    for driver in DRIVERS_2026:
        car = TEAM_CAR_2026[driver["team"]]
        practice = PRACTICE_SCORES.get(driver["name"], 0.0)
        # Practice pace: 55% (FP3-dominated, best qualifying proxy)
        # Car pace: 22% | Driver skill: 15% | Suzuka affinity: 8%
        qual_score = (
            0.22 * car["pace"] +
            0.15 * driver["skill"] +
            0.08 * driver["suzuka_affinity"] +
            0.55 * (75 + practice * 2.5) +
            random.gauss(0, 0.8)
        )
        scores.append({
            "name": driver["name"],
            "team": driver["team"],
            "number": driver["number"],
            "qual_score": qual_score,
            "champ_pts": STANDINGS_2026.get(driver["name"], 0),
            "fp1_gap": FP1_GAPS.get(driver["name"]),
            "fp2_gap": FP2_GAPS.get(driver["name"]),
            "fp3_gap": FP3_GAPS.get(driver["name"]),
            "practice_score": practice,
        })

    scores.sort(key=lambda x: x["qual_score"], reverse=True)
    for pos, entry in enumerate(scores, start=1):
        entry["predicted_grid"] = pos

    return scores
