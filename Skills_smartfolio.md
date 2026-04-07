# SmartFolio — Project Skills Reference

A real-time investment portfolio tracker and performance dashboard built with Streamlit, yfinance, Plotly, and pandas.

---

## Project Structure

```
smartfolio/
├── Home.py                     # Main dashboard page (entry point)
├── pages/
│   ├── 1_Portfolio.py          # Add / remove holdings
│   ├── 2_Performance.py        # Historical charts, candlesticks
│   └── 3_Risk_Metrics.py       # Sharpe, Beta, Volatility, Drawdown
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py         # yfinance wrappers
│   ├── calculations.py         # All financial math
│   └── charts.py               # Plotly chart builders
├── portfolio.json              # Persisted holdings (auto-created)
├── requirements.txt
└── venv/                       # Python virtual environment
```

---

## How to Run Locally

```bash
cd /Users/shifaasif/smartfolio
venv/bin/streamlit run Home.py
```

App opens at: `http://localhost:8501`

To run headless (background server, no auto-open browser):
```bash
venv/bin/streamlit run Home.py --server.headless true --server.port 8501 > /tmp/smartfolio.log 2>&1 &
```

---

## How to Install / Reinstall Dependencies

```bash
cd /Users/shifaasif/smartfolio
venv/bin/pip install -r requirements.txt
```

---

## Pages & Features

### Home (`Home.py`)
- Summary metric cards: Total Value, Daily P&L, Total Return, Cost Basis
- Portfolio value area chart (selectable period: 1mo → 5y)
- Asset allocation donut chart
- Holdings overview table with colour-coded returns

### Portfolio (`pages/1_Portfolio.py`)
- Add a holding: ticker symbol + shares + average purchase price
- Ticker validation via `validate_ticker()` before saving
- Per-holding display: current price, daily change, total return, allocation %
- Delete individual holdings
- Data saved to `portfolio.json`

### Performance (`pages/2_Performance.py`)
- Portfolio value over time (line/area chart)
- Normalised cumulative return comparison across all holdings (all start at 0%)
- Candlestick OHLC price chart per ticker
- Trading volume bar chart

### Risk Metrics (`pages/3_Risk_Metrics.py`)
- Sharpe Ratio (adjustable risk-free rate slider)
- Beta vs S&P 500 (`^GSPC`)
- Annualised Volatility
- Maximum Drawdown
- Best/Worst/Average daily return stats
- Daily returns distribution histogram
- 30-day rolling volatility chart
- Asset correlation heatmap (multi-holding only)
- Formula explainer expander

---

## Key Modules

### `src/data_fetcher.py`
| Function | Purpose |
|---|---|
| `fetch_multiple_prices(tickers)` | Batch-fetch current price + daily change for a list of tickers |
| `fetch_historical_data(ticker, period)` | Single ticker OHLCV history via `yf.Ticker.history()` |
| `fetch_market_benchmark(period)` | S&P 500 (`^GSPC`) history for beta calculation |
| `validate_ticker(ticker)` | Returns `True` if ticker has recent data on Yahoo Finance |
| `fetch_ticker_info(ticker)` | Returns name, sector, currency, market cap |

### `src/calculations.py`
| Function | Purpose |
|---|---|
| `calculate_portfolio_metrics(holdings, prices_data)` | Core metrics: total value, daily P&L, returns, per-holding breakdown |
| `calculate_historical_portfolio_value(holdings, period)` | DataFrame of daily total portfolio value; forward-fills missing days |
| `calculate_daily_returns(portfolio_history)` | `pct_change()` on total_value column |
| `calculate_sharpe_ratio(returns, risk_free_rate)` | `(mean_excess / std) × √252` |
| `calculate_beta(portfolio_returns, period)` | `Cov(portfolio, market) / Var(market)` |
| `calculate_volatility(returns)` | `std(returns) × √252 × 100` |
| `calculate_max_drawdown(portfolio_history)` | `min((value − peak) / peak) × 100` |
| `calculate_correlation_matrix(holdings, period)` | Pearson correlation of daily returns between all holdings |
| `calculate_individual_returns(holdings, period)` | Normalised cumulative returns per holding (starts at 0%) |

### `src/charts.py`
| Function | Chart Type |
|---|---|
| `portfolio_value_chart(history)` | Line + area chart of total portfolio value |
| `allocation_pie_chart(holdings_metrics)` | Donut chart of allocation % |
| `individual_performance_chart(returns_df)` | Multi-line normalised % return comparison |
| `candlestick_chart(hist, ticker)` | OHLC candlestick for a single ticker |
| `daily_returns_histogram(returns)` | Distribution histogram with mean/zero lines |
| `correlation_heatmap(corr_matrix)` | RdBu colour-coded Plotly heatmap |
| `rolling_volatility_chart(returns, window)` | Rolling annualised volatility line |

---

## Data Persistence

Holdings are stored in `portfolio.json` at the project root:
```json
{
  "holdings": [
    { "ticker": "AAPL", "shares": 10, "purchase_price": 150.00 }
  ]
}
```
This file is read on app start and written on every add/delete action.

---

## Ticker Formats (Yahoo Finance)
- Stocks: `AAPL`, `TSLA`, `MSFT`
- ETFs: `SPY`, `QQQ`, `VTI`
- Crypto: `BTC-USD`, `ETH-USD`
- Indices: `^GSPC` (S&P 500), `^IXIC` (NASDAQ)

---

## Dependencies (`requirements.txt`)
| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥1.32.0 | UI framework |
| `yfinance` | ≥0.2.36 | Yahoo Finance data |
| `pandas` | ≥2.0.0 | Data manipulation |
| `numpy` | ≥1.24.0 | Numerical calculations |
| `plotly` | ≥5.18.0 | Interactive charts |
| `requests` | ≥2.31.0 | HTTP (used by yfinance) |

---

## Common Tasks

### Add a new page
1. Create `pages/4_MyPage.py`
2. Import from `src/` as needed
3. Call `st.set_page_config(...)` at the top
4. Streamlit auto-discovers pages by filename order

### Add a new metric to Risk Metrics
1. Write the calculation function in `src/calculations.py`
2. Import it in `pages/3_Risk_Metrics.py`
3. Add a chart function in `src/charts.py` if a new visualisation is needed

### Add a new chart type
1. Add a function to `src/charts.py` returning a `go.Figure`
2. Call it from the relevant page with `st.plotly_chart(fig, use_container_width=True)`

### Change the colour scheme
- Edit constants at the top of `src/charts.py`: `GREEN`, `RED`, `BLUE`, `BG`, `GRID`

---

## Deployment Options

### Streamlit Community Cloud (free)
1. Push the project to a **public GitHub repo**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo, set entry point to `Home.py`
4. Deploy — gets a public URL like `https://yourapp.streamlit.app`
5. Note: `portfolio.json` won't persist between restarts on free tier (use a DB or secrets for production)

### Local network (share with others on same Wi-Fi)
```bash
venv/bin/streamlit run Home.py --server.address 0.0.0.0 --server.port 8501
```
Others can access via your machine's IP: `http://192.168.x.x:8501`

---

*Data provided by Yahoo Finance via yfinance. Prices may be delayed up to 15 minutes.*
