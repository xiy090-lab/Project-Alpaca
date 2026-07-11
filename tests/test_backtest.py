import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd

from backtest.backtest import Backtester


def _synthetic_df(n=120, seed=1):
    rng = np.random.default_rng(seed)
    prices = 100 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="D"),
            "close": prices,
        }
    )


def test_backtest_run_and_performance():
    df = _synthetic_df()
    fake_market = MagicMock()
    fake_market.get_historical_data.return_value = df

    with patch("backtest.backtest.MarketData", return_value=fake_market):
        bt = Backtester("TEST", initial_cash=10000)
        result = bt.run()
        stats = bt.performance(result)

    assert "portfolio" in result.columns
    assert stats["final_portfolio"] > 0
    assert stats["trades"] >= 0
    # Drawdown is a percentage <= 0 by definition.
    assert stats["max_drawdown_pct"] <= 0
