"""
Risk Analytics Dashboard
------------------------
Portfolio VaR (historical + parametric), CVaR (Expected Shortfall),
and Monte Carlo simulation.

Note: Parametric VaR assumes normally distributed returns. Historical
and Monte Carlo methods make no distributional assumption and are
generally more robust for fat-tailed assets.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.styling import apply_global_css, module_header, error_card, data_source_banner, ACCENT, DANGER, SUBTEXT_COLOR, PLOTLY_LAYOUT
from utils.helpers import fetch_price_history, compute_returns, validate_tickers, data_source_banner as _banner

apply_global_css(st)
module_header(st, "📉", "Risk Analytics Dashboard", "Portfolio VaR · CVaR (Expected Shortfall) · Monte Carlo Simulation")

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.markdown("### Portfolio Settings")
tickers_raw = st.sidebar.text_input("Tickers (comma-separated)", "SPY,QQQ,GLD,TLT")
weights_raw = st.sidebar.text_input("Weights (comma-separated, must sum to 1)", "0.4,0.3,0.2,0.1")
confidence = st.sidebar.slider("Confidence Level", 0.90, 0.99, 0.95, step=0.01, format="%.2f")
horizon = st.sidebar.slider("Time Horizon (days)", 1, 30, 1)
n_sims = st.sidebar.slider("Monte Carlo Paths", 1000, 10000, 5000, step=500)
portfolio_value = st.sidebar.number_input("Portfolio Value ($)", min_value=10_000, max_value=100_000_000, value=1_000_000, step=10_000)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
try:
    tickers = validate_tickers(tickers_raw.split(","))
    weights = [float(w.strip()) for w in weights_raw.split(",")]

    if len(tickers) != len(weights):
        error_card(st, "Number of tickers must match number of weights.")
        st.stop()
    if abs(sum(weights) - 1.0) > 0.01:
        error_card(st, f"Weights sum to {sum(weights):.3f} — must sum to 1.0.")
        st.stop()
    weights = np.array(weights)

    # ---------------------------------------------------------------------------
    # Data
    # ---------------------------------------------------------------------------
    with st.spinner("Fetching price data..."):
        prices, is_live = fetch_price_history(tickers, period="2y")
    _banner(st, is_live)

    # Align columns
    available = [t for t in tickers if t in prices.columns]
    if not available:
        error_card(st, "No valid price data found for any ticker.", "Check ticker symbols.")
        st.stop()

    prices = prices[available]
    weights_aligned = weights[:len(available)]
    weights_aligned = weights_aligned / weights_aligned.sum()

    returns = compute_returns(prices)
    port_returns = returns.dot(weights_aligned)

    # ---------------------------------------------------------------------------
    # VaR & CVaR calculations
    # ---------------------------------------------------------------------------
    alpha = 1 - confidence

    # Historical VaR
    hist_var_pct = float(np.percentile(port_returns, alpha * 100))
    hist_var = abs(hist_var_pct) * portfolio_value * np.sqrt(horizon)
    hist_cvar_pct = float(port_returns[port_returns <= hist_var_pct].mean())
    hist_cvar = abs(hist_cvar_pct) * portfolio_value * np.sqrt(horizon)

    # Parametric VaR (normal distribution assumption)
    from scipy import stats
    mu = port_returns.mean()
    sigma = port_returns.std()
    param_var_pct = abs(float(stats.norm.ppf(alpha, mu, sigma)))
    param_var = param_var_pct * portfolio_value * np.sqrt(horizon)
    param_cvar_pct = float(stats.norm.expect(lambda x: x, loc=mu, scale=sigma, lb=-np.inf, ub=stats.norm.ppf(alpha, mu, sigma)) / alpha)
    param_cvar = abs(param_cvar_pct) * portfolio_value * np.sqrt(horizon)

    # Monte Carlo VaR
    sim_returns = np.random.multivariate_normal(
        mean=returns[available].mean().values,
        cov=returns[available].cov().values,
        size=n_sims,
    )
    sim_port = sim_returns.dot(weights_aligned)
    mc_var_pct = abs(float(np.percentile(sim_port, alpha * 100)))
    mc_var = mc_var_pct * portfolio_value * np.sqrt(horizon)
    mc_cvar = abs(float(sim_port[sim_port <= -mc_var_pct].mean())) * portfolio_value * np.sqrt(horizon)

    # ---------------------------------------------------------------------------
    # Metric cards
    # ---------------------------------------------------------------------------
    st.markdown(f"#### {confidence:.0%} Confidence · {horizon}-Day Horizon · ${portfolio_value:,.0f} Portfolio")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Hist. VaR", f"${hist_var:,.0f}")
    c2.metric("Hist. CVaR", f"${hist_cvar:,.0f}")
    c3.metric("Param. VaR", f"${param_var:,.0f}")
    c4.metric("Param. CVaR", f"${param_cvar:,.0f}")
    c5.metric("MC VaR", f"${mc_var:,.0f}")
    c6.metric("MC CVaR", f"${mc_cvar:,.0f}")

    st.info(
        "**Note:** Parametric VaR assumes normally distributed returns. "
        "Historical and Monte Carlo methods make no distributional assumption "
        "and are generally more robust for fat-tailed assets.",
        icon="ℹ️",
    )

    st.markdown("---")

    # ---------------------------------------------------------------------------
    # Return distribution histogram
    # ---------------------------------------------------------------------------
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=port_returns * 100,
        nbinsx=60,
        marker_color=ACCENT,
        opacity=0.75,
        name="Daily Returns",
    ))
    fig_hist.add_vline(x=-hist_var_pct * 100, line_color=DANGER, line_width=2,
                       annotation_text=f"Hist VaR {confidence:.0%}",
                       annotation_font_color=DANGER)
    fig_hist.add_vline(x=-param_var_pct * 100, line_color="#FFC107", line_width=2, line_dash="dash",
                       annotation_text="Param VaR",
                       annotation_font_color="#FFC107")
    fig_hist.update_layout(
        **PLOTLY_LAYOUT,
        title="Portfolio Daily Return Distribution",
        height=320,
        xaxis=dict(title="Return (%)", showgrid=False),
        yaxis=dict(title="Frequency", showgrid=True, gridcolor="#2D2D44"),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # ---------------------------------------------------------------------------
    # Monte Carlo fan chart
    # ---------------------------------------------------------------------------
    st.markdown("#### Monte Carlo Simulation — Portfolio Value Paths")
    n_plot = min(200, n_sims)
    daily_sim = np.random.multivariate_normal(
        mean=returns[available].mean().values,
        cov=returns[available].cov().values,
        size=(n_plot, 30),
    )
    paths = portfolio_value * np.cumprod(1 + daily_sim.dot(weights_aligned), axis=1)

    fig_mc = go.Figure()
    for i in range(n_plot):
        fig_mc.add_trace(go.Scatter(
            y=paths[i],
            mode="lines",
            line=dict(color=ACCENT, width=0.4),
            opacity=0.15,
            showlegend=False,
        ))
    # Percentile bands
    p5 = np.percentile(paths, 5, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p95 = np.percentile(paths, 95, axis=0)
    days = list(range(1, 31))
    fig_mc.add_trace(go.Scatter(y=p95, x=days, line=dict(color="#FFC107", width=2), name="95th pct"))
    fig_mc.add_trace(go.Scatter(y=p50, x=days, line=dict(color=ACCENT, width=2), name="Median"))
    fig_mc.add_trace(go.Scatter(y=p5, x=days, line=dict(color=DANGER, width=2), name="5th pct"))
    fig_mc.update_layout(
        **PLOTLY_LAYOUT,
        height=350,
        xaxis=dict(title="Days", showgrid=False),
        yaxis=dict(title="Portfolio Value ($)", showgrid=True, gridcolor="#2D2D44"),
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    # ---------------------------------------------------------------------------
    # Cumulative returns by asset
    # ---------------------------------------------------------------------------
    st.markdown("#### Cumulative Returns by Asset")
    cum_ret = (1 + returns[available]).cumprod()
    fig_cum = go.Figure()
    colors = [ACCENT, "#FFC107", DANGER, "#A78BFA", "#60A5FA"]
    for i, col in enumerate(cum_ret.columns):
        fig_cum.add_trace(go.Scatter(
            x=cum_ret.index, y=cum_ret[col],
            mode="lines",
            name=col,
            line=dict(color=colors[i % len(colors)], width=1.5),
        ))
    fig_cum.update_layout(
        **PLOTLY_LAYOUT,
        height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Cumulative Return (1=start)", showgrid=True, gridcolor="#2D2D44"),
    )
    st.plotly_chart(fig_cum, use_container_width=True)

except Exception as e:
    error_card(st, str(e), "Check ticker symbols and weights format.")
