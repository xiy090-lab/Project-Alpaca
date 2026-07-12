# Backtesting
import pandas as pd

from config.config import Config
from data.market_data import MarketData
from strategy.moving_average import MovingAverageStrategy


class Backtester:

    def __init__(self, symbol="AAPL", initial_cash=None):

        self.symbol = symbol
        self.initial_cash = initial_cash or Config.INITIAL_CAPITAL

    def run(self):

        market = MarketData()

        df = market.get_historical_data(self.symbol)

        strategy = MovingAverageStrategy(
            Config.SHORT_WINDOW,
            Config.LONG_WINDOW
        )

        df = strategy.generate_signals(df)

        df["position"] = df["signal"].clip(lower=0)

        df["daily_return"] = df["close"].pct_change()

        df["strategy_return"] = (
            df["daily_return"]
            * df["position"].shift(1)
        )

        df["strategy_return"] = (
            df["strategy_return"]
            .fillna(0)
        ).fillna(0)

        turnover = df["position"].diff().abs().fillna(0)
        df["strategy_return"] = (
            df["strategy_return"]- turnover * Config.COMMISSION
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
            df["position"]
            .diff()
            .abs()
            .fillna(0)
            .sum()
        )

        # Max drawdown: largest drop from a running peak of the equity curve.
        running_max = df["portfolio"].cummax()
        drawdown = (df["portfolio"] - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        # Hit rate: share of invested days with a positive strategy return.
        invested = df[df["position"].shift(1).fillna(0) > 0]
        winning_days = (invested["strategy_return"] > 0).sum()
        hit_rate = (
            (winning_days / len(invested)) * 100
            if len(invested) > 0
            else 0.0
        )

        # Annualized Sharpe ratio (risk-free rate assumed 0), on daily
        # strategy returns scaled by sqrt(252) trading days.
        daily = df["strategy_return"]
        std = daily.std()
        sharpe = (
            (daily.mean() / std) * (252 ** 0.5)
            if std > 0
            else 0.0
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
            f"Max Drawdown: {max_drawdown:.2f}%"
        )

        print(
            f"Hit Rate: {hit_rate:.2f}%"
        )

        print(
            f"Sharpe Ratio: {sharpe:.2f}"
        )

        print(
            f"Trades: {int(trades)}"
        )

        print("=" * 40)

        return {
            "final_portfolio": df["portfolio"].iloc[-1],
            "profit": total_return,
            "return_pct": total_percent,
            "max_drawdown_pct": max_drawdown,
            "hit_rate_pct": hit_rate,
            "sharpe": sharpe,
            "trades": int(trades),
        }


if __name__ == "__main__":

    bt = Backtester("AAPL")

    result = bt.run()

    print(result.tail())

    bt.performance(result)
