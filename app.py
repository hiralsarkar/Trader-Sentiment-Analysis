import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Sentiment x Trader Performance", page_icon="📊", layout="wide")

ORDER5 = ['Extreme Fear','Fear','Neutral','Greed','Extreme Greed']
ORDER3 = ['Fear','Neutral','Greed']
COLORS5 = {'Extreme Fear':'#dc2626','Fear':'#f97316','Neutral':'#9ca3af','Greed':'#84cc16','Extreme Greed':'#16a34a'}
COLORS3 = {'Fear':'#f97316','Neutral':'#9ca3af','Greed':'#84cc16'}


@st.cache_data
def load_data():
    hist = pd.read_csv('data/historical_data.csv.gz')
    fg = pd.read_csv('data/fear_greed_index.csv')

    hist['Timestamp IST'] = pd.to_datetime(hist['Timestamp IST'], format='%d-%m-%Y %H:%M')
    hist['date'] = hist['Timestamp IST'].dt.date.astype(str)
    fg['date'] = pd.to_datetime(fg['date']).dt.date.astype(str)

    df = hist.merge(fg[['date', 'classification', 'value']], on='date', how='left')
    df = df.dropna(subset=['classification'])

    sent_map = {'Extreme Fear': 'Fear', 'Fear': 'Fear', 'Neutral': 'Neutral',
                 'Greed': 'Greed', 'Extreme Greed': 'Greed'}
    df['sentiment_simple'] = df['classification'].map(sent_map)
    df['date'] = pd.to_datetime(df['date'])
    return df


df = load_data()

# ---------------- Sidebar filters ----------------
st.sidebar.header("🔍 Filters")

min_date, max_date = df['date'].min().date(), df['date'].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date),
                                    min_value=min_date, max_value=max_date)

sent_options = st.sidebar.multiselect("Sentiment (5-level)", ORDER5, default=ORDER5)

accounts = sorted(df['Account'].unique())
acc_options = st.sidebar.multiselect("Accounts", accounts, default=[])

coins = sorted(df['Coin'].unique())
coin_options = st.sidebar.multiselect("Coins", coins, default=[])

# ---------------- Apply filters ----------------
mask = pd.Series(True, index=df.index)
if isinstance(date_range, tuple) and len(date_range) == 2:
    mask &= (df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])
if sent_options:
    mask &= df['classification'].isin(sent_options)
if acc_options:
    mask &= df['Account'].isin(acc_options)
if coin_options:
    mask &= df['Coin'].isin(coin_options)

fdf = df[mask]

# ---------------- Header ----------------
st.title("📊 Bitcoin Sentiment × Trader Performance")
st.caption(f"{len(fdf):,} trades · {fdf['Account'].nunique()} accounts · "
           f"{fdf['date'].min().date() if len(fdf) else '-'} → {fdf['date'].max().date() if len(fdf) else '-'}")

if fdf.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ---------------- KPIs ----------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Closed PnL", f"${fdf['Closed PnL'].sum():,.0f}")
c2.metric("Overall Win Rate", f"{(fdf['Closed PnL'] > 0).mean()*100:.1f}%")
c3.metric("Total Trades", f"{len(fdf):,}")
c4.metric("Avg Trade Size", f"${fdf['Size USD'].mean():,.0f}")
c5.metric("Total Volume", f"${fdf['Size USD'].sum()/1e6:,.1f}M")

st.divider()

# ---------------- Row 1: PnL & Win rate by sentiment ----------------
def agg_by(col, group):
    g = fdf.groupby(group)
    out = pd.DataFrame({
        'trades': g.size(),
        'total_pnl': g['Closed PnL'].sum(),
        'avg_pnl': g['Closed PnL'].mean(),
        'win_rate': g.apply(lambda x: (x['Closed PnL'] > 0).mean() * 100),
        'avg_size_usd': g['Size USD'].mean(),
    })
    order = ORDER5 if group == 'classification' else ORDER3
    return out.reindex([o for o in order if o in out.index])


by5 = agg_by('Closed PnL', 'classification')
colors = COLORS5

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(by5, x=by5.index, y='total_pnl', title="Total Closed PnL by Sentiment",
                  color=by5.index, color_discrete_map=colors)
    fig.update_layout(showlegend=False, yaxis_title="USD", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(by5, x=by5.index, y='win_rate', title="Win Rate (%) by Sentiment",
                  color=by5.index, color_discrete_map=colors)
    fig.update_layout(showlegend=False, yaxis_title="%", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Row 2: Avg trade size & Buy/Sell mix ----------------
col3, col4 = st.columns(2)
with col3:
    fig = px.bar(by5, x=by5.index, y='avg_size_usd', title="Avg Trade Size (USD) by Sentiment",
                  color=by5.index, color_discrete_map=colors)
    fig.update_layout(showlegend=False, yaxis_title="USD", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

with col4:
    side = fdf.groupby(['sentiment_simple', 'Side']).size().unstack(fill_value=0)
    side_pct = (side.div(side.sum(axis=1), axis=0) * 100).reindex([o for o in ORDER3 if o in side.index])
    fig = px.bar(side_pct, x=side_pct.index, y=['BUY', 'SELL'], title="Buy vs Sell Mix (%)",
                  color_discrete_map={'BUY': '#16a34a', 'SELL': '#dc2626'}, barmode='stack')
    fig.update_layout(yaxis_title="%", xaxis_title="", legend_title="")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Row 3: Daily PnL vs sentiment value ----------------
daily = fdf.groupby('date').agg(total_pnl=('Closed PnL', 'sum'), value=('value', 'first')).reset_index()
corr = daily['total_pnl'].corr(daily['value']) if len(daily) > 1 else np.nan

fig = go.Figure()
fig.add_trace(go.Scatter(x=daily['date'], y=daily['total_pnl'], name='Daily PnL ($)',
                          line=dict(color='#3b82f6', width=1.5)))
fig.add_trace(go.Scatter(x=daily['date'], y=daily['value'], name='F&G Value', yaxis='y2',
                          line=dict(color='#dc2626', width=1.5)))
fig.update_layout(
    title=f"Daily Closed PnL vs Fear & Greed Index (corr = {corr:.3f})",
    yaxis=dict(title="Daily PnL ($)"),
    yaxis2=dict(title="F&G Value", overlaying='y', side='right', range=[0, 100]),
    legend=dict(orientation='h', y=1.1)
)
st.plotly_chart(fig, use_container_width=True)

# ---------------- Row 4: Coin-level performance ----------------
top_coins = fdf.groupby('Coin')['Size USD'].sum().sort_values(ascending=False).head(10).index.tolist()
coin_sent = (fdf[fdf['Coin'].isin(top_coins)]
             .groupby(['Coin', 'sentiment_simple'])['Closed PnL'].mean()
             .unstack(fill_value=0).reindex(top_coins))
coin_sent = coin_sent[[c for c in ORDER3 if c in coin_sent.columns]]

fig = px.bar(coin_sent, x=coin_sent.index, y=coin_sent.columns,
              title="Avg PnL per Trade — Top 10 Coins by Volume, by Sentiment",
              barmode='group', color_discrete_map=COLORS3)
fig.update_layout(yaxis_title="Avg Closed PnL (USD)", xaxis_title="", legend_title="")
st.plotly_chart(fig, use_container_width=True)

# ---------------- Row 5: Account leaderboard ----------------
acc = fdf.groupby('Account').agg(
    trades=('Closed PnL', 'size'),
    total_pnl=('Closed PnL', 'sum'),
    win_rate=('Closed PnL', lambda x: (x > 0).mean() * 100)
).round(2)

col5, col6 = st.columns(2)
with col5:
    st.subheader("🏆 Top 10 Accounts by Total PnL")
    top10 = acc.sort_values('total_pnl', ascending=False).head(10)
    st.dataframe(top10, use_container_width=True)
    top5_share = top10.head(5)['total_pnl'].sum() / acc['total_pnl'].sum() * 100
    st.caption(f"Top 5 accounts generate **{top5_share:.1f}%** of total PnL "
               f"(${top10.head(5)['total_pnl'].sum():,.0f} of ${acc['total_pnl'].sum():,.0f}).")
with col6:
    st.subheader("📉 Bottom 10 Accounts by Total PnL")
    st.dataframe(acc.sort_values('total_pnl').head(10), use_container_width=True)

st.divider()

# ---------------- Key takeaways ----------------
st.subheader("💡 Key Takeaways")
st.markdown("""
- 🟢 **Extreme Greed** is the strongest regime: highest win rate (46.5%) and avg PnL/trade ($67.9), with smaller position sizes. At the broader "Greed" bucket level the edge shrinks to $53.9 vs $49.2 for Fear — the outperformance is concentrated in the *extreme* euphoria tail specifically, not greed in general.
- 🔴 **Extreme Fear** is the weakest regime: lowest win rate (37.1%) and lowest avg PnL/trade ($34.5), while plain **Fear** sees the largest average trade size (~$7.8k) — a risky, inverted sizing pattern.
- 📉 Raw sentiment **score** barely correlates with daily PnL (r ≈ -0.08) — the categorical regime (especially "Extreme" labels) matters more than the 0–100 number.
- 👥 PnL is **concentration-driven** — the top 5 of 32 accounts generated **$6.36M of the $10.25M total PnL (~62%)**, so strategies should be validated per-account.
""")

st.divider()

# ---------------- Recommendations ----------------
st.subheader("🎯 Recommendations to Maximize KPIs")
st.markdown("""
| Recommendation | Why (evidence) | Expected Impact |
|---|---|---|
| **Increase conviction in Extreme Greed** | Win rate 46.5% & avg PnL/trade $67.9 are regime highs, while avg size is already smallest ($3.1k) | ↑ Total PnL, ↑ PnL per $ exposure |
| **Cut size 30-50% in Extreme Fear** | Lowest win rate (37.1%) and avg PnL/trade ($34.5) of any regime | ↓ Drawdowns, ↑ Win Rate |
| **Fix inverted sizing in plain Fear** | Largest avg trade size ($7.8k) paired with only 42.1% win rate — opposite of optimal sizing | ↑ Risk-adjusted return |
| **Use sentiment category, not raw score, as a filter** | Score correlates only -0.08 with daily PnL; categorical regimes show 10pp+ win-rate spread | ↑ Signal quality |
| **Build per-coin, per-regime playbooks** | e.g. TRUMP: +$81 avg PnL in Fear vs -$454 in Greed; FARTCOIN: -$98 in Fear vs +$19 in Greed | ↑ Avg PnL/trade |
| **Take partial profits into Greed** | Sell share already rises to 52.9% in Greed vs ~50% elsewhere — formalize as scaled exits | ↑ Win Rate, locks gains |
| **Audit / reduce allocation to bottom-5 accounts** | Top 5 accounts = 62% of total PnL; bottom accounts are net drags | ↑ Total PnL, ↓ variance |
| **Reduce fee drag in Fear** | Avg fee per trade highest here ($1.50 vs $0.68 in Extreme Greed) — likely over-trading | ↑ Net PnL |

**Quick-reference regime cheat sheet**
- **Extreme Greed** → go bigger, trend-follow, let winners run
- **Greed / Neutral** → standard sizing, watch for early profit-taking signals
- **Fear** → reduce size despite the temptation to "average down"; expect higher fees
- **Extreme Fear** → defensive sizing, tighter stops, fewer new entries until regime shifts
""")

