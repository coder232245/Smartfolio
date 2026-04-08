import streamlit as st
from .data_fetcher import fetch_exchange_rate


CURRENCIES = {
    "USD": {"symbol": "$",  "code": "USD"},
    "PKR": {"symbol": "₨", "code": "PKR"},
}


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

    # Cache the rate in session state so we don't re-fetch on every interaction
    rate_key = f"rate_{currency}"
    if rate_key not in st.session_state:
        with st.sidebar:
            with st.spinner(f"Fetching USD/{currency} rate..."):
                st.session_state[rate_key] = fetch_exchange_rate(currency)

    rate = st.session_state[rate_key]
    symbol = CURRENCIES[currency]["symbol"]

    st.sidebar.caption(f"1 USD = {symbol}{rate:,.2f}")

    return symbol, rate
