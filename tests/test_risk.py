import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from risk.risk_manager import RiskManager


def test_allow_trade_within_limit():
    risk = RiskManager(max_position=100, stop_loss=0.05, take_profit=0.10)
    assert risk.allow_trade(50) is True


def test_allow_trade_rejects_over_limit():
    risk = RiskManager(max_position=100, stop_loss=0.05, take_profit=0.10)
    assert risk.allow_trade(200) is False


def test_allow_trade_accounts_for_existing_position():
    # Already holding 80 shares; adding 30 more would exceed the 100 cap.
    risk = RiskManager(max_position=100, stop_loss=0.05, take_profit=0.10)
    assert risk.allow_trade(30, current_qty=80) is False
    assert risk.allow_trade(20, current_qty=80) is True


def test_stop_loss_triggers_on_sufficient_loss():
    risk = RiskManager(max_position=100, stop_loss=0.05, take_profit=0.10)
    assert risk.check_stop_loss(entry_price=100, current_price=94) is True
    assert risk.check_stop_loss(entry_price=100, current_price=98) is False


def test_take_profit_triggers_on_sufficient_gain():
    risk = RiskManager(max_position=100, stop_loss=0.05, take_profit=0.10)
    assert risk.check_take_profit(entry_price=100, current_price=112) is True
    assert risk.check_take_profit(entry_price=100, current_price=105) is False
