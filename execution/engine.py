# Trading engine
#
# Runs the systematic strategy on a timer: for each ticker it pulls the
# latest bars, computes a signal, applies risk checks, and (only while the
# UI's Start/Stop switch is "on") routes the signal to the Trader as a paper
# order. This is the piece that closes the loop between "signal" and
# "order" -- without it the strategy only ever describes what *would*
# happen.

import csv
import os
import threading
from collections import deque
from datetime import datetime, timezone

from config.config import Config
from data.market_data import MarketData
from strategy.moving_average import MovingAverageStrategy
from risk.risk_manager import RiskManager
from execution.trader import Trader


class TradingEngine:
    """
    Background loop that turns strategy signals into paper trades.

    `is_running` is a zero-arg callable (backed by the UI's Start/Stop
    state) so the engine keeps polling in the background but only sends
    orders while the strategy is switched on.
    """

    def __init__(self, is_running, interval=None):
        self.is_running = is_running
        self.interval = interval or Config.ENGINE_INTERVAL_SECONDS

        self.market = MarketData()
        self.strategy = MovingAverageStrategy(
            Config.SHORT_WINDOW, Config.LONG_WINDOW
        )
        self.risk = RiskManager(
            max_position=Config.MAX_POSITION,
            stop_loss=Config.STOP_LOSS,
            take_profit=Config.TAKE_PROFIT,
        )
        self.trader = Trader(risk=self.risk)

        self._thread = None
        self._stop_event = threading.Event()

        # Recent activity kept in memory for the UI.
        self.events = deque(maxlen=200)
        self.trades = deque(maxlen=200)

        # symbol -> entry price of the currently open position, so stop
        # loss / take profit can be evaluated on every cycle.
        self._entry_price = {}

        os.makedirs(Config.LOG_FOLDER, exist_ok=True)
        self._events_path = os.path.join(Config.LOG_FOLDER, "events.csv")
        self._trades_path = os.path.join(Config.LOG_FOLDER, "trades.csv")

    def start(self):
        """Start the background polling loop. Safe to call more than once."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the background loop (does not flatten open positions)."""
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            if self.is_running():
                for symbol in Config.TICKERS:
                    try:
                        self._process_symbol(symbol)
                    except Exception as e:
                        self._log_event(symbol, "ERROR", str(e))

            # Wait `interval` seconds, but wake up immediately on stop().
            self._stop_event.wait(self.interval)

    def _process_symbol(self, symbol):
        df = self.market.get_historical_data(symbol, years=1)
        result = self.strategy.generate_signals(df)
        signal = self.strategy.latest_signal(result)
        price = float(result.iloc[-1]["close"])

        self._log_event(symbol, "SIGNAL", signal, price=price)

        qty, _ = self.trader.get_position_qty(symbol)

        # Risk-driven exit takes priority over the strategy signal.
        entry = self._entry_price.get(symbol)
        if qty > 0 and entry:
            if self.risk.check_stop_loss(entry, price):
                self._submit(symbol, "sell", qty, price, reason="stop_loss")
                return
            if self.risk.check_take_profit(entry, price):
                self._submit(symbol, "sell", qty, price, reason="take_profit")
                return

        if signal == "BUY" and qty == 0:
            trade_qty = Config.TRADE_QTY
            if self.risk.allow_trade(trade_qty, current_qty=qty):
                self._submit(symbol, "buy", trade_qty, price, reason="signal")
            else:
                self._log_event(symbol, "RISK_BLOCKED", signal, price=price)

        elif signal == "SELL" and qty > 0:
            self._submit(symbol, "sell", qty, price, reason="signal")

    def _submit(self, symbol, side, qty, price, reason):
        result = (
            self.trader.buy(symbol, qty)
            if side == "buy"
            else self.trader.sell(symbol, qty)
        )

        self._log_event(
            symbol, "ORDER", f"{side.upper()} {qty}", price=price,
            extra=result.get("status"),
        )

        if side == "buy":
            self._entry_price[symbol] = price
        else:
            entry = self._entry_price.pop(symbol, price)
            pnl = (price - entry) * qty

            trade = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "entry": round(entry, 2),
                "exit": round(price, 2),
                "qty": qty,
                "pnl": round(pnl, 2),
                "reason": reason,
            }
            self.trades.append(trade)
            self._log_trade(trade)

    def _log_event(self, symbol, kind, detail, price=None, extra=None):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "type": kind,
            "detail": detail,
            "price": price,
            "extra": extra,
        }
        self.events.append(event)
        self._append_csv(self._events_path, event)

    def _log_trade(self, trade):
        self._append_csv(self._trades_path, trade)

    @staticmethod
    def _append_csv(path, row):
        write_header = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    def metrics(self):
        """
        Basic live performance metrics computed from closed trades:
        cumulative P&L, max drawdown, trade count, and hit rate.
        """
        trades = list(self.trades)
        n = len(trades)
        wins = sum(1 for t in trades if t["pnl"] > 0)
        cumulative_pnl = sum(t["pnl"] for t in trades)

        equity = [0.0]
        for t in trades:
            equity.append(equity[-1] + t["pnl"])

        peak = equity[0]
        max_drawdown = 0.0
        for value in equity:
            peak = max(peak, value)
            max_drawdown = min(max_drawdown, value - peak)

        return {
            "trade_count": n,
            "hit_rate": round(wins / n, 3) if n else None,
            "cumulative_pnl": round(cumulative_pnl, 2),
            "max_drawdown": round(max_drawdown, 2),
        }
