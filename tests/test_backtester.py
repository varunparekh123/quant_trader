import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from backtester import build_portfolio_history, run_backtest  # noqa: E402


class BacktesterTests(unittest.TestCase):
    def test_backtest_shifts_position_and_charges_cost_on_execution_day(self):
        df = pd.DataFrame(
            {
                "close": [100.0, 110.0, 121.0, 108.9],
                "position": [1, 1, 0, 0],
            },
            index=pd.date_range("2025-01-01", periods=4, freq="D"),
        )

        result = run_backtest(df, transaction_cost_bps=10.0)

        self.assertEqual(result["position_shifted"].tolist(), [0, 1, 1, 0])
        self.assertEqual(result["turnover"].tolist(), [0, 1, 0, 1])
        self.assertAlmostEqual(result["strategy_return"].iloc[0], 0.0)
        self.assertAlmostEqual(result["strategy_return"].iloc[1], 0.099)
        self.assertAlmostEqual(result["strategy_return"].iloc[2], 0.10)
        self.assertAlmostEqual(result["strategy_return"].iloc[3], -0.001)

    def test_portfolio_history_uses_executable_position_for_trades(self):
        df = pd.DataFrame(
            {
                "close": [100.0, 110.0, 121.0, 108.9],
                "position": [1, 1, 0, 0],
            },
            index=pd.date_range("2025-01-01", periods=4, freq="D"),
        )

        backtest = run_backtest(df, transaction_cost_bps=10.0)
        portfolio, trades = build_portfolio_history(
            backtest,
            starting_capital=1000.0,
            transaction_cost_bps=10.0,
        )

        self.assertEqual(trades["signal"].tolist(), ["BUY", "SELL"])
        self.assertEqual(trades["date"].tolist(), [df.index[1], df.index[3]])
        self.assertAlmostEqual(portfolio["portfolio_value"].iloc[-1], 1000.0 * backtest["equity_curve"].iloc[-1])
        self.assertAlmostEqual(portfolio["cash"].iloc[-1], portfolio["portfolio_value"].iloc[-1])
        self.assertAlmostEqual(portfolio["shares"].iloc[-1], 0.0)

    def test_fractional_allocation_creates_partial_cash_and_trade_value(self):
        df = pd.DataFrame(
            {
                "close": [100.0, 100.0, 100.0],
                "position": [0.5, 0.5, 0.25],
            },
            index=pd.date_range("2025-01-01", periods=3, freq="D"),
        )

        backtest = run_backtest(df, transaction_cost_bps=0.0)
        portfolio, trades = build_portfolio_history(backtest, starting_capital=1000.0)

        self.assertEqual(backtest["position_shifted"].tolist(), [0.0, 0.5, 0.5])
        self.assertAlmostEqual(portfolio["cash"].iloc[1], 500.0)
        self.assertAlmostEqual(portfolio["invested_value"].iloc[1], 500.0)
        self.assertAlmostEqual(trades["allocation_after"].iloc[0], 0.5)
        self.assertAlmostEqual(trades["trade_value"].iloc[0], 500.0)


if __name__ == "__main__":
    unittest.main()
