# Architecture Notes

Quant Trader should be designed as a research platform, not a single script.

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

Future direction: add local caching, source adapters, and data quality checks.

`indicators.py`

- Compute reusable technical indicators.
- Keep indicator math separate from strategy logic.

Future direction: add indicator metadata and avoid recomputing duplicate rolling
windows.

`strategy.py`

- Convert historical data and indicators into target positions.
- Keep strategies explainable and deterministic.
- Avoid portfolio accounting inside strategy code.

Future direction: move each strategy into a class or registry if the strategy
list becomes large.

`risk.py`

- Convert raw strategy intent into position sizes.
- Handle volatility targeting, exposure caps, and future drawdown controls.

This layer is what separates "I like this signal" from "I know how much capital
I want to risk."

`backtester.py`

- Simulate execution timing, transaction costs, returns, equity curves, cash,
  shares, and trade logs.
- Avoid lookahead bias by using shifted executable positions.

Future direction: add slippage, order types, rebalancing schedules, and richer
fill simulation.

`metrics.py`

- Compute performance and risk metrics.
- Keep reporting math independent from plotting and CLI code.

Future direction: add benchmark-relative metrics, tail risk, and regime metrics.

`optimizer.py`

- Run parameter searches.
- Separate training performance from test performance.
- Save ranked results and visual summaries.

Future direction: generalize beyond moving averages into a reusable experiment
runner.

`walk_forward.py`

- Evaluate strategies across rolling train/test windows.
- Help detect overfitting and time-period dependence.

## Design Rules

- Strategies output target positions. They do not execute trades.
- The backtester decides executable positions and accounting.
- Risk management can scale or cap positions before backtesting.
- Metrics should be computed from returns, not from screenshots or manual math.
- Every major experiment should save machine-readable outputs.
- Any future paper-trading adapter should reuse the same signal and risk layers.

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

## Interview Explanation

The important design choice is separation of concerns:

- Strategy logic decides what the system wants to hold.
- Risk logic decides how much exposure is appropriate.
- Execution/backtesting logic decides what could actually have been traded.
- Metrics/reporting logic evaluates the outcome.

That separation makes it easier to test, extend, and explain.
