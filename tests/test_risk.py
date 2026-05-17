import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from risk import apply_volatility_target  # noqa: E402


class RiskTests(unittest.TestCase):
    def test_volatility_target_caps_allocation(self):
        df = pd.DataFrame(
            {
                "close": [100, 101, 99, 102, 98, 103, 97, 104],
                "position": [1] * 8,
            },
            index=pd.date_range("2025-01-01", periods=8, freq="D"),
        )

        result = apply_volatility_target(
            df,
            target_volatility=0.10,
            lookback=3,
            max_allocation=0.75,
        )

        self.assertTrue((result["position"] <= 0.75).all())
        self.assertIn("raw_position", result.columns)
        self.assertIn("realized_volatility", result.columns)
        self.assertIn("volatility_scale", result.columns)


if __name__ == "__main__":
    unittest.main()
