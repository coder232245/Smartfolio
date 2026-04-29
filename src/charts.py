import plotly.graph_objects as go
import pandas as pd
import numpy as np


# ── Colour palette ────────────────────────────────────────────────────────────
GREEN = "#00C805"
RED = "#FF3B3B"
BLUE = "#636EFA"
BG = "rgba(0,0,0,0)"
GRID = "rgba(128,128,128,0.15)"


def _base_layout(title: str, height: int = 400) -> dict:
    """Shared Plotly layout settings."""
    return dict(
        title=title,
        height=height,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color="#FAFAFA"),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
    )


# ── Portfolio value over time ─────────────────────────────────────────────────
def portfolio_value_chart(portfolio_history: pd.DataFrame) -> go.Figure:
    """Line + area chart of total portfolio value over time."""
    values = portfolio_history["total_value"]
    color = GREEN if values.iloc[-1] >= values.iloc[0] else RED

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolio_history.index,
        y=values,
        mode="lines",
        name="Portfolio Value",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor="rgba(0,200,5,0.10)" if color == GREEN else "rgba(255,59,59,0.10)",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Value: $%{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(**_base_layout("Portfolio Value Over Time", 420))
    return fig


# ── Asset allocation pie ───────────────────────────────────────────────────────
def allocation_pie_chart(holdings_metrics: list) -> go.Figure:
    """Donut chart showing allocation % per holding."""
    labels = [h["ticker"] for h in holdings_metrics]
    values = [h["current_value"] for h in holdings_metrics]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Value: $%{value:,.2f}<br>Allocation: %{percent}<extra></extra>",
    )])
    fig.update_layout(
        title="Asset Allocation",
        height=420,
        paper_bgcolor=BG,
        font=dict(color="#FAFAFA"),
        legend=dict(orientation="v"),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# ── Individual holdings performance (normalised %) ────────────────────────────
def individual_performance_chart(returns_df: pd.DataFrame) -> go.Figure:
    """
    Normalised cumulative return comparison for all holdings.
    Each line starts at 0% and shows gain/loss over time.
    """
    fig = go.Figure()
    for ticker in returns_df.columns:
        fig.add_trace(go.Scatter(
            x=returns_df.index,
            y=returns_df[ticker],
            mode="lines",
            name=ticker,
            hovertemplate=f"<b>{ticker}</b>  %{{x|%b %d, %Y}}<br>Return: %{{y:.2f}}%<extra></extra>",
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    layout = _base_layout("Individual Holdings Performance (Normalised %)", 450)
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    fig.update_layout(**layout)
    return fig


# ── Candlestick chart ─────────────────────────────────────────────────────────
def candlestick_chart(hist: pd.DataFrame, ticker: str) -> go.Figure:
    """OHLC candlestick chart for a single ticker."""
    fig = go.Figure(data=go.Candlestick(
        x=hist.index,
        open=hist["Open"],
        high=hist["High"],
        low=hist["Low"],
        close=hist["Close"],
        name=ticker,
        increasing_line_color=GREEN,
        decreasing_line_color=RED,
    ))
    layout = _base_layout(f"{ticker} — Price Chart", 450)
    layout["xaxis"]["rangeslider"] = dict(visible=False)
    fig.update_layout(**layout)
    return fig


# ── Daily returns histogram ───────────────────────────────────────────────────
def daily_returns_histogram(returns: pd.Series) -> go.Figure:
    """Histogram of daily return distribution with mean line."""
    pct = returns * 100
    mean_val = float(np.mean(pct.values))

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=pct,
        nbinsx=50,
        name="Daily Returns",
        marker_color=BLUE,
        opacity=0.80,
        hovertemplate="Return: %{x:.2f}%<br>Count: %{y}<extra></extra>",
    ))
    fig.add_vline(x=0, line_dash="solid", line_color=RED, opacity=0.6,
                  annotation_text="0%", annotation_position="top right")
    fig.add_vline(x=mean_val, line_dash="dash", line_color="orange",
                  annotation_text=f"Mean: {mean_val:.2f}%", annotation_position="top left")

    layout = _base_layout("Daily Returns Distribution", 380)
    layout["xaxis"]["title"] = "Daily Return (%)"
    layout["yaxis"]["title"] = "Frequency"
    layout.pop("hovermode")
    fig.update_layout(**layout)
    return fig





# ── Rolling volatility ────────────────────────────────────────────────────────
def rolling_volatility_chart(returns: pd.Series, window: int = 30) -> go.Figure:
    """Rolling annualised volatility over time."""
    roll_vol = returns.rolling(window).std() * np.sqrt(252) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=roll_vol.index,
        y=roll_vol,
        mode="lines",
        name=f"{window}-day Rolling Volatility",
        line=dict(color="#FFA500", width=2),
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>Volatility: %{y:.2f}%<extra></extra>",
    ))
    layout = _base_layout(f"{window}-Day Rolling Volatility (Annualised %)", 350)
    layout["yaxis"]["title"] = "Volatility (%)"
    fig.update_layout(**layout)
    return fig
