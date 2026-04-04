"""
signals.py
Combines LSTM neural-network output, technical indicators, and war tension
into a final actionable trading signal with position sizing.

Signal pipeline
---------------
  1. LSTM output        → directional vote + raw confidence
  2. War tension regime → regime filter (blocks buys in EXTREME tension)
  3. Technical confirms → RSI, MACD, Bollinger Band agreement check
  4. Confidence gate    → signal suppressed if confidence < threshold
  5. Position sizing    → Kelly-fractional sizing adjusted for risk score

Output
------
  {
    "action":         "BUY" | "SELL" | "HOLD",
    "confidence":     0.0-1.0,
    "position_size":  0.0-1.0  (fraction of capital to deploy),
    "war_regime":     "LOW|MODERATE|ELEVATED|HIGH|EXTREME",
    "war_tension":    float (0-100),
    "war_trend":      "ESCALATING|STABLE|DE-ESCALATING",
    "technicals":     {"rsi": float, "macd": str, "bb": str},
    "reasoning":      [str, ...]   list of decision factors
  }
"""

import numpy as np
from .war_indicators import WarTensionIndicator
from .model          import TradingLSTM, SIGNAL_LABELS
from .features       import FeatureEngine, FEATURE_NAMES
from .risk_metrics   import RiskMetrics


# Confidence threshold below which we force HOLD
MIN_CONFIDENCE = 0.45

# Kelly fraction cap (never risk more than this per trade)
MAX_POSITION   = 0.25


# ---------------------------------------------------------------------------
class SignalGenerator:
    """
    End-to-end signal generator.  Call  .generate()  with the latest
    feature matrix and war-indicator state to get a full signal dict.
    """

    def __init__(
        self,
        model:       TradingLSTM | None = None,
        risk_metrics: RiskMetrics | None = None,
        min_confidence: float = MIN_CONFIDENCE,
    ):
        self.model          = model or TradingLSTM()
        self.risk_metrics   = risk_metrics or RiskMetrics()
        self.min_conf       = min_confidence
        self.signal_history: list[dict] = []

    # ------------------------------------------------------------------
    def generate(
        self,
        features:    np.ndarray,          # (T, FEATURE_DIM) from FeatureEngine
        war_ind:     WarTensionIndicator,  # live WarTensionIndicator instance
    ) -> dict:
        """
        Run the full signal pipeline and return an actionable signal dict.
        """
        # --- 1. LSTM prediction ---
        nn_out     = self.model.predict(features)
        nn_action  = nn_out["signal"]
        nn_conf    = nn_out["confidence"]
        nn_probs   = nn_out["probs"]
        reasoning  = []

        # --- 2. Extract latest feature values ---
        latest = features[-1]
        feat   = dict(zip(FEATURE_NAMES, latest))

        rsi      = feat.get("rsi_14",     0.5)
        macd     = feat.get("macd_signal", 0.5)
        bb       = feat.get("bb_position", 0.5)
        vix_n    = feat.get("vix_norm",    0.3)
        war_t    = feat.get("war_tension", 0.0) * 100.0   # back to 0-100 scale
        war_tr   = feat.get("war_trend",   0.5)

        war_regime = war_ind.regime()
        war_slope  = war_ind.trend(5)
        if   war_slope >  1.0: war_trend_label = "ESCALATING"
        elif war_slope < -1.0: war_trend_label = "DE-ESCALATING"
        else:                  war_trend_label = "STABLE"

        # --- 3. Technical confirms ---
        rsi_signal   = "oversold" if rsi < 0.35 else ("overbought" if rsi > 0.65 else "neutral")
        macd_signal  = "bullish"  if macd > 0.55 else ("bearish" if macd < 0.45 else "neutral")
        bb_signal    = "at_lower" if bb < 0.25 else ("at_upper" if bb > 0.75 else "mid_range")

        tech_confirms_buy  = (rsi_signal == "oversold"   and macd_signal != "bearish")
        tech_confirms_sell = (rsi_signal == "overbought" and macd_signal != "bullish")

        reasoning.append(f"LSTM→{nn_action}  conf={nn_conf:.2f}")
        reasoning.append(f"RSI={rsi:.2f}({rsi_signal})  MACD={macd_signal}  BB={bb_signal}")
        reasoning.append(f"War tension={war_t:.1f}/100  regime={war_regime}  trend={war_trend_label}")

        # --- 4. Regime filter ---
        action = nn_action
        if war_regime == "EXTREME" and action == "BUY":
            action = "HOLD"
            reasoning.append("BLOCKED: no buys during EXTREME war tension")
        if war_regime in ("HIGH", "EXTREME") and action == "BUY" and not tech_confirms_buy:
            action = "HOLD"
            reasoning.append("BLOCKED: buy signal lacks technical confirmation in HIGH tension")

        # Conflict escalation → lean bearish
        if war_trend_label == "ESCALATING" and action == "BUY":
            # Downgrade buy confidence
            nn_conf = nn_conf * 0.75
            reasoning.append("REDUCED CONF: conflict is escalating")

        # --- 5. Confidence gate ---
        if nn_conf < self.min_conf and action != "HOLD":
            action = "HOLD"
            reasoning.append(f"FILTERED: confidence {nn_conf:.2f} < threshold {self.min_conf}")

        # --- 6. Position sizing (fractional Kelly) ---
        position_size = self._kelly_size(
            action    = action,
            confidence= nn_conf,
            war_t     = war_t,
            vix_n     = vix_n,
        )

        signal = {
            "action":        action,
            "confidence":    round(nn_conf, 4),
            "position_size": round(position_size, 4),
            "war_regime":    war_regime,
            "war_tension":   round(war_t, 2),
            "war_trend":     war_trend_label,
            "technicals": {
                "rsi":      round(rsi, 3),
                "rsi_signal":  rsi_signal,
                "macd":        macd_signal,
                "bb":          bb_signal,
                "vix_norm":  round(vix_n, 3),
            },
            "nn_probs":  {k: round(v, 4) for k, v in nn_probs.items()},
            "reasoning": reasoning,
        }
        self.signal_history.append(signal)
        return signal

    # ------------------------------------------------------------------
    def _kelly_size(
        self,
        action:     str,
        confidence: float,
        war_t:      float,
        vix_n:      float,
    ) -> float:
        """
        Fractional Kelly criterion for position sizing.
        f* = (p * b - q) / b  where b = win/loss ratio assumption
        Capped at MAX_POSITION and scaled down by war tension + VIX.
        """
        if action == "HOLD":
            return 0.0

        p  = confidence          # estimated win probability
        q  = 1.0 - p
        b  = max(self.risk_metrics.avg_win_loss_ratio(), 1.2)  # R-ratio
        kelly = (p * b - q) / (b + 1e-9)
        kelly = max(kelly, 0.0)

        # Quarter-Kelly for conservatism
        kelly *= 0.25

        # Scale down in high tension / high vol environments
        tension_penalty = 1.0 - (war_t / 100.0) * 0.6   # 0.4 at max tension
        vol_penalty     = 1.0 - vix_n * 0.4              # 0.6 at max VIX

        sized = kelly * tension_penalty * vol_penalty
        return float(np.clip(sized, 0.0, MAX_POSITION))

    # ------------------------------------------------------------------
    def print_signal(self, signal: dict | None = None):
        s = signal or (self.signal_history[-1] if self.signal_history else {})
        if not s:
            print("No signal generated yet.")
            return

        action = s["action"]
        arrow  = {"BUY": "▲", "SELL": "▼", "HOLD": "●"}.get(action, "?")
        color_tag = {"BUY": "[+]", "SELL": "[-]", "HOLD": "[=]"}.get(action, "")

        print("=" * 60)
        print(f"  TRADING SIGNAL   {color_tag} {arrow} {action}")
        print("=" * 60)
        print(f"  Confidence       : {s['confidence']*100:.1f}%")
        print(f"  Position Size    : {s['position_size']*100:.1f}% of capital")
        print(f"  War Tension      : {s['war_tension']:.1f}/100  ({s['war_regime']})")
        print(f"  War Trend        : {s['war_trend']}")
        print(f"  RSI              : {s['technicals']['rsi']:.3f}  ({s['technicals']['rsi_signal']})")
        print(f"  MACD             : {s['technicals']['macd']}")
        print(f"  Bollinger Band   : {s['technicals']['bb']}")
        print(f"  VIX (norm)       : {s['technicals']['vix_norm']:.3f}")
        print("-" * 60)
        print("  NN Probabilities :")
        for label, prob in s["nn_probs"].items():
            bar = "#" * int(prob * 30)
            print(f"    {label:<5} {prob*100:>5.1f}%  {bar}")
        print("-" * 60)
        print("  Reasoning:")
        for r in s["reasoning"]:
            print(f"    • {r}")
        print("=" * 60)

    # ------------------------------------------------------------------
    def backtest(
        self,
        all_features:  np.ndarray,    # (T, FEATURE_DIM)
        price_series:  np.ndarray,    # (T,) actual prices for P&L
        war_ind:       WarTensionIndicator,
        seq_len:       int = 20,
    ) -> RiskMetrics:
        """
        Simple walk-forward backtest over feature history.
        Returns a RiskMetrics object populated with trade returns.
        """
        T             = len(all_features)
        trade_returns = []
        equity        = [1.0]
        capital       = 1.0
        position      = 0.0   # current exposure (fraction of capital, signed)
        entry_price   = None

        for t in range(seq_len, T - 1):
            window  = all_features[max(0, t - seq_len): t]
            signal  = self.generate(window, war_ind)
            action  = signal["action"]
            size    = signal["position_size"]
            price_t = price_series[t]
            price_n = price_series[t + 1]

            # Close any open position
            if position != 0 and entry_price is not None:
                ret   = (price_t - entry_price) / entry_price * np.sign(position)
                trade_returns.append(float(ret * abs(position)))
                capital *= (1 + ret * abs(position))
                equity.append(capital)
                position    = 0
                entry_price = None

            # Open new position
            if action == "BUY":
                position    = size
                entry_price = price_t
            elif action == "SELL":
                position    = -size
                entry_price = price_t

        return RiskMetrics(
            trade_returns=trade_returns,
            equity_curve=equity,
        )
