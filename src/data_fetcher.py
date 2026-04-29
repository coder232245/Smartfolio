import yfinance as yf
import pandas as pd
import numpy as np


def fetch_multiple_prices(tickers: list) -> dict:
    """Fetch current price and daily change for multiple tickers at once."""
    result = {}
    if not tickers:
        return result

    try:
        data = yf.download(tickers, period="5d", progress=False, auto_adjust=True)

        if data.empty:
            return {t: {"price": None, "valid": False} for t in tickers}

        if len(tickers) == 1:
            ticker = tickers[0]
            closes = data["Close"].dropna()
            if len(closes) >= 1:
                current = float(closes.iloc[-1])
                prev = float(closes.iloc[-2]) if len(closes) > 1 else current
                result[ticker] = {
                    "price": current,
                    "prev_close": prev,
                    "daily_change": current - prev,
                    "daily_change_pct": ((current - prev) / prev * 100) if prev != 0 else 0.0,
                    "valid": True,
                }
            else:
                result[ticker] = {"price": None, "valid": False}
        else:
            closes = data["Close"]
            for ticker in tickers:
                if ticker in closes.columns:
                    series = closes[ticker].dropna()
                    if len(series) >= 1:
                        current = float(series.iloc[-1])
                        prev = float(series.iloc[-2]) if len(series) > 1 else current
                        result[ticker] = {
                            "price": current,
                            "prev_close": prev,
                            "daily_change": current - prev,
                            "daily_change_pct": ((current - prev) / prev * 100) if prev != 0 else 0.0,
                            "valid": True,
                        }
                    else:
                        result[ticker] = {"price": None, "valid": False}
                else:
                    result[ticker] = {"price": None, "valid": False}

    except Exception as e:
        for ticker in tickers:
            result[ticker] = {"price": None, "valid": False, "error": str(e)}

    return result


def fetch_historical_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch historical OHLCV data for a single ticker."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, auto_adjust=True)
        return hist
    except Exception:
        return pd.DataFrame()





def validate_ticker(ticker: str) -> bool:
    """Return True if the ticker is valid and has recent price data."""
    try:
        data = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
        return not data.empty
    except Exception:
        return False


def fetch_exchange_rate(to_currency: str = "PKR") -> float:
    """Fetch live exchange rate from USD to the given currency."""
    try:
        ticker = yf.Ticker(f"{to_currency}=X")
        hist = ticker.history(period="2d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return 1.0
    except Exception:
        return 1.0


def fetch_ticker_info(ticker: str) -> dict:
    """Fetch basic info (name, sector, currency) for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "currency": info.get("currency", "USD"),
            "market_cap": info.get("marketCap", None),
        }
    except Exception:
        return {"name": ticker, "sector": "N/A", "currency": "USD", "market_cap": None}
