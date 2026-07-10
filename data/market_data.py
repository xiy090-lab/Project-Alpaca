# Market data module
import os
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestQuoteRequest
)
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live import StockDataStream
from alpaca.data.enums import DataFeed


class MarketData:

    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Missing Alpaca API Keys. Please check your .env file."
            )

        self.client = StockHistoricalDataClient(
            self.api_key,
            self.secret_key
        )

        # DataFeed.IEX is the free data feed. The default SIP feed needs a
        # paid subscription and will error on a free paper account.
        self.stream = StockDataStream(
            self.api_key,
            self.secret_key,
            feed=DataFeed.IEX
        )

        # Every incoming tick is kept here so the rest of the system can read
        # the latest prices (simple in-memory store).
        self.ticks = []

    async def on_quote(self, quote):
        """
        Handler called on every incoming quote (bid / ask).
        """

        tick = {
            "type": "quote",
            "symbol": quote.symbol,
            "bid": quote.bid_price,
            "ask": quote.ask_price,
            "timestamp": quote.timestamp,
        }

        self.ticks.append(tick)
        self._log_tick(tick)

        print(
            f"[QUOTE] {tick['symbol']:<5} "
            f"bid {tick['bid']:.2f}  ask {tick['ask']:.2f}"
        )

    async def on_trade(self, trade):
        """
        Handler called on every executed trade (price + size).
        """

        tick = {
            "type": "trade",
            "symbol": trade.symbol,
            "price": trade.price,
            "size": trade.size,
            "timestamp": trade.timestamp,
        }

        self.ticks.append(tick)
        self._log_tick(tick)

        print(
            f"[TRADE] {tick['symbol']:<5} "
            f"price {tick['price']:.2f}  size {tick['size']}"
        )

    def _log_tick(self, tick):
        """
        Append one tick to a CSV log so incoming data is stored on disk.
        """

        os.makedirs("logs", exist_ok=True)

        with open("logs/ticks.csv", "a") as f:
            f.write(
                f"{tick['timestamp']},{tick['type']},"
                f"{tick['symbol']},"
                f"{tick.get('bid', '')},{tick.get('ask', '')},"
                f"{tick.get('price', '')},{tick.get('size', '')}\n"
            )

    def stream_quotes(self, *symbols):
        """
        Connect to Alpaca and stream live quotes for one or more symbols.

        Example: market.stream_quotes("AAPL", "MSFT")
        This blocks and runs until stopped (Ctrl+C).
        """

        self.stream.subscribe_quotes(self.on_quote, *symbols)
        self.stream.run()

    def stream_trades(self, *symbols):
        """
        Connect to Alpaca and stream live trades for one or more symbols.
        """

        self.stream.subscribe_trades(self.on_trade, *symbols)
        self.stream.run()

    def get_historical_data(
        self,
        symbol,
        years=5,
        timeframe=TimeFrame.Day
    ):
        """
        Download historical OHLCV data.
        """

        end = datetime.now()
        start = end - timedelta(days=365 * years)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start,
            end=end
        )

        bars = self.client.get_stock_bars(request)

        df = bars.df

        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol)

        df.reset_index(inplace=True)

        return df

    def get_latest_quote(self, symbol):
        """
        Get latest bid / ask quote.
        """

        request = StockLatestQuoteRequest(
            symbol_or_symbols=symbol
        )

        quote = self.client.get_stock_latest_quote(request)

        return quote[symbol]

    def save_csv(self, df, filename):
        """
        Save DataFrame to CSV.
        """

        df.to_csv(filename, index=False)

        print(f"Saved data to {filename}")


if __name__ == "__main__":

    market = MarketData()

    df = market.get_historical_data("AAPL")

    print(df.head())

    market.save_csv(df, "AAPL_history.csv")

    latest = market.get_latest_quote("AAPL")

    print("\nLatest Quote")

    print(latest)
