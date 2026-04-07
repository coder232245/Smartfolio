import streamlit as st
import pandas as pd
import json
import os

from src.data_fetcher import fetch_multiple_prices
from src.calculations import calculate_portfolio_metrics, calculate_historical_portfolio_value
from src.charts import portfolio_value_chart, allocation_pie_chart

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartFolio",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.6rem; }
    [data-testid="stMetricDelta"] { font-size: 1rem; }
    .section-header { font-size: 1.1rem; font-weight: 600; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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

# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_refresh = st.columns([5, 1])
with col_title:
    st.title("📈 SmartFolio")
    st.caption("Real-Time Investment Portfolio Tracker & Performance Dashboard")
with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.divider()

# ── Empty state ────────────────────────────────────────────────────────────────
if not holdings:
    st.info(
        "👋 **Welcome to SmartFolio!**  \n"
        "Head to the **Portfolio** page in the sidebar to add your first holding."
    )
    st.stop()

# ── Fetch live prices ──────────────────────────────────────────────────────────
tickers = [h["ticker"] for h in holdings]
with st.spinner("Fetching live market data..."):
    prices_data = fetch_multiple_prices(tickers)

metrics = calculate_portfolio_metrics(holdings, prices_data)

# ── Summary metric cards ───────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        label="💼 Total Portfolio Value",
        value=f"${metrics['total_value']:,.2f}",
    )

with c2:
    sign = "+" if metrics["daily_pnl"] >= 0 else ""
    st.metric(
        label="📅 Daily P&L",
        value=f"${metrics['daily_pnl']:,.2f}",
        delta=f"{sign}${metrics['daily_pnl']:,.2f}",
    )

with c3:
    sign = "+" if metrics["overall_return"] >= 0 else ""
    st.metric(
        label="📊 Total Return",
        value=f"${metrics['overall_return']:,.2f}",
        delta=f"{sign}{metrics['overall_return_pct']:.2f}%",
    )

with c4:
    st.metric(
        label="💰 Total Cost Basis",
        value=f"${metrics['total_cost']:,.2f}",
    )

st.divider()

# ── Charts row ─────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    period = st.selectbox(
        "Period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3,
        key="home_period",
    )
    with st.spinner("Loading portfolio history..."):
        history = calculate_historical_portfolio_value(holdings, period)

    if not history.empty:
        st.plotly_chart(portfolio_value_chart(history), use_container_width=True)
    else:
        st.warning("Could not load historical data.")

with col_right:
    if metrics["holdings"]:
        st.plotly_chart(allocation_pie_chart(metrics["holdings"]), use_container_width=True)

st.divider()

# ── Holdings table ─────────────────────────────────────────────────────────────
st.subheader("Holdings Overview")

if metrics["holdings"]:
    rows = []
    for h in metrics["holdings"]:
        rows.append({
            "Ticker":           h["ticker"],
            "Shares":           h["shares"],
            "Avg Cost ($)":     h["purchase_price"],
            "Current Price ($)": h["current_price"],
            "Market Value ($)": h["current_value"],
            "Cost Basis ($)":   h["cost_basis"],
            "Daily P&L ($)":    h["daily_pnl"],
            "Daily Change (%)": h["daily_change_pct"],
            "Total Return ($)": h["total_return"],
            "Total Return (%)": h["total_return_pct"],
            "Allocation (%)":   h["allocation_pct"],
        })

    df = pd.DataFrame(rows)

    # Style rows: green if total return positive, red if negative
    def colour_return(val):
        colour = "#00C805" if val >= 0 else "#FF3B3B"
        return f"color: {colour}"

    styled = (
        df.style
        .format({
            "Shares":            "{:.4f}",
            "Avg Cost ($)":      "${:,.2f}",
            "Current Price ($)": "${:,.2f}",
            "Market Value ($)":  "${:,.2f}",
            "Cost Basis ($)":    "${:,.2f}",
            "Daily P&L ($)":     "${:+,.2f}",
            "Daily Change (%)":  "{:+.2f}%",
            "Total Return ($)":  "${:+,.2f}",
            "Total Return (%)":  "{:+.2f}%",
            "Allocation (%)":    "{:.2f}%",
        })
        .map(colour_return, subset=["Daily P&L ($)", "Total Return ($)", "Total Return (%)"])
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.warning("No valid price data could be fetched for your holdings.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Data provided by Yahoo Finance via yfinance · Prices may be delayed up to 15 minutes.")
