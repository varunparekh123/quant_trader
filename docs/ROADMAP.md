# Roadmap

This roadmap is organized around credibility. Each phase should make the project
more realistic, explainable, and useful for long-term learning.

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

Success criteria:

- A user can run a reproducible backtest from the terminal.
- Results include benchmark comparison, risk metrics, trades, and saved outputs.
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

Success criteria:

- The project can show when a strategy works, when it fails, and whether it only
  worked because of one overfit parameter choice.
- Reports separate in-sample and out-of-sample performance.

## Phase 3: Better Research Artifacts

Status: planned

- Standard experiment runner that saves config, metrics, plots, and logs
- Markdown or HTML research reports
- Reproducible experiment IDs
- Data cache to avoid repeated downloads
- Cleaner output folder structure
- Benchmark comparison across SPY, QQQ, GLD, TLT, and sector ETFs

Success criteria:

- Each experiment produces an artifact that can be reviewed later without
  rerunning code.
- Results are easy to include in GitHub, LinkedIn, and interviews.

## Phase 4: Risk And Portfolio Construction

Status: planned

- Stop-loss and trailing-stop simulation
- Drawdown-based risk reduction
- Volatility regime detection
- Multi-asset portfolio allocation
- Rebalancing schedules
- Correlation-aware diversification
- Exposure and turnover constraints

Success criteria:

- The platform evaluates not just "which signal is good," but "how much risk
  should the portfolio take?"

## Phase 5: Paper Trading

Status: planned

- Paper broker adapter
- Read-only live market data mode
- Signal generation on scheduled intervals
- Paper order logging
- Paper portfolio reconciliation
- Alerts and daily summaries

Success criteria:

- The system can run safely without real-money execution.
- Every paper trade is traceable to a strategy signal and logged for review.

## Phase 6: Dashboard And Deployment

Status: planned

- Streamlit or lightweight web dashboard
- Strategy comparison pages
- Equity curves, drawdowns, trades, and current paper positions
- Cloud or local scheduled runs
- CI tests
- Documentation site or polished GitHub README

Success criteria:

- The project can be demoed in an interview without digging through terminal
  output.

## Phase 7: Advanced Research

Status: future

- Feature engineering from price, volatility, breadth, rates, or macro data
- Machine learning models for ranking or regime classification
- Alternative data experiments
- Event studies
- Monte Carlo stress tests
- Slippage models
- Broker-like order fill simulation

Success criteria:

- Advanced features are added only after the basic research engine is honest,
  tested, and explainable.
