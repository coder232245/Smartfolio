import streamlit as st
import json
import os

from src.data_fetcher import fetch_historical_data, fetch_multiple_prices
from src.calculations import (
    calculate_historical_portfolio_value,
    calculate_individual_returns,
    calculate_portfolio_metrics,
)
from src.charts import (
    portfolio_value_chart,
    individual_performance_chart,
    candlestick_chart,
)
from src.currency import render_currency_selector

st.set_page_config(page_title="Performance — SmartFolio", page_icon="📊", layout="wide")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")


def load_portfolio() -> dict:
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {"holdings": []}


if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio()

holdings = st.session_state.portfolio.get("holdings", [])

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 Performance")
st.caption("Historical portfolio value, individual holdings, and return comparisons.")
st.divider()

if not holdings:
    st.info("No holdings found. Add some on the **Portfolio** page first.")
    st.stop()

# ── Period selector ────────────────────────────────────────────────────────────
period = st.radio(
    "Select Time Period",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,
    horizontal=True,
)

sym, rate = render_currency_selector()
st.divider()

# ── 1. Portfolio value over time ───────────────────────────────────────────────
st.subheader("Portfolio Value Over Time")
with st.spinner("Loading portfolio history..."):
    history = calculate_historical_portfolio_value(holdings, period)

if not history.empty:
    first_val = history["total_value"].iloc[0]
    last_val  = history["total_value"].iloc[-1]
    period_return     = last_val - first_val
    period_return_pct = (period_return / first_val) * 100 if first_val != 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Start of Period", f"{sym}{first_val * rate:,.2f}")
    with c2:
        st.metric("Current Value", f"{sym}{last_val * rate:,.2f}")
    with c3:
        sign = "+" if period_return >= 0 else ""
        st.metric(
            "Period Return",
            f"{sym}{period_return * rate:,.2f}",
            delta=f"{sign}{period_return_pct:.2f}%",
        )

    st.plotly_chart(portfolio_value_chart(history), use_container_width=True)
else:
    st.warning("Could not load portfolio history.")

st.divider()

# ── 2. Individual holdings performance ─────────────────────────────────────────
st.subheader("Individual Holdings Performance (Normalised %)")
st.caption("All holdings start at 0% so you can compare returns on the same scale.")

with st.spinner("Loading individual performance..."):
    returns_df = calculate_individual_returns(holdings, period)

if not returns_df.empty:
    st.plotly_chart(individual_performance_chart(returns_df), use_container_width=True)

    # Return table
    if not returns_df.empty:
        last_returns = returns_df.iloc[-1].sort_values(ascending=False)
        st.markdown("**Return over period:**")
        cols = st.columns(len(last_returns))
        for col, (ticker, ret) in zip(cols, last_returns.items()):
            colour = "#00C805" if ret >= 0 else "#FF3B3B"
            sign = "+" if ret >= 0 else ""
            col.markdown(
                f"<div style='text-align:center'>"
                f"<b>{ticker}</b><br>"
                f"<span style='color:{colour}; font-size:1.2rem'>{sign}{ret:.2f}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
else:
    st.warning("Could not load individual performance data.")

st.divider()

# ── 3. Candlestick chart for a single holding ──────────────────────────────────
st.subheader("Candlestick Price Chart")

tickers = [h["ticker"] for h in holdings]
selected_ticker = st.selectbox("Select a holding", options=tickers)

with st.spinner(f"Loading {selected_ticker} price data..."):
    hist = fetch_historical_data(selected_ticker, period)

if not hist.empty:
    st.plotly_chart(candlestick_chart(hist, selected_ticker), use_container_width=True)

    # Volume bar chart
    if "Volume" in hist.columns and hist["Volume"].sum() > 0:
        import plotly.graph_objects as go
        vol_fig = go.Figure()
        vol_fig.add_trace(go.Bar(
            x=hist.index,
            y=hist["Volume"],
            name="Volume",
            marker_color="rgba(100,150,255,0.5)",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volume: %{y:,.0f}<extra></extra>",
        ))
        vol_fig.update_layout(
            title=f"{selected_ticker} — Trading Volume",
            height=220,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.15)"),
            margin=dict(l=10, r=10, t=50, b=10),
            showlegend=False,
        )
        st.plotly_chart(vol_fig, use_container_width=True)
else:
    st.warning(f"Could not load price data for {selected_ticker}.")

st.divider()
st.caption("Data provided by Yahoo Finance via yfinance · Prices may be delayed up to 15 minutes.")
