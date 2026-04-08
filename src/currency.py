import streamlit as st
import yfinance as yf


CURRENCIES = {
    "USD": {"symbol": "$",  "code": "USD"},
    "PKR": {"symbol": "₨", "code": "PKR"},
}


def _fetch_exchange_rate(to_currency: str) -> float:
    """Fetch live USD to target currency exchange rate."""
    try:
        ticker = yf.Ticker(f"{to_currency}=X")
        hist = ticker.history(period="2d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return 1.0
    except Exception:
        return 1.0


def render_currency_selector() -> tuple:
    """
    Renders a currency selector in the sidebar.
    Returns (symbol, rate) where rate is the multiplier from USD.
    """
    currency = st.sidebar.selectbox(
        "Currency",
        options=list(CURRENCIES.keys()),
        index=0,
        key="selected_currency",
    )

    if currency == "USD":
        return "$", 1.0

    rate_key = f"rate_{currency}"
    if rate_key not in st.session_state:
        with st.sidebar:
            with st.spinner(f"Fetching USD/{currency} rate..."):
                st.session_state[rate_key] = _fetch_exchange_rate(currency)

    rate = st.session_state[rate_key]
    symbol = CURRENCIES[currency]["symbol"]

    st.sidebar.caption(f"1 USD = {symbol}{rate:,.2f}")

    return symbol, rate
