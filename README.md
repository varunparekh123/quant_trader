Quant Trader
============

Quant Trader is my personal systematic trading research lab: a Python platform
for testing ETF strategy ideas against historical market data with realistic
execution assumptions, transaction costs, risk controls, performance analytics,
and validation workflows.

The goal is not to market this as a "profitable trading bot." The goal is to
build a serious, explainable, and extensible research platform for learning
markets, software engineering, risk management, and quantitative
decision-making.

Project docs
------------

- [Vision](docs/VISION.md): long-term purpose and philosophy.
- [Architecture](docs/ARCHITECTURE.md): how the system is organized.
- [Roadmap](docs/ROADMAP.md): phased plan for making the platform stronger.
- [Interview Guide](docs/INTERVIEW_GUIDE.md): resume and interview positioning.

What it does
------------

- Downloads historical OHLCV data with `yfinance`.
- Builds technical indicators such as moving averages, RSI, and ATR.
- Generates long/cash strategy signals from reusable strategy modes.
- Shifts positions by one trading day to avoid lookahead bias.
- Applies transaction costs when the executable position changes.
- Supports volatility-targeted position sizing instead of only all-in/all-out trades.
- Reports total return, annualized return, volatility, Sharpe, Sortino, Calmar,
  max drawdown, win rate, and alpha versus buy-and-hold.
- Saves equity curves, trade logs, and backtest plots.
- Supports multi-strategy comparison, moving-average parameter optimization, and
  walk-forward validation.

Quick start
-----------

```bash
pip install -r requirements.txt
python src/main.py --symbol QQQ --strategy trend_ma200 --start 2018-01-01 --end 2026-01-01
```

Outputs are written to `outputs/`:

- `{symbol}_{strategy}_equity.csv`
- `{symbol}_{strategy}_trades.csv`
- `{symbol}_{strategy}_backtest.png`

Useful commands
---------------

```bash
# Try a different strategy
python src/main.py --symbol SPY --strategy ma_cross_20_50

# Increase transaction costs and starting capital
python src/main.py --symbol QQQ --transaction-cost-bps 10 --starting-capital 10000

# Add volatility targeting: scale exposure toward 15% annualized volatility
python src/main.py --symbol QQQ --strategy trend_ma200 --vol-target 0.15

# Compare every built-in strategy across multiple ETFs
python src/compare_strategies.py

# Optimize moving-average crossover windows with train/test validation
python src/optimizer.py --symbol QQQ --short-windows 10:60:10 --long-windows 50:250:25

# Run walk-forward validation
python src/walk_forward.py

# Run unit tests
python -m unittest discover -s tests
```

Built-in strategies
-------------------

- `trend_ma200`: long when price is above the 200-day moving average.
- `ma_cross_20_50`: long when the 20-day moving average is above the 50-day moving average.
- `ma_cross_50_200`: long when the 50-day moving average is above the 200-day moving average.
- `trend_pullback_rsi`: long-term trend filter with RSI pullback entries.
- `rsi_mean_reversion`: buy oversold RSI and sell overbought RSI.

Resume talking points
---------------------

- Built a modular Python backtesting engine for ETF trading strategies using
  pandas, NumPy, matplotlib, and yfinance.
- Implemented technical indicators, signal generation, transaction-cost-aware
  backtesting, trade logs, equity curve visualization, and risk-adjusted metrics.
- Reduced lookahead bias by separating strategy signals from executable
  positions through one-day position shifting.
- Built a parameter optimizer for moving-average strategies using train/test
  validation to compare in-sample performance against out-of-sample robustness.
- Added volatility-targeted position sizing so the strategy can scale exposure
  based on realized market risk instead of using only binary buy/sell exposure.
- Added walk-forward validation to evaluate strategy robustness across rolling
  out-of-sample windows.
- Added unit tests for core portfolio accounting and transaction cost behavior.

How this differs from a basic MA20/MA50 project
-----------------------------------------------

A simple MA20/MA50 project usually demonstrates one fixed crossover strategy.
This project is designed as a research workflow:

- It tests multiple strategies, not one hard-coded crossover.
- It searches many moving-average parameter pairs and ranks them by out-of-sample
  performance.
- It models transaction costs and avoids same-day lookahead bias.
- It supports fractional allocations through volatility targeting.
- It produces reusable CSV artifacts, trade logs, plots, and testable modules.
- It includes walk-forward validation and unit tests, which makes the work easier
  to defend in interviews.

Important note
--------------

This project is for research and education. It does not place live trades and
should not be treated as financial advice.
