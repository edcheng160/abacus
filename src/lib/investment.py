# Investment -10x Bear Model
# Disclaimer: For educational and modeling purposes ONLY.
# This is NOT financial advice. Past performance does not guarantee future results.
# Short/inverse instruments and options can lose 100% of invested capital rapidly.

class InvestmentModel:
    """
    Models a $1000 SHORT/INVERSE portfolio targeting 10x gains from a severe bear market.
    The '-10x' label means the underlying market moves -10x (catastrophic crash),
    driving these inverse/short instruments to 10x returns.

    Instruments used:
      - Deep out-of-the-money put options (high leverage, all-or-nothing)
      - 3x leveraged inverse ETFs (amplify market declines 3:1)
      - Long volatility ETF (VIX spikes sharply during crashes)
    """

    # Bear-market scenario: S&P 500 drops ~50%+, Nasdaq drops ~60%+, VIX spikes to 80+.
    # Multipliers reflect projected instrument gains under that crash scenario.
    # Put options gain the most (deep OTM turns into deep ITM); inverse ETFs gain 3x decline.
    PORTFOLIO = {
        "SPY_PUTS":  {"sector": "S&P 500 Put Options",    "allocation": 0.20, "projected_multiplier": 26.0},
        "QQQ_PUTS":  {"sector": "Nasdaq Put Options",     "allocation": 0.15, "projected_multiplier": 20.0},
        "SQQQ":      {"sector": "3x Inverse Nasdaq ETF",  "allocation": 0.25, "projected_multiplier":  3.0},
        "UVIX":      {"sector": "2x Long VIX ETF",        "allocation": 0.20, "projected_multiplier":  3.0},
        "SPXU":      {"sector": "3x Inverse S&P ETF",     "allocation": 0.20, "projected_multiplier":  2.25},
    }

    def __init__(self, initial_investment: float):
        self.initial = initial_investment

    def calculate_returns(self) -> tuple:
        """Returns per-position results dict and total projected value."""
        results = {}
        total_value = 0.0
        for ticker, data in self.PORTFOLIO.items():
            allocated = self.initial * data["allocation"]
            projected = allocated * data["projected_multiplier"]
            results[ticker] = {
                "sector": data["sector"],
                "multiplier": data["projected_multiplier"],
                "allocated": allocated,
                "projected_value": projected,
                "gain": projected - allocated,
            }
            total_value += projected
        return results, total_value

    def overall_multiplier(self) -> float:
        _, total = self.calculate_returns()
        return total / self.initial

    def print_model(self):
        results, total = self.calculate_returns()
        width = 80
        print("=" * width)
        print("  -10X BEAR MODEL  —  Educational / Hypothetical Scenario Only")
        print("  (Short/inverse portfolio that PROFITS when the market CRASHES)")
        print("=" * width)
        print(f"  Initial Investment : ${self.initial:>10,.2f}")
        print(f"  Target             : 10x  (${self.initial * 10:>10,.2f})")
        print(f"  Market assumption  : S&P -50%+, Nasdaq -60%+, VIX spikes to 80+")
        print("=" * width)
        header = f"{'Ticker':<10} {'Instrument':<26} {'Alloc%':>6}  {'Allocated':>10}  {'Proj. Value':>11}  {'Mult':>5}"
        print(header)
        print("-" * width)
        for ticker, r in results.items():
            alloc_pct = self.PORTFOLIO[ticker]["allocation"] * 100
            print(
                f"{ticker:<10} {r['sector']:<26} {alloc_pct:>5.0f}%"
                f"  ${r['allocated']:>9,.2f}  ${r['projected_value']:>10,.2f}  {r['multiplier']:>4.1f}x"
            )
        print("-" * width)
        print(
            f"{'TOTAL':<10} {'':26} {'100%':>6}"
            f"  ${self.initial:>9,.2f}  ${total:>10,.2f}  {self.overall_multiplier():>4.1f}x"
        )
        print("=" * width)
        print()
        print("  RISK NOTES:")
        print("  - These projections are speculative scenarios, NOT predictions.")
        print("  - Put options expire worthless if the crash does NOT happen in time.")
        print("  - Leveraged inverse ETFs decay daily — lose value in flat/rising markets.")
        print("  - In a bull market this entire portfolio could go to $0.")
        print("  - Consult a licensed financial advisor before investing.")
        print("=" * width)
