# Architecture Notes

I want Quant Trader to be a research platform, not a single script. The main
idea is to keep each part of the system separate enough that I can test it,
replace it, and explain it.

## Current Flow

```text
market data
   -> indicators
   -> strategy signals
   -> optional risk sizing
   -> backtester
   -> metrics, trade logs, plots, CSV outputs
```

## Module Responsibilities

`data_loader.py`

- Fetch historical OHLCV data.
- Normalize column names.
- Validate required fields.

Next direction: I want to add local caching, source adapters, and data quality
checks.

`indicators.py`

- Compute reusable technical indicators.
- Keep indicator math separate from strategy logic.

Next direction: I want to add indicator metadata and avoid recomputing duplicate
rolling windows.

`strategy.py`

- Convert historical data and indicators into target positions.
- Keep strategies explainable and deterministic.
- Avoid portfolio accounting inside strategy code.

Next direction: if the strategy list gets large, I want to move strategies into
a cleaner registry or class-based structure.

`risk.py`

- Convert raw strategy intent into position sizes.
- Handle volatility targeting, exposure caps, and future drawdown controls.

This layer is important because it separates "I like this signal" from "I know
how much capital I want to risk."

`backtester.py`

- Simulate execution timing, transaction costs, returns, equity curves, cash,
  shares, and trade logs.
- Avoid lookahead bias by using shifted executable positions.

Next direction: I want to add slippage, order types, rebalancing schedules, and
richer fill simulation.

`metrics.py`

- Compute performance and risk metrics.
- Keep reporting math independent from plotting and CLI code.

Next direction: I want to add benchmark-relative metrics, tail risk, and regime
metrics.

`optimizer.py`

- Run parameter searches.
- Separate training performance from test performance.
- Save ranked results and visual summaries.

Next direction: I want to generalize this beyond moving averages into a reusable
experiment runner.

`walk_forward.py`

- Evaluate strategies across rolling train/test windows.
- Help detect overfitting and time-period dependence.

## Design Rules

- Strategies should output target positions. They should not execute trades.
- I want the backtester to decide executable positions and accounting.
- I want risk management to scale or cap positions before backtesting.
- I want metrics to come from returns, not screenshots or manual math.
- I want every major experiment to save machine-readable outputs.
- I want any future paper-trading adapter to reuse the same signal and risk layers.

## Future Target Architecture

```text
config
  -> data adapter/cache
  -> feature/indicator pipeline
  -> strategy registry
  -> risk model
  -> execution simulator or paper broker
  -> portfolio accounting
  -> metrics engine
  -> report/dashboard
```

## Why I Structured It This Way

The important design choice is separation of concerns:

- Strategy logic decides what the system wants to hold.
- Risk logic decides how much exposure is appropriate.
- Execution/backtesting logic decides what could actually have been traded.
- Metrics/reporting logic evaluates the outcome.

That separation makes the project easier for me to test, extend, and explain as
it grows.
