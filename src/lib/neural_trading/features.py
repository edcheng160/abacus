"""
features.py
Converts raw price arrays and news sentiment into the normalised feature
vector consumed by the LSTM.

Feature vector (17 dimensions):
  [0]  spy_return_1d        — S&P 500 1-day return
  [1]  spy_return_5d        — S&P 500 5-day return
  [2]  qqq_return_1d        — Nasdaq 1-day return
  [3]  rsi_14               — 14-day RSI on SPY  (0-1 normalised)
  [4]  macd_signal          — MACD histogram normalised
  [5]  bb_position          — Bollinger Band position  (0=lower, 1=upper)
  [6]  atr_pct              — ATR as % of price (volatility measure)
  [7]  vix_norm             — VIX normalised to [0,1] over 9-85 range
  [8]  vix_change_1d        — VIX 1-day change normalised
  [9]  defense_return_1d    — ITA (defense ETF) 1-day return
  [10] gold_return_1d       — GLD 1-day return
  [11] oil_return_1d        — USO 1-day return
  [12] bond_return_1d       — TLT 1-day return
  [13] usd_return_1d        — UUP 1-day return
  [14] war_tension          — WarTensionIndicator score (0-1 normalised)
  [15] war_trend            — 5-day tension slope normalised
  [16] news_sentiment       — keyword sentiment [-1,0] mapped to [0,1]
"""

import numpy as np
from .war_indicators import WarTensionIndicator, CONFLICT_KEYWORDS

FEATURE_DIM = 17
FEATURE_NAMES = [
    "spy_ret_1d", "spy_ret_5d", "qqq_ret_1d",
    "rsi_14", "macd_signal", "bb_position", "atr_pct",
    "vix_norm", "vix_chg_1d",
    "defense_ret", "gold_ret", "oil_ret", "bond_ret", "usd_ret",
    "war_tension", "war_trend", "news_sentiment",
]


# ---------------------------------------------------------------------------
def _returns(prices: np.ndarray, n: int = 1) -> np.ndarray:
    """Simple n-period returns series, same length as input (first n = 0)."""
    ret = np.zeros_like(prices)
    ret[n:] = (prices[n:] - prices[:-n]) / (prices[:-n] + 1e-9)
    return ret


def _rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    delta = np.diff(prices, prepend=prices[0])
    gain  = np.where(delta > 0, delta, 0.0)
    loss  = np.where(delta < 0, -delta, 0.0)
    rsi   = np.full(len(prices), 0.5)
    for i in range(period, len(prices)):
        avg_gain = gain[i-period+1:i+1].mean()
        avg_loss = loss[i-period+1:i+1].mean()
        rs = avg_gain / (avg_loss + 1e-9)
        rsi[i] = rs / (1 + rs)   # normalised to [0,1]
    return rsi


def _macd(prices: np.ndarray,
          fast: int = 12, slow: int = 26, signal: int = 9) -> np.ndarray:
    def ema(arr, span):
        k, out = 2 / (span + 1), np.zeros_like(arr)
        out[0] = arr[0]
        for i in range(1, len(arr)):
            out[i] = arr[i] * k + out[i-1] * (1 - k)
        return out
    macd_line   = ema(prices, fast) - ema(prices, slow)
    signal_line = ema(macd_line, signal)
    histogram   = macd_line - signal_line
    # Normalise by rolling std
    std = np.std(histogram) + 1e-9
    return np.clip(histogram / std, -3, 3) / 6 + 0.5  # → [0,1]


def _bollinger_position(prices: np.ndarray, window: int = 20) -> np.ndarray:
    """0 = at lower band, 0.5 = at mid, 1 = at upper band."""
    pos = np.full(len(prices), 0.5)
    for i in range(window, len(prices)):
        window_slice = prices[i-window:i]
        mid  = window_slice.mean()
        std  = window_slice.std() + 1e-9
        upper = mid + 2 * std
        lower = mid - 2 * std
        pos[i] = np.clip((prices[i] - lower) / (upper - lower + 1e-9), 0, 1)
    return pos


def _atr_pct(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Average True Range as fraction of price."""
    tr  = np.abs(np.diff(prices, prepend=prices[0]))
    atr = np.zeros_like(tr)
    atr[0] = tr[0]
    alpha = 1 / period
    for i in range(1, len(tr)):
        atr[i] = tr[i] * alpha + atr[i-1] * (1 - alpha)
    return np.clip(atr / (prices + 1e-9), 0, 0.1) / 0.1  # normalise to [0,1]


def _news_sentiment(headlines: list[str]) -> float:
    """
    Fast keyword-based conflict sentiment.
    Returns [0,1] where 1 = heavy conflict language, 0 = benign.
    """
    if not headlines:
        return 0.5
    hits = sum(
        1 for h in headlines
        for kw in CONFLICT_KEYWORDS if kw in h.lower()
    )
    density = hits / (len(headlines) * 3.0)
    conflict_score = min(density, 1.0)
    # Remap: 0 conflict → 0.0, full conflict → 1.0
    return conflict_score


# ---------------------------------------------------------------------------
class FeatureEngine:
    """
    Builds the (T × FEATURE_DIM) matrix for a rolling lookback window,
    ready to feed into TradingLSTM.
    """

    def __init__(self):
        self.war_ind = WarTensionIndicator()

    # ------------------------------------------------------------------
    def build(
        self,
        prices: dict[str, np.ndarray],
        headlines: list[str],
    ) -> np.ndarray:
        """
        Parameters
        ----------
        prices    : dict with keys matching MARKET_TICKERS labels
                    (spy, qqq, ita, gld, uso, tlt, vix, uup)
        headlines : list of news headline strings (most recent batch)

        Returns
        -------
        features : np.ndarray of shape (T, FEATURE_DIM)
                   T = shortest common length across all price series
        """
        T = min(len(v) for v in prices.values())
        # Trim all series to same length
        p = {k: v[-T:] for k, v in prices.items()}

        spy_r1  = _returns(p["spy"], 1)
        spy_r5  = _returns(p["spy"], 5)
        qqq_r1  = _returns(p["qqq"], 1)
        rsi     = _rsi(p["spy"])
        macd    = _macd(p["spy"])
        bb      = _bollinger_position(p["spy"])
        atr     = _atr_pct(p["spy"])

        vix_norm= np.clip((p["vix"] - 9) / (85 - 9), 0, 1)
        vix_chg = _returns(p["vix"], 1)
        vix_chg_norm = np.clip(vix_chg / 0.3 * 0.5 + 0.5, 0, 1)

        def_r  = _returns(p["ita"], 1)
        gld_r  = _returns(p["gld"], 1)
        oil_r  = _returns(p["uso"], 1)
        bnd_r  = _returns(p["tlt"], 1)
        usd_r  = _returns(p["uup"], 1)

        # Normalise returns to [0,1]: clip at ±5%
        def norm_ret(r): return np.clip(r / 0.05 * 0.5 + 0.5, 0, 1)
        spy_r1_n = norm_ret(spy_r1)
        spy_r5_n = np.clip(spy_r5 / 0.15 * 0.5 + 0.5, 0, 1)
        qqq_r1_n = norm_ret(qqq_r1)
        def_r_n  = norm_ret(def_r)
        gld_r_n  = norm_ret(gld_r)
        oil_r_n  = norm_ret(oil_r)
        bnd_r_n  = norm_ret(bnd_r)
        usd_r_n  = norm_ret(usd_r)

        # War tension per time step
        news_sent = _news_sentiment(headlines)
        war_scores = np.zeros(T)
        war_trends = np.zeros(T)
        ind = WarTensionIndicator()
        for i in range(T):
            ind.compute(
                defense_return = def_r[i],
                gold_return    = gld_r[i],
                oil_return     = oil_r[i],
                news_sentiment = news_sent * -1,   # our scale is [0,1]; indicator wants [-1,0]
                vix            = p["vix"][i],
            )
            war_scores[i] = ind.history[-1] / 100.0   # normalise to [0,1]
            war_trends[i] = np.clip(ind.trend(5) / 5.0 * 0.5 + 0.5, 0, 1)

        news_col = np.full(T, news_sent)

        features = np.column_stack([
            spy_r1_n, spy_r5_n, qqq_r1_n,
            rsi, macd, bb, atr,
            vix_norm, vix_chg_norm,
            def_r_n, gld_r_n, oil_r_n, bnd_r_n, usd_r_n,
            war_scores, war_trends, news_col,
        ])
        return features.astype(np.float32)

    # ------------------------------------------------------------------
    def latest_vector(
        self,
        prices: dict[str, np.ndarray],
        headlines: list[str],
    ) -> np.ndarray:
        """Return only the most recent feature row (1 × FEATURE_DIM)."""
        return self.build(prices, headlines)[-1:]
