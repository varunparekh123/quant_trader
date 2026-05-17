import pandas as pd
import numpy as np


def compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """
    Wilder's RSI — the industry standard.
    Uses EMA-based smoothing (alpha = 1/window), NOT simple rolling mean.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder smoothing: seed with simple mean, then apply EMA
    alpha = 1.0 / window
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ma10"]  = out["close"].rolling(10).mean()
    out["ma20"]  = out["close"].rolling(20).mean()
    out["ma50"]  = out["close"].rolling(50).mean()
    out["ma200"] = out["close"].rolling(200).mean()

    # RSI variants using proper Wilder smoothing
    out["rsi5"]  = compute_rsi(out["close"], 5)
    out["rsi14"] = compute_rsi(out["close"], 14)

    # ATR for volatility-aware position sizing (future use)
    high_low   = out["high"] - out["low"]
    high_close = (out["high"] - out["close"].shift()).abs()
    low_close  = (out["low"]  - out["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    out["atr14"] = true_range.rolling(14).mean()

    return out
