"""
war_indicators.py
Tracks geopolitical / conflict tension via proxy market signals and keyword scoring.

Tension Score (0-100):
  - Defense sector returns   → conflict spending ramps up
  - Gold / safe-haven moves  → capital flight from risk assets
  - Oil / energy spikes      → supply disruption fears
  - News keyword density     → media conflict signal
  - VIX elevation            → market fear gauge
"""

import numpy as np

# --- Asset proxies ---------------------------------------------------------
DEFENSE_TICKERS  = ["LMT", "RTX", "NOC", "GD", "BA"]   # defense contractors
SAFE_HAVEN       = ["GLD", "SLV", "TLT", "UUP"]         # gold, silver, bonds, USD
ENERGY_TICKERS   = ["USO", "XLE"]                        # crude oil proxies
CONFLICT_KEYWORDS = [
    "war", "conflict", "military", "strike", "invasion", "offensive",
    "ceasefire", "nato", "troops", "missile", "drone", "sanctions",
    "escalation", "airstrike", "casualties", "siege", "occupation",
    "nuclear", "chemical weapons", "refugee", "evacuation",
]


class WarTensionIndicator:
    """
    Composite war tension score (0-100) built from five sub-components.
    Each sub-score is normalized so the total never exceeds 100.

    Sub-scores
    ----------
    defense_score  (0-25): defense stock outperformance
    gold_score     (0-20): gold / safe-haven inflows
    oil_score      (0-20): oil / energy spike
    news_score     (0-20): conflict keyword density in news sentiment
    vix_score      (0-15): VIX elevation above baseline
    """

    WEIGHTS = {
        "defense": 0.25,
        "gold":    0.20,
        "oil":     0.20,
        "news":    0.20,
        "vix":     0.15,
    }

    def __init__(self):
        self.history: list[float] = []
        self.sub_scores: list[dict] = []

    # ------------------------------------------------------------------
    def compute(
        self,
        defense_return: float,   # daily return of defense ETF (e.g. 0.03 = +3%)
        gold_return:    float,   # daily return of GLD
        oil_return:     float,   # daily return of USO
        news_sentiment: float,   # [-1, +1] — negative = bearish/conflict-heavy
        vix:            float,   # VIX level (baseline ~15, crisis ~40+)
    ) -> float:
        d = min(max(defense_return * 100 / 4.0, 0.0), 1.0) * 25   # cap at 4% daily
        g = min(max(gold_return    * 100 / 3.0, 0.0), 1.0) * 20   # cap at 3% daily
        o = min(max(oil_return     * 100 / 5.0, 0.0), 1.0) * 20   # cap at 5% daily
        n = min(max((0.0 - news_sentiment) / 1.0, 0.0), 1.0) * 20 # negative news → high
        v = min(max((vix - 15.0) / 65.0, 0.0), 1.0) * 15          # VIX 15→80 maps 0→15

        score = d + g + o + n + v
        self.history.append(score)
        self.sub_scores.append({
            "defense": round(d, 2), "gold": round(g, 2),
            "oil":     round(o, 2), "news": round(n, 2),
            "vix":     round(v, 2), "total": round(score, 2),
        })
        return score

    # ------------------------------------------------------------------
    def trend(self, window: int = 5) -> float:
        """
        Linear slope of tension over the last `window` readings.
        Positive = escalating, negative = de-escalating.
        """
        if len(self.history) < 2:
            return 0.0
        w = min(window, len(self.history))
        y = np.array(self.history[-w:])
        x = np.arange(w, dtype=float)
        slope = float(np.polyfit(x, y, 1)[0])
        return round(slope, 4)

    # ------------------------------------------------------------------
    def regime(self) -> str:
        """Classify current tension into a named regime."""
        if not self.history:
            return "UNKNOWN"
        score = self.history[-1]
        if score >= 70:   return "EXTREME"
        if score >= 50:   return "HIGH"
        if score >= 30:   return "ELEVATED"
        if score >= 15:   return "MODERATE"
        return "LOW"

    # ------------------------------------------------------------------
    @staticmethod
    def keyword_score(headlines: list[str]) -> float:
        """
        Returns a [-1, 0] sentiment proxy from conflict keyword density.
        0  = no conflict keywords found
        -1 = every headline contains multiple conflict terms
        """
        if not headlines:
            return 0.0
        hits = 0
        for h in headlines:
            h_lower = h.lower()
            hits += sum(1 for kw in CONFLICT_KEYWORDS if kw in h_lower)
        # normalise: assume ~3 keywords per headline is "fully negative"
        density = hits / (len(headlines) * 3.0)
        return -min(density, 1.0)

    # ------------------------------------------------------------------
    def summary(self) -> dict:
        if not self.history:
            return {}
        return {
            "current_score": round(self.history[-1], 2),
            "regime":        self.regime(),
            "trend_5d":      self.trend(5),
            "avg_7d":        round(float(np.mean(self.history[-7:])), 2),
            "max_ever":      round(float(np.max(self.history)), 2),
            "sub_scores":    self.sub_scores[-1] if self.sub_scores else {},
        }
