"""
Credit Risk Model
-----------------
Trains a logistic regression on the UCI German Credit dataset (US proxy)
or a synthetic Indian credit dataset. Outputs PD, risk tier, and expected loss.
Basel II/III framing: PD × LGD × EAD = Expected Loss.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import os

from utils.styling import apply_global_css, module_header, error_card, ACCENT, DANGER, SUBTEXT_COLOR, PLOTLY_LAYOUT

apply_global_css(st)
module_header(st, "🏦", "Credit Risk Model", "Probability of Default (PD) · Loss Given Default (LGD) · Expected Loss · Basel II/III")

# ---------------------------------------------------------------------------
# Market toggle
# ---------------------------------------------------------------------------
market = st.radio("Market", ["🇺🇸 US Market (FICO)", "🇮🇳 Indian Market (CIBIL)"], horizontal=True)
is_india = "CIBIL" in market
st.markdown("---")

# ---------------------------------------------------------------------------
# Load / generate training data
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_german_credit() -> pd.DataFrame:
    """
    Load UCI German Credit dataset from data/sample/.
    Falls back to a synthetically generated dataset with the same schema.
    Features used: credit_score (FICO proxy), loan_amount, dti, emp_years, default (0/1).
    """
    path = os.path.join(os.path.dirname(__file__), "..", "data", "sample", "german_credit.csv")
    path = os.path.normpath(path)
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df
    # Synthetic fallback with realistic US credit distributions
    np.random.seed(0)
    n = 1000
    fico = np.clip(np.random.normal(680, 80, n), 300, 850).astype(int)
    loan = np.random.lognormal(10.5, 0.6, n)
    dti = np.clip(np.random.normal(0.35, 0.15, n), 0.01, 0.99)
    emp = np.clip(np.random.exponential(5, n), 0, 40)
    # Default probability increases with low FICO, high DTI, low employment
    log_odds = -4 + (-0.008) * fico + 2.5 * dti + (-0.05) * emp
    prob = 1 / (1 + np.exp(-log_odds))
    default = np.random.binomial(1, prob)
    return pd.DataFrame({"credit_score": fico, "loan_amount": loan, "dti": dti, "emp_years": emp, "default": default})


@st.cache_data(show_spinner=False)
def load_india_credit() -> pd.DataFrame:
    """
    Synthetic Indian credit dataset using CIBIL score conventions.
    CIBIL range: 300-900. High scores (750+) → low default risk.
    """
    np.random.seed(1)
    n = 1000
    cibil = np.clip(np.random.normal(700, 90, n), 300, 900).astype(int)
    loan = np.random.lognormal(11.5, 0.7, n)
    dti = np.clip(np.random.normal(0.40, 0.18, n), 0.01, 0.99)
    emp = np.clip(np.random.exponential(4, n), 0, 35)
    log_odds = -5 + (-0.007) * cibil + 3.0 * dti + (-0.06) * emp
    prob = 1 / (1 + np.exp(-log_odds))
    default = np.random.binomial(1, prob)
    return pd.DataFrame({"credit_score": cibil, "loan_amount": loan, "dti": dti, "emp_years": emp, "default": default})


@st.cache_resource(show_spinner=False)
def train_model(market_key: str):
    df = load_india_credit() if market_key == "india" else load_german_credit()
    X = df[["credit_score", "loan_amount", "dti", "emp_years"]]
    y = df["default"]
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=500, random_state=42)),
    ])
    pipeline.fit(X, y)
    return pipeline, df


market_key = "india" if is_india else "us"
model, training_df = train_model(market_key)

# ---------------------------------------------------------------------------
# Sidebar: user inputs
# ---------------------------------------------------------------------------
st.sidebar.markdown("### Loan Parameters")

score_label = "CIBIL Score (300–900)" if is_india else "FICO Score (300–850)"
score_min, score_max, score_default = (300, 900, 700) if is_india else (300, 850, 680)

credit_score = st.sidebar.slider(score_label, score_min, score_max, score_default)
loan_amount = st.sidebar.number_input("Loan Amount ($)" if not is_india else "Loan Amount (₹)", min_value=1000, max_value=5_000_000, value=250_000, step=5000)
dti = st.sidebar.slider("Debt-to-Income Ratio", 0.01, 0.99, 0.35, step=0.01, format="%.2f")
emp_years = st.sidebar.slider("Employment Years", 0, 40, 5)
lgd_input = st.sidebar.slider("Loss Given Default (LGD %)", 10, 90, 45, help="Estimated % of loan lost if default occurs. Collateral reduces this.")

# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
try:
    X_input = pd.DataFrame([[credit_score, loan_amount, dti, emp_years]],
                           columns=["credit_score", "loan_amount", "dti", "emp_years"])
    pd_score = float(model.predict_proba(X_input)[0][1])
    lgd = lgd_input / 100
    ead = loan_amount
    expected_loss = pd_score * lgd * ead

    if pd_score < 0.15:
        risk_tier = "LOW"
        tier_color = ACCENT
    elif pd_score < 0.40:
        risk_tier = "MEDIUM"
        tier_color = "#FFC107"
    else:
        risk_tier = "HIGH"
        tier_color = DANGER

    # ---------------------------------------------------------------------------
    # Output metrics
    # ---------------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Probability of Default", f"{pd_score:.1%}")
    col2.metric("Risk Tier", risk_tier)
    col3.metric("Loss Given Default", f"{lgd_input}%")
    col4.metric("Expected Loss", f"${expected_loss:,.0f}" if not is_india else f"₹{expected_loss:,.0f}")

    st.markdown(
        f'<p style="color:{SUBTEXT_COLOR}; font-size:0.8rem;">'
        "Basel II/III Formula: <strong style='color:#FFF'>Expected Loss = PD × LGD × EAD</strong>"
        f" = {pd_score:.1%} × {lgd_input}% × {'$' if not is_india else '₹'}{loan_amount:,}"
        f" = {'$' if not is_india else '₹'}{expected_loss:,.0f}</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---------------------------------------------------------------------------
    # Charts: gauge + feature importance
    # ---------------------------------------------------------------------------
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Risk gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pd_score * 100,
            title={"text": "PD Score (%)", "font": {"color": "#FFFFFF", "size": 14}},
            number={"suffix": "%", "font": {"color": "#FFFFFF", "size": 28}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#A0AEC0"},
                "bar": {"color": tier_color},
                "bgcolor": "#1C1C2E",
                "bordercolor": "#2D2D44",
                "steps": [
                    {"range": [0, 15], "color": "rgba(0,212,170,0.15)"},
                    {"range": [15, 40], "color": "rgba(255,193,7,0.15)"},
                    {"range": [40, 100], "color": "rgba(255,107,107,0.15)"},
                ],
                "threshold": {
                    "line": {"color": tier_color, "width": 3},
                    "thickness": 0.75,
                    "value": pd_score * 100,
                },
            },
        ))
        fig_gauge.update_layout(**PLOTLY_LAYOUT, height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with chart_col2:
        # Feature importance (logistic regression coefficients)
        clf = model.named_steps["clf"]
        scaler = model.named_steps["scaler"]
        coef = clf.coef_[0]
        features = [score_label.split(" (")[0], "Loan Amount", "DTI Ratio", "Employment Years"]
        colors = [DANGER if c > 0 else ACCENT for c in coef]

        fig_imp = go.Figure(go.Bar(
            x=coef,
            y=features,
            orientation="h",
            marker_color=colors,
            text=[f"{c:+.3f}" for c in coef],
            textposition="outside",
            textfont=dict(color="#FFFFFF"),
        ))
        fig_imp.update_layout(
            **PLOTLY_LAYOUT,
            title="Feature Importance (Log-Odds Coefficients)",
            height=300,
            xaxis=dict(title="Coefficient", showgrid=True, gridcolor="#2D2D44"),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    # ---------------------------------------------------------------------------
    # PD distribution context
    # ---------------------------------------------------------------------------
    st.markdown("#### Where does this borrower sit in the training population?")
    train_pds = model.predict_proba(training_df[["credit_score", "loan_amount", "dti", "emp_years"]])[:, 1]
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=train_pds,
        nbinsx=40,
        marker_color=ACCENT,
        opacity=0.7,
        name="Population PD",
    ))
    fig_hist.add_vline(x=pd_score, line_color=DANGER, line_width=2,
                       annotation_text=f"This borrower: {pd_score:.1%}",
                       annotation_font_color=DANGER)
    fig_hist.update_layout(
        **PLOTLY_LAYOUT,
        title="PD Distribution — Training Population",
        height=280,
        xaxis=dict(title="Probability of Default", showgrid=False),
        yaxis=dict(title="Count", showgrid=True, gridcolor="#2D2D44"),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown(
        f'<p style="color:{SUBTEXT_COLOR}; font-size:0.78rem; margin-top:-0.5rem;">'
        f"Model trained on {'synthetic Indian credit data (CIBIL conventions)' if is_india else 'UCI German Credit dataset (US proxy)'}. "
        "For illustrative purposes only."
        "</p>",
        unsafe_allow_html=True,
    )

except Exception as e:
    error_card(st, str(e), "Try adjusting the input values.")
