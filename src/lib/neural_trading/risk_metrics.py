"""
risk_metrics.py
Averaged composite metrics for risk and trading success.

Individual metrics
------------------
  sharpe_ratio      — return per unit of total risk (annualised, rf=0)
  sortino_ratio     — return per unit of downside risk
  max_drawdown      — worst peak-to-trough loss (0-1, lower = better)
  win_rate          — fraction of trades that were profitable
  profit_factor     — gross profit / gross loss
  calmar_ratio      — annualised return / max drawdown
  avg_win_loss      — average win size / average loss size (R-ratio)
  volatility_ann    — annualised return volatility

Composite scores
----------------
  RISK SCORE  (0-100):  higher = MORE risky
  SUCCESS SCORE (0-100): higher = better performance
  EDGE SCORE  (0-100):  combined signal strength (geometric mean)
"""

import numpy as np


TRADING_DAYS = 252


# ---------------------------------------------------------------------------
class RiskMetrics:
    """
    Compute and aggregate all performance/risk metrics from a list of
    trade returns (each entry = fractional P&L for one completed trade,
    e.g. +0.03 = +3%, -0.015 = -1.5%).

    Also accepts a daily equity curve (running portfolio value) for
    drawdown and volatility calculations.
    """

    def __init__(
        self,
        trade_returns:  list[float] | None = None,
        equity_curve:   list[float] | None = None,
        risk_free_rate: float = 0.0,
    ):
        self.trade_returns  = np.array(trade_returns or [], dtype=float)
        self.equity_curve   = np.array(equity_curve  or [], dtype=float)
        self.rfr            = risk_free_rate / TRADING_DAYS   # daily rf

    # ------------------------------------------------------------------
    # Individual metrics
    # ------------------------------------------------------------------
    def sharpe_ratio(self) -> float:
        r = self._daily_returns()
        if len(r) < 2:
            return 0.0
        excess = r - self.rfr
        return float(np.mean(excess) / (np.std(excess) + 1e-9) * np.sqrt(TRADING_DAYS))

    def sortino_ratio(self) -> float:
        r = self._daily_returns()
        if len(r) < 2:
            return 0.0
        excess    = r - self.rfr
        downside  = excess[excess < 0]
        down_std  = np.std(downside) if len(downside) > 1 else 1e-9
        return float(np.mean(excess) / (down_std + 1e-9) * np.sqrt(TRADING_DAYS))

    def max_drawdown(self) -> float:
        """Returns max drawdown as a positive fraction (0.20 = 20% drawdown)."""
        curve = self._equity()
        if len(curve) < 2:
            return 0.0
        peak    = np.maximum.accumulate(curve)
        dd      = (curve - peak) / (peak + 1e-9)
        return float(-dd.min())

    def win_rate(self) -> float:
        if len(self.trade_returns) == 0:
            return 0.0
        return float(np.sum(self.trade_returns > 0) / len(self.trade_returns))

    def profit_factor(self) -> float:
        wins  = self.trade_returns[self.trade_returns > 0]
        losses= self.trade_returns[self.trade_returns < 0]
        if len(losses) == 0 or losses.sum() == 0:
            return float("inf") if len(wins) > 0 else 1.0
        return float(wins.sum() / (-losses.sum()))

    def calmar_ratio(self) -> float:
        mdd = self.max_drawdown()
        if mdd < 1e-9:
            return 0.0
        ann_ret = self._annualised_return()
        return float(ann_ret / mdd)

    def avg_win_loss_ratio(self) -> float:
        """Average winner / average loser (R-ratio)."""
        wins  = self.trade_returns[self.trade_returns > 0]
        losses= self.trade_returns[self.trade_returns < 0]
        if len(losses) == 0 or len(wins) == 0:
            return 1.0
        return float(wins.mean() / (-losses.mean()))

    def annualised_volatility(self) -> float:
        r = self._daily_returns()
        if len(r) < 2:
            return 0.0
        return float(np.std(r) * np.sqrt(TRADING_DAYS))

    def annualised_return(self) -> float:
        return self._annualised_return()

    # ------------------------------------------------------------------
    # Composite scores
    # ------------------------------------------------------------------
    def risk_score(self) -> float:
        """
        0-100 composite risk score.  Higher = more risk.
        Components:
          - Max drawdown   (40%): high drawdown → high risk
          - Ann. vol       (30%): high vol → high risk
          - Loss frequency (20%): 1 - win_rate
          - Sortino inverse(10%): poor downside management
        """
        mdd     = np.clip(self.max_drawdown() / 0.50, 0, 1)       # 50% drawdown → max
        vol     = np.clip(self.annualised_volatility() / 1.0, 0, 1) # 100% ann vol → max
        loss_fr = 1.0 - self.win_rate()
        sortino = np.clip(1.0 - self.sortino_ratio() / 5.0, 0, 1)  # sortino 5+ → min risk

        score = (mdd * 40 + vol * 30 + loss_fr * 20 + sortino * 10)
        return round(float(score), 2)

    def success_score(self) -> float:
        """
        0-100 composite success score.  Higher = better performance.
        Components:
          - Sharpe ratio   (30%): risk-adjusted return
          - Win rate       (20%): raw hit rate
          - Profit factor  (20%): gross profit quality
          - Calmar ratio   (15%): return vs drawdown
          - R-ratio        (15%): average winner vs loser
        """
        sharpe  = np.clip(self.sharpe_ratio()   / 3.0, 0, 1)   # Sharpe 3+ → max
        wr      = self.win_rate()
        pf      = np.clip((self.profit_factor() - 1) / 3.0, 0, 1)  # PF 4+ → max
        calmar  = np.clip(self.calmar_ratio()   / 3.0, 0, 1)
        rr      = np.clip((self.avg_win_loss_ratio() - 1) / 3.0, 0, 1)

        score = (sharpe * 30 + wr * 20 + pf * 20 + calmar * 15 + rr * 15)
        return round(float(score), 2)

    def edge_score(self) -> float:
        """
        0-100 combined edge.  Geometric mean of risk (inverted) and success.
        A high edge score means: good returns AND controlled risk.
        """
        s = self.success_score() / 100.0
        r = 1.0 - self.risk_score() / 100.0
        edge = np.sqrt(max(s * r, 0)) * 100
        return round(float(edge), 2)

    # ------------------------------------------------------------------
    def summary(self) -> dict:
        return {
            # Raw metrics
            "sharpe_ratio":       round(self.sharpe_ratio(),        3),
            "sortino_ratio":      round(self.sortino_ratio(),       3),
            "max_drawdown_pct":   round(self.max_drawdown() * 100,  2),
            "win_rate_pct":       round(self.win_rate() * 100,      2),
            "profit_factor":      round(self.profit_factor(),       3),
            "calmar_ratio":       round(self.calmar_ratio(),        3),
            "avg_win_loss_ratio": round(self.avg_win_loss_ratio(),  3),
            "ann_volatility_pct": round(self.annualised_volatility() * 100, 2),
            "ann_return_pct":     round(self.annualised_return() * 100,     2),
            # Composite scores
            "risk_score":         self.risk_score(),
            "success_score":      self.success_score(),
            "edge_score":         self.edge_score(),
        }

    def print_summary(self):
        s = self.summary()
        w = 52
        print("=" * w)
        print("  RISK & SUCCESS METRICS")
        print("=" * w)
        print(f"  {'Sharpe Ratio':<28} {s['sharpe_ratio']:>8.3f}")
        print(f"  {'Sortino Ratio':<28} {s['sortino_ratio']:>8.3f}")
        print(f"  {'Max Drawdown':<28} {s['max_drawdown_pct']:>7.2f}%")
        print(f"  {'Win Rate':<28} {s['win_rate_pct']:>7.2f}%")
        print(f"  {'Profit Factor':<28} {s['profit_factor']:>8.3f}")
        print(f"  {'Calmar Ratio':<28} {s['calmar_ratio']:>8.3f}")
        print(f"  {'Avg Win / Avg Loss (R)':<28} {s['avg_win_loss_ratio']:>8.3f}")
        print(f"  {'Ann. Volatility':<28} {s['ann_volatility_pct']:>7.2f}%")
        print(f"  {'Ann. Return':<28} {s['ann_return_pct']:>7.2f}%")
        print("-" * w)
        print(f"  {'RISK SCORE  (0=safe, 100=extreme)':<28} {s['risk_score']:>7.1f}")
        print(f"  {'SUCCESS SCORE (0=poor, 100=great)':<28} {s['success_score']:>7.1f}")
        print(f"  {'EDGE SCORE  (combined)':<28} {s['edge_score']:>7.1f}")
        print("=" * w)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _equity(self) -> np.ndarray:
        if len(self.equity_curve) > 0:
            return self.equity_curve
        # Reconstruct from trade returns if no curve provided
        if len(self.trade_returns) > 0:
            return np.cumprod(1 + self.trade_returns)
        return np.array([1.0, 1.0])

    def _daily_returns(self) -> np.ndarray:
        if len(self.equity_curve) > 1:
            c = self.equity_curve
            return (c[1:] - c[:-1]) / (c[:-1] + 1e-9)
        return self.trade_returns if len(self.trade_returns) > 0 else np.array([0.0])

    def _annualised_return(self) -> float:
        curve = self._equity()
        if len(curve) < 2:
            return 0.0
        total   = curve[-1] / (curve[0] + 1e-9)
        periods = len(curve)
        return float(total ** (TRADING_DAYS / periods) - 1)
