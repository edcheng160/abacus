"""
Japan F1 Grand Prix 2025 - Race Prediction Runner
Suzuka International Racing Course | April 6, 2025

Usage:
    python japan_f1_prediction.py
    python japan_f1_prediction.py --weather wet
    python japan_f1_prediction.py --sims 5000 --weather mixed
"""

import sys
import argparse
sys.path.insert(0, ".")

import lib.japan_f1_model as model


def fmt_bar(pct: float, width: int = 25) -> str:
    filled = int(round(pct / 100 * width))
    return "█" * filled + "░" * (width - filled)


def print_header(title: str) -> None:
    line = "=" * 62
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def print_qualifying(quali_result: list[dict]) -> None:
    print_header("PREDICTED QUALIFYING — SUZUKA 2025")
    print(f"  {'P':>3}  {'#':>3}  {'Driver':<22}  {'Team':<20}")
    print("  " + "-" * 55)
    for entry in quali_result:
        grid = entry["predicted_grid"]
        flag = " ◄ POLE" if grid == 1 else ""
        print(f"  {grid:>3}  #{entry['number']:<3}  {entry['name']:<22}  {entry['team']:<20}{flag}")


def print_single_race(race_result: list[dict], weather: str) -> None:
    weather_label = {"dry": "DRY", "wet": "WET", "mixed": "MIXED / CHANGEABLE"}.get(weather, weather.upper())
    print_header(f"PREDICTED RACE RESULT — SUZUKA 2025  [{weather_label}]")
    print(f"  {'Pos':>4}  {'#':>3}  {'Driver':<22}  {'Team':<20}  Status")
    print("  " + "-" * 65)
    for entry in race_result[:20]:
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(entry["position"], "  ")
        status = "DNF" if entry["dnf"] else f"P{entry['position']}"
        grid = entry["grid"]
        delta = entry["grid"] - entry["position"]
        delta_str = f"(▲{delta})" if delta > 0 else (f"(▼{abs(delta)})" if delta < 0 else "(=)")
        print(f"  {medal} {entry['position']:>2}  #{entry['number']:<3}  {entry['name']:<22}  "
              f"{entry['team']:<20}  {status}  Grid:{grid} {delta_str}")


def print_monte_carlo(stats: dict, weather: str, n_sims: int) -> None:
    weather_label = {"dry": "DRY", "wet": "WET", "mixed": "MIXED"}.get(weather, weather.upper())
    print_header(f"MONTE CARLO PROBABILITIES ({n_sims:,} simulations) — {weather_label}")
    print(f"  {'Driver':<22}  {'Team':<20}  {'Win%':>6}  {'Podium%':>8}  {'Pts%':>6}  {'AvgPos':>7}")
    print("  " + "-" * 75)

    sorted_stats = sorted(stats.items(), key=lambda x: x[1]["avg_finish"])
    for name, s in sorted_stats:
        win_bar = fmt_bar(s["win_pct"], 15)
        print(f"  {name:<22}  {s['team']:<20}  {s['win_pct']:>5.1f}%  "
              f"{s['podium_pct']:>7.1f}%  {s['points_pct']:>5.1f}%  {s['avg_finish']:>7.2f}")

    print()
    # Top win contenders bar chart
    print("  WIN PROBABILITY BREAKDOWN")
    print("  " + "-" * 50)
    top = [(n, s) for n, s in sorted_stats if s["win_pct"] > 0.5][:10]
    for name, s in sorted(top, key=lambda x: x[1]["win_pct"], reverse=True):
        bar = fmt_bar(s["win_pct"], 30)
        print(f"  {name:<22} {bar}  {s['win_pct']:.1f}%")


def print_suzuka_notes() -> None:
    print_header("SUZUKA CIRCUIT NOTES")
    notes = [
        "Lap distance : 5.807 km  |  Race laps: 53  |  Total: ~307.7 km",
        "DRS zones    : 1 (main straight only — overtaking is VERY difficult)",
        "Key sectors  : S1 Esses (high-speed, high-downforce critical)",
        "               S2 Degner curves + Hairpin (braking zones)",
        "               S3 Spoon curve + 130R (aero efficiency key)",
        "Tire strategy: Typically 1-stop preferred; medium → hard compound",
        "Weather risk : April weather can bring rain; mixed sessions possible",
        "Historical   : Pole sitter wins ~55% of races here",
        "               Red Bull won last 3 consecutive Japan GPs (2022-2024)",
    ]
    for note in notes:
        print(f"  • {note}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Japan F1 2025 Prediction Model")
    parser.add_argument("--weather", choices=["dry", "wet", "mixed"], default="dry",
                        help="Expected race weather (default: dry)")
    parser.add_argument("--sims", type=int, default=10000,
                        help="Monte Carlo simulation count (default: 10000)")
    parser.add_argument("--seed", type=int, default=2025,
                        help="Random seed for single-race simulation")
    parser.add_argument("--sc-prob", type=float, default=0.35,
                        help="Safety car probability 0.0-1.0 (default: 0.35)")
    args = parser.parse_args()

    print("\n" + "╔" + "═" * 60 + "╗")
    print("║" + "  JAPAN GRAND PRIX 2025 — PREDICTION MODEL".center(60) + "║")
    print("║" + "  Suzuka International Racing Course".center(60) + "║")
    print("╚" + "═" * 60 + "╝")

    # 1. Predicted qualifying
    quali = model.predict_qualifying()
    print_qualifying(quali)
    qualifying_order = [e["name"] for e in quali]

    # 2. Single deterministic race simulation
    race_result = model.simulate_race(
        qualifying_order=qualifying_order,
        weather=args.weather,
        safety_car_probability=args.sc_prob,
        seed=args.seed,
    )
    print_single_race(race_result, args.weather)

    # 3. Monte Carlo probability analysis
    print(f"\n  Running {args.sims:,} Monte Carlo simulations... ", end="", flush=True)
    mc_stats = model.run_monte_carlo(
        n_simulations=args.sims,
        qualifying_order=qualifying_order,
        weather=args.weather,
        safety_car_probability=args.sc_prob,
    )
    print("done.")
    print_monte_carlo(mc_stats, args.weather, args.sims)

    # 4. Circuit notes
    print_suzuka_notes()

    # 5. Summary prediction
    winner = race_result[0]
    top_win = max(mc_stats.items(), key=lambda x: x[1]["win_pct"])
    print_header("MODEL SUMMARY")
    print(f"  Single-sim winner    :  {winner['name']} ({winner['team']})")
    print(f"  Highest win prob     :  {top_win[0]} — {top_win[1]['win_pct']}%")
    print(f"  Weather condition    :  {args.weather.upper()}")
    print(f"  Safety car prob      :  {args.sc_prob * 100:.0f}%")
    print(f"  Simulations run      :  {args.sims:,}")
    print()


if __name__ == "__main__":
    main()
