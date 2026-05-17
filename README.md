Quant Trader
============

I built Quant Trader as my personal markets lab: a Python research platform for
testing ETF strategy ideas against historical market data. I wanted this to be
more serious than a one-off moving-average script, so I added realistic
execution assumptions, transaction costs, risk controls, performance analytics,
and validation workflows.

I am not trying to present this as a "profitable trading bot." I am building it
as a long-term engineering and finance project where I can test ideas, see where
they fail, and keep improving the system as I learn more about markets and
software design.

Project docs
------------

- [Vision](docs/VISION.md): long-term purpose and philosophy.
- [Architecture](docs/ARCHITECTURE.md): how I organized the system.
- [Roadmap](docs/ROADMAP.md): what I want to build next.

What I built
------------

- I download historical OHLCV data with `yfinance`.
- I calculate indicators like moving averages, RSI, and ATR.
- I generate strategy signals from reusable strategy modes.
- I shift positions by one trading day to reduce lookahead bias.
- I apply transaction costs when the executable position changes.
- I added volatility-targeted sizing so strategies are not only all-in/all-out.
- I report total return, annualized return, volatility, Sharpe, Sortino, Calmar,
  max drawdown, win rate, and alpha versus buy-and-hold.
- I save equity curves, trade logs, and backtest plots.
- I support multi-strategy comparison, moving-average parameter optimization, and
  walk-forward validation.

Quick start
-----------

```bash
pip install -r requirements.txt
python src/main.py --symbol QQQ --strategy trend_ma200 --start 2018-01-01 --end 2026-01-01
```

Each run writes outputs to `outputs/`:

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

Strategies
----------

- `trend_ma200`: long when price is above the 200-day moving average.
- `ma_cross_20_50`: long when the 20-day moving average is above the 50-day moving average.
- `ma_cross_50_200`: long when the 50-day moving average is above the 200-day moving average.
- `trend_pullback_rsi`: long-term trend filter with RSI pullback entries.
- `rsi_mean_reversion`: buy oversold RSI and sell overbought RSI.

How this differs from a basic MA20/MA50 project
-----------------------------------------------

I already had experience with a simpler MA20/MA50-style project. For this one,
I wanted to go further and make the project feel more like a research workflow:

- I test multiple strategies instead of one hard-coded crossover.
- I search many moving-average parameter pairs and rank them by out-of-sample
  performance.
- I model transaction costs and avoid same-day lookahead bias.
- I support fractional allocations through volatility targeting.
- I produce reusable CSV artifacts, trade logs, plots, and testable modules.
- I include walk-forward validation and unit tests so the results are easier to
  trust and explain.

Important note
--------------

I built this project for research and education. It does not place live trades,
and it should not be treated as financial advice.
