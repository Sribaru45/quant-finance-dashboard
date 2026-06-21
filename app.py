import streamlit as st
from utils.styling import apply_global_css, sidebar_footer, ACCENT, SUBTEXT_COLOR

st.set_page_config(
    page_title="Financial Analytics Platform | Sriram Bharadwaj",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_css(st)

# ---------------------------------------------------------------------------
# Page definitions
# ---------------------------------------------------------------------------
pages = {
    "home": st.Page("pages/home.py", title="Home", icon="🏠", default=True),
    "credit_risk": st.Page("pages/credit_risk.py", title="Credit Risk Model", icon="🏦"),
    "risk_analytics": st.Page("pages/risk_analytics.py", title="Risk Analytics", icon="📉"),
    "options_pricing": st.Page("pages/options_pricing.py", title="Options Pricing", icon="⚙️"),
    "portfolio_opt": st.Page("pages/portfolio_opt.py", title="Portfolio Optimization", icon="📈"),
    "pairs_trading": st.Page("pages/pairs_trading.py", title="Pairs Trading", icon="🔁"),
    "financial_dashboard": st.Page("pages/financial_dashboard.py", title="Financial Dashboard", icon="🖥️"),
}

nav = st.navigation(list(pages.values()))
sidebar_footer(st)
nav.run()
