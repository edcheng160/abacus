"""
generate_dashboard_data.py
Runs the neural trading system and writes dashboard_data.json for the HTML map.
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from lib.neural_trading import (
    DataFeed, FeatureEngine, TradingLSTM,
    RiskMetrics, SignalGenerator, WarTensionIndicator,
)
from lib.neural_trading.features import FEATURE_NAMES

def run():
    feed     = DataFeed(lookback_days=60, mock=True)
    prices   = feed.get_all_prices()
    headlines= feed.get_headlines()
    engine   = FeatureEngine()
    features = engine.build(prices, headlines)

    war_ind  = WarTensionIndicator()
    for i in range(len(features)):
        f = dict(zip(FEATURE_NAMES, features[i]))
        war_ind.compute(
            defense_return = (f["defense_ret"] - 0.5) * 0.1,
            gold_return    = (f["gold_ret"]    - 0.5) * 0.06,
            oil_return     = (f["oil_ret"]     - 0.5) * 0.10,
            news_sentiment = -(f["news_sentiment"]),
            vix            = f["vix_norm"] * 76 + 9,
        )

    nn_model = TradingLSTM(seq_len=20)
    sig_gen  = SignalGenerator(model=nn_model)

    # Walk-forward: generate signal for each day
    SEQ = 20
    T   = len(features)
    days, war_scores, tensions, signals_out = [], [], [], []
    spy  = prices["spy"].tolist()
    vix  = prices["vix"].tolist()
    ita  = prices["ita"].tolist()
    gld  = prices["gld"].tolist()
    uso  = prices["uso"].tolist()

    war_ind2 = WarTensionIndicator()
    for t in range(SEQ, T):
        window = features[max(0, t-SEQ):t]
        f = dict(zip(FEATURE_NAMES, features[t]))
        war_ind2.compute(
            defense_return = (f["defense_ret"] - 0.5) * 0.1,
            gold_return    = (f["gold_ret"]    - 0.5) * 0.06,
            oil_return     = (f["oil_ret"]     - 0.5) * 0.10,
            news_sentiment = -(f["news_sentiment"]),
            vix            = f["vix_norm"] * 76 + 9,
        )
        sig = sig_gen.generate(window, war_ind2)
        days.append(t)
        war_scores.append(round(war_ind2.history[-1], 2))
        tensions.append(war_ind2.regime())
        signals_out.append({
            "day": t,
            "action": sig["action"],
            "confidence": round(sig["confidence"] * 100, 1),
            "position_size": round(sig["position_size"] * 100, 1),
            "war_tension": sig["war_tension"],
            "war_regime": sig["war_regime"],
            "war_trend": sig["war_trend"],
            "nn_probs": sig["nn_probs"],
            "technicals": sig["technicals"],
            "reasoning": sig["reasoning"],
        })

    # Backtest metrics
    bt = sig_gen.backtest(features, prices["spy"], war_ind2, seq_len=SEQ)
    metrics = bt.summary()

    latest_sig = signals_out[-1] if signals_out else {}
    ws = war_ind2.summary()

    data = {
        "days": days,
        "spy":  [round(v, 2) for v in spy[SEQ:]],
        "vix":  [round(v, 2) for v in vix[SEQ:]],
        "ita":  [round(v, 2) for v in ita[SEQ:]],
        "gld":  [round(v, 2) for v in gld[SEQ:]],
        "uso":  [round(v, 2) for v in uso[SEQ:]],
        "war_scores": war_scores,
        "signals": signals_out,
        "latest_signal": latest_sig,
        "war_summary": ws,
        "risk_metrics": metrics,
        "headlines": headlines[:8],
        "feature_names": FEATURE_NAMES,
        "latest_features": [round(float(v), 4) for v in features[-1]],
    }

    import numpy as np

    class _Enc(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, (np.floating, np.float32, np.float64)): return float(o)
            if isinstance(o, (np.integer,)):                          return int(o)
            return super().default(o)

    out = os.path.join(os.path.dirname(__file__), "dashboard_data.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2, cls=_Enc)
    print(f"Wrote {out}")
    return data

if __name__ == "__main__":
    run()


def build_html(data: dict) -> str:
    import json as _json

    class _Enc(_json.JSONEncoder):
        def default(self, o):
            try:
                import numpy as np
                if isinstance(o, (np.floating, np.float32, np.float64)): return float(o)
                if isinstance(o, np.integer): return int(o)
            except ImportError:
                pass
            return super().default(o)

    json_blob = _json.dumps(data, cls=_Enc)

    action      = data.get("latest_signal", {}).get("action", "HOLD")
    war_score   = data.get("war_summary", {}).get("current_score", 0)
    war_regime  = data.get("war_summary", {}).get("regime", "UNKNOWN")
    risk_score  = data.get("risk_metrics", {}).get("risk_score", 0)
    succ_score  = data.get("risk_metrics", {}).get("success_score", 0)
    edge_score  = data.get("risk_metrics", {}).get("edge_score", 0)

    action_color = {"BUY": "#00e676", "SELL": "#ff1744", "HOLD": "#ffc107"}.get(action, "#ffc107")
    regime_color = {"LOW":"#00e676","MODERATE":"#69f0ae","ELEVATED":"#ffc107",
                    "HIGH":"#ff6d00","EXTREME":"#ff1744"}.get(war_regime, "#ffc107")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>War-Volatility Neural Trading Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0a0e1a;color:#e0e6f0;font-family:'Segoe UI',monospace;font-size:13px}}
  h1{{font-size:1.1rem;letter-spacing:2px;color:#7ecfff;text-transform:uppercase}}
  h2{{font-size:.75rem;letter-spacing:1.5px;color:#7ecfff;text-transform:uppercase;margin-bottom:8px}}
  header{{background:#0d1526;border-bottom:1px solid #1e2d4a;padding:12px 20px;display:flex;align-items:center;gap:16px}}
  .tag{{font-size:.65rem;padding:2px 8px;border-radius:3px;font-weight:700;letter-spacing:1px}}
  .grid{{display:grid;grid-template-columns:220px 1fr 260px;grid-template-rows:auto auto auto;gap:10px;padding:10px}}
  .card{{background:#0d1526;border:1px solid #1e2d4a;border-radius:6px;padding:14px}}
  /* Signal card */
  #signal-card{{text-align:center}}
  .signal-action{{font-size:2.4rem;font-weight:700;letter-spacing:3px;margin:8px 0}}
  .signal-conf{{font-size:.85rem;color:#aab}}
  .signal-size{{font-size:.75rem;color:#7ecfff;margin-top:4px}}
  /* Gauge arc */
  .gauge-wrap{{display:flex;flex-direction:column;align-items:center;margin:6px 0}}
  canvas.gauge{{max-width:160px}}
  /* Architecture */
  #arch-card{{grid-column:3;grid-row:1/4}}
  .arch-svg{{width:100%;height:100%;min-height:480px}}
  /* Sub-scores */
  .sub-grid{{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:8px}}
  .sub-item{{background:#111c30;border-radius:4px;padding:5px 8px}}
  .sub-label{{color:#7a8aaa;font-size:.68rem}}
  .sub-val{{font-weight:700;font-size:.95rem}}
  /* Feature bars */
  .feat-bar-wrap{{display:flex;align-items:center;gap:6px;margin:2px 0}}
  .feat-name{{width:90px;color:#7a8aaa;font-size:.65rem;text-align:right;flex-shrink:0}}
  .feat-track{{flex:1;height:10px;background:#111c30;border-radius:5px;overflow:hidden}}
  .feat-fill{{height:100%;border-radius:5px;transition:width .4s}}
  .feat-val{{width:36px;font-size:.65rem;color:#aab;text-align:right}}
  /* Headlines */
  .headline{{border-left:3px solid #1e2d4a;padding:4px 8px;margin:4px 0;font-size:.72rem;color:#b0bcd0;line-height:1.4}}
  .headline.hot{{border-color:#ff6d00;color:#ffd180}}
  /* Reasoning */
  .reason{{font-size:.7rem;color:#7a8aaa;padding:2px 0;border-bottom:1px solid #111c30}}
  /* Probability bars */
  .prob-row{{display:flex;align-items:center;gap:6px;margin:3px 0}}
  .prob-label{{width:36px;font-size:.72rem;font-weight:700}}
  .prob-track{{flex:1;height:14px;background:#111c30;border-radius:4px;overflow:hidden}}
  .prob-fill{{height:100%;border-radius:4px}}
  .prob-pct{{width:38px;font-size:.72rem;color:#aab;text-align:right}}
  /* Responsive scroll */
  .chart-wrap{{position:relative;height:180px}}
  .chart-wrap-sm{{position:relative;height:130px}}
</style>
</head>
<body>
<header>
  <h1>&#9889; War-Volatility Neural Trading</h1>
  <span class="tag" style="background:#1e2d4a;color:#7ecfff">EDUCATIONAL DEMO</span>
  <span class="tag" style="background:#1a2a10;color:#69f0ae">MOCK DATA</span>
  <span style="margin-left:auto;color:#556;font-size:.7rem">Powered by LSTM + War Tension Indicators</span>
</header>

<div class="grid">

  <!-- ── Col 1 Row 1: Signal ── -->
  <div class="card" id="signal-card">
    <h2>Current Signal</h2>
    <div class="signal-action" style="color:{action_color}">{action}</div>
    <div class="signal-conf" id="conf-label">Loading...</div>
    <div class="signal-size" id="size-label"></div>
    <hr style="border-color:#1e2d4a;margin:10px 0"/>
    <h2>NN Probabilities</h2>
    <div id="prob-bars"></div>
    <hr style="border-color:#1e2d4a;margin:10px 0"/>
    <h2>Reasoning</h2>
    <div id="reasoning"></div>
  </div>

  <!-- ── Col 1 Row 2: War Gauge ── -->
  <div class="card">
    <h2>War Tension Score</h2>
    <div class="gauge-wrap">
      <canvas id="warGauge" class="gauge" height="110"></canvas>
      <div style="font-size:1.6rem;font-weight:700;color:{regime_color}" id="war-score-label">{war_score:.1f}</div>
      <div style="font-size:.75rem;color:{regime_color};letter-spacing:1px">{war_regime}</div>
    </div>
    <h2 style="margin-top:8px">Sub-Scores</h2>
    <div class="sub-grid" id="sub-scores"></div>
  </div>

  <!-- ── Col 1 Row 3: Risk Scores ── -->
  <div class="card">
    <h2>Composite Scores</h2>
    <div class="gauge-wrap">
      <canvas id="riskGauge"  class="gauge" height="90"></canvas>
      <div style="color:#ff6d00;font-size:.75rem">RISK &nbsp;{risk_score:.0f}/100</div>
    </div>
    <div class="gauge-wrap">
      <canvas id="succGauge"  class="gauge" height="90"></canvas>
      <div style="color:#00e676;font-size:.75rem">SUCCESS &nbsp;{succ_score:.0f}/100</div>
    </div>
    <div class="gauge-wrap">
      <canvas id="edgeGauge"  class="gauge" height="90"></canvas>
      <div style="color:#7ecfff;font-size:.75rem">EDGE &nbsp;{edge_score:.0f}/100</div>
    </div>
  </div>

  <!-- ── Col 2 Row 1-2: Price + War Timeline ── -->
  <div class="card" style="grid-column:2;grid-row:1/3">
    <h2>SPY Price &amp; War Tension Timeline</h2>
    <div class="chart-wrap" style="height:200px"><canvas id="priceChart"></canvas></div>
    <div class="chart-wrap-sm" style="margin-top:10px"><canvas id="warChart"></canvas></div>
    <div class="chart-wrap-sm" style="margin-top:10px"><canvas id="assetChart"></canvas></div>
  </div>

  <!-- ── Col 2 Row 3: Features ── -->
  <div class="card" style="grid-column:2;grid-row:3">
    <h2>Latest Feature Vector (17 dims)</h2>
    <div id="feat-bars"></div>
  </div>

  <!-- ── Col 3: Architecture + Headlines ── -->
  <div class="card" id="arch-card">
    <h2>System Architecture</h2>
    <svg class="arch-svg" viewBox="0 0 240 520" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill="#7ecfff" opacity=".7"/>
        </marker>
      </defs>
      <!-- Boxes -->
      <!-- 1 DataFeed -->
      <rect x="40" y="10" width="160" height="44" rx="6" fill="#112240" stroke="#1e4a8a" stroke-width="1.5"/>
      <text x="120" y="28" text-anchor="middle" fill="#7ecfff" font-size="10" font-weight="700">DATA FEED</text>
      <text x="120" y="42" text-anchor="middle" fill="#556" font-size="8">yfinance + RSS news + mock</text>
      <!-- arrow -->
      <line x1="120" y1="54" x2="120" y2="72" stroke="#7ecfff" stroke-width="1.5" marker-end="url(#arr)" opacity=".7"/>
      <!-- 2 War Indicators -->
      <rect x="40" y="72" width="160" height="56" rx="6" fill="#1a1a10" stroke="#8a6a00" stroke-width="1.5"/>
      <text x="120" y="90" text-anchor="middle" fill="#ffc107" font-size="10" font-weight="700">WAR INDICATORS</text>
      <text x="120" y="104" text-anchor="middle" fill="#556" font-size="8">Defense · Gold · Oil</text>
      <text x="120" y="118" text-anchor="middle" fill="#556" font-size="8">News Keywords · VIX</text>
      <!-- arrow -->
      <line x1="120" y1="128" x2="120" y2="146" stroke="#7ecfff" stroke-width="1.5" marker-end="url(#arr)" opacity=".7"/>
      <!-- 3 Feature Engine -->
      <rect x="40" y="146" width="160" height="56" rx="6" fill="#0d1f12" stroke="#1a5c2a" stroke-width="1.5"/>
      <text x="120" y="164" text-anchor="middle" fill="#69f0ae" font-size="10" font-weight="700">FEATURE ENGINE</text>
      <text x="120" y="178" text-anchor="middle" fill="#556" font-size="8">RSI · MACD · BB · ATR</text>
      <text x="120" y="192" text-anchor="middle" fill="#556" font-size="8">17-dim normalised vector</text>
      <!-- arrow -->
      <line x1="120" y1="202" x2="120" y2="220" stroke="#7ecfff" stroke-width="1.5" marker-end="url(#arr)" opacity=".7"/>
      <!-- 4 LSTM -->
      <rect x="30" y="220" width="180" height="64" rx="6" fill="#1a0d2e" stroke="#6a1aaa" stroke-width="1.5"/>
      <text x="120" y="238" text-anchor="middle" fill="#ce93d8" font-size="10" font-weight="700">LSTM NEURAL NETWORK</text>
      <text x="120" y="252" text-anchor="middle" fill="#556" font-size="8">Layer 1: 64 hidden units</text>
      <text x="120" y="264" text-anchor="middle" fill="#556" font-size="8">Layer 2: 32 hidden units</text>
      <text x="120" y="276" text-anchor="middle" fill="#556" font-size="8">FC: 32→16→3 (Softmax)</text>
      <!-- arrow -->
      <line x1="120" y1="284" x2="120" y2="302" stroke="#7ecfff" stroke-width="1.5" marker-end="url(#arr)" opacity=".7"/>
      <!-- 5 Signal Generator -->
      <rect x="30" y="302" width="180" height="72" rx="6" fill="#1a1020" stroke="#8a1a6a" stroke-width="1.5"/>
      <text x="120" y="320" text-anchor="middle" fill="#f48fb1" font-size="10" font-weight="700">SIGNAL GENERATOR</text>
      <text x="120" y="334" text-anchor="middle" fill="#556" font-size="8">Regime filter (block BUY/EXTREME)</text>
      <text x="120" y="348" text-anchor="middle" fill="#556" font-size="8">Technical confirmation</text>
      <text x="120" y="362" text-anchor="middle" fill="#556" font-size="8">Confidence gate · Kelly sizing</text>
      <!-- arrow -->
      <line x1="120" y1="374" x2="120" y2="392" stroke="#7ecfff" stroke-width="1.5" marker-end="url(#arr)" opacity=".7"/>
      <!-- 6 Risk Metrics -->
      <rect x="40" y="392" width="160" height="56" rx="6" fill="#0d1a1a" stroke="#006464" stroke-width="1.5"/>
      <text x="120" y="410" text-anchor="middle" fill="#80deea" font-size="10" font-weight="700">RISK METRICS</text>
      <text x="120" y="424" text-anchor="middle" fill="#556" font-size="8">Sharpe · Sortino · Calmar</text>
      <text x="120" y="438" text-anchor="middle" fill="#556" font-size="8">Risk · Success · Edge Score</text>
      <!-- arrow -->
      <line x1="120" y1="448" x2="120" y2="466" stroke="#7ecfff" stroke-width="1.5" marker-end="url(#arr)" opacity=".7"/>
      <!-- 7 Output -->
      <rect x="50" y="466" width="140" height="44" rx="6" fill="#0a1a0a" stroke="{action_color}" stroke-width="2"/>
      <text x="120" y="486" text-anchor="middle" fill="{action_color}" font-size="12" font-weight="700">{action}</text>
      <text x="120" y="500" text-anchor="middle" fill="#556" font-size="8">BUY · HOLD · SELL + size</text>
    </svg>
    <hr style="border-color:#1e2d4a;margin:10px 0"/>
    <h2>War Headlines</h2>
    <div id="headlines"></div>
  </div>

</div><!-- /grid -->

<script>
const D = {json_blob};

// ── Helpers ──────────────────────────────────────────────────────────────
function drawArcGauge(canvasId, value, max, color, label) {{
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width  = canvas.offsetWidth  || 160;
  const H = canvas.height = canvas.offsetHeight || 100;
  ctx.clearRect(0, 0, W, H);
  const cx = W/2, cy = H*0.82, r = Math.min(cx, cy)*0.85;
  const startA = Math.PI, endA = 2*Math.PI;
  const pct = Math.min(value/max, 1);
  // Track
  ctx.beginPath(); ctx.arc(cx,cy,r,startA,endA);
  ctx.strokeStyle='#1e2d4a'; ctx.lineWidth=12; ctx.stroke();
  // Fill
  ctx.beginPath(); ctx.arc(cx,cy,r,startA,startA+pct*Math.PI);
  ctx.strokeStyle=color; ctx.lineWidth=12; ctx.lineCap='round'; ctx.stroke();
  // Value text
  ctx.fillStyle=color; ctx.font='bold 14px monospace'; ctx.textAlign='center';
  ctx.fillText(Math.round(value), cx, cy-4);
}}

function makeColor(action) {{
  return {{BUY:'#00e676',SELL:'#ff1744',HOLD:'#ffc107'}}[action] || '#ffc107';
}}

// ── Signal panel ─────────────────────────────────────────────────────────
const ls = D.latest_signal || {{}};
document.getElementById('conf-label').textContent =
  `Confidence: ${{(ls.confidence||0).toFixed(1)}}%`;
document.getElementById('size-label').textContent =
  `Position size: ${{(ls.position_size||0).toFixed(1)}}% of capital`;

// Probability bars
const probDiv = document.getElementById('prob-bars');
const probs = ls.nn_probs || {{SELL:0,HOLD:1,BUY:0}};
[['BUY','#00e676'],['HOLD','#ffc107'],['SELL','#ff1744']].forEach(([lbl,col])=>{{
  const p = (probs[lbl]||0)*100;
  probDiv.innerHTML += `
  <div class="prob-row">
    <div class="prob-label" style="color:${{col}}">${{lbl}}</div>
    <div class="prob-track"><div class="prob-fill" style="width:${{p.toFixed(1)}}%;background:${{col}}"></div></div>
    <div class="prob-pct">${{p.toFixed(1)}}%</div>
  </div>`;
}});

// Reasoning
const reasonDiv = document.getElementById('reasoning');
(ls.reasoning || []).forEach(r => {{
  reasonDiv.innerHTML += `<div class="reason">• ${{r}}</div>`;
}});

// ── Sub-scores ───────────────────────────────────────────────────────────
const sub = (D.war_summary.sub_scores || {{}});
const subEl = document.getElementById('sub-scores');
const subCols = {{defense:'#ffa726',gold:'#ffd54f',oil:'#ff7043',news:'#ef5350',vix:'#ab47bc'}};
Object.entries(sub).filter(([k])=>k!=='total').forEach(([k,v])=>{{
  subEl.innerHTML += `
  <div class="sub-item">
    <div class="sub-label">${{k.toUpperCase()}}</div>
    <div class="sub-val" style="color:${{subCols[k]||'#aab'}}">${{parseFloat(v).toFixed(1)}}</div>
  </div>`;
}});

// ── Gauges ───────────────────────────────────────────────────────────────
const ws = D.war_summary;
const rm = D.risk_metrics;
setTimeout(()=>{{
  drawArcGauge('warGauge',  ws.current_score, 100, '{regime_color}');
  drawArcGauge('riskGauge', rm.risk_score,    100, '#ff6d00');
  drawArcGauge('succGauge', rm.success_score, 100, '#00e676');
  drawArcGauge('edgeGauge', rm.edge_score,    100, '#7ecfff');
}}, 100);

// ── Price Chart ───────────────────────────────────────────────────────────
const labels = D.days.map(d=>`Day ${{d}}`);
const signalColors = D.signals.map(s=>makeColor(s.action));

// Scatter points for signals (non-HOLD)
const buyPts  = D.signals.map((s,i)=>s.action==='BUY'  ?{{x:i,y:D.spy[i]}}:null).filter(Boolean);
const sellPts = D.signals.map((s,i)=>s.action==='SELL' ?{{x:i,y:D.spy[i]}}:null).filter(Boolean);

new Chart(document.getElementById('priceChart'),{{
  type:'line',
  data:{{
    labels,
    datasets:[
      {{label:'SPY',data:D.spy,borderColor:'#7ecfff',borderWidth:2,pointRadius:0,tension:.3,yAxisID:'y1'}},
      {{label:'BUY',data:buyPts, type:'scatter',backgroundColor:'#00e676',pointRadius:7,pointStyle:'triangle',yAxisID:'y1'}},
      {{label:'SELL',data:sellPts,type:'scatter',backgroundColor:'#ff1744',pointRadius:7,pointStyle:'triangle',rotation:180,yAxisID:'y1'}},
    ]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{labels:{{color:'#7a8aaa',font:{{size:10}}}}}}}},
    scales:{{
      x:{{ticks:{{color:'#556',maxTicksLimit:8}},grid:{{color:'#111c30'}}}},
      y1:{{position:'left',ticks:{{color:'#7ecfff'}},grid:{{color:'#111c30'}},title:{{display:true,text:'SPY',color:'#7ecfff',font:{{size:10}}}}}}
    }}
  }}
}});

// ── War Timeline ──────────────────────────────────────────────────────────
const warColors = D.war_scores.map(s=>
  s>=70?'#ff1744':s>=50?'#ff6d00':s>=30?'#ffc107':s>=15?'#69f0ae':'#00e676');

new Chart(document.getElementById('warChart'),{{
  type:'bar',
  data:{{
    labels,
    datasets:[{{
      label:'War Tension (0-100)',
      data:D.war_scores,
      backgroundColor:warColors,
      borderRadius:2,
    }}]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{labels:{{color:'#7a8aaa',font:{{size:10}}}}}}}},
    scales:{{
      x:{{ticks:{{color:'#556',maxTicksLimit:8}},grid:{{color:'#111c30'}}}},
      y:{{min:0,max:100,ticks:{{color:'#ffc107'}},grid:{{color:'#111c30'}},
          title:{{display:true,text:'Tension',color:'#ffc107',font:{{size:10}}}}}}
    }}
  }}
}});

// ── Asset Chart (GLD, ITA, USO) ──────────────────────────────────────────
function normalise(arr){{const mn=Math.min(...arr),mx=Math.max(...arr);return arr.map(v=>(v-mn)/(mx-mn+1e-9)*100)}}
new Chart(document.getElementById('assetChart'),{{
  type:'line',
  data:{{
    labels,
    datasets:[
      {{label:'ITA (Defense)',data:normalise(D.ita),borderColor:'#ff6d00',borderWidth:1.5,pointRadius:0,tension:.3}},
      {{label:'GLD (Gold)',   data:normalise(D.gld),borderColor:'#ffd54f',borderWidth:1.5,pointRadius:0,tension:.3}},
      {{label:'USO (Oil)',    data:normalise(D.uso),borderColor:'#90a4ae',borderWidth:1.5,pointRadius:0,tension:.3}},
      {{label:'VIX',         data:normalise(D.vix),borderColor:'#ce93d8',borderWidth:1.5,pointRadius:0,tension:.3,borderDash:[4,2]}},
    ]
  }},
  options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{labels:{{color:'#7a8aaa',font:{{size:10}},boxWidth:12}}}}}},
    scales:{{
      x:{{ticks:{{color:'#556',maxTicksLimit:8}},grid:{{color:'#111c30'}}}},
      y:{{ticks:{{color:'#aab'}},grid:{{color:'#111c30'}},
          title:{{display:true,text:'Normalised 0-100',color:'#556',font:{{size:9}}}}}}
    }}
  }}
}});

// ── Feature Bars ──────────────────────────────────────────────────────────
const featDiv = document.getElementById('feat-bars');
D.feature_names.forEach((name,i)=>{{
  const v = D.latest_features[i];
  const pct = (v*100).toFixed(0);
  const col = v>0.6?'#00e676':v<0.4?'#ff1744':'#7ecfff';
  featDiv.innerHTML += `
  <div class="feat-bar-wrap">
    <div class="feat-name">${{name}}</div>
    <div class="feat-track"><div class="feat-fill" style="width:${{Math.abs(v*100).toFixed(1)}}%;background:${{col}}"></div></div>
    <div class="feat-val">${{v.toFixed(3)}}</div>
  </div>`;
}});

// ── Headlines ─────────────────────────────────────────────────────────────
const CONFLICT = ['war','conflict','military','strike','invasion','missile','sanctions',
                  'ceasefire','troops','drone','attack','nuclear','casualties'];
const hdEl = document.getElementById('headlines');
D.headlines.forEach(h=>{{
  const hot = CONFLICT.some(kw=>h.toLowerCase().includes(kw));
  hdEl.innerHTML += `<div class="headline ${{hot?'hot':''}}">${{h}}</div>`;
}});

// ── Redraw gauges on resize ───────────────────────────────────────────────
window.addEventListener('resize',()=>{{
  drawArcGauge('warGauge',  ws.current_score, 100, '{regime_color}');
  drawArcGauge('riskGauge', rm.risk_score,    100, '#ff6d00');
  drawArcGauge('succGauge', rm.success_score, 100, '#00e676');
  drawArcGauge('edgeGauge', rm.edge_score,    100, '#7ecfff');
}});
</script>
</body>
</html>"""


if __name__ == "__main__":
    data = run()
    html = build_html(data)
    out_html = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(out_html, "w") as f:
        f.write(html)
    print(f"Wrote {out_html}")
    print(f"Open in browser: file://{out_html}")
