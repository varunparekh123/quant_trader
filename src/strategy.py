import pandas as pd


def generate_ma_crossover_signals(
    df: pd.DataFrame,
    short_window: int,
    long_window: int,
) -> pd.DataFrame:
    """Generate long/cash signals for an arbitrary moving-average pair."""
    if short_window >= long_window:
        raise ValueError("short_window must be less than long_window")

    out = df.copy()
    short_col = f"ma{short_window}"
    long_col = f"ma{long_window}"
    if short_col not in out.columns:
        out[short_col] = out["close"].rolling(short_window).mean()
    if long_col not in out.columns:
        out[long_col] = out["close"].rolling(long_window).mean()

    out["position"] = (out[short_col] > out[long_col]).astype(float)
    return out


def generate_signals(df: pd.DataFrame, mode: str = "trend_ma200") -> pd.DataFrame:
    out = df.copy()

    if mode == "trend_ma200":
        # Long when price > 200-day MA; cash otherwise
        out["position"] = (out["close"] > out["ma200"]).astype(int)

    elif mode == "ma_cross_20_50":
        # Golden/death cross: long when 20MA > 50MA
        out = generate_ma_crossover_signals(out, 20, 50)

    elif mode == "ma_cross_50_200":
        # Slower golden cross: long when 50MA > 200MA
        out = generate_ma_crossover_signals(out, 50, 200)

    elif mode == "trend_pullback_rsi":
        # Long-term bullish filter + RSI(14) dip entry
        bullish    = out["close"] > out["ma200"]
        buy_signal = bullish & (out["rsi14"] < 35)
        sell_signal = (out["rsi14"] > 65) | (out["close"] < out["ma200"])

        position, in_position = [], 0
        for i in range(len(out)):
            if in_position == 0 and buy_signal.iloc[i]:
                in_position = 1
            elif in_position == 1 and sell_signal.iloc[i]:
                in_position = 0
            position.append(in_position)
        out["position"] = position

    elif mode == "rsi_mean_reversion":
        # Pure mean reversion: buy oversold, sell overbought (no trend filter)
        buy_signal  = out["rsi14"] < 30
        sell_signal = out["rsi14"] > 70

        position, in_position = [], 0
        for i in range(len(out)):
            if in_position == 0 and buy_signal.iloc[i]:
                in_position = 1
            elif in_position == 1 and sell_signal.iloc[i]:
                in_position = 0
            position.append(in_position)
        out["position"] = position

    else:
        raise ValueError(f"Unknown strategy mode: {mode}")

    return out


ALL_STRATEGIES = [
    "trend_ma200",
    "ma_cross_20_50",
    "ma_cross_50_200",
    "trend_pullback_rsi",
    "rsi_mean_reversion",
]
