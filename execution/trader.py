# Order execution
#
# Wraps Alpaca's TradingClient to submit paper-trading orders.
# Uses the RiskManager to check trades before they are sent.

import os

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from config.config import Config
from risk.risk_manager import RiskManager


class Trader:
    """
    Submits market orders to Alpaca paper trading and reports order status.
    """

    def __init__(self, risk=None):
        load_dotenv()

        api_key = Config.API_KEY
        api_secret = Config.API_SECRET

        if not api_key or not api_secret:
            raise ValueError(
                "Missing Alpaca API Keys. Please check your .env file."
            )

        # paper=True keeps us on the paper-trading account (no real money)
        self.client = TradingClient(api_key, api_secret, paper=Config.PAPER)

        # Risk checks run before every order
        self.risk = risk or RiskManager(
            max_position=Config.MAX_POSITION,
            stop_loss=Config.STOP_LOSS,
            take_profit=Config.TAKE_PROFIT,
        )

    def buy(self, symbol, quantity):
        """Submit a market BUY order."""
        return self._submit(symbol, quantity, OrderSide.BUY)

    def sell(self, symbol, quantity):
        """Submit a market SELL order."""
        return self._submit(symbol, quantity, OrderSide.SELL)

    def _submit(self, symbol, quantity, side):
        """
        Run risk checks, submit the order, and return a simple result dict.
        """

        # 1. Risk check
        if not self.risk.allow_trade(quantity):
            print(f"[RISK] Rejected {side.value} {quantity} {symbol} "
                  f"(exceeds max position {self.risk.max_position})")
            return {"status": "rejected", "reason": "risk", "symbol": symbol}

        # 2. Build the order
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=side,
            time_in_force=TimeInForce.DAY,
        )

        # 3. Submit, with error handling for rejects / network issues
        try:
            order = self.client.submit_order(order_data)

            print(f"[ORDER] {side.value.upper()} {quantity} {symbol} "
                  f"-> {order.status} (id {order.id})")

            return {
                "status": str(order.status),
                "symbol": symbol,
                "side": side.value,
                "qty": quantity,
                "order_id": str(order.id),
            }

        except Exception as e:
            print(f"[ERROR] Order failed for {symbol}: {e}")
            return {"status": "error", "reason": str(e), "symbol": symbol}

    def get_positions(self):
        """Return current open positions."""
        return self.client.get_all_positions()

    def get_position_qty(self, symbol):
        """
        Return (qty, avg_entry_price) for an open position, or (0.0, 0.0)
        if there is no open position for `symbol`.
        """
        try:
            position = self.client.get_open_position(symbol)
            return float(position.qty), float(position.avg_entry_price)
        except Exception:
            return 0.0, 0.0

    def get_account(self):
        """Return account info (equity, buying power, etc.)."""
        return self.client.get_account()


if __name__ == "__main__":

    trader = Trader()

    account = trader.get_account()
    print("Account equity:", account.equity)
    print("Buying power:", account.buying_power)

    # Example (uncomment to place a real paper order):
    # result = trader.buy("AAPL", 1)
    # print(result)
