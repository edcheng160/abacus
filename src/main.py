import lib.compute as comp
import lib.investment as inv
from lib.neural_trading import (
    DataFeed, FeatureEngine, TradingLSTM,
    RiskMetrics, SignalGenerator, WarTensionIndicator,
)

def run_calculator():
    obj = comp.Compute([9.0,3.0,2.0])
    obj.add()
    obj.multiply()
    obj.subtract()
    obj.divide()
    obj.power()

def run_investment_model():
    model = inv.InvestmentModel(1000.0)
    model.print_model()

def run_neural_trading():
    print("\n" + "=" * 60)
    print("  NEURAL TRADING SYSTEM  —  War-Volatility Edition")
    print("  (Educational demo — mock data, no live trades)")
    print("=" * 60)

    # --- Data ---
    print("\n[1/5] Loading market data and news headlines...")
    feed     = DataFeed(lookback_days=60, mock=True)
    prices   = feed.get_all_prices()
    headlines= feed.get_headlines()
    print(f"      Loaded {len(prices)} price series  |  {len(headlines)} headlines")

    # --- Features ---
    print("[2/5] Engineering features...")
    engine   = FeatureEngine()
    features = engine.build(prices, headlines)
    print(f"      Feature matrix: {features.shape}  (days × features)")

    # --- War indicators ---
    print("[3/5] Computing war tension indicators...")
    war_ind  = WarTensionIndicator()
    for i in range(len(features)):
        f = dict(zip(
            ["spy_ret_1d","spy_ret_5d","qqq_ret_1d","rsi_14","macd_signal",
             "bb_position","atr_pct","vix_norm","vix_chg_1d",
             "defense_ret","gold_ret","oil_ret","bond_ret","usd_ret",
             "war_tension","war_trend","news_sentiment"],
            features[i]
        ))
        war_ind.compute(
            defense_return = (f["defense_ret"] - 0.5) * 0.1,
            gold_return    = (f["gold_ret"]    - 0.5) * 0.06,
            oil_return     = (f["oil_ret"]     - 0.5) * 0.10,
            news_sentiment = -(f["news_sentiment"]),
            vix            = f["vix_norm"] * 76 + 9,
        )
    ws = war_ind.summary()
    print(f"      War tension: {ws['current_score']:.1f}/100  |  Regime: {ws['regime']}")
    print(f"      5-day trend: {ws['trend_5d']:+.3f}  |  7-day avg: {ws['avg_7d']:.1f}")

    # --- Neural network signal ---
    print("[4/5] Running LSTM neural network...")
    nn_model  = TradingLSTM(seq_len=20)
    sig_gen   = SignalGenerator(model=nn_model)
    signal    = sig_gen.generate(features, war_ind)
    print()
    sig_gen.print_signal(signal)

    # --- Backtest & risk metrics ---
    print("\n[5/5] Running walk-forward backtest...")
    spy_prices = prices["spy"]
    bt_metrics = sig_gen.backtest(features, spy_prices, war_ind, seq_len=20)
    print()
    bt_metrics.print_summary()

    print("\n  Selected headlines driving war tension score:")
    for h in headlines[:5]:
        print(f"    » {h}")
    print()

def main():
    run_calculator()
    run_investment_model()
    run_neural_trading()

if __name__ == "__main__":
    main()
