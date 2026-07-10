# Configuration
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Global configuration for the trading system.
    """

    # -------------------------
    # Alpaca API
    # -------------------------
    API_KEY = os.getenv("APCA_API_KEY_ID")
    API_SECRET = os.getenv("APCA_API_SECRET_KEY")

    PAPER = True

    # -------------------------
    # Trading Assets
    # -------------------------
    TICKERS = [
        "AAPL",
        "MSFT",
        "GOOG",
        "AMZN",
        "NVDA"
    ]

    # -------------------------
    # Strategy Parameters
    # -------------------------
    SHORT_WINDOW = 20
    LONG_WINDOW = 50

    # -------------------------
    # Risk Management
    # -------------------------
    MAX_POSITION = 100

    STOP_LOSS = 0.05

    TAKE_PROFIT = 0.10

    # -------------------------
    # Logging
    # -------------------------
    LOG_FOLDER = "logs"

    # -------------------------
    # Backtest
    # -------------------------
    INITIAL_CAPITAL = 100000

    COMMISSION = 0.0
