# Trading strategy
import pandas as pd


class MovingAverageStrategy:
    """
    Dual Moving Average Strategy

    Buy  -> Short MA crosses above Long MA
    Sell -> Short MA crosses below Long MA
    Hold -> Otherwise
    """

    def __init__(self, short_window=20, long_window=50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df):
        """
        Generate trading signals.

        Parameters
        ----------
        df : pandas.DataFrame
            Historical OHLCV data

        Returns
        -------
        pandas.DataFrame
            Original dataframe with indicators and signals
        """

        data = df.copy()

        data["short_ma"] = (
            data["close"]
            .rolling(self.short_window)
            .mean()
        )

        data["long_ma"] = (
            data["close"]
            .rolling(self.long_window)
            .mean()
        )

        data["signal"] = 0

        data.loc[
            data["short_ma"] > data["long_ma"],
            "signal"
        ] = 1

        data.loc[
            data["short_ma"] < data["long_ma"],
            "signal"
        ] = -1

        data["position_change"] = (
            data["signal"].diff()
        )

        return data

    def latest_signal(self, df):
        """
        Return latest trading signal.
        """

        signal = df.iloc[-1]["signal"]

        if signal == 1:
            return "BUY"

        elif signal == -1:
            return "SELL"

        return "HOLD"


if __name__ == "__main__":

    import numpy as np

    prices = np.random.normal(
        100,
        3,
        200
    )

    df = pd.DataFrame({
        "close": prices
    })

    strategy = MovingAverageStrategy()

    result = strategy.generate_signals(df)

    print(result.tail())

    print(
        "\nLatest Signal:",
        strategy.latest_signal(result)
    )
