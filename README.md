# Fear, Greed & PnL: Sentiment-Driven Trader Performance Analysis

Exploratory analysis of 211K+ Hyperliquid trades across 32 accounts, merged with the Bitcoin Fear & Greed Index (2023–2025), to uncover how market sentiment regimes affect win rate, position sizing, and profitability — plus actionable recommendations to optimize trading KPIs.

## Contents

- [`Sentiment_Trader_Analysis.ipynb`](Sentiment_Trader_Analysis.ipynb) — full analysis notebook (data cleaning, EDA, observations, recommendations)
- [`app.py`](app.py) — interactive Streamlit dashboard
- [`dashboard.html`](dashboard.html) / [`dashboard_data.js`](dashboard_data.js) — standalone static dashboard (no server needed, open directly in a browser)
- `data/` — source datasets (`historical_data.csv.gz`, `fear_greed_index.csv`)

## Key Findings

- **Extreme Greed** is the strongest regime: highest win rate (46.5%) and avg PnL/trade ($67.9), with the smallest average position sizes ($3.1k). The edge is concentrated in the *extreme* euphoria tail, not "Greed" broadly.
- **Extreme Fear** is the weakest regime: lowest win rate (37.1%) and lowest avg PnL/trade ($34.5), while plain **Fear** has the largest average trade size (~$7.8k) — an inverted, riskier sizing pattern.
- The raw Fear & Greed **score** barely correlates with daily PnL (r ≈ -0.08); the categorical regime (especially "Extreme" labels) is the stronger signal.
- PnL is **concentration-driven** — the top 5 of 32 accounts generated $6.36M of the $10.25M total PnL (~62%).

See the notebook for full methodology, charts, and the complete recommendations table.

## Running the dashboard

```bash
pip install -r requirements.txt
streamlit run app.py
```

Alternatively, open [`dashboard.html`](dashboard.html) directly in a browser for a static, dependency-free view.

## Running the notebook

```bash
pip install -r requirements.txt
jupyter notebook Sentiment_Trader_Analysis.ipynb
```

## Data

- `data/historical_data.csv.gz` — Hyperliquid historical trade data (211,224 rows, 32 accounts), gzip-compressed
- `data/fear_greed_index.csv` — Bitcoin Fear & Greed Index, daily classification and value (2018–2025)
