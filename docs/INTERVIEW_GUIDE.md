# Interview And Resume Guide

## One-Sentence Pitch

Built a Python-based systematic trading research platform for testing ETF
strategies with realistic execution assumptions, transaction costs,
risk-adjusted metrics, parameter optimization, walk-forward validation, and
paper-trading-oriented architecture.

## Strong Resume Bullet

- Built a modular Python quant research platform using pandas, NumPy,
  matplotlib, and yfinance to backtest ETF strategies with transaction costs,
  lookahead-bias controls, volatility-targeted sizing, parameter optimization,
  walk-forward validation, trade logs, and risk-adjusted performance analytics.

## Short Interview Explanation

I started with a basic moving-average strategy, but I wanted the project to be
more realistic than a one-off notebook. I separated the system into data loading,
indicators, strategy signals, risk sizing, backtesting, metrics, and reporting.
That lets me test different strategies under the same execution and risk
framework.

The main thing I focused on was honest evaluation. Signals are shifted by one
day so the system does not use today's close to earn today's return. I also add
transaction costs, compare against buy-and-hold, run parameter optimization, and
separate in-sample from out-of-sample performance.

## What Makes It Stronger Than A Basic MA20/MA50 Project

A basic MA20/MA50 project usually answers:

> What happens if I trade this one fixed crossover?

This project answers better questions:

- Which parameter combinations work best out-of-sample?
- Does performance survive transaction costs?
- How does the strategy compare to buy-and-hold?
- How much volatility and drawdown does it take?
- Does it work across multiple market regimes?
- Can the system explain each trade?
- Can exposure be scaled based on market risk?

## Concepts To Be Ready To Explain

Lookahead bias:

- A backtest is biased if it uses information that would not have been available
  at the time of the trade.
- This project shifts positions by one day so signals generated from today's
  close are executed later.

Transaction costs:

- Trading is not free.
- The backtester subtracts costs when the executable position changes.

Sharpe ratio:

- Measures return relative to volatility.
- Useful because high returns are less impressive if they require extreme risk.

Drawdown:

- Measures the decline from a previous portfolio peak.
- Important because investors experience losses path-by-path, not just by final
  return.

Out-of-sample testing:

- Parameters can look good in the training period by luck.
- Testing on a later unseen period gives a better sense of robustness.

Volatility targeting:

- Instead of always going 100% long, exposure can be scaled down when realized
  volatility rises.
- This introduces risk-aware position sizing.

## Honest Limitations To Mention

- Historical backtests do not guarantee future performance.
- yfinance data is useful for research but not institutional-grade.
- The current execution model is still simplified.
- Slippage, liquidity, taxes, and bid-ask spreads need deeper modeling.
- The project is currently research and paper-trading focused, not live trading.

Honest limitations make the project sound more credible, not weaker.

## LinkedIn Project Description

I am building Quant Trader as a long-term personal markets lab: a Python research
platform for testing systematic trading ideas against historical market data.

The project includes modular strategy logic, technical indicators,
transaction-cost-aware backtesting, lookahead-bias controls, risk-adjusted
metrics, volatility-targeted position sizing, parameter optimization, and
walk-forward validation. My goal is not to market it as a "profitable bot," but
to build a realistic and explainable research system for learning markets,
software engineering, risk management, and quantitative decision-making.
