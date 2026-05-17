import pandas as pd


def run_backtest(df: pd.DataFrame, transaction_cost_bps: float = 0.0) -> pd.DataFrame:
    out = df.copy()

    out["return"] = out["close"].pct_change()

    # shift position by 1 day to avoid lookahead bias
    out["position"] = pd.to_numeric(out["position"], errors="coerce").fillna(0)
    out["position_shifted"] = out["position"].shift(1).fillna(0)

    # Costs should land when the shifted, executable position changes.
    out["turnover"] = out["position_shifted"].diff().abs().fillna(0)

    cost = (transaction_cost_bps / 10000.0) * out["turnover"]
    out["strategy_return"] = (out["position_shifted"] * out["return"]).fillna(0) - cost

    out["equity_curve"] = (1 + out["strategy_return"]).cumprod()
    out["buy_hold_curve"] = (1 + out["return"].fillna(0)).cumprod()

    return out


def build_portfolio_history(
    df: pd.DataFrame,
    starting_capital: float = 100.0,
    transaction_cost_bps: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Add dollar portfolio fields and build a trade log from the executable position.

    The backtester computes returns from position_shifted so a signal generated
    from today's close is not allowed to earn today's return. This function uses
    the same shifted position for shares, cash, and trades.
    """
    required = {"close", "equity_curve", "position_shifted"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required backtest columns: {missing}")

    out = df.copy()
    executed_position = out["position_shifted"].fillna(0).astype(float)

    out["portfolio_value"] = starting_capital * out["equity_curve"]
    out["allocation"] = executed_position
    out["invested_value"] = out["portfolio_value"] * out["allocation"]
    out["cash"] = out["portfolio_value"] - out["invested_value"]
    out["shares"] = out["invested_value"] / out["close"]

    cost_rate = transaction_cost_bps / 10000.0
    trades = []
    prev_position = 0.0
    for date, row in out.iterrows():
        position = float(row["position_shifted"])
        position_delta = position - prev_position
        if abs(position_delta) < 1e-12:
            continue

        portfolio_value = float(row["portfolio_value"])
        trade_value = abs(position_delta) * portfolio_value
        estimated_cost = trade_value * cost_rate
        signal = "BUY" if position_delta > 0 else "SELL"
        trades.append({
            "date": date,
            "signal": signal,
            "price": float(row["close"]),
            "allocation_before": prev_position,
            "allocation_after": position,
            "shares": float(row["shares"]),
            "trade_value": trade_value,
            "portfolio_value": portfolio_value,
            "estimated_cost": estimated_cost,
            "cash_after": float(row["cash"]),
        })
        prev_position = position

    return out, pd.DataFrame(trades)
