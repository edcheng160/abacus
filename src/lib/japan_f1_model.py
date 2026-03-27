"""
Japan F1 Grand Prix Prediction Model
Suzuka International Racing Course

Uses historical race data, driver skill ratings, team performance,
qualifying positions, and circuit-specific factors to predict race outcomes.
"""

import math
import random
from typing import Optional


# --- Historical Suzuka GP Winner Data (2015-2024) ---
SUZUKA_WINNERS = {
    2015: {"driver": "Lewis Hamilton",    "team": "Mercedes",    "grid": 1},
    2016: {"driver": "Nico Rosberg",      "team": "Mercedes",    "grid": 2},
    2017: {"driver": "Lewis Hamilton",    "team": "Mercedes",    "grid": 1},
    2018: {"driver": "Lewis Hamilton",    "team": "Mercedes",    "grid": 1},
    2019: {"driver": "Valtteri Bottas",   "team": "Mercedes",    "grid": 2},
    2022: {"driver": "Max Verstappen",    "team": "Red Bull",    "grid": 1},
    2023: {"driver": "Max Verstappen",    "team": "Red Bull",    "grid": 1},
    2024: {"driver": "Max Verstappen",    "team": "Red Bull",    "grid": 1},
}

# --- 2025 Driver Lineup with base ratings (0-100) ---
# Ratings: overall_skill, suzuka_affinity, wet_weather, consistency, overtaking
DRIVERS_2025 = [
    {
        "name": "Max Verstappen",
        "team": "Red Bull Racing",
        "number": 1,
        "skill": 97,
        "suzuka_affinity": 95,   # 3 wins at Suzuka
        "wet_weather": 92,
        "consistency": 95,
        "overtaking": 88,
    },
    {
        "name": "Liam Lawson",
        "team": "Red Bull Racing",
        "number": 30,
        "skill": 78,
        "suzuka_affinity": 60,
        "wet_weather": 70,
        "consistency": 72,
        "overtaking": 75,
    },
    {
        "name": "Lewis Hamilton",
        "team": "Ferrari",
        "number": 44,
        "skill": 91,
        "suzuka_affinity": 88,   # 4 wins at Suzuka
        "wet_weather": 90,
        "consistency": 85,
        "overtaking": 82,
    },
    {
        "name": "Charles Leclerc",
        "team": "Ferrari",
        "number": 16,
        "skill": 89,
        "suzuka_affinity": 75,
        "wet_weather": 82,
        "consistency": 80,
        "overtaking": 80,
    },
    {
        "name": "George Russell",
        "team": "Mercedes",
        "number": 63,
        "skill": 86,
        "suzuka_affinity": 72,
        "wet_weather": 83,
        "consistency": 84,
        "overtaking": 78,
    },
    {
        "name": "Kimi Antonelli",
        "team": "Mercedes",
        "number": 12,
        "skill": 76,
        "suzuka_affinity": 55,
        "wet_weather": 70,
        "consistency": 72,
        "overtaking": 74,
    },
    {
        "name": "Lando Norris",
        "team": "McLaren",
        "number": 4,
        "skill": 90,
        "suzuka_affinity": 78,
        "wet_weather": 82,
        "consistency": 83,
        "overtaking": 84,
    },
    {
        "name": "Oscar Piastri",
        "team": "McLaren",
        "number": 81,
        "skill": 85,
        "suzuka_affinity": 70,
        "wet_weather": 78,
        "consistency": 82,
        "overtaking": 78,
    },
    {
        "name": "Fernando Alonso",
        "team": "Aston Martin",
        "number": 14,
        "skill": 87,
        "suzuka_affinity": 80,   # 2006 winner
        "wet_weather": 88,
        "consistency": 82,
        "overtaking": 85,
    },
    {
        "name": "Lance Stroll",
        "team": "Aston Martin",
        "number": 18,
        "skill": 72,
        "suzuka_affinity": 58,
        "wet_weather": 68,
        "consistency": 68,
        "overtaking": 65,
    },
    {
        "name": "Carlos Sainz",
        "team": "Williams",
        "number": 55,
        "skill": 84,
        "suzuka_affinity": 72,
        "wet_weather": 80,
        "consistency": 83,
        "overtaking": 76,
    },
    {
        "name": "Alexander Albon",
        "team": "Williams",
        "number": 23,
        "skill": 78,
        "suzuka_affinity": 65,
        "wet_weather": 74,
        "consistency": 76,
        "overtaking": 72,
    },
    {
        "name": "Nico Hulkenberg",
        "team": "Sauber",
        "number": 27,
        "skill": 76,
        "suzuka_affinity": 65,
        "wet_weather": 74,
        "consistency": 74,
        "overtaking": 70,
    },
    {
        "name": "Gabriel Bortoleto",
        "team": "Sauber",
        "number": 5,
        "skill": 74,
        "suzuka_affinity": 58,
        "wet_weather": 68,
        "consistency": 70,
        "overtaking": 72,
    },
    {
        "name": "Pierre Gasly",
        "team": "Alpine",
        "number": 10,
        "skill": 78,
        "suzuka_affinity": 68,
        "wet_weather": 75,
        "consistency": 74,
        "overtaking": 73,
    },
    {
        "name": "Jack Doohan",
        "team": "Alpine",
        "number": 7,
        "skill": 73,
        "suzuka_affinity": 58,
        "wet_weather": 66,
        "consistency": 68,
        "overtaking": 70,
    },
    {
        "name": "Yuki Tsunoda",
        "team": "RB",
        "number": 22,
        "skill": 79,
        "suzuka_affinity": 82,   # Home race boost
        "wet_weather": 76,
        "consistency": 72,
        "overtaking": 78,
    },
    {
        "name": "Isack Hadjar",
        "team": "RB",
        "number": 6,
        "skill": 74,
        "suzuka_affinity": 60,
        "wet_weather": 68,
        "consistency": 70,
        "overtaking": 73,
    },
    {
        "name": "Esteban Ocon",
        "team": "Haas",
        "number": 31,
        "skill": 76,
        "suzuka_affinity": 66,
        "wet_weather": 73,
        "consistency": 74,
        "overtaking": 70,
    },
    {
        "name": "Oliver Bearman",
        "team": "Haas",
        "number": 87,
        "skill": 74,
        "suzuka_affinity": 58,
        "wet_weather": 67,
        "consistency": 70,
        "overtaking": 71,
    },
]

# --- Team car performance ratings (0-100) ---
TEAM_CAR_2025 = {
    "Red Bull Racing": {"pace": 94, "reliability": 90, "tire_management": 92, "downforce": 92},
    "Ferrari":         {"pace": 91, "reliability": 86, "tire_management": 88, "downforce": 90},
    "McLaren":         {"pace": 92, "reliability": 88, "tire_management": 91, "downforce": 89},
    "Mercedes":        {"pace": 88, "reliability": 91, "tire_management": 89, "downforce": 87},
    "Aston Martin":    {"pace": 82, "reliability": 87, "tire_management": 83, "downforce": 84},
    "Williams":        {"pace": 80, "reliability": 85, "tire_management": 81, "downforce": 78},
    "RB":              {"pace": 79, "reliability": 83, "tire_management": 80, "downforce": 80},
    "Alpine":          {"pace": 78, "reliability": 82, "tire_management": 78, "downforce": 77},
    "Haas":            {"pace": 76, "reliability": 80, "tire_management": 77, "downforce": 75},
    "Sauber":          {"pace": 74, "reliability": 79, "tire_management": 76, "downforce": 73},
}

# --- Suzuka circuit characteristics ---
SUZUKA_FACTORS = {
    "circuit_type": "technical",         # High-downforce, technical circuit
    "lap_length_km": 5.807,
    "race_laps": 53,
    "drs_zones": 1,                       # Only 1 DRS zone (hard to overtake)
    "overtaking_difficulty": 0.85,        # 1.0 = very hard, 0.0 = easy
    "tire_degradation": "medium",
    "weather_variability": 0.25,          # Suzuka can be unpredictable
    "pole_to_win_rate": 0.55,             # Historical pole-to-win conversion
}


def _weighted_score(driver: dict, car: dict, grid_pos: int,
                    weather: str, safety_car_prob: float) -> float:
    """
    Compute a composite performance score for a driver given race conditions.
    """
    # Base driver+car score (60% driver, 40% car)
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

    combined = 0.60 * driver_score + 0.40 * car_score

    # Grid position penalty (harder to win from the back at Suzuka)
    overtake_difficulty = SUZUKA_FACTORS["overtaking_difficulty"]
    if grid_pos == 1:
        grid_bonus = 8.0
    elif grid_pos == 2:
        grid_bonus = 5.0
    elif grid_pos <= 5:
        grid_bonus = (6 - grid_pos) * 1.5
    elif grid_pos <= 10:
        grid_bonus = -(grid_pos - 5) * 1.2 * overtake_difficulty
    else:
        grid_bonus = -(grid_pos - 5) * 2.0 * overtake_difficulty

    # Weather modifier
    if weather == "wet":
        wet_boost = (driver["wet_weather"] - 75) * 0.15
        combined += wet_boost
    elif weather == "mixed":
        wet_boost = (driver["wet_weather"] - 75) * 0.07
        combined += wet_boost

    # Safety car randomness factor (bunches up the field)
    sc_equalizer = safety_car_prob * 5.0 * (1 - (grid_pos / 20))

    score = combined + grid_bonus + sc_equalizer

    # Add small random noise to simulate race chaos
    noise = random.gauss(0, 2.5)
    score += noise

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
        qualifying_order: List of driver names in grid order (P1 first).
                          If None, uses a predicted qualifying order based on car pace.
        weather: 'dry', 'wet', or 'mixed'
        safety_car_probability: Probability of safety car deployment (0.0-1.0)
        seed: Random seed for reproducibility

    Returns:
        List of dicts with predicted finishing positions, sorted P1 to P20.
    """
    if seed is not None:
        random.seed(seed)

    # Build lookup maps
    driver_map = {d["name"]: d for d in DRIVERS_2025}

    # Determine grid order
    if qualifying_order is None:
        # Predict quali order: sort by car pace + driver skill
        predicted_quali = sorted(
            DRIVERS_2025,
            key=lambda d: (
                0.55 * TEAM_CAR_2025[d["team"]]["pace"] +
                0.30 * d["skill"] +
                0.15 * d["suzuka_affinity"] +
                random.gauss(0, 1.5)
            ),
            reverse=True,
        )
        qualifying_order = [d["name"] for d in predicted_quali]

    # Score every driver
    results = []
    for grid_pos, name in enumerate(qualifying_order, start=1):
        if name not in driver_map:
            continue
        driver = driver_map[name]
        car = TEAM_CAR_2025[driver["team"]]
        score = _weighted_score(driver, car, grid_pos, weather, safety_car_probability)

        # Reliability DNF check
        reliability = car["reliability"] / 100.0
        dnf = random.random() > reliability * 0.97  # ~3% base DNF chance per car
        results.append({
            "name": name,
            "team": driver["team"],
            "number": driver["number"],
            "grid": grid_pos,
            "score": score,
            "dnf": dnf,
        })

    # Sort: finishers by score desc, DNFs at the back
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
    """
    Run N Monte Carlo simulations and aggregate win/podium probabilities.

    Returns:
        Dict mapping driver name -> {win_pct, podium_pct, points_pct, avg_finish}
    """
    win_counts: dict[str, int] = {}
    podium_counts: dict[str, int] = {}
    points_counts: dict[str, int] = {}
    finish_totals: dict[str, int] = {}
    dnf_counts: dict[str, int] = {}

    for driver in DRIVERS_2025:
        name = driver["name"]
        win_counts[name] = 0
        podium_counts[name] = 0
        points_counts[name] = 0
        finish_totals[name] = 0
        dnf_counts[name] = 0

    for sim in range(n_simulations):
        result = simulate_race(
            qualifying_order=qualifying_order,
            weather=weather,
            safety_car_probability=safety_car_probability,
            seed=None,
        )
        for entry in result:
            name = entry["name"]
            pos = entry["position"]
            if entry["dnf"]:
                dnf_counts[name] += 1
                finish_totals[name] += 20  # treat DNF as last
            else:
                finish_totals[name] += pos
                if pos == 1:
                    win_counts[name] += 1
                if pos <= 3:
                    podium_counts[name] += 1
                if pos <= 10:
                    points_counts[name] += 1

    stats = {}
    for driver in DRIVERS_2025:
        name = driver["name"]
        stats[name] = {
            "team": driver["team"],
            "number": driver["number"],
            "win_pct": round(100 * win_counts[name] / n_simulations, 1),
            "podium_pct": round(100 * podium_counts[name] / n_simulations, 1),
            "points_pct": round(100 * points_counts[name] / n_simulations, 1),
            "avg_finish": round(finish_totals[name] / n_simulations, 2),
            "dnf_pct": round(100 * dnf_counts[name] / n_simulations, 1),
        }

    return stats


def predict_qualifying() -> list[dict]:
    """
    Predict qualifying order based on car pace, driver skill and Suzuka affinity.
    Returns sorted list P1 to P20.
    """
    random.seed(42)
    scores = []
    for driver in DRIVERS_2025:
        car = TEAM_CAR_2025[driver["team"]]
        qual_score = (
            0.50 * car["pace"] +
            0.30 * driver["skill"] +
            0.20 * driver["suzuka_affinity"] +
            random.gauss(0, 1.0)
        )
        scores.append({"name": driver["name"], "team": driver["team"],
                        "number": driver["number"], "qual_score": qual_score})

    scores.sort(key=lambda x: x["qual_score"], reverse=True)
    for pos, entry in enumerate(scores, start=1):
        entry["predicted_grid"] = pos

    return scores
