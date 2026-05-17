"""
Walk-Forward Validation
-----------------------
Splits the full date range into rolling train/test windows.
Trains (selects) on the in-sample window, then evaluates on the
out-of-sample test window. Reports per-window and aggregate metrics.

Usage:
    from walk_forward import walk_forward_analysis
    results = walk_forward_analysis(symbol="QQQ", start="2018-01-01", end="2026-01-01")
"""

import pandas as pd
import numpy as np
from typing import List, Dict

from data_loader import load_price_data
from indicators import add_indicators
from strategy import generate_signals, ALL_STRATEGIES
from backtester import run_backtest
from metrics import compute_metrics_from_returns


def run_single_window(
    df: pd.DataFrame,
    strategy: str,
    train_start: str,
    train_end: str,
    test_start: str,
    test_end: str,
    transaction_cost_bps: float = 5.0,
) -> Dict:
    """Run one train/test window for one strategy. Returns OOS metrics."""

    # ----- in-sample (used only to confirm signal logic exists) -----
    train_df = df.loc[train_start:train_end].copy()
    train_df = generate_signals(train_df, mode=strategy)
    train_df = run_backtest(train_df, transaction_cost_bps=transaction_cost_bps)
    train_metrics = compute_metrics_from_returns(train_df["strategy_return"])

    # ----- out-of-sample -----
    test_df = df.loc[test_start:test_end].copy()
    if test_df.empty:
        return {}
    test_df = generate_signals(test_df, mode=strategy)
    test_df = run_backtest(test_df, transaction_cost_bps=transaction_cost_bps)
    oos_metrics = compute_metrics_from_returns(test_df["strategy_return"])

    return {
        "strategy": strategy,
        "train_start": train_start,
        "train_end": train_end,
        "test_start": test_start,
        "test_end": test_end,
        "is_sharpe": round(train_metrics.get("sharpe_ratio", 0), 3),
        "oos_sharpe": round(oos_metrics.get("sharpe_ratio", 0), 3),
        "oos_annualized_return": round(oos_metrics.get("annualized_return", 0), 4),
        "oos_max_drawdown": round(oos_metrics.get("max_drawdown", 0), 4),
        "oos_sortino": round(oos_metrics.get("sortino_ratio", 0), 3),
        "oos_calmar": round(oos_metrics.get("calmar_ratio", 0), 3),
        "oos_n_days": oos_metrics.get("n_days", 0),
    }


def walk_forward_analysis(
    symbol: str = "QQQ",
    start: str = "2015-01-01",
    end: str = "2026-01-01",
    train_years: int = 3,
    test_years: int = 1,
    step_years: int = 1,
    transaction_cost_bps: float = 5.0,
    strategies: List[str] = None,
) -> pd.DataFrame:
    """
    Rolls a train/test window across the full date range.

    Parameters
    ----------
    train_years       : Years of in-sample data per window
    test_years        : Years of out-of-sample data per window
    step_years        : How many years to advance the window each iteration
    transaction_cost_bps : Round-trip cost per trade in basis points
    strategies        : List of strategy modes to test (defaults to ALL_STRATEGIES)
    """
    if strategies is None:
        strategies = ALL_STRATEGIES

    print(f"\nLoading data for {symbol} ({start} → {end})...")
    df = load_price_data(symbol, start, end)
    df = add_indicators(df)
    df = df.dropna(subset=["ma200"])  # need full indicator warmup

    full_start = df.index[0]
    full_end   = df.index[-1]

    # Build window boundaries
    windows = []
    anchor = full_start
    while True:
        train_start = anchor
        train_end   = anchor + pd.DateOffset(years=train_years) - pd.DateOffset(days=1)
        test_start  = anchor + pd.DateOffset(years=train_years)
        test_end    = test_start + pd.DateOffset(years=test_years) - pd.DateOffset(days=1)

        if test_end > full_end:
            break
        windows.append((
            train_start.strftime("%Y-%m-%d"),
            train_end.strftime("%Y-%m-%d"),
            test_start.strftime("%Y-%m-%d"),
            test_end.strftime("%Y-%m-%d"),
        ))
        anchor += pd.DateOffset(years=step_years)

    if not windows:
        raise ValueError("Not enough data for even one walk-forward window. Extend your date range.")

    print(f"Running {len(windows)} windows × {len(strategies)} strategies "
          f"= {len(windows) * len(strategies)} backtests...\n")

    results = []
    for train_start, train_end, test_start, test_end in windows:
        for strategy in strategies:
            row = run_single_window(
                df, strategy,
                train_start, train_end,
                test_start, test_end,
                transaction_cost_bps,
            )
            if row:
                results.append(row)
                print(f"  [{test_start} → {test_end}] {strategy:25s} "
                      f"OOS Sharpe: {row['oos_sharpe']:+.2f}  "
                      f"OOS Return: {row['oos_annualized_return']:+.1%}")

    results_df = pd.DataFrame(results)

    # ---- Summary by strategy ----
    print("\n" + "=" * 70)
    print("WALK-FORWARD SUMMARY (averaged across all OOS windows)")
    print("=" * 70)
    summary = (
        results_df.groupby("strategy")
        .agg(
            windows=("oos_sharpe", "count"),
            avg_oos_sharpe=("oos_sharpe", "mean"),
            avg_oos_return=("oos_annualized_return", "mean"),
            avg_oos_drawdown=("oos_max_drawdown", "mean"),
            avg_oos_sortino=("oos_sortino", "mean"),
            avg_oos_calmar=("oos_calmar", "mean"),
            pct_positive_sharpe=("oos_sharpe", lambda x: (x > 0).mean()),
        )
        .sort_values("avg_oos_sharpe", ascending=False)
        .round(4)
    )
    print(summary.to_string())
    print()

    return results_df, summary


if __name__ == "__main__":
    results_df, summary = walk_forward_analysis(
        symbol="QQQ",
        start="2015-01-01",
        end="2026-01-01",
        train_years=3,
        test_years=1,
        step_years=1,
        transaction_cost_bps=5.0,
    )
    results_df.to_csv("walk_forward_results.csv", index=False)
    summary.to_csv("walk_forward_summary.csv")
    print("Saved: walk_forward_results.csv, walk_forward_summary.csv")
