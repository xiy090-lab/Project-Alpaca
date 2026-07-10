# Backtesting
import pandas as pd

from data.market_data import MarketData
from strategy.moving_average import MovingAverageStrategy


class Backtester:

    def __init__(self, symbol="AAPL", initial_cash=100000):

        self.symbol = symbol
        self.initial_cash = initial_cash

    def run(self):

        market = MarketData()

        df = market.get_historical_data(self.symbol)

        strategy = MovingAverageStrategy()

        df = strategy.generate_signals(df)

        df["daily_return"] = df["close"].pct_change()

        df["strategy_return"] = (
            df["daily_return"]
            * df["signal"].shift(1)
        )

        df["strategy_return"] = (
            df["strategy_return"]
            .fillna(0)
        )

        df["portfolio"] = (
            1 + df["strategy_return"]
        ).cumprod() * self.initial_cash

        return df

    def performance(self, df):

        total_return = (
            df["portfolio"].iloc[-1]
            - self.initial_cash
        )

        total_percent = (
            total_return
            / self.initial_cash
        ) * 100

        trades = (
            df["position_change"]
            .abs()
            .fillna(0)
            .sum()
        )

        print("=" * 40)

        print("Backtest Summary")

        print("=" * 40)

        print(f"Symbol: {self.symbol}")

        print(f"Initial Capital: ${self.initial_cash:,.2f}")

        print(
            f"Final Portfolio: ${df['portfolio'].iloc[-1]:,.2f}"
        )

        print(
            f"Profit: ${total_return:,.2f}"
        )

        print(
            f"Return: {total_percent:.2f}%"
        )

        print(
            f"Trades: {int(trades)}"
        )

        print("=" * 40)


if __name__ == "__main__":

    bt = Backtester("AAPL")

    result = bt.run()

    print(result.tail())

    bt.performance(result)
