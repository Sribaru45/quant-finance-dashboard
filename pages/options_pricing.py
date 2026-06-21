"""
Options Pricing Dashboard
-------------------------
Black-Scholes model for European call and put options.
Outputs option price + full Greeks: Delta, Gamma, Theta, Vega, Rho.
Sensitivity heatmaps show how price varies with spot and volatility.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import norm

from utils.styling import apply_global_css, module_header, error_card, ACCENT, DANGER, SUBTEXT_COLOR, PLOTLY_LAYOUT

apply_global_css(st)
module_header(st, "⚙️", "Options Pricing Dashboard", "Black-Scholes · Delta · Gamma · Theta · Vega · Rho · Sensitivity Heatmaps")

# ---------------------------------------------------------------------------
# Black-Scholes engine
# ---------------------------------------------------------------------------

def black_scholes(S, K, T, r, sigma, option_type="call"):
    """
    S: spot price, K: strike, T: time to expiry (years),
    r: risk-free rate, sigma: implied volatility.
    Returns (price, d1, d2).
    """
    if T <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
        return intrinsic, 0, 0
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return price, d1, d2


def compute_greeks(S, K, T, r, sigma, option_type="call"):
    price, d1, d2 = black_scholes(S, K, T, r, sigma, option_type)
    if T <= 0 or sigma <= 0:
        return {"Price": price, "Delta": 0, "Gamma": 0, "Theta": 0, "Vega": 0, "Rho": 0}
    sqrt_T = np.sqrt(T)
    pdf_d1 = norm.pdf(d1)

    delta = norm.cdf(d1) if option_type == "call" else norm.cdf(d1) - 1
    gamma = pdf_d1 / (S * sigma * sqrt_T)
    # Theta expressed per calendar day
    theta_raw = (
        -(S * pdf_d1 * sigma) / (2 * sqrt_T)
        - r * K * np.exp(-r * T) * (norm.cdf(d2) if option_type == "call" else norm.cdf(-d2))
    )
    theta = theta_raw / 365
    vega = S * pdf_d1 * sqrt_T / 100   # per 1% vol move
    rho_raw = K * T * np.exp(-r * T) * (norm.cdf(d2) if option_type == "call" else norm.cdf(-d2))
    rho = rho_raw / 100   # per 1% rate move

    return {"Price": round(price, 4), "Delta": round(delta, 4), "Gamma": round(gamma, 6),
            "Theta": round(theta, 4), "Vega": round(vega, 4), "Rho": round(rho, 4)}


# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.markdown("### Option Parameters")
S = st.sidebar.number_input("Spot Price ($)", 1.0, 10_000.0, 150.0, step=1.0)
K = st.sidebar.number_input("Strike Price ($)", 1.0, 10_000.0, 155.0, step=1.0)
T_days = st.sidebar.slider("Time to Expiry (days)", 1, 730, 90)
T = T_days / 365
r = st.sidebar.slider("Risk-Free Rate (%)", 0.0, 15.0, 5.0, step=0.1) / 100
sigma = st.sidebar.slider("Implied Volatility (%)", 1.0, 150.0, 25.0, step=0.5) / 100
option_type = st.sidebar.radio("Option Type", ["call", "put"], horizontal=True)

# ---------------------------------------------------------------------------
# Greeks output
# ---------------------------------------------------------------------------
try:
    greeks = compute_greeks(S, K, T, r, sigma, option_type)

    cols = st.columns(6)
    labels = ["Price", "Delta", "Gamma", "Theta", "Vega", "Rho"]
    descs = ["$", "Δ", "Γ", "Θ/day", "ν/1%σ", "ρ/1%r"]
    for i, (col, key) in enumerate(zip(cols, labels)):
        val = greeks[key]
        col.metric(label=f"{key} ({descs[i]})", value=f"{val:.4f}")

    moneyness = "ATM" if abs(S - K) / K < 0.01 else ("ITM" if (option_type == "call" and S > K) or (option_type == "put" and S < K) else "OTM")
    st.markdown(
        f'<p style="color:{SUBTEXT_COLOR}; font-size:0.82rem;">'
        f"Option is <strong style='color:#FFF'>{moneyness}</strong> · "
        f"Intrinsic value: <strong style='color:#FFF'>${max(S-K,0) if option_type=='call' else max(K-S,0):.2f}</strong> · "
        f"Time value: <strong style='color:#FFF'>${greeks['Price'] - (max(S-K,0) if option_type=='call' else max(K-S,0)):.2f}</strong>"
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---------------------------------------------------------------------------
    # Greeks bar chart
    # ---------------------------------------------------------------------------
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        greek_keys = ["Delta", "Gamma", "Theta", "Vega", "Rho"]
        greek_vals = [greeks[k] for k in greek_keys]
        colors = [ACCENT if v >= 0 else DANGER for v in greek_vals]
        fig_greeks = go.Figure(go.Bar(
            x=greek_keys,
            y=greek_vals,
            marker_color=colors,
            text=[f"{v:.4f}" for v in greek_vals],
            textposition="outside",
            textfont=dict(color="#FFFFFF"),
        ))
        fig_greeks.update_layout(
            **PLOTLY_LAYOUT,
            title=f"Greeks — {option_type.upper()} Option",
            height=320,
            yaxis=dict(showgrid=True, gridcolor="#2D2D44"),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_greeks, use_container_width=True)

    with chart_col2:
        # Delta vs spot price
        spot_range = np.linspace(S * 0.6, S * 1.4, 80)
        deltas = [compute_greeks(s, K, T, r, sigma, option_type)["Delta"] for s in spot_range]
        prices_line = [compute_greeks(s, K, T, r, sigma, option_type)["Price"] for s in spot_range]

        fig_delta = go.Figure()
        fig_delta.add_trace(go.Scatter(x=spot_range, y=deltas, name="Delta",
                                       line=dict(color=ACCENT, width=2)))
        fig_delta.add_trace(go.Scatter(x=spot_range, y=prices_line, name="Price",
                                       line=dict(color="#FFC107", width=2, dash="dash"),
                                       yaxis="y2"))
        fig_delta.add_vline(x=S, line_color=DANGER, line_dash="dot",
                            annotation_text="Current Spot", annotation_font_color=DANGER)
        fig_delta.update_layout(
            **PLOTLY_LAYOUT,
            title="Delta & Price vs Spot",
            height=320,
            yaxis=dict(title="Delta", showgrid=True, gridcolor="#2D2D44"),
            yaxis2=dict(title="Option Price ($)", overlaying="y", side="right"),
            xaxis=dict(title="Spot Price ($)", showgrid=False),
        )
        st.plotly_chart(fig_delta, use_container_width=True)

    # ---------------------------------------------------------------------------
    # Heatmaps
    # ---------------------------------------------------------------------------
    st.markdown("#### Sensitivity Heatmaps")
    hm_col1, hm_col2 = st.columns(2)

    spot_axis = np.linspace(S * 0.7, S * 1.3, 30)
    vol_axis = np.linspace(0.05, 0.80, 30)

    # Price vs Spot × Vol
    price_matrix = np.array([
        [black_scholes(s, K, T, r, v, option_type)[0] for s in spot_axis]
        for v in vol_axis
    ])
    with hm_col1:
        fig_hm1 = go.Figure(go.Heatmap(
            z=price_matrix,
            x=np.round(spot_axis, 1),
            y=np.round(vol_axis * 100, 1),
            colorscale=[[0, "#0E1117"], [0.5, "#00D4AA"], [1, "#FFFFFF"]],
            colorbar=dict(title="Price ($)"),
        ))
        fig_hm1.add_vline(x=S, line_color=DANGER, line_width=1.5)
        fig_hm1.add_hline(y=sigma * 100, line_color=DANGER, line_width=1.5)
        fig_hm1.update_layout(
            **PLOTLY_LAYOUT,
            title="Option Price: Spot × Volatility",
            height=340,
            xaxis=dict(title="Spot Price ($)"),
            yaxis=dict(title="Volatility (%)"),
        )
        st.plotly_chart(fig_hm1, use_container_width=True)

    # Delta vs Spot × Vol
    delta_matrix = np.array([
        [compute_greeks(s, K, T, r, v, option_type)["Delta"] for s in spot_axis]
        for v in vol_axis
    ])
    with hm_col2:
        fig_hm2 = go.Figure(go.Heatmap(
            z=delta_matrix,
            x=np.round(spot_axis, 1),
            y=np.round(vol_axis * 100, 1),
            colorscale=[[0, DANGER], [0.5, "#1C1C2E"], [1, ACCENT]],
            colorbar=dict(title="Delta"),
        ))
        fig_hm2.add_vline(x=S, line_color="#FFFFFF", line_width=1.5)
        fig_hm2.add_hline(y=sigma * 100, line_color="#FFFFFF", line_width=1.5)
        fig_hm2.update_layout(
            **PLOTLY_LAYOUT,
            title="Delta: Spot × Volatility",
            height=340,
            xaxis=dict(title="Spot Price ($)"),
            yaxis=dict(title="Volatility (%)"),
        )
        st.plotly_chart(fig_hm2, use_container_width=True)

except Exception as e:
    error_card(st, str(e), "Adjust input parameters and try again.")
