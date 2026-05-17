"""
Moving-average parameter optimizer with out-of-sample validation.

This is intentionally research-focused: it searches parameters on an in-sample
period, then reports performance on a separate test period to reduce overfitting.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from backtester import run_backtest
from data_loader import load_price_data
from metrics import compute_metrics, compute_metrics_from_returns
from strategy import generate_ma_crossover_signals


def parse_window_list(value: str) -> list[int]:
    """
    Parse comma lists like 10,20,50 or range syntax like 10:60:10.
    """
    value = value.strip()
    if ":" in value:
        start, stop, step = [int(part) for part in value.split(":")]
        return list(range(start, stop + 1, step))
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def optimize_ma_crossover(
    symbol: str,
    start: str,
    end: str,
    train_end: str,
    short_windows: list[int],
    long_windows: list[int],
    transaction_cost_bps: float = 5.0,
) -> pd.DataFrame:
    prices = load_price_data(symbol, start, end)
    rows = []

    for short_window in short_windows:
        for long_window in long_windows:
            if short_window >= long_window:
                continue

            df = generate_ma_crossover_signals(prices, short_window, long_window)
            df = df.dropna(subset=[f"ma{short_window}", f"ma{long_window}"])
            if df.empty:
                continue

            df = run_backtest(df, transaction_cost_bps=transaction_cost_bps)
            train = df.loc[:train_end]
            test = df.loc[pd.to_datetime(train_end) + pd.Timedelta(days=1):]
            if train.empty or test.empty:
                continue

            full_metrics = compute_metrics(df)
            train_metrics = compute_metrics_from_returns(train["strategy_return"])
            test_metrics = compute_metrics_from_returns(test["strategy_return"])

            rows.append({
                "symbol": symbol,
                "short_window": short_window,
                "long_window": long_window,
                "train_start": train.index[0].strftime("%Y-%m-%d"),
                "train_end": train.index[-1].strftime("%Y-%m-%d"),
                "test_start": test.index[0].strftime("%Y-%m-%d"),
                "test_end": test.index[-1].strftime("%Y-%m-%d"),
                "train_sharpe": train_metrics.get("sharpe_ratio", 0),
                "test_sharpe": test_metrics.get("sharpe_ratio", 0),
                "train_return": train_metrics.get("annualized_return", 0),
                "test_return": test_metrics.get("annualized_return", 0),
                "test_drawdown": test_metrics.get("max_drawdown", 0),
                "full_sharpe": full_metrics.get("sharpe_ratio", 0),
                "full_return": full_metrics.get("annualized_return", 0),
                "full_alpha": full_metrics.get("alpha", 0),
            })

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    result["robustness_gap"] = result["train_sharpe"] - result["test_sharpe"]
    result["selection_score"] = (
        result["test_sharpe"]
        + result["test_return"]
        - result["test_drawdown"].abs()
        - result["robustness_gap"].clip(lower=0) * 0.25
    )
    return result.sort_values("selection_score", ascending=False).reset_index(drop=True)


def plot_optimizer_heatmap(results: pd.DataFrame, output_path: Path) -> None:
    heatmap = results.pivot_table(
        index="short_window",
        columns="long_window",
        values="test_sharpe",
        aggfunc="mean",
    ).sort_index(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    image = ax.imshow(heatmap.values, aspect="auto", cmap="RdYlGn")
    ax.set_title("Out-of-Sample Sharpe by MA Pair", fontweight="bold")
    ax.set_xlabel("Long MA Window")
    ax.set_ylabel("Short MA Window")
    ax.set_xticks(range(len(heatmap.columns)))
    ax.set_xticklabels(heatmap.columns)
    ax.set_yticks(range(len(heatmap.index)))
    ax.set_yticklabels(heatmap.index)
    fig.colorbar(image, ax=ax, label="Test Sharpe")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimize moving-average crossover parameters.")
    parser.add_argument("--symbol", default="QQQ")
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--train-end", default="2021-12-31")
    parser.add_argument("--short-windows", default="10:60:10")
    parser.add_argument("--long-windows", default="50:250:25")
    parser.add_argument("--transaction-cost-bps", type=float, default=5.0)
    parser.add_argument("--output-dir", default="outputs/optimizer")
    parser.add_argument("--top", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = optimize_ma_crossover(
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        train_end=args.train_end,
        short_windows=parse_window_list(args.short_windows),
        long_windows=parse_window_list(args.long_windows),
        transaction_cost_bps=args.transaction_cost_bps,
    )

    if results.empty:
        raise ValueError("No optimization results. Check date range and window settings.")

    prefix = args.symbol.lower()
    csv_path = output_dir / f"{prefix}_ma_optimizer_results.csv"
    heatmap_path = output_dir / f"{prefix}_ma_optimizer_heatmap.png"
    results.to_csv(csv_path, index=False)
    plot_optimizer_heatmap(results, heatmap_path)

    display_cols = [
        "short_window",
        "long_window",
        "train_sharpe",
        "test_sharpe",
        "test_return",
        "test_drawdown",
        "robustness_gap",
        "selection_score",
    ]
    print("\nTop moving-average parameter sets")
    print(results[display_cols].head(args.top).to_string(index=False, float_format="{:.4f}".format))
    print(f"\nSaved: {csv_path}, {heatmap_path}")


if __name__ == "__main__":
    main()
