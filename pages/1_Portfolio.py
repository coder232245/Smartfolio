import streamlit as st
import json
import os

from src.data_fetcher import validate_ticker, fetch_ticker_info, fetch_multiple_prices
from src.calculations import calculate_portfolio_metrics

st.set_page_config(page_title="Portfolio — SmartFolio", page_icon="💼", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")


# ── Helpers ────────────────────────────────────────────────────────────────────
def load_portfolio() -> dict:
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {"holdings": []}


def save_portfolio(portfolio: dict) -> None:
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


# ── Session state ──────────────────────────────────────────────────────────────
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio()

portfolio = st.session_state.portfolio
holdings = portfolio.get("holdings", [])

# ── Page header ────────────────────────────────────────────────────────────────
st.title("💼 Portfolio Manager")
st.caption("Add, view, and remove your investment holdings.")
st.divider()

# ── Add new holding ────────────────────────────────────────────────────────────
st.subheader("Add a New Holding")

with st.form("add_holding_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        ticker_input = st.text_input(
            "Ticker Symbol",
            placeholder="e.g. AAPL, BTC-USD, SPY",
            help="Use standard Yahoo Finance tickers. For crypto use format like BTC-USD.",
        ).strip().upper()

    with col2:
        shares_input = st.number_input(
            "Number of Shares / Units",
            min_value=0.0001,
            step=0.01,
            format="%.4f",
            help="Enter the quantity you own.",
        )

    with col3:
        price_input = st.number_input(
            "Your Average Purchase Price ($)",
            min_value=0.01,
            step=0.01,
            format="%.2f",
            help="The average price per share/unit you paid.",
        )

    submitted = st.form_submit_button("➕ Add Holding", use_container_width=True)

if submitted:
    if not ticker_input:
        st.error("Please enter a ticker symbol.")
    elif shares_input <= 0:
        st.error("Shares must be greater than 0.")
    elif price_input <= 0:
        st.error("Purchase price must be greater than 0.")
    else:
        # Check for duplicate
        existing_tickers = [h["ticker"] for h in holdings]
        if ticker_input in existing_tickers:
            st.warning(f"**{ticker_input}** is already in your portfolio. Remove it first if you want to update it.")
        else:
            with st.spinner(f"Validating {ticker_input}..."):
                is_valid = validate_ticker(ticker_input)

            if not is_valid:
                st.error(
                    f"**{ticker_input}** does not appear to be a valid ticker. "
                    "Please double-check the symbol (e.g. BTC-USD for Bitcoin)."
                )
            else:
                info = fetch_ticker_info(ticker_input)
                new_holding = {
                    "ticker": ticker_input,
                    "shares": shares_input,
                    "purchase_price": price_input,
                }
                holdings.append(new_holding)
                portfolio["holdings"] = holdings
                st.session_state.portfolio = portfolio
                save_portfolio(portfolio)
                st.success(
                    f"✅ Added **{ticker_input}** ({info.get('name', ticker_input)})  "
                    f"— {shares_input} shares @ ${price_input:.2f}"
                )
                st.rerun()

st.divider()

# ── Current holdings ───────────────────────────────────────────────────────────
st.subheader("Your Holdings")

if not holdings:
    st.info("No holdings yet. Add your first one above.")
else:
    # Fetch prices for the summary view
    tickers = [h["ticker"] for h in holdings]
    with st.spinner("Fetching current prices..."):
        prices_data = fetch_multiple_prices(tickers)

    metrics = calculate_portfolio_metrics(holdings, prices_data)
    holding_map = {h["ticker"]: h for h in metrics["holdings"]}

    for i, h in enumerate(holdings):
        ticker = h["ticker"]
        m = holding_map.get(ticker)

        with st.container():
            col_info, col_price, col_return, col_delete = st.columns([3, 2, 2, 1])

            with col_info:
                st.markdown(f"**{ticker}**")
                st.caption(f"{h['shares']} shares · Avg cost: ${h['purchase_price']:.2f}")

            with col_price:
                if m:
                    delta_color = "🟢" if m["daily_change_pct"] >= 0 else "🔴"
                    st.markdown(f"**${m['current_price']:,.2f}**")
                    st.caption(
                        f"{delta_color} {m['daily_change_pct']:+.2f}% today · "
                        f"Value: ${m['current_value']:,.2f}"
                    )
                else:
                    st.caption("Price unavailable")

            with col_return:
                if m:
                    colour = "#00C805" if m["total_return"] >= 0 else "#FF3B3B"
                    sign = "+" if m["total_return"] >= 0 else ""
                    st.markdown(
                        f"<span style='color:{colour}; font-weight:600'>"
                        f"{sign}${m['total_return']:,.2f} ({sign}{m['total_return_pct']:.2f}%)"
                        f"</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Allocation: {m['allocation_pct']:.1f}%")

            with col_delete:
                if st.button("🗑️", key=f"delete_{ticker}_{i}", help=f"Remove {ticker}"):
                    holdings.pop(i)
                    portfolio["holdings"] = holdings
                    st.session_state.portfolio = portfolio
                    save_portfolio(portfolio)
                    st.success(f"Removed **{ticker}**.")
                    st.rerun()

        st.divider()

    # ── Summary row ────────────────────────────────────────────────────────────
    if metrics["holdings"]:
        st.markdown("### Portfolio Summary")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Value", f"${metrics['total_value']:,.2f}")
        with c2:
            st.metric("Total Cost Basis", f"${metrics['total_cost']:,.2f}")
        with c3:
            sign = "+" if metrics["overall_return"] >= 0 else ""
            st.metric(
                "Overall Return",
                f"${metrics['overall_return']:,.2f}",
                delta=f"{sign}{metrics['overall_return_pct']:.2f}%",
            )
