# Order execution
class RiskManager:
    """
    Basic Risk Management Module
    """

    def __init__(
        self,
        max_position=100,
        stop_loss=0.05,
        take_profit=0.10
    ):
        self.max_position = max_position
        self.stop_loss = stop_loss
        self.take_profit = take_profit

    def check_position_size(self, quantity):
        """
        Check if position size exceeds the limit.
        """

        if quantity > self.max_position:
            return False

        return True

    def check_stop_loss(self, entry_price, current_price):
        """
        Return True if stop loss is triggered.
        """

        loss = (entry_price - current_price) / entry_price

        return loss >= self.stop_loss

    def check_take_profit(self, entry_price, current_price):
        """
        Return True if take profit is triggered.
        """

        profit = (current_price - entry_price) / entry_price

        return profit >= self.take_profit

    def allow_trade(self, quantity):
        """
        Determine whether a trade is allowed.
        """

        return self.check_position_size(quantity)


if __name__ == "__main__":

    risk = RiskManager()

    print("Position Check:", risk.allow_trade(50))
    print("Position Check:", risk.allow_trade(200))

    print(
        "Stop Loss:",
        risk.check_stop_loss(100, 94)
    )

    print(
        "Take Profit:",
        risk.check_take_profit(100, 112)
    )
