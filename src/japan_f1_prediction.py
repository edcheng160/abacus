"""
Japan F1 Grand Prix 2026 — Race Prediction Runner
Suzuka International Racing Course | March 29, 2026

Data: Australia R1 + China R2 results + Suzuka FP1/FP2/FP3 + confirmed qualifying grid

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
    if form > 3:   return f"+{form:.1f} ▲▲"
    elif form > 1: return f"+{form:.1f} ▲"
    elif form < -3: return f"{form:.1f} ▼▼"
    elif form < -1: return f"{form:.1f} ▼"
    else:           return f"{form:+.1f} ~"


def fmt_gap(gap) -> str:
    if gap is None:
        return "  no time"
    return f" +{gap:.3f}s"


def print_header(title: str) -> None:
    line = "=" * 66
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def print_qualifying_confirmed(grid: list[dict]) -> None:
    print_header("CONFIRMED QUALIFYING GRID — SUZUKA 2026  (March 28)")
    print(f"  {'P':>3}  {'#':>3}  {'Driver':<22}  {'Team':<20}  {'Q Time':>10}  {'Gap':>9}  {'Stage'}")
    print("  " + "-" * 78)
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for entry in grid:
        p = entry["grid"]
        medal = medals.get(p, "  ")
        flag = " ◄ POLE" if p == 1 else ""
        print(f"  {medal}{p:>2}  #{entry['number']:<3}  {entry['name']:<22}  "
              f"{entry['team']:<20}  {entry['q_time']:>10}  {entry['q_gap']:>9}  "
              f"{entry['q_stage']}{flag}")
    print()
    print("  KEY QUALIFYING NOTES")
    print("  " + "-" * 60)
    for note in model.QUALIFYING_NOTES:
        print(f"  ⚡ {note}")


def print_practice_summary() -> None:
    """Compact practice summary (full detail in separate section)."""
    print_header("PRACTICE SUMMARY  (FP1–FP3 fastest laps)")
    sessions = [
        ("FP1", model.FP1_GAPS, "Russell   1:31.666"),
        ("FP2", model.FP2_GAPS, "Piastri   1:30.133"),
        ("FP3", model.FP3_GAPS, "Antonelli 1:29.362"),
    ]
    for label, gaps, fastest in sessions:
        order = sorted([(n, g) for n, g in gaps.items() if g is not None], key=lambda x: x[1])
        top5 = ", ".join(f"{n.split()[-1]}(+{g:.3f})" for n, g in order[:5])
        print(f"  {label}  Fastest: {fastest}  |  Top 5: {top5}")


def print_race(race_result: list[dict], weather: str) -> None:
    wlabel = {"dry": "DRY", "wet": "WET", "mixed": "MIXED / CHANGEABLE"}.get(weather, weather.upper())
    print_header(f"PREDICTED RACE RESULT — SUZUKA 2026  [{wlabel}]")
    print(f"  {'Pos':>4}  {'#':>3}  {'Driver':<22}  {'Team':<20}  {'Status':<6}  {'Grid':>4}  {'Move'}")
    print("  " + "-" * 72)
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for entry in race_result:
        medal = medals.get(entry["position"], "  ")
        status = "DNF" if entry["dnf"] else f"P{entry['position']}"
        delta = entry["grid"] - entry["position"]
        delta_str = f"▲{delta}" if delta > 0 else (f"▼{abs(delta)}" if delta < 0 else "=")
        print(f"  {medal} {entry['position']:>2}  #{entry['number']:<3}  {entry['name']:<22}  "
              f"{entry['team']:<20}  {status:<6}  G{entry['grid']:<3}  {delta_str}")


def print_monte_carlo(stats: dict, weather: str, n_sims: int) -> None:
    wlabel = {"dry": "DRY", "wet": "WET", "mixed": "MIXED"}.get(weather, weather.upper())
    print_header(f"MONTE CARLO RACE PROBABILITIES  ({n_sims:,} sims) — {wlabel}")
    print(f"  {'Driver':<22}  {'Team':<20}  {'Grid':>5}  {'Win%':>6}  {'Podium%':>8}  "
          f"{'Pts%':>6}  {'AvgPos':>7}  {'DNF%':>6}  Form")
    print("  " + "-" * 96)

    # Sort by avg finish
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]["avg_finish"])
    grid_map = {e["name"]: e["grid"] for e in model.get_confirmed_grid()}

    for name, s in sorted_stats:
        grid = grid_map.get(name, "—")
        print(f"  {name:<22}  {s['team']:<20}  {str(grid):>5}  {s['win_pct']:>5.1f}%  "
              f"{s['podium_pct']:>7.1f}%  {s['points_pct']:>5.1f}%  {s['avg_finish']:>7.2f}  "
              f"{s['dnf_pct']:>5.1f}%  {fmt_form(s['form'])}")

    print()
    print("  WIN PROBABILITY BREAKDOWN")
    print("  " + "-" * 55)
    top = [(n, s) for n, s in sorted_stats if s["win_pct"] >= 0.3]
    for name, s in sorted(top, key=lambda x: x[1]["win_pct"], reverse=True):
        bar = fmt_bar(s["win_pct"], 30)
        print(f"  {name:<22} {bar}  {s['win_pct']:.1f}%")


def print_key_battles() -> None:
    print_header("KEY RACE BATTLES TO WATCH")
    battles = [
        ("FRONT ROW",   "Antonelli vs Russell — Mercedes 1-2, Suzuka pole sitter wins 55% historically"),
        ("P3 threat",   "Piastri (McLaren P3) — blazing fast but ~40% DNF risk; Norris P5 same concern"),
        ("Ferrari",     "Leclerc P4 / Hamilton P6 — strong race pace, could exploit McLaren DNFs"),
        ("Verstappen",  "P11 start — needs 8+ overtakes at Suzuka (DRS zone = 1). Almost impossible"),
        ("Gasly P7",    "Alpine surprise — likely to hold station; Suzuka rewards qualifying position"),
        ("Hadjar P8",   "Red Bull's best hope today — ahead of Verstappen on the grid"),
        ("Bearman P18", "Haas race ace started P18 after Q1 shock exit — can he recover to points?"),
        ("Aston Martin","P21/P22 — Alonso/Stroll need a miracle or safety car to score"),
    ]
    for label, detail in battles:
        print(f"  [{label:<12}]  {detail}")


def main():
    parser = argparse.ArgumentParser(description="Japan F1 2026 Race Prediction")
    parser.add_argument("--weather", choices=["dry", "wet", "mixed"], default="dry")
    parser.add_argument("--sims", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--sc-prob", type=float, default=0.35)
    args = parser.parse_args()

    print("\n" + "╔" + "═" * 64 + "╗")
    print("║" + "  JAPAN GRAND PRIX 2026 — RACE PREDICTION".center(64) + "║")
    print("║" + "  Suzuka | Round 3 | Race: March 29, 2026".center(64) + "║")
    print("║" + "  Grid: CONFIRMED qualifying results (March 28)".center(64) + "║")
    print("╚" + "═" * 64 + "╝")

    # 1. Confirmed qualifying grid
    grid = model.get_confirmed_grid()
    print_qualifying_confirmed(grid)

    # 2. Practice summary
    print_practice_summary()

    # 3. Single deterministic race (from real grid)
    race_result = model.simulate_race(
        weather=args.weather,
        safety_car_probability=args.sc_prob,
        seed=args.seed,
    )
    print_race(race_result, args.weather)

    # 4. Monte Carlo
    print(f"\n  Running {args.sims:,} Monte Carlo simulations... ", end="", flush=True)
    mc_stats = model.run_monte_carlo(
        n_simulations=args.sims,
        weather=args.weather,
        safety_car_probability=args.sc_prob,
    )
    print("done.")
    print_monte_carlo(mc_stats, args.weather, args.sims)

    # 5. Key battles
    print_key_battles()

    # 6. Summary
    winner = race_result[0]
    top_win = max(mc_stats.items(), key=lambda x: x[1]["win_pct"])
    print_header("MODEL SUMMARY")
    print(f"  Pole position        :  Kimi Antonelli (Mercedes) — 1:28.778")
    print(f"  Single-sim winner    :  {winner['name']} ({winner['team']})")
    print(f"  Highest win prob     :  {top_win[0]} — {top_win[1]['win_pct']}%")
    print(f"  Championship leader  :  George Russell (Mercedes) — 51 pts")
    print(f"  Weather condition    :  {args.weather.upper()}")
    print(f"  Safety car prob      :  {args.sc_prob * 100:.0f}%")
    print(f"  Simulations run      :  {args.sims:,}")
    print(f"  Grid source          :  Confirmed qualifying — March 28, 2026")
    print()


if __name__ == "__main__":
    main()
