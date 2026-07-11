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
    # Trading Engine
    # -------------------------
    # Shares bought per BUY signal (subject to MAX_POSITION).
    TRADE_QTY = 5

    # How often (seconds) the engine re-checks each ticker for a new signal.
    ENGINE_INTERVAL_SECONDS = 60

    # -------------------------
    # Logging
    # -------------------------
    LOG_FOLDER = "logs"

    # -------------------------
    # Backtest
    # -------------------------
    INITIAL_CAPITAL = 100000

    COMMISSION = 0.0
