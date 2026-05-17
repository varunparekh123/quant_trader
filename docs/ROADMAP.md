# Roadmap

I am organizing this roadmap around realism and long-term learning. I want each
phase to make the project more useful as a markets lab, not just add features
for the sake of adding features.

## Phase 1: Research Core

Status: in progress

- Data loading from historical market sources
- Technical indicators
- Modular strategy functions
- Transaction-cost-aware backtesting
- One-day execution delay to reduce lookahead bias
- Performance metrics
- Trade logs and equity curve plots
- Unit tests for backtest accounting
- CLI entry points

What I want from this phase:

- I can run a reproducible backtest from the terminal.
- The output includes benchmark comparison, risk metrics, trades, and saved files.
- Core portfolio math is covered by tests.

## Phase 2: Robustness And Validation

Status: started

- Multi-strategy comparison
- Moving-average parameter optimizer
- Train/test validation
- Walk-forward validation
- Volatility-targeted position sizing
- Parameter sensitivity reporting
- Regime-aware performance breakdowns

What I want from this phase:

- I can show when a strategy works, when it fails, and whether it only
  worked because of one overfit parameter choice.
- I can separate in-sample and out-of-sample performance.

## Phase 3: Better Research Artifacts

Status: planned

- Standard experiment runner that saves config, metrics, plots, and logs
- Markdown or HTML research reports
- Reproducible experiment IDs
- Data cache to avoid repeated downloads
- Cleaner output folder structure
- Benchmark comparison across SPY, QQQ, GLD, TLT, and sector ETFs

What I want from this phase:

- Each experiment produces an artifact I can review later without
  rerunning code.
- Results are easy to understand from the repo without needing a long explanation.

## Phase 4: Risk And Portfolio Construction

Status: planned

- Stop-loss and trailing-stop simulation
- Drawdown-based risk reduction
- Volatility regime detection
- Multi-asset portfolio allocation
- Rebalancing schedules
- Correlation-aware diversification
- Exposure and turnover constraints

What I want from this phase:

- I can evaluate not just "which signal is good," but "how much risk
  should the portfolio take?"

## Phase 5: Paper Trading

Status: planned

- Paper broker adapter
- Read-only live market data mode
- Signal generation on scheduled intervals
- Paper order logging
- Paper portfolio reconciliation
- Alerts and daily summaries

What I want from this phase:

- I can run the system safely without real-money execution.
- Every paper trade is traceable to a strategy signal and logged for review.

## Phase 6: Dashboard And Deployment

Status: planned

- Streamlit or lightweight web dashboard
- Strategy comparison pages
- Equity curves, drawdowns, trades, and current paper positions
- Cloud or local scheduled runs
- CI tests
- Documentation site or polished GitHub README

What I want from this phase:

- I can demo the project cleanly without digging through terminal output.

## Phase 7: Advanced Research

Status: future

- Feature engineering from price, volatility, breadth, rates, or macro data
- Machine learning models for ranking or regime classification
- Alternative data experiments
- Event studies
- Monte Carlo stress tests
- Slippage models
- Broker-like order fill simulation

What I want from this phase:

- I add advanced features only after the basic research engine is honest,
  tested, and explainable.
