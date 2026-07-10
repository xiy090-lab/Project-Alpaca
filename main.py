from config.config import Config
from data.market_data import MarketData
from strategy.moving_average import MovingAverageStrategy
from risk.risk_manager import RiskManager
from execution.trader import Trader


def main():

    print("=" * 50)
    print("Alpaca Trading System")
    print("=" * 50)

    market = MarketData()

    strategy = MovingAverageStrategy(
        short_window=Config.SHORT_WINDOW,
        long_window=Config.LONG_WINDOW
    )

    risk = RiskManager(
        max_position=Config.MAX_POSITION,
        stop_loss=Config.STOP_LOSS,
        take_profit=Config.TAKE_PROFIT
    )

    trader = Trader()

    for symbol in Config.TICKERS:

        print(f"\nProcessing {symbol}")

        try:

            df = market.get_historical_data(symbol)

            result = strategy.generate_signals(df)

            signal = strategy.latest_signal(result)

            latest_price = result.iloc[-1]["close"]

            print(f"Latest Price: {latest_price:.2f}")

            print(f"Signal: {signal}")

            quantity = 10

            if not risk.allow_trade(quantity):
                print("Trade rejected by Risk Manager")
                continue

            # Uncomment when ready for paper trading

            # if signal == "BUY":
            #     trader.buy(symbol, quantity)

            # elif signal == "SELL":
            #     trader.sell(symbol, quantity)

        except Exception as e:

            print(f"Error processing {symbol}: {e}")

    print("\nSystem Finished")


if __name__ == "__main__":
    main()
