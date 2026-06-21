"""
Portfolio Optimization
----------------------
Markowitz mean-variance optimization.
Efficient frontier via random portfolio sampling + scipy minimize for Sharpe max.
Supports long-only and long/short modes.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.optimize import minimize

from utils.styling import apply_global_css, module_header, error_card, ACCENT, DANGER, SUBTEXT_COLOR, PLOTLY_LAYOUT
from utils.helpers import fetch_price_history, compute_returns, validate_tickers, data_source_banner

apply_global_css(st)
module_header(st, "📈", "Portfolio Optimization", "Markowitz Mean-Variance · Efficient Frontier · Sharpe Ratio Maximization")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown("### Portfolio Settings")
tickers_raw = st.sidebar.text_input("Tickers (comma-separated)", "AAPL,MSFT,GOOGL,JPM,GLD")
allow_short = st.sidebar.toggle("Allow Short Selling", value=False,
                                 help="When on: weights can be negative (short positions). When off: long-only.")
risk_free = st.sidebar.slider("Risk-Free Rate (%)", 0.0, 10.0, 4.0, step=0.1) / 100
n_portfolios = st.sidebar.slider("Random Portfolios (frontier)", 2000, 8000, 4000, step=500)

if allow_short:
    st.sidebar.info("Short selling enabled — weights may be negative.", icon="⚠️")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
try:
    tickers = validate_tickers(tickers_raw.split(","))
    if len(tickers) < 2:
        error_card(st, "Enter at least 2 ticker symbols.")
        st.stop()

    with st.spinner("Fetching price data..."):
        prices, is_live = fetch_price_history(tickers, period="3y")
    data_source_banner(st, is_live)

    available = [t for t in tickers if t in prices.columns]
    if len(available) < 2:
        error_card(st, "Could not retrieve data for enough tickers.", "Try different symbols.")
        st.stop()

    returns = compute_returns(prices[available])
    mu = returns.mean().values * 252          # annualised expected returns
    cov = returns.cov().values * 252          # annualised covariance
    n = len(available)

    # ---------------------------------------------------------------------------
    # Random portfolio sampling for efficient frontier
    # ---------------------------------------------------------------------------
    port_returns, port_vols, port_sharpes = [], [], []
    weights_list = []

    for _ in range(n_portfolios):
        if allow_short:
            w = np.random.randn(n)
        else:
            w = np.random.dirichlet(np.ones(n))
        w = w / w.sum()
        ret = float(w @ mu)
        vol = float(np.sqrt(w @ cov @ w))
        sharpe = (ret - risk_free) / vol if vol > 0 else 0
        port_returns.append(ret)
        port_vols.append(vol)
        port_sharpes.append(sharpe)
        weights_list.append(w)

    port_returns = np.array(port_returns)
    port_vols = np.array(port_vols)
    port_sharpes = np.array(port_sharpes)

    # ---------------------------------------------------------------------------
    # Sharpe maximization via scipy
    # ---------------------------------------------------------------------------
    def neg_sharpe(w):
        ret = w @ mu
        vol = np.sqrt(w @ cov @ w)
        return -(ret - risk_free) / vol if vol > 0 else 0

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = (None if allow_short else [(0, 1)] * n)
    x0 = np.ones(n) / n
    result = minimize(neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    opt_w = result.x
    opt_ret = float(opt_w @ mu)
    opt_vol = float(np.sqrt(opt_w @ cov @ opt_w))
    opt_sharpe = (opt_ret - risk_free) / opt_vol

    # Minimum variance portfolio
    def port_vol_sq(w):
        return w @ cov @ w

    mv_result = minimize(port_vol_sq, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    mv_w = mv_result.x
    mv_ret = float(mv_w @ mu)
    mv_vol = float(np.sqrt(mv_w @ cov @ mv_w))

    # ---------------------------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Optimal Return (Ann.)", f"{opt_ret:.1%}")
    c2.metric("Optimal Volatility (Ann.)", f"{opt_vol:.1%}")
    c3.metric("Max Sharpe Ratio", f"{opt_sharpe:.2f}")
    c4.metric("Min Vol Portfolio", f"{mv_vol:.1%}")

    st.markdown("---")

    # ---------------------------------------------------------------------------
    # Efficient frontier chart
    # ---------------------------------------------------------------------------
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=port_vols * 100, y=port_returns * 100,
        mode="markers",
        marker=dict(
            color=port_sharpes,
            colorscale=[[0, "#1C1C2E"], [0.5, ACCENT], [1, "#FFFFFF"]],
            size=3,
            opacity=0.6,
            colorbar=dict(title="Sharpe", thickness=12, len=0.6),
        ),
        name="Random Portfolios",
        text=[f"Sharpe: {s:.2f}" for s in port_sharpes],
    ))
    fig.add_trace(go.Scatter(
        x=[opt_vol * 100], y=[opt_ret * 100],
        mode="markers+text",
        marker=dict(color=ACCENT, size=14, symbol="star"),
        text=["Max Sharpe"], textposition="top center",
        textfont=dict(color=ACCENT),
        name="Max Sharpe",
    ))
    fig.add_trace(go.Scatter(
        x=[mv_vol * 100], y=[mv_ret * 100],
        mode="markers+text",
        marker=dict(color="#FFC107", size=12, symbol="diamond"),
        text=["Min Vol"], textposition="top center",
        textfont=dict(color="#FFC107"),
        name="Min Volatility",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Efficient Frontier",
        height=420,
        xaxis=dict(title="Annualised Volatility (%)", showgrid=True, gridcolor="#2D2D44"),
        yaxis=dict(title="Annualised Return (%)", showgrid=True, gridcolor="#2D2D44"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------------------------
    # Optimal weights
    # ---------------------------------------------------------------------------
    st.markdown("#### Optimal Portfolio Weights (Max Sharpe)")
    wt_col1, wt_col2 = st.columns(2)

    with wt_col1:
        weight_df = pd.DataFrame({
            "Ticker": available,
            "Weight": [f"{w:.1%}" for w in opt_w],
            "Direction": ["LONG" if w > 0 else "SHORT" for w in opt_w],
        })
        st.dataframe(weight_df, use_container_width=True, hide_index=True)

    with wt_col2:
        colors = [ACCENT if w > 0 else DANGER for w in opt_w]
        fig_pie = go.Figure(go.Bar(
            x=available,
            y=opt_w * 100,
            marker_color=colors,
            text=[f"{w:.1%}" for w in opt_w],
            textposition="outside",
            textfont=dict(color="#FFFFFF"),
        ))
        fig_pie.update_layout(
            **PLOTLY_LAYOUT,
            title="Weight Allocation",
            height=300,
            yaxis=dict(title="Weight (%)", showgrid=True, gridcolor="#2D2D44"),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    if allow_short:
        st.info(
            "Short selling is enabled. Negative weights represent short positions. "
            "In practice, short positions require a margin account and incur borrowing costs.",
            icon="ℹ️",
        )

except Exception as e:
    error_card(st, str(e), "Check ticker symbols and try again.")
