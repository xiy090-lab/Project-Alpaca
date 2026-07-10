# Live data store
#
# A small thread-safe store that holds the latest streamed quotes.
# The WebSocket thread writes into it; the Flask UI reads from it.

import threading
from collections import defaultdict, deque


class LiveStore:
    """
    Keeps the most recent quote per symbol, plus a short rolling history
    so the UI can draw a live chart.
    """

    def __init__(self, maxlen=300):
        self._lock = threading.Lock()
        self._latest = {}                                   # symbol -> latest quote
        self._history = defaultdict(lambda: deque(maxlen=maxlen))  # symbol -> recent quotes

    def update_quote(self, symbol, bid, ask, timestamp):
        """Store one incoming quote."""
        row = {
            "bid": float(bid),
            "ask": float(ask),
            "timestamp": str(timestamp),
        }

        with self._lock:
            self._latest[symbol] = row
            self._history[symbol].append(row)

    def get_latest(self, symbol):
        """Return the latest quote for a symbol, or None if nothing yet."""
        with self._lock:
            return self._latest.get(symbol)

    def get_history(self, symbol):
        """Return the recent quote history for a symbol as a list."""
        with self._lock:
            return list(self._history[symbol])
