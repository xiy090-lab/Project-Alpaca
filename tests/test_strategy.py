import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from strategy.moving_average import MovingAverageStrategy


def _prices(values):
    return pd.DataFrame({"close": values})


def test_signal_is_buy_when_short_ma_above_long_ma():
    # A steadily rising series pulls the short MA above the long MA.
    df = _prices(list(range(1, 61)))
    strategy = MovingAverageStrategy(short_window=5, long_window=20)

    result = strategy.generate_signals(df)

    assert strategy.latest_signal(result) == "BUY"
    assert result.iloc[-1]["signal"] == 1


def test_signal_is_sell_when_short_ma_below_long_ma():
    # A steadily falling series pulls the short MA below the long MA.
    df = _prices(list(range(60, 0, -1)))
    strategy = MovingAverageStrategy(short_window=5, long_window=20)

    result = strategy.generate_signals(df)

    assert strategy.latest_signal(result) == "SELL"
    assert result.iloc[-1]["signal"] == -1


def test_signal_is_hold_before_enough_history():
    # With only a handful of rows, both rolling means are still NaN.
    df = _prices([100, 101, 102])
    strategy = MovingAverageStrategy(short_window=5, long_window=20)

    result = strategy.generate_signals(df)

    assert strategy.latest_signal(result) == "HOLD"
