"""
Main entry point — runs a single full backtest with all metrics,
trade log, and equity curve plot. For walk-forward or multi-strategy
comparison, run walk_forward.py or compare_strategies.py directly.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from data_loader import load_price_data
from indicators import add_indicators
from risk import apply_volatility_target
from strategy import generate_signals, ALL_STRATEGIES
from backtester import build_portfolio_history, run_backtest
from metrics import compute_metrics

# ─── CONFIG ────────────────────────────────────────────────────────────────────
SYMBOL              = "QQQ"
START               = "2018-01-01"
END                 = "2026-01-01"
STRATEGY            = "trend_ma200"   # change to any in ALL_STRATEGIES
TRANSACTION_COST_BPS = 5.0            # 5bps per trade (realistic for ETFs)
STARTING_CAPITAL    = 100.0
OUTPUT_DIR          = "outputs"
# ───────────────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single quant-trader backtest.")
    parser.add_argument("--symbol", default=SYMBOL, help="Ticker symbol to backtest.")
    parser.add_argument("--start", default=START, help="Start date, YYYY-MM-DD.")
    parser.add_argument("--end", default=END, help="End date, YYYY-MM-DD.")
    parser.add_argument("--strategy", default=STRATEGY, choices=ALL_STRATEGIES)
    parser.add_argument("--transaction-cost-bps", type=float, default=TRANSACTION_COST_BPS)
    parser.add_argument("--starting-capital", type=float, default=STARTING_CAPITAL)
    parser.add_argument("--vol-target", type=float, default=None, help="Optional annualized volatility target, e.g. 0.15.")
    parser.add_argument("--vol-lookback", type=int, default=20, help="Lookback window for volatility targeting.")
    parser.add_argument("--max-allocation", type=float, default=1.0, help="Maximum portfolio allocation to the strategy.")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Directory for CSV and plot outputs.")
    parser.add_argument("--max-trades-print", type=int, default=25, help="Maximum trade rows to print in the terminal.")
    parser.add_argument("--show-plot", action="store_true", help="Open the matplotlib plot window.")
    return parser.parse_args()


def run_single_backtest(
    symbol: str,
    start: str,
    end: str,
    strategy: str,
    transaction_cost_bps: float,
    starting_capital: float,
    vol_target: float | None = None,
    vol_lookback: int = 20,
    max_allocation: float = 1.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    df = load_price_data(symbol, start, end)
    df = add_indicators(df)
    df = df.dropna(subset=["ma200"])
    if df.empty:
        raise ValueError("Not enough rows after indicator warmup. Use an earlier start date.")

    df = generate_signals(df, mode=strategy)
    if vol_target is not None:
        df = apply_volatility_target(
            df,
            target_volatility=vol_target,
            lookback=vol_lookback,
            max_allocation=max_allocation,
        )
    df = run_backtest(df, transaction_cost_bps=transaction_cost_bps)
    df, trades_df = build_portfolio_history(
        df,
        starting_capital=starting_capital,
        transaction_cost_bps=transaction_cost_bps,
    )

    metrics = compute_metrics(df)
    return df, trades_df, metrics


def print_metrics(metrics: dict) -> None:
    print("\n─── STRATEGY METRICS ────────────────────────────────────")
    metric_labels = {
        "total_return":          "Total Return",
        "annualized_return":     "Annualized Return",
        "bh_annualized_return":  "Buy-Hold Annualized Return",
        "alpha":                 "Alpha (vs Buy-Hold)",
        "annualized_volatility": "Annualized Volatility",
        "sharpe_ratio":          "Sharpe Ratio (rf=4%)",
        "sortino_ratio":         "Sortino Ratio",
        "calmar_ratio":          "Calmar Ratio",
        "max_drawdown":          "Max Drawdown",
        "win_rate":              "Win Rate (active days)",
    }
    for key, label in metric_labels.items():
        val = metrics.get(key, 0)
        if key in ("total_return", "annualized_return", "bh_annualized_return",
                   "alpha", "max_drawdown", "win_rate", "annualized_volatility"):
            print(f"  {label:<35}: {val:+.2%}")
        else:
            print(f"  {label:<35}: {val:+.3f}")


def print_live_signal(df: pd.DataFrame, symbol: str) -> None:
    latest = df.iloc[-1]

    print("\n─── LIVE SIGNAL ─────────────────────────────────────────")
    executed_position = float(latest["position_shifted"])
    target_position = float(latest["position"])
    if target_position > executed_position + 1e-6:
        signal = "BUY / INCREASE"
    elif target_position < executed_position - 1e-6:
        signal = "SELL / REDUCE"
    else:
        signal = "HOLD"

    print(f"  Signal          : {signal}")
    print(f"  Current Alloc.  : {executed_position:.1%}")
    print(f"  Next Target     : {target_position:.1%}")
    print(f"  Portfolio Value : ${latest['portfolio_value']:.2f}")
    print(f"  Cash            : ${latest['cash']:.2f}")
    print(f"  Shares Held     : {latest['shares']:.6f}")
    print(f"  {symbol} Price  : ${latest['close']:.2f}")
    print(f"  MA200           : ${latest['ma200']:.2f}")
    print(f"  Last Data Date  : {latest.name.strftime('%Y-%m-%d')}")


def print_trade_log(trades_df: pd.DataFrame, max_rows: int = 25) -> None:
    print("\n─── TRADE LOG ───────────────────────────────────────────")
    if trades_df.empty:
        print("  No trades generated.")
    else:
        display_df = trades_df.copy()
        display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%Y-%m-%d")
        if max_rows > 0 and len(display_df) > max_rows:
            print(f"  Showing latest {max_rows} of {len(display_df)} trades/rebalances. Full log is saved to CSV.")
            display_df = display_df.tail(max_rows)
        print(display_df.to_string(index=False))


def save_outputs(
    df: pd.DataFrame,
    trades_df: pd.DataFrame,
    symbol: str,
    strategy: str,
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{symbol.lower()}_{strategy}"
    equity_path = output_dir / f"{prefix}_equity.csv"
    trades_path = output_dir / f"{prefix}_trades.csv"
    plot_path = output_dir / f"{prefix}_backtest.png"

    df.to_csv(equity_path)
    trades_df.to_csv(trades_path, index=False)
    return equity_path, trades_path, plot_path


def plot_backtest(
    df: pd.DataFrame,
    symbol: str,
    strategy: str,
    starting_capital: float,
    plot_path: Path,
    show_plot: bool,
) -> None:
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(14, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )

    ax1.plot(df.index, df["portfolio_value"], label=f"Strategy ({strategy})", linewidth=1.5)
    ax1.plot(df.index, df["buy_hold_curve"] * starting_capital,
             label="Buy & Hold", linewidth=1.2, linestyle="--", alpha=0.7, color="gray")
    ax1.set_title(f"{symbol} — {strategy} vs Buy & Hold", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Portfolio Value ($)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Drawdown panel
    running_max = df["equity_curve"].cummax()
    drawdown    = (df["equity_curve"] / running_max - 1) * 100
    ax2.fill_between(df.index, drawdown, 0, alpha=0.4, color="red", label="Drawdown %")
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_xlabel("Date")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    if show_plot:
        plt.show()
    else:
        plt.close(fig)


def main():
    args = parse_args()
    print(f"\nRunning backtest: {args.symbol} | {args.strategy} | {args.start} → {args.end}")

    df, trades_df, metrics = run_single_backtest(
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        strategy=args.strategy,
        transaction_cost_bps=args.transaction_cost_bps,
        starting_capital=args.starting_capital,
        vol_target=args.vol_target,
        vol_lookback=args.vol_lookback,
        max_allocation=args.max_allocation,
    )

    print_metrics(metrics)
    print_live_signal(df, args.symbol)
    print_trade_log(trades_df, max_rows=args.max_trades_print)

    output_dir = Path(args.output_dir)
    equity_path, trades_path, plot_path = save_outputs(
        df,
        trades_df,
        args.symbol,
        args.strategy,
        output_dir,
    )
    plot_backtest(
        df,
        args.symbol,
        args.strategy,
        args.starting_capital,
        plot_path,
        args.show_plot,
    )
    print(f"\nSaved: {equity_path}, {trades_path}, {plot_path}")


if __name__ == "__main__":
    main()
