# Investment 2x Model
# Disclaimer: For educational and modeling purposes ONLY.
# This is NOT financial advice. Past performance does not guarantee future results.
# All investments carry risk, including possible loss of principal.

class InvestmentModel:
    """
    Models a $1000 portfolio targeting 2x returns in one year.
    Allocates across established growth companies and blue-chip tech —
    a more conservative approach than speculative small-caps or crypto.
    """

    # Conservative-to-moderate growth candidates.
    # Multipliers reflect realistic bull-case annual returns based on recent history.
    # NVDA doubled in 2023 and again in 2024. MSFT, GOOGL, META all had strong years.
    PORTFOLIO = {
        "NVDA":  {"sector": "AI / Semiconductors",   "allocation": 0.25, "projected_multiplier": 2.5},
        "META":  {"sector": "Social Media / AI",     "allocation": 0.20, "projected_multiplier": 2.0},
        "GOOGL": {"sector": "Search / Cloud / AI",   "allocation": 0.20, "projected_multiplier": 1.8},
        "MSFT":  {"sector": "Cloud / AI",            "allocation": 0.15, "projected_multiplier": 1.7},
        "AMZN":  {"sector": "E-Commerce / Cloud",    "allocation": 0.10, "projected_multiplier": 1.8},
        "PLTR":  {"sector": "AI / Data Analytics",   "allocation": 0.10, "projected_multiplier": 2.0},
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
        print("  2X INVESTMENT MODEL  —  Educational / Hypothetical Scenario Only")
        print("=" * width)
        print(f"  Initial Investment : ${self.initial:>10,.2f}")
        print(f"  Target             :  2x  (${self.initial * 2:>10,.2f})")
        print("=" * width)
        header = f"{'Ticker':<7} {'Sector':<26} {'Alloc%':>6}  {'Allocated':>10}  {'Proj. Value':>11}  {'Mult':>5}"
        print(header)
        print("-" * width)
        for ticker, r in results.items():
            alloc_pct = self.PORTFOLIO[ticker]["allocation"] * 100
            print(
                f"{ticker:<7} {r['sector']:<26} {alloc_pct:>5.0f}%"
                f"  ${r['allocated']:>9,.2f}  ${r['projected_value']:>10,.2f}  {r['multiplier']:>4.1f}x"
            )
        print("-" * width)
        print(
            f"{'TOTAL':<7} {'':26} {'100%':>6}"
            f"  ${self.initial:>9,.2f}  ${total:>10,.2f}  {self.overall_multiplier():>4.1f}x"
        )
        print("=" * width)
        print()
        print("  RISK NOTES:")
        print("  - These projections are speculative scenarios, NOT predictions.")
        print("  - Even blue-chip stocks can decline 20-40%+ in a bear market.")
        print("  - Diversification reduces but does NOT eliminate risk.")
        print("  - Consult a licensed financial advisor before investing.")
        print("=" * width)
