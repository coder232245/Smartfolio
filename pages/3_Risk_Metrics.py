import streamlit as st
import pandas as pd
import numpy as np
import json
import os

from src.calculations import (
    calculate_historical_portfolio_value,
    calculate_daily_returns,
    calculate_sharpe_ratio,
    calculate_volatility,
    calculate_max_drawdown,
)
from src.charts import (
    daily_returns_histogram,
    correlation_heatmap,
    rolling_volatility_chart,
)
from src.currency import render_currency_selector

st.set_page_config(page_title="Risk Metrics — SmartFolio", page_icon="⚠️", layout="wide")

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
st.title("⚠️ Risk Metrics")
st.caption("Sharpe Ratio, Beta, Volatility, Max Drawdown, and more.")
st.divider()

if not holdings:
    st.info("No holdings found. Add some on the **Portfolio** page first.")
    st.stop()

# ── Controls ───────────────────────────────────────────────────────────────────
sym, rate = render_currency_selector()
col_period, col_rf = st.columns([2, 2])
with col_period:
    period = st.selectbox(
        "Analysis Period",
        options=["3mo", "6mo", "1y", "2y", "3y"],
        index=2,
    )
with col_rf:
    risk_free_rate = st.slider(
        "Risk-Free Rate (Annual %)",
        min_value=0.0,
        max_value=10.0,
        value=5.0,
        step=0.25,
        help="Typically the current US 10-year Treasury yield.",
    ) / 100

st.divider()

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("Computing risk metrics..."):
    history = calculate_historical_portfolio_value(holdings, period)

if history.empty:
    st.error("Could not load historical data to compute risk metrics.")
    st.stop()

returns = calculate_daily_returns(history)

# Compute all metrics
sharpe    = calculate_sharpe_ratio(returns, risk_free_rate)
vol       = calculate_volatility(returns)
max_dd    = calculate_max_drawdown(history)
mean_ret  = float(np.mean(returns.values) * 100)
best_day  = float(returns.max() * 100)
worst_day = float(returns.min() * 100)

# ── Metric cards ───────────────────────────────────────────────────────────────
st.subheader("Key Risk Indicators")

c1, c2, c3 = st.columns(3)

with c1:
    colour = "#00C805" if sharpe >= 1.0 else ("#FFA500" if sharpe >= 0 else "#FF3B3B")
    st.metric("Sharpe Ratio", f"{sharpe:.2f}")
    if sharpe >= 2.0:
        st.caption("🟢 Excellent — high return per unit of risk")
    elif sharpe >= 1.0:
        st.caption("🟡 Good — decent risk-adjusted return")
    elif sharpe >= 0:
        st.caption("🟠 Below average — low return for risk taken")
    else:
        st.caption("🔴 Negative — worse than risk-free asset")


with c2:
    st.metric("Annualised Volatility", f"{vol:.2f}%")
    if vol < 10:
        st.caption("🟢 Low volatility")
    elif vol < 20:
        st.caption("🟡 Moderate volatility")
    else:
        st.caption("🔴 High volatility")

with c3:
    st.metric("Max Drawdown", f"{max_dd:.2f}%")
    if max_dd > -10:
        st.caption("🟢 Small drawdown")
    elif max_dd > -25:
        st.caption("🟡 Moderate drawdown")
    else:
        st.caption("🔴 Large drawdown — significant peak-to-trough loss")

st.divider()

# ── Secondary stats ────────────────────────────────────────────────────────────
st.subheader("Return Statistics")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Avg Daily Return", f"{mean_ret:+.3f}%")
with c2:
    st.metric("Best Single Day", f"{best_day:+.2f}%")
with c3:
    st.metric("Worst Single Day", f"{worst_day:+.2f}%")

st.divider()

# ── Daily returns histogram ────────────────────────────────────────────────────
st.subheader("Daily Returns Distribution")
st.caption(
    "Shows how often your portfolio gained or lost on a given day. "
    "A tight, right-skewed distribution is ideal."
)
st.plotly_chart(daily_returns_histogram(returns), use_container_width=True)

st.divider()

# ── Rolling volatility ─────────────────────────────────────────────────────────
st.subheader("Rolling 30-Day Volatility")
st.caption("Tracks how volatility has changed over time. Spikes indicate periods of market stress.")
st.plotly_chart(rolling_volatility_chart(returns, window=30), use_container_width=True)

st.divider()



# ── Sharpe ratio explainer ─────────────────────────────────────────────────────
with st.expander("📖 How are these metrics calculated?"):
    st.markdown(f"""
| Metric | Formula |
|---|---|
| **Sharpe Ratio** | `(mean_daily_return − daily_risk_free_rate) / std(returns) × √252` |
| **Volatility** | `std(daily_returns) × √252 × 100` |
| **Max Drawdown** | `min((value − rolling_peak) / rolling_peak) × 100` |

- Risk-free rate used: **{risk_free_rate*100:.2f}%** per year → **{risk_free_rate/252*100:.4f}%** per day
- All metrics computed over the **{period}** period using **{len(returns)}** trading days of data.
- Daily returns: `pct_change()` on total portfolio value (pandas).

    """)

st.caption("Data provided by Yahoo Finance via yfinance · Prices may be delayed up to 15 minutes.")
