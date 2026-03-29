# Investment 10x Model
# Disclaimer: For educational and modeling purposes ONLY.
# This is NOT financial advice. Past performance does not guarantee future results.
# High-return investments carry extreme risk, including total loss of capital.

class InvestmentModel:
    """
    Models a $1000 portfolio targeting 10x returns in one year.
    Allocates across high-growth sectors: AI, semiconductors, crypto, quantum computing.
    """

    # Hypothetical high-growth candidates with sector, allocation %, and projected multiplier.
    # Multipliers reflect "bull-case" speculative scenarios, NOT guarantees.
    # RGTI was up ~1500% in late 2024; PLTR was up ~340% in 2024; BTC did ~150% in 2024.
    # These are the kinds of outlier moves needed to target 10x in one year.
    PORTFOLIO = {
        "RGTI":  {"sector": "Quantum Computing",     "allocation": 0.35, "projected_multiplier": 15.0},
        "IONQ":  {"sector": "Quantum Computing",     "allocation": 0.20, "projected_multiplier": 10.0},
        "MSTR":  {"sector": "Bitcoin Treasury",      "allocation": 0.15, "projected_multiplier": 8.0},
        "BTC":   {"sector": "Cryptocurrency",        "allocation": 0.15, "projected_multiplier": 5.0},
        "PLTR":  {"sector": "AI / Data Analytics",   "allocation": 0.10, "projected_multiplier": 5.0},
        "COIN":  {"sector": "Crypto Exchange",       "allocation": 0.05, "projected_multiplier": 6.0},
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
        print("  10X INVESTMENT MODEL  —  Educational / Hypothetical Scenario Only")
        print("=" * width)
        print(f"  Initial Investment : ${self.initial:>10,.2f}")
        print(f"  Target             : 10x  (${self.initial * 10:>10,.2f})")
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
        print("  - Crypto and small-cap stocks can lose 50-90%+ in a single year.")
        print("  - Diversification reduces but does NOT eliminate risk.")
        print("  - Consult a licensed financial advisor before investing.")
        print("=" * width)
