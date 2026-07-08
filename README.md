# Financial Analytics Platform

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python) ![Streamlit](https://img.shields.io/badge/Streamlit-1.45-red?logo=streamlit) ![Plotly](https://img.shields.io/badge/Plotly-5.24-purple?logo=plotly) ![License](https://img.shields.io/badge/License-MIT-green)

### 🔗 [Live Demo → srirambharadwaj.duckdns.org](https://srirambharadwaj.duckdns.org)

A Bloomberg-lite quantitative finance toolkit built with Python and Streamlit. Designed to demonstrate practical knowledge of risk modeling, derivatives pricing, and portfolio analytics for capital markets roles.

---

## Modules

| # | Module | Description |
|---|--------|-------------|
| 1 | **Credit Risk Model** | PD/LGD/Expected Loss via logistic regression · US (FICO) and Indian (CIBIL) markets |
| 2 | **Risk Analytics** | Portfolio VaR, CVaR, Monte Carlo simulation (1,000–10,000 paths) |
| 3 | **Options Pricing** | Black-Scholes pricing + full Greeks (Δ Γ Θ ν ρ) + sensitivity heatmaps |
| 4 | **Portfolio Optimization** | Markowitz efficient frontier · Sharpe maximization · long-only & short-selling modes |
| 5 | **Pairs Trading** | Engle-Granger cointegration · z-score backtest · P&L tracking |
| 6 | **Financial Dashboard** | Live price/volume · key ratios · revenue trends · peer comparison |

---

## Screenshots

> _Add screenshots here after running the app locally._

---

## Installation

```bash
git clone https://github.com/Sribaru45/quant-finance-dashboard.git
cd quant-finance-dashboard
pip install -r requirements.txt
streamlit run app.py
```

All modules work offline using generated sample data if yfinance is unavailable.

---

## Tech Stack

- **Framework:** Streamlit 1.45
- **Visualizations:** Plotly 5.24 (dark theme throughout)
- **Data:** yfinance (live) · pandas / numpy (processing)
- **Modeling:** scikit-learn · scipy · statsmodels
- **Finance:** Basel II/III (credit risk) · Black-Scholes · Markowitz · Engle-Granger

---

Built by [Sriram Bharadwaj](https://github.com/Sribaru45)
