import pandas as pd
import numpy as np
from src.data_fetcher import fetch_historical_data, fetch_market_benchmark


def calculate_portfolio_metrics(holdings: list, prices_data: dict) -> dict:
    """
    Calculate core portfolio metrics for all holdings.
    Returns total value, daily P&L, total return, and per-holding breakdown.
    """
    total_value = 0.0
    total_cost = 0.0
    daily_pnl = 0.0
    holding_metrics = []

    for h in holdings:
        ticker = h["ticker"]
        shares = float(h["shares"])
        purchase_price = float(h["purchase_price"])

        price_info = prices_data.get(ticker, {})
        if not price_info.get("valid") or price_info.get("price") is None:
            continue

        current_price = price_info["price"]
        current_value = shares * current_price
        cost_basis = shares * purchase_price
        total_return_dollar = current_value - cost_basis
        total_return_pct = ((current_price - purchase_price) / purchase_price) * 100
        daily_pnl_holding = shares * price_info["daily_change"]

        total_value += current_value
        total_cost += cost_basis
        daily_pnl += daily_pnl_holding

        holding_metrics.append({
            "ticker": ticker,
            "shares": shares,
            "purchase_price": purchase_price,
            "current_price": current_price,
            "current_value": current_value,
            "cost_basis": cost_basis,
            "total_return": total_return_dollar,
            "total_return_pct": total_return_pct,
            "daily_change": price_info["daily_change"],
            "daily_change_pct": price_info["daily_change_pct"],
            "daily_pnl": daily_pnl_holding,
            "allocation_pct": 0.0,
        })

    # Calculate allocation % now that we know total_value
    for h in holding_metrics:
        h["allocation_pct"] = (h["current_value"] / total_value * 100) if total_value > 0 else 0.0

    overall_return = total_value - total_cost
    overall_return_pct = ((overall_return / total_cost) * 100) if total_cost > 0 else 0.0

    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "daily_pnl": daily_pnl,
        "overall_return": overall_return,
        "overall_return_pct": overall_return_pct,
        "holdings": holding_metrics,
    }


def calculate_historical_portfolio_value(holdings: list, period: str = "1y") -> pd.DataFrame:
    """
    Build a DataFrame of total portfolio value per day over the given period.
    Each holding's daily value = shares * closing price.
    Missing days (e.g. holidays) are forward-filled.
    """
    if not holdings:
        return pd.DataFrame()

    all_series = {}
    for h in holdings:
        hist = fetch_historical_data(h["ticker"], period)
        if not hist.empty:
            all_series[h["ticker"]] = hist["Close"] * float(h["shares"])

    if not all_series:
        return pd.DataFrame()

    portfolio_df = pd.DataFrame(all_series)
    portfolio_df = portfolio_df.ffill()       # forward-fill missing trading days
    portfolio_df["total_value"] = portfolio_df.sum(axis=1)
    portfolio_df = portfolio_df.dropna(subset=["total_value"])
    return portfolio_df


def calculate_daily_returns(portfolio_history: pd.DataFrame) -> pd.Series:
    """Calculate daily percentage returns from portfolio history."""
    if portfolio_history.empty:
        return pd.Series(dtype=float)
    returns = portfolio_history["total_value"].pct_change().dropna()
    return returns


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.05) -> float:
    """
    Calculate the annualized Sharpe Ratio.

    Formula:
        Sharpe = (mean_excess_return / std_return) * sqrt(252)

    Parameters:
        returns        : daily portfolio returns (pandas Series)
        risk_free_rate : annual risk-free rate (default 5% US Treasury)
    """
    if returns.empty or len(returns) < 2:
        return 0.0

    daily_rf = risk_free_rate / 252                    # convert annual → daily
    excess_returns = returns - daily_rf
    mean_excess = np.mean(excess_returns.values)
    std_returns = np.std(returns.values, ddof=1)

    if std_returns == 0:
        return 0.0

    sharpe = (mean_excess / std_returns) * np.sqrt(252)
    return round(float(sharpe), 2)


def calculate_beta(portfolio_returns: pd.Series, period: str = "1y") -> float:
    """
    Calculate portfolio beta relative to the S&P 500.

    Formula:
        Beta = Cov(portfolio, market) / Var(market)

    A beta of 1 means the portfolio moves with the market.
    """
    try:
        market_hist = fetch_market_benchmark(period)
        if market_hist.empty:
            return 1.0

        market_returns = market_hist["Close"].pct_change().dropna()

        combined = pd.DataFrame({
            "portfolio": portfolio_returns,
            "market": market_returns,
        }).dropna()

        if len(combined) < 10:
            return 1.0

        p = combined["portfolio"].values
        m = combined["market"].values

        cov_matrix = np.cov(p, m)            # 2x2 covariance matrix
        beta = cov_matrix[0, 1] / cov_matrix[1, 1]
        return round(float(beta), 2)

    except Exception:
        return 1.0


def calculate_volatility(returns: pd.Series) -> float:
    """
    Calculate annualized volatility as a percentage.

    Formula:
        Volatility = std(daily_returns) * sqrt(252) * 100
    """
    if returns.empty:
        return 0.0
    daily_vol = np.std(returns.values, ddof=1)
    annualized = daily_vol * np.sqrt(252) * 100
    return round(float(annualized), 2)


def calculate_max_drawdown(portfolio_history: pd.DataFrame) -> float:
    """
    Calculate the maximum drawdown as a percentage.

    Formula:
        Drawdown = (value - rolling_peak) / rolling_peak
        Max Drawdown = min(drawdown)
    """
    if portfolio_history.empty:
        return 0.0

    values = portfolio_history["total_value"].values
    peak = np.maximum.accumulate(values)
    drawdown = (values - peak) / peak
    max_dd = float(np.min(drawdown)) * 100
    return round(max_dd, 2)


def calculate_correlation_matrix(holdings: list, period: str = "1y") -> pd.DataFrame:
    """
    Calculate the Pearson correlation matrix of daily returns between all holdings.
    Uses pandas .corr() which internally uses numpy.
    """
    returns_data = {}
    for h in holdings:
        hist = fetch_historical_data(h["ticker"], period)
        if not hist.empty:
            returns_data[h["ticker"]] = hist["Close"].pct_change().dropna()

    if not returns_data:
        return pd.DataFrame()

    returns_df = pd.DataFrame(returns_data).dropna()
    return returns_df.corr().round(3)


def calculate_individual_returns(holdings: list, period: str = "1y") -> pd.DataFrame:
    """
    Calculate normalized cumulative returns for each holding (starts at 0%).
    Used for the performance comparison chart.
    """
    data = {}
    for h in holdings:
        hist = fetch_historical_data(h["ticker"], period)
        if not hist.empty:
            normalized = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
            data[h["ticker"]] = normalized

    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)
