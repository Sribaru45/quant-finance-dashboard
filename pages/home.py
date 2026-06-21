import streamlit as st
import plotly.graph_objects as go
from utils.styling import apply_global_css, ACCENT, SUBTEXT_COLOR, PLOTLY_LAYOUT
from utils.helpers import fetch_price_history, data_source_banner

apply_global_css(st)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div style="text-align:center; padding: 2rem 0 1rem 0;">
        <h1 style="font-size:2.4rem; color:#FFFFFF; font-family:'Courier New',monospace; margin-bottom:0;">
            📊 Financial Analytics Platform
        </h1>
        <p style="color:{SUBTEXT_COLOR}; font-size:1rem; margin-top:0.5rem;">
            A Bloomberg-lite quant finance toolkit · Built by Sriram Bharadwaj
        </p>
        <hr style="border-color:#2D2D44; margin: 1rem auto; width:60%;">
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Live market snapshot (SPY, QQQ, VIX proxies)
# ---------------------------------------------------------------------------
WATCHLIST = ["SPY", "QQQ", "GLD", "^VIX"]
prices, is_live = fetch_price_history(["SPY", "QQQ", "GLD"], period="5d")
data_source_banner(st, is_live)

col1, col2, col3, col4 = st.columns(4)
snapshot_items = [
    ("SPY", "S&P 500 ETF"),
    ("QQQ", "Nasdaq 100 ETF"),
    ("GLD", "Gold ETF"),
]

for col, (ticker, label) in zip([col1, col2, col3], snapshot_items):
    try:
        series = prices[ticker].dropna()
        latest = series.iloc[-1]
        prev = series.iloc[-2]
        chg = (latest - prev) / prev * 100
        delta_str = f"{chg:+.2f}%"
        col.metric(label=label, value=f"${latest:.2f}", delta=delta_str)
    except Exception:
        col.metric(label=label, value="N/A", delta="—")

col4.metric(label="Platform Modules", value="6", delta="Active")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Mini SPY price chart
# ---------------------------------------------------------------------------
try:
    spy = prices["SPY"].dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spy.index, y=spy.values,
        mode="lines",
        line=dict(color=ACCENT, width=2),
        fill="tozeroy",
        fillcolor="rgba(0,212,170,0.08)",
        name="SPY",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="SPY — 2 Year Price History",
        height=220,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#2D2D44"),
        showlegend=False,
        margin=dict(l=40, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)
except Exception:
    pass

st.markdown("---")

# ---------------------------------------------------------------------------
# Module grid
# ---------------------------------------------------------------------------
st.markdown(
    f'<h3 style="color:{ACCENT}; font-family:Courier New; margin-bottom:1rem;">Modules</h3>',
    unsafe_allow_html=True,
)

modules = [
    ("🏦", "Credit Risk Model", "PD modeling, LGD estimation, expected loss · US & India markets", "credit_risk"),
    ("📉", "Risk Analytics", "Portfolio VaR, CVaR, Monte Carlo simulation", "risk_analytics"),
    ("⚙️", "Options Pricing", "Black-Scholes pricing, full Greeks, sensitivity heatmaps", "options_pricing"),
    ("📈", "Portfolio Optimization", "Markowitz efficient frontier, Sharpe maximization", "portfolio_opt"),
    ("🔁", "Pairs Trading", "Cointegration backtest, z-score signals, P&L tracking", "pairs_trading"),
    ("🖥️", "Financial Dashboard", "Live stock overview, ratios, revenue trends", "financial_dashboard"),
]

col_a, col_b = st.columns(2)
for i, (icon, name, desc, _) in enumerate(modules):
    target = col_a if i % 2 == 0 else col_b
    target.markdown(
        f'<div class="module-card"><h4>{icon} {name}</h4><p>{desc}</p></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f'<p style="color:{SUBTEXT_COLOR}; font-size:0.8rem; text-align:center;">'
    "All modules support offline mode with sample data. Live data powered by yfinance."
    "</p>",
    unsafe_allow_html=True,
)
