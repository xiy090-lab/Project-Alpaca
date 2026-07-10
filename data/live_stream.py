# Live WebSocket stream (background thread)
#
# Connects to Alpaca's real-time feed and pushes every quote into a LiveStore.
# Runs in its own thread so it does not block the Flask server.

import threading

from alpaca.data.live import StockDataStream
from alpaca.data.enums import DataFeed

from config.config import Config


class LiveStream:
    """
    Streams live quotes for a set of symbols into a LiveStore.
    """

    def __init__(self, store):
        self.store = store
        self.stream = None
        self.thread = None

    async def _on_quote(self, quote):
        """Handler fired on every incoming quote."""
        self.store.update_quote(
            quote.symbol,
            quote.bid_price,
            quote.ask_price,
            quote.timestamp,
        )

    def start(self, symbols):
        """
        Subscribe to symbols and start streaming in a background thread.
        Returns True if the stream was started, False if keys are missing.
        """

        # Already running
        if self.thread and self.thread.is_alive():
            return True

        if not (Config.API_KEY and Config.API_SECRET):
            return False

        # DataFeed.IEX is the free feed (SIP needs a paid subscription).
        self.stream = StockDataStream(
            Config.API_KEY,
            Config.API_SECRET,
            feed=DataFeed.IEX,
        )

        self.stream.subscribe_quotes(self._on_quote, *symbols)

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return True

    def _run(self):
        """Run the blocking stream loop (inside the background thread)."""
        try:
            self.stream.run()
        except Exception as e:
            print(f"[LiveStream] stopped: {e}")
