"""
Pairs Trading Backtest
----------------------
Engle-Granger cointegration test to identify statistically related pairs.
Z-score of the spread drives entry/exit signals.
Full P&L backtest with cumulative returns, win rate, and Sharpe ratio.

Note: This backtest uses in-sample signals and may overstate performance.
Walk-forward validation is recommended for production use.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from utils.styling import apply_global_css, module_header, error_card, ACCENT, DANGER, SUBTEXT_COLOR, PLOTLY_LAYOUT
from utils.helpers import fetch_price_history, validate_tickers, data_source_banner

apply_global_css(st)
module_header(st, "🔁", "Pairs Trading Backtest", "Engle-Granger Cointegration · Z-Score Signals · P&L Simulation")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown("### Pair Settings")
ticker1 = st.sidebar.text_input("Ticker 1", "KO").upper().strip()
ticker2 = st.sidebar.text_input("Ticker 2", "PEP").upper().strip()
lookback = st.sidebar.slider("Lookback Window (days)", 20, 120, 60, help="Rolling window for spread z-score calculation.")
entry_z = st.sidebar.slider("Entry Z-Score Threshold", 1.0, 3.5, 2.0, step=0.1)
exit_z = st.sidebar.slider("Exit Z-Score Threshold", 0.0, 1.5, 0.5, step=0.1)
transaction_cost = st.sidebar.slider("Transaction Cost (bps)", 0, 50, 10) / 10_000

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
try:
    tickers = validate_tickers([ticker1, ticker2])
    if len(set(tickers)) < 2:
        error_card(st, "Enter two different ticker symbols.")
        st.stop()

    with st.spinner("Fetching price data..."):
        prices, is_live = fetch_price_history(tickers, period="3y")
    data_source_banner(st, is_live)

    available = [t for t in tickers if t in prices.columns]
    if len(available) < 2:
        error_card(st, "Could not retrieve data for both tickers.", "Check ticker symbols.")
        st.stop()

    p1 = prices[available[0]].dropna()
    p2 = prices[available[1]].dropna()
    common_idx = p1.index.intersection(p2.index)
    p1, p2 = p1[common_idx], p2[common_idx]

    # ---------------------------------------------------------------------------
    # Engle-Granger cointegration test
    # ---------------------------------------------------------------------------
    # Step 1: OLS regression of p1 on p2
    slope, intercept, r_value, _, _ = stats.linregress(p2.values, p1.values)
    spread = p1 - (slope * p2 + intercept)

    # Step 2: ADF test on the residuals (proxy for cointegration p-value)
    from statsmodels.tsa.stattools import adfuller
    adf_result = adfuller(spread.dropna(), maxlag=1, autolag=None)
    adf_stat, adf_pval = adf_result[0], adf_result[1]

    coint_color = ACCENT if adf_pval < 0.05 else DANGER
    coint_label = "Cointegrated ✓" if adf_pval < 0.05 else "Not Cointegrated ✗"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pair", f"{available[0]} / {available[1]}")
    c2.metric("Hedge Ratio (β)", f"{slope:.4f}")
    c3.metric("ADF Statistic", f"{adf_stat:.3f}")
    c4.metric("Cointegration (p-value)", f"{adf_pval:.4f}")

    st.markdown(
        f'<p style="color:{coint_color}; font-weight:600; font-size:0.9rem;">● {coint_label} (p={adf_pval:.4f})</p>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---------------------------------------------------------------------------
    # Z-score calculation
    # ---------------------------------------------------------------------------
    roll_mean = spread.rolling(lookback).mean()
    roll_std = spread.rolling(lookback).std()
    zscore = (spread - roll_mean) / roll_std

    # ---------------------------------------------------------------------------
    # Backtest engine
    # ---------------------------------------------------------------------------
    position = 0    # +1 = long spread, -1 = short spread, 0 = flat
    positions = []
    trades = []
    entry_price = 0

    for i in range(len(zscore)):
        z = zscore.iloc[i]
        if np.isnan(z):
            positions.append(0)
            continue

        if position == 0:
            if z > entry_z:
                position = -1   # short the spread (z too high → mean revert down)
                entry_price = spread.iloc[i]
                trades.append({"entry_idx": i, "direction": -1, "entry_z": z})
            elif z < -entry_z:
                position = 1    # long the spread
                entry_price = spread.iloc[i]
                trades.append({"entry_idx": i, "direction": 1, "entry_z": z})
        elif position == 1 and z >= -exit_z:
            position = 0
            if trades:
                trades[-1]["exit_idx"] = i
                trades[-1]["exit_z"] = z
        elif position == -1 and z <= exit_z:
            position = 0
            if trades:
                trades[-1]["exit_idx"] = i
                trades[-1]["exit_z"] = z

        positions.append(position)

    positions = pd.Series(positions, index=zscore.index[:len(positions)])

    # Daily P&L: position × daily spread change − transaction costs on turns
    spread_changes = spread.diff()
    pnl = positions.shift(1) * spread_changes
    # Apply transaction cost on position changes
    pos_changes = positions.diff().abs()
    pnl -= pos_changes * transaction_cost * spread.mean()
    pnl = pnl.fillna(0)

    cum_pnl = pnl.cumsum()
    total_return = cum_pnl.iloc[-1] / (spread.std() * 100) if spread.std() > 0 else 0

    # Trade statistics
    completed_trades = [t for t in trades if "exit_idx" in t]
    if completed_trades:
        trade_pnls = [
            positions.iloc[t["entry_idx"]] * (spread.iloc[t["exit_idx"]] - spread.iloc[t["entry_idx"]])
            for t in completed_trades
        ]
        wins = sum(1 for p in trade_pnls if p > 0)
        win_rate = wins / len(trade_pnls)
        avg_win = np.mean([p for p in trade_pnls if p > 0]) if wins > 0 else 0
        avg_loss = np.mean([p for p in trade_pnls if p <= 0]) if wins < len(trade_pnls) else 0
    else:
        win_rate, avg_win, avg_loss = 0, 0, 0

    pnl_sharpe = (pnl.mean() / pnl.std() * np.sqrt(252)) if pnl.std() > 0 else 0

    # Metric summary
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Trades", len(completed_trades))
    m2.metric("Win Rate", f"{win_rate:.1%}")
    m3.metric("Sharpe Ratio", f"{pnl_sharpe:.2f}")
    m4.metric("Avg Win", f"{avg_win:.2f}")
    m5.metric("Avg Loss", f"{avg_loss:.2f}")

    st.info(
        "**Note:** This backtest uses in-sample signals and may overstate performance. "
        "Walk-forward validation is recommended for production use.",
        icon="ℹ️",
    )

    st.markdown("---")

    # ---------------------------------------------------------------------------
    # Charts
    # ---------------------------------------------------------------------------
    # Price chart
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=p1.index, y=p1, name=available[0], line=dict(color=ACCENT, width=1.5)))
    fig_price.add_trace(go.Scatter(x=p2.index, y=p2, name=available[1], line=dict(color="#FFC107", width=1.5)))
    fig_price.update_layout(**PLOTLY_LAYOUT, title="Price History", height=240,
                            xaxis=dict(showgrid=False), yaxis=dict(title="Price ($)", showgrid=True, gridcolor="#2D2D44"))
    st.plotly_chart(fig_price, use_container_width=True)

    # Spread + z-score with signals
    fig_z = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.4, 0.6], vertical_spacing=0.05)

    fig_z.add_trace(go.Scatter(x=spread.index, y=spread, name="Spread",
                               line=dict(color=ACCENT, width=1.5)), row=1, col=1)

    fig_z.add_trace(go.Scatter(x=zscore.index, y=zscore, name="Z-Score",
                               line=dict(color="#A78BFA", width=1.5)), row=2, col=1)
    fig_z.add_hline(y=entry_z, line_color=DANGER, line_dash="dash", row=2, col=1)
    fig_z.add_hline(y=-entry_z, line_color=ACCENT, line_dash="dash", row=2, col=1)
    fig_z.add_hline(y=exit_z, line_color="#FFC107", line_dash="dot", row=2, col=1)
    fig_z.add_hline(y=-exit_z, line_color="#FFC107", line_dash="dot", row=2, col=1)
    fig_z.add_hline(y=0, line_color="#FFFFFF", line_width=0.5, row=2, col=1)

    # Plot trade entry/exit markers
    for t in completed_trades[:50]:   # cap at 50 for visual clarity
        ei = t["entry_idx"]
        xi = t["exit_idx"]
        marker_color = ACCENT if t["direction"] == 1 else DANGER
        fig_z.add_trace(go.Scatter(
            x=[zscore.index[ei]], y=[zscore.iloc[ei]],
            mode="markers", marker=dict(color=marker_color, size=8, symbol="triangle-up" if t["direction"] == 1 else "triangle-down"),
            showlegend=False,
        ), row=2, col=1)

    fig_z.update_layout(**PLOTLY_LAYOUT, height=400,
                        yaxis=dict(title="Spread", showgrid=True, gridcolor="#2D2D44"),
                        yaxis2=dict(title="Z-Score", showgrid=True, gridcolor="#2D2D44"))
    st.plotly_chart(fig_z, use_container_width=True)

    # Cumulative P&L
    fig_pnl = go.Figure()
    fig_pnl.add_trace(go.Scatter(
        x=cum_pnl.index, y=cum_pnl,
        mode="lines",
        line=dict(color=ACCENT, width=2),
        fill="tozeroy",
        fillcolor="rgba(0,212,170,0.08)",
        name="Cumulative P&L",
    ))
    fig_pnl.update_layout(
        **PLOTLY_LAYOUT,
        title="Cumulative P&L",
        height=260,
        xaxis=dict(showgrid=False),
        yaxis=dict(title="P&L ($)", showgrid=True, gridcolor="#2D2D44"),
    )
    st.plotly_chart(fig_pnl, use_container_width=True)

except ImportError:
    error_card(st, "statsmodels is required for the cointegration test.", "Run: pip install statsmodels")
except Exception as e:
    error_card(st, str(e), "Check ticker symbols and try again.")
