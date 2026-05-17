import numpy as np
import pandas as pd


RISK_FREE_RATE = 0.04  # 4% annualized — update to current T-bill rate


def compute_metrics(df: pd.DataFrame, risk_free_rate: float = RISK_FREE_RATE) -> dict:
    returns = df["strategy_return"].dropna()

    if returns.empty:
        return {}

    total_return = df["equity_curve"].iloc[-1] - 1
    n_days = len(returns)
    annualized_return = (1 + total_return) ** (252 / n_days) - 1
    annualized_vol = returns.std() * np.sqrt(252)

    # Sharpe with risk-free rate
    excess_return = annualized_return - risk_free_rate
    sharpe = excess_return / annualized_vol if annualized_vol != 0 else 0

    # Sortino: penalizes downside volatility only
    downside_returns = returns[returns < 0]
    downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
    sortino = excess_return / downside_vol if downside_vol != 0 else 0

    # Max drawdown
    running_max = df["equity_curve"].cummax()
    drawdown = df["equity_curve"] / running_max - 1
    max_drawdown = drawdown.min()

    # Calmar: annualized return / max drawdown magnitude
    calmar = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

    # Win rate: % of active trading days that were positive
    active_days = returns[returns != 0]
    win_rate = (active_days > 0).mean() if len(active_days) > 0 else 0

    # Buy-and-hold comparison
    bh_total = df["buy_hold_curve"].iloc[-1] - 1
    bh_annualized = (1 + bh_total) ** (252 / n_days) - 1

    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_vol,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "bh_annualized_return": bh_annualized,
        "alpha": annualized_return - bh_annualized,
        "n_days": n_days,
    }


def compute_metrics_from_returns(returns: pd.Series, risk_free_rate: float = RISK_FREE_RATE) -> dict:
    """Compute metrics directly from a returns series (for walk-forward windows)."""
    if returns.empty:
        return {}

    equity = (1 + returns.fillna(0)).cumprod()
    total_return = equity.iloc[-1] - 1
    n_days = len(returns)
    annualized_return = (1 + total_return) ** (252 / n_days) - 1
    annualized_vol = returns.std() * np.sqrt(252)

    excess_return = annualized_return - risk_free_rate
    sharpe = excess_return / annualized_vol if annualized_vol != 0 else 0

    downside = returns[returns < 0]
    downside_vol = downside.std() * np.sqrt(252) if len(downside) > 0 else 0
    sortino = excess_return / downside_vol if downside_vol != 0 else 0

    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = drawdown.min()
    calmar = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

    return {
        "total_return": round(total_return, 4),
        "annualized_return": round(annualized_return, 4),
        "annualized_volatility": round(annualized_vol, 4),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "calmar_ratio": round(calmar, 4),
        "max_drawdown": round(max_drawdown, 4),
        "n_days": n_days,
    }
