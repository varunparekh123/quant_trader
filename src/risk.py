import numpy as np
import pandas as pd


def apply_volatility_target(
    df: pd.DataFrame,
    target_volatility: float = 0.15,
    lookback: int = 20,
    max_allocation: float = 1.0,
) -> pd.DataFrame:
    """
    Scale strategy exposure using realized volatility.

    A raw signal still decides whether the strategy wants exposure. This layer
    decides how much exposure to take, capped by max_allocation.
    """
    if target_volatility <= 0:
        raise ValueError("target_volatility must be positive")
    if lookback < 2:
        raise ValueError("lookback must be at least 2")
    if max_allocation <= 0:
        raise ValueError("max_allocation must be positive")

    out = df.copy()
    daily_returns = out["close"].pct_change()
    realized_vol = daily_returns.rolling(lookback).std() * np.sqrt(252)
    scale = (target_volatility / realized_vol).clip(lower=0, upper=max_allocation)

    raw_position = pd.to_numeric(out["position"], errors="coerce").fillna(0)
    out["raw_position"] = raw_position
    out["realized_volatility"] = realized_vol
    out["volatility_scale"] = scale.fillna(0)
    out["position"] = (raw_position * out["volatility_scale"]).clip(lower=0, upper=max_allocation)
    return out
