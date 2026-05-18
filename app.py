import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from data_loader import load_price_data  # noqa: E402
from indicators import add_indicators  # noqa: E402
from metrics import compute_metrics  # noqa: E402
from risk import apply_volatility_target  # noqa: E402
from strategy import ALL_STRATEGIES, generate_signals  # noqa: E402
from backtester import build_portfolio_history, run_backtest  # noqa: E402


STRATEGY_NOTES = {
    "trend_ma200": "I use the 200-day moving average as a long-term trend filter. If price is above it, the strategy wants risk-on exposure. If price is below it, the strategy moves toward cash.",
    "ma_cross_20_50": "I compare a faster 20-day moving average with a slower 50-day moving average. When the faster average is above the slower one, momentum is positive.",
    "ma_cross_50_200": "I compare the 50-day and 200-day moving averages. This reacts more slowly, but it filters out more short-term noise.",
    "trend_pullback_rsi": "I only look for RSI pullbacks when the long-term trend is positive. The idea is to buy weakness inside an uptrend instead of buying every dip blindly.",
    "rsi_mean_reversion": "I treat low RSI as oversold and high RSI as overbought. This is a mean-reversion idea, so it can behave very differently from trend strategies.",
}


METRIC_HELP = {
    "Total Return": "How much the strategy grew from the beginning to the end of the test.",
    "Annualized Return": "The return converted into an approximate yearly rate.",
    "Alpha vs Buy/Hold": "How much annualized return the strategy added or lost compared with simply holding the asset.",
    "Sharpe": "Return relative to volatility. Higher is better, but it should not be read alone.",
    "Max Drawdown": "The worst peak-to-trough portfolio decline. This is one of the most important reality checks.",
    "Win Rate": "The percentage of non-zero strategy return days that were positive.",
}


def format_pct(value: float) -> str:
    return f"{value:+.2%}"


def format_money(value: float) -> str:
    return f"${value:,.2f}"


@st.cache_data(ttl=3600, show_spinner=False)
def load_market_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    return load_price_data(symbol, start, end)


def run_dashboard_backtest(
    symbol: str,
    start: str,
    end: str,
    strategy: str,
    transaction_cost_bps: float,
    starting_capital: float,
    use_vol_target: bool,
    vol_target: float,
    vol_lookback: int,
    max_allocation: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    df = load_market_data(symbol, start, end)
    df = add_indicators(df)
    df = df.dropna(subset=["ma200"])
    if df.empty:
        raise ValueError("Not enough data after indicator warmup. Try an earlier start date.")

    df = generate_signals(df, mode=strategy)
    if use_vol_target:
        df = apply_volatility_target(
            df,
            target_volatility=vol_target,
            lookback=vol_lookback,
            max_allocation=max_allocation,
        )

    df = run_backtest(df, transaction_cost_bps=transaction_cost_bps)
    df, trades = build_portfolio_history(
        df,
        starting_capital=starting_capital,
        transaction_cost_bps=transaction_cost_bps,
    )
    return df, trades, compute_metrics(df)


def explain_decision(row: pd.Series, strategy: str, use_vol_target: bool) -> list[str]:
    notes = []
    price = float(row["close"])
    target = float(row["position"])
    executed = float(row["position_shifted"])

    if strategy == "trend_ma200":
        ma200 = float(row["ma200"])
        if price > ma200:
            notes.append(f"Price is above MA200 ({format_money(price)} > {format_money(ma200)}), so the raw trend signal is risk-on.")
        else:
            notes.append(f"Price is below MA200 ({format_money(price)} < {format_money(ma200)}), so the raw trend signal is defensive.")

    elif strategy == "ma_cross_20_50":
        if row["ma20"] > row["ma50"]:
            notes.append("MA20 is above MA50, so short-term momentum is stronger than the slower trend.")
        else:
            notes.append("MA20 is below MA50, so the strategy treats momentum as weak.")

    elif strategy == "ma_cross_50_200":
        if row["ma50"] > row["ma200"]:
            notes.append("MA50 is above MA200, so the slower trend filter is risk-on.")
        else:
            notes.append("MA50 is below MA200, so the slower trend filter is defensive.")

    elif strategy == "trend_pullback_rsi":
        notes.append(f"RSI14 is {row['rsi14']:.1f}. This strategy looks for oversold pullbacks while price is still above MA200.")

    elif strategy == "rsi_mean_reversion":
        notes.append(f"RSI14 is {row['rsi14']:.1f}. Low RSI can trigger a mean-reversion entry; high RSI can trigger an exit.")

    if use_vol_target and "volatility_scale" in row:
        notes.append(f"Volatility targeting scales the raw signal to {target:.1%} target allocation based on recent realized volatility.")

    if target > executed + 1e-6:
        notes.append(f"The next target allocation is higher than the current executable allocation ({target:.1%} vs {executed:.1%}), so the bot would increase exposure.")
    elif target < executed - 1e-6:
        notes.append(f"The next target allocation is lower than the current executable allocation ({target:.1%} vs {executed:.1%}), so the bot would reduce exposure.")
    else:
        notes.append(f"The target allocation matches the current executable allocation ({target:.1%}), so the bot holds.")

    return notes


def make_equity_chart(df: pd.DataFrame, symbol: str, starting_capital: float, selected_date) -> plt.Figure:
    chart_df = df.loc[:selected_date]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(chart_df.index, chart_df["portfolio_value"], label="Strategy", linewidth=2.0, color="#2563eb")
    ax.plot(
        chart_df.index,
        chart_df["buy_hold_curve"] * starting_capital,
        label=f"Buy & Hold {symbol}",
        linewidth=1.5,
        linestyle="--",
        color="#6b7280",
    )
    ax.set_title("Portfolio Growth")
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    return fig


def make_price_chart(df: pd.DataFrame, trades: pd.DataFrame, selected_date) -> plt.Figure:
    chart_df = df.loc[:selected_date]
    visible_trades = trades[trades["date"] <= selected_date] if not trades.empty else trades

    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(chart_df.index, chart_df["close"], label="Close", linewidth=1.6, color="#111827")
    ax.plot(chart_df.index, chart_df["ma50"], label="MA50", linewidth=1.1, color="#0f766e", alpha=0.8)
    ax.plot(chart_df.index, chart_df["ma200"], label="MA200", linewidth=1.1, color="#b45309", alpha=0.8)

    if not visible_trades.empty:
        buys = visible_trades[visible_trades["signal"] == "BUY"]
        sells = visible_trades[visible_trades["signal"] == "SELL"]
        ax.scatter(buys["date"], buys["price"], marker="^", s=60, color="#16a34a", label="Buy / Increase", zorder=3)
        ax.scatter(sells["date"], sells["price"], marker="v", s=60, color="#dc2626", label="Sell / Reduce", zorder=3)

    ax.set_title("Price, Moving Averages, and Trades")
    ax.set_ylabel("Price")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left")
    return fig


def make_drawdown_chart(df: pd.DataFrame, selected_date) -> plt.Figure:
    chart_df = df.loc[:selected_date]
    running_max = chart_df["equity_curve"].cummax()
    drawdown = chart_df["equity_curve"] / running_max - 1

    fig, ax = plt.subplots(figsize=(11, 3.2))
    ax.fill_between(chart_df.index, drawdown * 100, 0, color="#dc2626", alpha=0.35)
    ax.set_title("Drawdown")
    ax.set_ylabel("Drawdown %")
    ax.grid(True, alpha=0.25)
    return fig


def render_metric_card(label: str, value: str, help_text: str) -> None:
    st.metric(label, value)
    st.caption(help_text)


def main() -> None:
    st.set_page_config(page_title="Quant Trader Lab", page_icon="📈", layout="wide")
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; max-width: 1420px; }
        div[data-testid="stMetric"] { background: #f8fafc; border: 1px solid #e5e7eb; padding: 0.8rem; border-radius: 8px; }
        div[data-testid="stMetric"] * { color: #111827 !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.85rem; }
        div[data-testid="stMetricValue"] { font-size: 1.35rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Quant Trader Lab")
    st.caption("An interactive research dashboard for watching my strategy logic, risk controls, trades, and performance move through time.")

    with st.sidebar:
        st.header("Experiment Setup")
        symbol = st.text_input("Ticker", value="QQQ").upper().strip()
        start = st.date_input("Start date", value=pd.to_datetime("2018-01-01"))
        end = st.date_input("End date", value=pd.to_datetime("2026-01-01"))
        strategy = st.selectbox("Strategy", ALL_STRATEGIES)
        starting_capital = st.number_input("Starting capital", min_value=100.0, value=10_000.0, step=500.0)
        transaction_cost_bps = st.slider("Transaction cost per rebalance (bps)", 0.0, 50.0, 5.0, 1.0)

        st.divider()
        use_vol_target = st.toggle("Use volatility targeting", value=False)
        vol_target = st.slider("Target annualized volatility", 0.05, 0.40, 0.15, 0.01)
        vol_lookback = st.slider("Volatility lookback days", 5, 80, 20, 5)
        max_allocation = st.slider("Maximum allocation", 0.10, 1.00, 1.00, 0.05)

        st.divider()
        st.caption("I use this panel to change the research question, then the dashboard recomputes the backtest.")

    try:
        df, trades, metrics = run_dashboard_backtest(
            symbol=symbol,
            start=str(start),
            end=str(end),
            strategy=strategy,
            transaction_cost_bps=transaction_cost_bps,
            starting_capital=starting_capital,
            use_vol_target=use_vol_target,
            vol_target=vol_target,
            vol_lookback=vol_lookback,
            max_allocation=max_allocation,
        )
    except Exception as exc:
        st.error(f"I could not run this experiment: {exc}")
        st.stop()

    selected_idx = st.slider(
        "Replay strategy timeline",
        min_value=0,
        max_value=len(df) - 1,
        value=len(df) - 1,
        help="Move this to watch how the bot's state changes through the backtest.",
    )
    selected_date = df.index[selected_idx]
    current = df.iloc[selected_idx]
    visible_df = df.iloc[: selected_idx + 1]
    visible_metrics = compute_metrics(visible_df) if len(visible_df) > 2 else metrics

    left, right = st.columns([1.25, 0.75], gap="large")

    with left:
        st.subheader(f"{symbol} / {strategy}")
        st.write(STRATEGY_NOTES[strategy])

        metric_cols = st.columns(3)
        with metric_cols[0]:
            render_metric_card("Total Return", format_pct(visible_metrics.get("total_return", 0)), METRIC_HELP["Total Return"])
        with metric_cols[1]:
            render_metric_card("Annualized", format_pct(visible_metrics.get("annualized_return", 0)), METRIC_HELP["Annualized Return"])
        with metric_cols[2]:
            render_metric_card("Alpha", format_pct(visible_metrics.get("alpha", 0)), METRIC_HELP["Alpha vs Buy/Hold"])

        metric_cols = st.columns(3)
        with metric_cols[0]:
            render_metric_card("Sharpe", f"{visible_metrics.get('sharpe_ratio', 0):+.2f}", METRIC_HELP["Sharpe"])
        with metric_cols[1]:
            render_metric_card("Max Drawdown", format_pct(visible_metrics.get("max_drawdown", 0)), METRIC_HELP["Max Drawdown"])
        with metric_cols[2]:
            render_metric_card("Win Rate", format_pct(visible_metrics.get("win_rate", 0)), METRIC_HELP["Win Rate"])

        tab_equity, tab_price, tab_drawdown = st.tabs(["Portfolio", "Price + Trades", "Drawdown"])
        with tab_equity:
            st.pyplot(make_equity_chart(df, symbol, starting_capital, selected_date), clear_figure=True)
        with tab_price:
            st.pyplot(make_price_chart(df, trades, selected_date), clear_figure=True)
        with tab_drawdown:
            st.pyplot(make_drawdown_chart(df, selected_date), clear_figure=True)

    with right:
        st.subheader("Bot State")
        st.caption(f"Replay date: {selected_date.strftime('%Y-%m-%d')}")
        state_cols = st.columns(2)
        state_cols[0].metric("Current allocation", f"{float(current['position_shifted']):.1%}")
        state_cols[1].metric("Next target", f"{float(current['position']):.1%}")
        state_cols[0].metric("Portfolio value", format_money(float(current["portfolio_value"])))
        state_cols[1].metric("Cash", format_money(float(current["cash"])))
        state_cols[0].metric("Shares", f"{float(current['shares']):,.4f}")
        state_cols[1].metric("Close", format_money(float(current["close"])))

        st.markdown("#### Why the bot is doing this")
        for note in explain_decision(current, strategy, use_vol_target):
            st.write(f"- {note}")

        st.markdown("#### Latest trades")
        if trades.empty:
            st.info("No trades have been generated in this run yet.")
        else:
            visible_trades = trades[trades["date"] <= selected_date].tail(8).copy()
            if visible_trades.empty:
                st.info("No trades have occurred by this replay date.")
            else:
                visible_trades["date"] = pd.to_datetime(visible_trades["date"]).dt.strftime("%Y-%m-%d")
                st.dataframe(
                    visible_trades[
                        ["date", "signal", "price", "allocation_before", "allocation_after", "trade_value", "estimated_cost"]
                    ],
                    hide_index=True,
                    width="stretch",
                )

    st.divider()
    st.subheader("Learning Notes")
    learn_cols = st.columns(3)
    with learn_cols[0]:
        st.markdown("**Signal vs execution**")
        st.write("The strategy creates a target position from historical data. The backtester shifts that position by one day so it does not pretend to trade before the signal was knowable.")
    with learn_cols[1]:
        st.markdown("**Risk-adjusted performance**")
        st.write("A high return is not enough. I look at drawdown, volatility, Sharpe, Sortino, and alpha to understand how much risk the strategy took.")
    with learn_cols[2]:
        st.markdown("**Parameter sensitivity**")
        st.write("If a strategy only works for one exact parameter pair, I should be skeptical. That is why this project includes optimization and walk-forward validation.")


if __name__ == "__main__":
    main()
