import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from execution.engine import TradingEngine


def _build_engine():
    # MarketData/Trader both require live Alpaca keys to construct; patch
    # them out since these tests only exercise the metrics math.
    with patch("execution.engine.MarketData"), patch("execution.engine.Trader"):
        return TradingEngine(is_running=lambda: False)


def test_metrics_with_no_trades():
    engine = _build_engine()

    metrics = engine.metrics()

    assert metrics == {
        "trade_count": 0,
        "hit_rate": None,
        "cumulative_pnl": 0,
        "max_drawdown": 0.0,
    }


def test_metrics_computes_pnl_hit_rate_and_drawdown():
    engine = _build_engine()
    engine.trades.extend(
        [
            {"pnl": 10.0},
            {"pnl": -5.0},
            {"pnl": 20.0},
        ]
    )

    metrics = engine.metrics()

    assert metrics["trade_count"] == 3
    assert metrics["hit_rate"] == round(2 / 3, 3)
    assert metrics["cumulative_pnl"] == 25.0
    # Equity path is 0 -> 10 -> 5 -> 25; the only drawdown is 10 -> 5.
    assert metrics["max_drawdown"] == -5.0
