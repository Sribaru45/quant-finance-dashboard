import pandas as pd
import numpy as np
import streamlit as st

# ---------------------------------------------------------------------------
# yfinance wrapper with sample-data fallback
# ---------------------------------------------------------------------------

def fetch_price_history(tickers: list, period: str = "2y") -> tuple[pd.DataFrame, bool]:
    """Return (price_df, is_live). Falls back to synthetic data on failure."""
    try:
        import yfinance as yf
        raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)
        if raw.empty:
            raise ValueError("Empty response")
        if isinstance(tickers, list) and len(tickers) > 1:
            prices = raw["Close"]
        else:
            prices = raw[["Close"]].rename(columns={"Close": tickers[0] if isinstance(tickers, list) else tickers})
        prices = prices.dropna(how="all")
        if prices.empty:
            raise ValueError("No valid price data")
        return prices, True
    except Exception:
        return _synthetic_prices(tickers), False


def _synthetic_prices(tickers) -> pd.DataFrame:
    """Generate realistic-looking synthetic OHLC prices for offline demo."""
    if isinstance(tickers, str):
        tickers = [tickers]
    np.random.seed(42)
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=504)
    data = {}
    for i, t in enumerate(tickers):
        drift = 0.0003 + i * 0.00005
        vol = 0.015 + i * 0.002
        returns = np.random.normal(drift, vol, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))
        data[t] = prices
    return pd.DataFrame(data, index=dates)


def fetch_ticker_info(ticker: str) -> tuple[dict, bool]:
    """Return (info_dict, is_live)."""
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        if not info or "regularMarketPrice" not in info:
            raise ValueError("No info")
        return info, True
    except Exception:
        return _synthetic_info(ticker), False


def _synthetic_info(ticker: str) -> dict:
    return {
        "regularMarketPrice": 150.0,
        "fiftyTwoWeekHigh": 185.0,
        "fiftyTwoWeekLow": 115.0,
        "regularMarketVolume": 25_000_000,
        "marketCap": 2_400_000_000_000,
        "trailingPE": 28.5,
        "priceToBook": 4.2,
        "returnOnEquity": 0.28,
        "debtToEquity": 45.0,
        "shortName": ticker,
        "sector": "Technology",
        "industry": "Software",
    }


# ---------------------------------------------------------------------------
# Data fallback banner
# ---------------------------------------------------------------------------

def data_source_banner(st, is_live: bool):
    if not is_live:
        st.warning(
            "Live data unavailable — showing sample data. "
            "Check your internet connection or try again later.",
            icon="⚠️",
        )


# ---------------------------------------------------------------------------
# Shared finance helpers
# ---------------------------------------------------------------------------

def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()


def annualized_return(returns: pd.Series) -> float:
    return float((1 + returns.mean()) ** 252 - 1)


def annualized_vol(returns: pd.Series) -> float:
    return float(returns.std() * np.sqrt(252))


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.04) -> float:
    ann_r = annualized_return(returns)
    ann_v = annualized_vol(returns)
    if ann_v == 0:
        return 0.0
    return (ann_r - risk_free) / ann_v


def validate_tickers(tickers: list) -> list:
    """Strip whitespace and uppercase."""
    return [t.strip().upper() for t in tickers if t.strip()]
