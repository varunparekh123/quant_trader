"""
Multi-Strategy Comparison
--------------------------
Runs all strategies on one or more tickers across the full date range
and produces a ranked comparison table + equity curve plot.

Usage:
    python compare_strategies.py
    from compare_strategies import run_comparison
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from data_loader import load_price_data
from indicators import add_indicators
from strategy import generate_signals, ALL_STRATEGIES
from backtester import run_backtest
from metrics import compute_metrics


def run_comparison(
    symbols: list = None,
    start: str = "2018-01-01",
    end: str = "2026-01-01",
    transaction_cost_bps: float = 5.0,
    strategies: list = None,
    plot: bool = True,
) -> pd.DataFrame:
    """
    Run every strategy on every symbol. Returns a ranked DataFrame of metrics.
    """
    if symbols is None:
        symbols = ["QQQ", "SPY", "GLD", "TLT"]
    if strategies is None:
        strategies = ALL_STRATEGIES

    rows = []

    for symbol in symbols:
        print(f"\nLoading {symbol}...")
        try:
            df = load_price_data(symbol, start, end)
            df = add_indicators(df)
            df = df.dropna(subset=["ma200"])
        except Exception as e:
            print(f"  Skipping {symbol}: {e}")
            continue

        for strategy in strategies:
            try:
                sdf = generate_signals(df.copy(), mode=strategy)
                sdf = run_backtest(sdf, transaction_cost_bps=transaction_cost_bps)
                m   = compute_metrics(sdf)
                m["symbol"]   = symbol
                m["strategy"] = strategy
                m["label"]    = f"{symbol} | {strategy}"
                rows.append(m)
            except Exception as e:
                print(f"  Error {symbol}/{strategy}: {e}")

    if not rows:
        print("No results generated.")
        return pd.DataFrame()

    result_df = pd.DataFrame(rows)
    result_df = result_df.sort_values("sharpe_ratio", ascending=False).reset_index(drop=True)

    # Pretty print
    display_cols = [
        "symbol", "strategy", "annualized_return", "sharpe_ratio",
        "sortino_ratio", "calmar_ratio", "max_drawdown", "alpha", "win_rate"
    ]
    print("\n" + "=" * 90)
    print("STRATEGY COMPARISON (sorted by Sharpe)")
    print("=" * 90)
    print(result_df[display_cols].to_string(index=False, float_format="{:.4f}".format))

    if plot:
        _plot_comparison(result_df, symbols, start, end, transaction_cost_bps)

    return result_df


def _plot_comparison(result_df, symbols, start, end, transaction_cost_bps):
    """Plot equity curves for all strategy/ticker combos."""
    n_symbols = len(symbols)
    fig = plt.figure(figsize=(16, 5 * n_symbols))
    gs  = gridspec.GridSpec(n_symbols, 1, hspace=0.4)

    colors = plt.cm.tab10.colors

    for i, symbol in enumerate(symbols):
        ax = fig.add_subplot(gs[i])
        symbol_rows = result_df[result_df["symbol"] == symbol]

        if symbol_rows.empty:
            continue

        try:
            df = load_price_data(symbol, start, end)
            df = add_indicators(df)
            df = df.dropna(subset=["ma200"])
        except Exception:
            continue

        # Plot buy-and-hold first
        bh = run_backtest(generate_signals(df.copy(), mode="trend_ma200"), transaction_cost_bps=0)
        ax.plot(bh.index, bh["buy_hold_curve"], color="black",
                linewidth=1.5, linestyle="--", label="Buy & Hold", alpha=0.6)

        for j, strategy in enumerate(ALL_STRATEGIES):
            sdf = generate_signals(df.copy(), mode=strategy)
            sdf = run_backtest(sdf, transaction_cost_bps=transaction_cost_bps)
            ax.plot(sdf.index, sdf["equity_curve"],
                    color=colors[j % len(colors)],
                    linewidth=1.2, label=strategy, alpha=0.85)

        ax.set_title(f"{symbol} — Equity Curves (strategy vs Buy & Hold)", fontsize=12, fontweight="bold")
        ax.set_ylabel("Portfolio Growth (×)")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Date")

    plt.suptitle("Multi-Strategy Comparison", fontsize=14, fontweight="bold", y=1.01)
    plt.savefig("strategy_comparison.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("\nSaved: strategy_comparison.png")


if __name__ == "__main__":
    result_df = run_comparison(
        symbols=["QQQ", "SPY", "GLD", "TLT"],
        start="2018-01-01",
        end="2026-01-01",
        transaction_cost_bps=5.0,
        plot=True,
    )
    result_df.to_csv("strategy_comparison.csv", index=False)
    print("Saved: strategy_comparison.csv")
