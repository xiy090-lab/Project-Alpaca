# Alpaca Trading System

## Project Overview

A systematic, end-to-end trading system built on **Alpaca paper trading**. It fetches
market data, generates signals from a dual moving-average strategy, applies risk
checks, and exposes a **Flask** web dashboard to monitor and control the system.

## Features

- Market data pipeline (Alpaca `alpaca-py`)
- Dual moving-average crossover strategy
- Basic risk management (position size, stop-loss, take-profit)
- Backtest mode on historical data
- Flask web dashboard (price/MA chart, signals, positions, P&L, start/stop)

## Project Structure

```
config/     configuration & parameters (tickers, MA windows, risk limits)
data/       Alpaca market-data client
strategy/   moving-average signal logic
risk/       risk checks
execution/  order routing (paper)
backtest/   historical backtester
ui/         Flask dashboard (app.py + templates/)
main.py     runs the strategy loop over the ticker universe
```

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add your Alpaca paper-trading keys.** Copy the example and fill in real keys:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   APCA_API_KEY_ID=your_paper_key
   APCA_API_SECRET_KEY=your_paper_secret
   ```
   Get keys from the Alpaca dashboard → Paper Trading → API Keys.
   `.env` is git-ignored — never commit real keys.

## How to Run

**Web dashboard (Flask):**
```bash
python ui/app.py
```
Then open http://127.0.0.1:5000

**Strategy loop (console):**
```bash
python main.py
```

**Backtest:**
```bash
python backtest/backtest.py
```

## Strategy

Dual moving-average crossover:
- **BUY** when the short MA is above the long MA
- **SELL** when the short MA is below the long MA
- **HOLD** otherwise

Windows and the ticker universe are configured in `config/config.py`.

## Risk Controls

- Max position size per trade
- Stop-loss and take-profit thresholds

All trading runs in Alpaca **paper mode** only.
