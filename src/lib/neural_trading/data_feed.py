"""
data_feed.py
Fetches market prices and news headlines.

Live mode  : uses yfinance (pip install yfinance) + RSS news feeds.
Mock mode  : generates synthetic war-period market data for offline use.
             Automatically falls back to mock when yfinance is not installed
             or network is unavailable.
"""

import numpy as np
import datetime
import urllib.request
import json
import re

# ---------------------------------------------------------------------------
# RSS feeds – public, no API key required
# ---------------------------------------------------------------------------
NEWS_FEEDS = {
    "reuters_world":  "https://feeds.reuters.com/reuters/worldNews",
    "bbc_world":      "http://feeds.bbci.co.uk/news/world/rss.xml",
    "ap_top":         "https://rsshub.app/ap/topics/apf-topnews",
}

# Tickers to track for the full feature vector
MARKET_TICKERS = {
    "spy":  "SPY",    # S&P 500
    "qqq":  "QQQ",    # Nasdaq 100
    "ita":  "ITA",    # US defense ETF
    "gld":  "GLD",    # Gold
    "uso":  "USO",    # Crude oil
    "tlt":  "TLT",    # Long treasury bonds
    "vix":  "^VIX",   # Volatility index
    "uup":  "UUP",    # US Dollar index
    "eur":  "EURUSD=X",
    "jpy":  "JPY=X",
}


# ---------------------------------------------------------------------------
class DataFeed:
    """
    Provides a unified interface to market prices and news headlines.
    Falls back to synthetic data automatically when live sources fail.
    """

    def __init__(self, lookback_days: int = 60, mock: bool = False):
        self.lookback = lookback_days
        self.mock = mock
        self._yf_available = self._check_yfinance()

    # ------------------------------------------------------------------
    @staticmethod
    def _check_yfinance() -> bool:
        try:
            import yfinance  # noqa: F401
            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    def get_prices(self, ticker: str) -> np.ndarray:
        """Return array of daily closing prices (oldest → newest)."""
        if not self.mock and self._yf_available:
            return self._live_prices(ticker)
        return self._mock_prices(ticker)

    def _live_prices(self, ticker: str) -> np.ndarray:
        try:
            import yfinance as yf
            end   = datetime.date.today()
            start = end - datetime.timedelta(days=self.lookback + 10)
            df = yf.download(ticker, start=str(start), end=str(end),
                             progress=False, auto_adjust=True)
            return df["Close"].dropna().values[-self.lookback:]
        except Exception:
            return self._mock_prices(ticker)

    def _mock_prices(self, ticker: str) -> np.ndarray:
        """
        Synthetic price series with embedded war-period shock pattern:
          Phase 1 (days 0-15):  calm, low vol
          Phase 2 (days 16-25): conflict onset – sharp drop / spike
          Phase 3 (days 26-45): elevated vol, trending recovery or deterioration
          Phase 4 (days 46-60): new equilibrium
        """
        rng = np.random.default_rng(seed=abs(hash(ticker)) % (2**31))
        n   = self.lookback

        # Base drift + volatility profile per asset class
        profiles = {
            "ITA": (0.0008, 0.012, +1.0),  # defense: positive shock
            "GLD": (0.0004, 0.010, +0.8),  # gold: safe-haven bid
            "USO": (0.0006, 0.025, +1.2),  # oil: supply shock spike
            "TLT": (0.0002, 0.009, +0.5),  # bonds: flight to quality
            "UUP": (0.0001, 0.006, +0.4),  # dollar: safe haven
            "SPY": (0.0003, 0.015, -1.0),  # equities: sell-off
            "QQQ": (0.0003, 0.018, -1.3),  # tech: larger sell-off
            "^VIX":(0.000,  0.000,  0.0),  # handled separately below
        }
        if ticker.upper() == "^VIX":
            return self._mock_vix(rng, n)

        drift, vol, shock_dir = profiles.get(ticker.upper(), (0.0003, 0.015, -0.5))
        returns = rng.normal(drift, vol, n)

        # Embed shock at day 20-25
        shock_start = min(20, n // 3)
        shock_len   = 5
        for i in range(shock_start, min(shock_start + shock_len, n)):
            returns[i] += shock_dir * rng.uniform(0.01, 0.03)

        # Reconstruct prices from returns starting at a canonical base
        bases = {"ITA": 110, "GLD": 185, "USO": 65, "TLT": 98,
                 "UUP": 28, "SPY": 450, "QQQ": 370}
        base = bases.get(ticker.upper(), 100.0)
        prices = base * np.cumprod(1 + returns)
        return prices

    @staticmethod
    def _mock_vix(rng: np.random.Generator, n: int) -> np.ndarray:
        vix = np.full(n, 16.0)
        shock = min(20, n // 3)
        for i in range(n):
            if i < shock:
                vix[i] = 16 + rng.normal(0, 1)
            elif i < shock + 5:
                vix[i] = 16 + (i - shock) * 5 + rng.normal(0, 2)
            elif i < shock + 20:
                vix[i] = 41 - (i - shock - 5) * 1.2 + rng.normal(0, 2)
            else:
                vix[i] = max(20, 41 - (i - shock) * 0.6 + rng.normal(0, 1.5))
        return np.clip(vix, 9, 85)

    # ------------------------------------------------------------------
    def get_all_prices(self) -> dict[str, np.ndarray]:
        """Fetch all tracked tickers and return {label: price_array}."""
        return {label: self.get_prices(ticker)
                for label, ticker in MARKET_TICKERS.items()}

    # ------------------------------------------------------------------
    def get_headlines(self, max_headlines: int = 30) -> list[str]:
        """
        Fetch recent news headlines from RSS feeds.
        Returns list of headline strings; falls back to mock on failure.
        """
        if self.mock:
            return self._mock_headlines()
        headlines = []
        for name, url in NEWS_FEEDS.items():
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    xml = resp.read().decode("utf-8", errors="ignore")
                titles = re.findall(r"<title>(.*?)</title>", xml, re.DOTALL)
                headlines.extend([t.strip() for t in titles[1:] if t.strip()])
            except Exception:
                continue
        return (headlines or self._mock_headlines())[:max_headlines]

    @staticmethod
    def _mock_headlines() -> list[str]:
        return [
            "NATO allies increase military support amid escalating conflict",
            "Oil prices surge on fears of supply disruption from war zone",
            "Gold hits 6-month high as investors flee to safe havens",
            "Missile strikes target civilian infrastructure, casualties reported",
            "Ceasefire talks collapse as fighting intensifies on eastern front",
            "Defense contractors LMT and RTX surge on new government contracts",
            "Sanctions tighten: central bank assets frozen, exports halted",
            "Refugees cross border as military offensive pushes deeper inland",
            "Markets volatile as conflict enters third week with no end in sight",
            "G7 emergency summit called to coordinate response to invasion",
            "Drone strikes disrupt grain exports, food prices spike globally",
            "Pentagon authorizes additional weapons package amid ongoing war",
            "Energy crisis deepens as pipeline shutdown cuts supply to Europe",
            "Stock markets plunge on fears of wider regional conflict",
            "UN Security Council deadlocked over ceasefire resolution",
        ]
