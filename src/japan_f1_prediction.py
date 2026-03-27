"""
Japan F1 Grand Prix 2026 — Race Prediction Runner
Suzuka International Racing Course | March 29, 2026

Data: Australia R1 + China R2 results + Suzuka FP1/FP2 practice (March 27)

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


def fmt_form(form: float) -> str:
    if form > 3:
        return f"+{form:.1f} ▲▲"
    elif form > 1:
        return f"+{form:.1f} ▲"
    elif form < -3:
        return f"{form:.1f} ▼▼"
    elif form < -1:
        return f"{form:.1f} ▼"
    else:
        return f"{form:+.1f} ~"


def print_header(title: str) -> None:
    line = "=" * 66
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def fmt_gap(gap) -> str:
    if gap is None:
        return "  no time"
    return f" +{gap:.3f}s"


def print_practice() -> None:
    print_header("SUZUKA PRACTICE RESULTS  (Friday March 27)")

    print(f"\n  FP1 — Russell fastest (1:31.666) | Cool & dry, new asphalt low-grip")
    print(f"  {'P':>3}  {'Driver':<22}  {'Team':<20}  {'Gap':>10}")
    print("  " + "-" * 58)
    fp1_order = sorted(
        [(n, g) for n, g in model.FP1_GAPS.items() if g is not None],
        key=lambda x: x[1]
    )
    for pos, (name, gap) in enumerate(fp1_order, start=1):
        team = next((d["team"] for d in model.DRIVERS_2026 if d["name"] == name), "—")
        note = " *sandbagging" if name == "Max Verstappen" else ""
        print(f"  {pos:>3}  {name:<22}  {team:<20}  {fmt_gap(gap)}{note}")
    print(f"   —   {'Alonso (Crawford sub)':<22}  {'Aston Martin':<20}  {'no time':>10}")
    print(f"   —   {'Verstappen':<22}  {'Red Bull Racing':<20}  {'long runs only':>10}")

    print(f"\n  FP2 — Piastri fastest (1:30.133) | Track rubbered in, all soft tyres")
    print(f"  {'P':>3}  {'Driver':<22}  {'Team':<20}  {'Gap':>10}  FP2 Significance")
    print("  " + "-" * 75)
    fp2_order = sorted(
        [(n, g) for n, g in model.FP2_GAPS.items() if g is not None],
        key=lambda x: x[1]
    )
    highlights = {
        "Oscar Piastri":    "McLaren fastest — car suits Suzuka",
        "Nico Hulkenberg":  "best midfield — Audi surprise",
        "Alex Albon":       "Williams stronger than expected",
        "Max Verstappen":   "P10 — understeer, car struggling here",
        "Fernando Alonso":  "returned after missing FP1",
    }
    for pos, (name, gap) in enumerate(fp2_order, start=1):
        team = next((d["team"] for d in model.DRIVERS_2026 if d["name"] == name), "—")
        hl = f"  ← {highlights[name]}" if name in highlights else ""
        print(f"  {pos:>3}  {name:<22}  {team:<20}  {fmt_gap(gap)}{hl}")
    print(f"   —   {'Lindblad':<22}  {'Racing Bulls':<20}  {'no time':>10}  ← gearbox failure")

    print(f"\n  KEY PRACTICE INCIDENTS")
    print("  " + "-" * 58)
    for note in model.PRACTICE_INCIDENTS:
        print(f"  ⚠  {note}")


def print_standings() -> None:
    print_header("2026 CHAMPIONSHIP STANDINGS  (after R2 — China)")
    print(f"  {'Pos':>3}  {'Driver':<22}  {'Team':<20}  {'Pts':>5}  {'Form':<12}")
    print("  " + "-" * 62)
    sorted_standings = sorted(model.STANDINGS_2026.items(), key=lambda x: x[1], reverse=True)
    for pos, (name, pts) in enumerate(sorted_standings, start=1):
        team = next((d["team"] for d in model.DRIVERS_2026 if d["name"] == name), "—")
        form = model.FORM_SCORES.get(name, 0.0)
        print(f"  {pos:>3}  {name:<22}  {team:<20}  {pts:>5}  {fmt_form(form)}")


def print_qualifying(quali_result: list[dict]) -> None:
    print_header("PREDICTED QUALIFYING — SUZUKA 2026")
    print(f"  {'P':>3}  {'#':>3}  {'Driver':<22}  {'Team':<20}  {'FP1 Gap':>9}  {'FP2 Gap':>9}  {'Champ Pts':>10}")
    print("  " + "-" * 80)
    for entry in quali_result:
        grid = entry["predicted_grid"]
        flag = " ◄ POLE" if grid == 1 else ""
        fp1 = fmt_gap(entry.get("fp1_gap"))
        fp2 = fmt_gap(entry.get("fp2_gap"))
        print(f"  {grid:>3}  #{entry['number']:<3}  {entry['name']:<22}  "
              f"{entry['team']:<20}  {fp1:>9}  {fp2:>9}  {entry['champ_pts']:>10}{flag}")


def print_single_race(race_result: list[dict], weather: str) -> None:
    weather_label = {"dry": "DRY", "wet": "WET", "mixed": "MIXED / CHANGEABLE"}.get(weather, weather.upper())
    print_header(f"PREDICTED RACE RESULT — SUZUKA 2026  [{weather_label}]")
    print(f"  {'Pos':>4}  {'#':>3}  {'Driver':<22}  {'Team':<20}  {'Status':<6}  {'Grid':>4}  {'Move'}")
    print("  " + "-" * 70)
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for entry in race_result:
        medal = medals.get(entry["position"], "  ")
        status = "DNF" if entry["dnf"] else f"P{entry['position']}"
        delta = entry["grid"] - entry["position"]
        delta_str = f"▲{delta}" if delta > 0 else (f"▼{abs(delta)}" if delta < 0 else "=")
        print(f"  {medal} {entry['position']:>2}  #{entry['number']:<3}  {entry['name']:<22}  "
              f"{entry['team']:<20}  {status:<6}  G{entry['grid']:<3}  {delta_str}")


def print_monte_carlo(stats: dict, weather: str, n_sims: int) -> None:
    weather_label = {"dry": "DRY", "wet": "WET", "mixed": "MIXED"}.get(weather, weather.upper())
    print_header(f"MONTE CARLO PROBABILITIES  ({n_sims:,} simulations) — {weather_label}")
    print(f"  {'Driver':<22}  {'Team':<20}  {'Win%':>6}  {'Podium%':>8}  {'Pts%':>6}  "
          f"{'AvgPos':>7}  {'DNF%':>6}  {'Form'}")
    print("  " + "-" * 88)

    sorted_stats = sorted(stats.items(), key=lambda x: x[1]["avg_finish"])
    for name, s in sorted_stats:
        print(f"  {name:<22}  {s['team']:<20}  {s['win_pct']:>5.1f}%  "
              f"{s['podium_pct']:>7.1f}%  {s['points_pct']:>5.1f}%  {s['avg_finish']:>7.2f}  "
              f"{s['dnf_pct']:>5.1f}%  {fmt_form(s['form'])}")

    print()
    print("  WIN PROBABILITY BREAKDOWN")
    print("  " + "-" * 55)
    top = [(n, s) for n, s in sorted_stats if s["win_pct"] >= 0.5]
    for name, s in sorted(top, key=lambda x: x[1]["win_pct"], reverse=True):
        bar = fmt_bar(s["win_pct"], 30)
        print(f"  {name:<22} {bar}  {s['win_pct']:.1f}%")


def print_season_context() -> None:
    print_header("2026 SEASON CONTEXT  (heading into Japan — R3)")
    notes = [
        "Mercedes has scored 1-2 in BOTH races — dominant with new 2026 regs",
        "Russell leads Antonelli by 4pts; both drivers are genuine title threats",
        "Ferrari comfortably second — Hamilton & Leclerc both on the podium each race",
        "McLaren (reigning champ Norris) fast but hit by reliability disasters (DNS China)",
        "Red Bull struggling — Verstappen P6 from P20 (AUS) then DNF (CHN)",
        "Haas surprising strong: Bearman P7 AUS + P5 CHN — car over-performing",
        "Audi & Cadillac made F1 debuts in Australia (11th team: Cadillac)",
        "Aston Martin yet to score: both cars DNF in both races",
    ]
    for note in notes:
        print(f"  • {note}")


def print_suzuka_notes() -> None:
    print_header("SUZUKA CIRCUIT NOTES")
    notes = [
        "Lap distance : 5.807 km  |  Race laps: 53  |  Total: ~307.7 km",
        "DRS zones    : 1 (main straight only — overtaking extremely difficult)",
        "Key sectors  : S1 Esses (high-speed, high-downforce critical)",
        "               S2 Degner curves + Hairpin (braking zones)",
        "               S3 Spoon curve + 130R (aero efficiency key)",
        "Tire strategy: Typically 1-stop; medium → hard compound",
        "Weather      : Late March at Suzuka — historically mixed/damp possible",
        "Historical   : Pole sitter wins ~55% of Suzuka races",
    ]
    for note in notes:
        print(f"  • {note}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Japan F1 2026 Prediction Model")
    parser.add_argument("--weather", choices=["dry", "wet", "mixed"], default="dry",
                        help="Expected race weather (default: dry)")
    parser.add_argument("--sims", type=int, default=10000,
                        help="Monte Carlo simulation count (default: 10000)")
    parser.add_argument("--seed", type=int, default=2026,
                        help="Random seed for single-race simulation")
    parser.add_argument("--sc-prob", type=float, default=0.35,
                        help="Safety car probability 0.0-1.0 (default: 0.35)")
    args = parser.parse_args()

    print("\n" + "╔" + "═" * 64 + "╗")
    print("║" + "  JAPAN GRAND PRIX 2026 — PREDICTION MODEL".center(64) + "║")
    print("║" + "  Suzuka | Round 3 | March 29, 2026".center(64) + "║")
    print("║" + "  Data: R1+R2 results + Suzuka FP1/FP2 (March 27)".center(64) + "║")
    print("╚" + "═" * 64 + "╝")

    # 1. Practice session results
    print_practice()

    # 2. Championship context
    print_standings()

    # 2. Predicted qualifying
    quali = model.predict_qualifying()
    print_qualifying(quali)
    qualifying_order = [e["name"] for e in quali]

    # 3. Single deterministic race
    race_result = model.simulate_race(
        qualifying_order=qualifying_order,
        weather=args.weather,
        safety_car_probability=args.sc_prob,
        seed=args.seed,
    )
    print_single_race(race_result, args.weather)

    # 4. Monte Carlo
    print(f"\n  Running {args.sims:,} Monte Carlo simulations... ", end="", flush=True)
    mc_stats = model.run_monte_carlo(
        n_simulations=args.sims,
        qualifying_order=qualifying_order,
        weather=args.weather,
        safety_car_probability=args.sc_prob,
    )
    print("done.")
    print_monte_carlo(mc_stats, args.weather, args.sims)

    # 5. Context
    print_season_context()
    print_suzuka_notes()

    # 6. Summary
    winner = race_result[0]
    top_win = max(mc_stats.items(), key=lambda x: x[1]["win_pct"])
    print_header("MODEL SUMMARY")
    print(f"  Single-sim winner    :  {winner['name']} ({winner['team']})")
    print(f"  Highest win prob     :  {top_win[0]} — {top_win[1]['win_pct']}%")
    print(f"  Championship leader  :  George Russell (Mercedes) — 51 pts")
    print(f"  Weather condition    :  {args.weather.upper()}")
    print(f"  Safety car prob      :  {args.sc_prob * 100:.0f}%")
    print(f"  Simulations run      :  {args.sims:,}")
    print(f"  Data source          :  R1 Australia + R2 China + Suzuka FP1/FP2")
    print()


if __name__ == "__main__":
    main()
