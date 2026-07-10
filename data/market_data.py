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
