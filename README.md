# Alpaca Trading System

## Project Overview

A systematic, end-to-end trading system built on **Alpaca paper trading**. It streams
market data, generates signals from a dual moving-average strategy, applies risk
checks, routes orders through a background trading engine, and exposes a **Flask**
web dashboard to monitor and control the system.

**Goal:** demonstrate a complete signal → risk → execution loop against Alpaca's
paper API, with a UI that shows what the system is doing (and why) in real time.

## Architecture

```
                     +-------------------+
   Alpaca REST/WS -->|   data/           |--> logs/ticks.csv
                     | market_data.py     |
                     | live_stream.py     |--> LiveStore (in-memory)
                     | live_store.py      |
                     +--------+----------+
                              |
                              v
                     +-------------------+
                     |   strategy/        |
                     | moving_average.py  |  BUY / SELL / HOLD signal
                     +--------+----------+
                              |
                              v
                     +-------------------+        +------------------+
                     |   execution/       |<------>|   risk/           |
                     |   engine.py        |        | risk_manager.py   |
                     | (background loop,  |        | position size,    |
                     |  signal -> order)  |        | stop-loss/TP      |
                     +--------+----------+        +------------------+
                              |
                              v
                     +-------------------+
                     |   execution/       |--> Alpaca paper account
                     |   trader.py        |
                     +--------+----------+
                              |
                              v
                     +-------------------+
                     |   ui/app.py        |  Flask dashboard (Start/Stop,
                     | (Flask + templates)|  positions, signals, orders,
                     +-------------------+  P&L, drawdown, hit rate)
```

- **Data pipeline** (`data/`): historical bars via REST for signal generation, plus a
  live WebSocket quote stream that is stored in memory and logged to
  `logs/ticks.csv`.
- **Strategy** (`strategy/`): dual moving-average crossover signal generation.
- **Risk** (`risk/`): position-size cap (accounting for what's already held) and
  stop-loss / take-profit checks.
- **Execution** (`execution/`): `trader.py` wraps Alpaca's `TradingClient` to submit
  paper orders; `engine.py` is the background loop that actually turns signals into
  orders — it polls each ticker on an interval, checks risk, and calls the trader.
  This is what the UI's Start/Stop switch controls.
- **UI** (`ui/`): Flask dashboard showing live quotes, the strategy chart, account
  equity/positions, recent orders, and the engine's own signal/order/trade log with
  live P&L, drawdown, and hit-rate metrics.
- **Backtest** (`backtest/`): runs the same strategy over historical data and reports
  return, max drawdown, hit rate, and trade count.

## Features

- Live market data pipeline (Alpaca `alpaca-py`, REST + WebSocket) with tick logging
- Dual moving-average crossover strategy
- Autonomous trading engine: polls signals on a timer and routes them to paper orders
- Risk management: max position size (cumulative), stop-loss, take-profit
- Backtest mode on historical data (return, drawdown, hit rate, trade count)
- Flask web dashboard: live quotes, price/MA chart, account & positions, recent
  orders, engine signal/order log, closed trades, cumulative P&L / drawdown / hit
  rate, Start/Stop control
- Structured logs for every quote, signal, order, and closed trade (`logs/`)
- Unit tests for strategy, risk, backtest, and engine logic (no live API needed)

## Project Structure

```
config/     configuration & parameters (tickers, MA windows, risk limits)
data/       Alpaca market-data client + live WebSocket stream/store
strategy/   moving-average signal logic
risk/       position-size and stop-loss/take-profit checks
execution/  trader.py (order routing) + engine.py (signal -> order loop)
backtest/   historical backtester with performance metrics
ui/         Flask dashboard (app.py + templates/)
tests/      pytest unit tests (strategy, risk, backtest, engine)
main.py     starts the live stream, trading engine, and dashboard
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
   `.env` is git-ignored — never commit real keys. Without keys, the dashboard still
   runs, but the live stream, account panel, and trading engine stay disconnected.

## How to Run

**Full system (dashboard + live stream + trading engine):**
```bash
python main.py
```
Then open http://127.0.0.1:5001. Click **Start Strategy** to let the engine start
routing signals to paper orders (it polls every `ENGINE_INTERVAL_SECONDS`, default
60s); **Stop Strategy** halts new orders without closing open positions.

**Backtest:**
```bash
python backtest/backtest.py
```

**Tests:**
```bash
pytest tests/
```

## Strategy

Dual moving-average, **state-based** (not a one-shot crossover event):
- **BUY** state when the short MA is above the long MA
- **SELL** state when the short MA is below the long MA
- **HOLD** before there is enough history for both MAs

The system is **long-only**. The engine enters a long position on the first BUY
state while flat and exits on the first SELL state while holding; it never shorts.
The backtester models the same long-only behavior, so its metrics correspond to
what the paper engine actually does.

Windows and the ticker universe are configured in `config/config.py`. The intuition
is standard trend-following: while the short-term average sits above the long-term
average, recent price action is outpacing the trend, which tends to persist over the
next few bars — the strategy holds the position for the duration of that state and
exits when it flips.

## Risk Controls

- **Max position size** (`MAX_POSITION`): a hard cap on shares held per asset,
  checked against the position already open on Alpaca before any buy. Because the
  engine enters only when flat and buys `TRADE_QTY` shares (with
  `TRADE_QTY` < `MAX_POSITION` by default), this acts as a safety guardrail rather
  than a routinely-binding limit — set `TRADE_QTY` closer to `MAX_POSITION`, or allow
  adding to positions, to exercise it.
- **Trade size** (`TRADE_QTY`): shares bought per BUY signal.
- **Stop-loss / take-profit** (`STOP_LOSS`, `TAKE_PROFIT`): checked every engine cycle
  against the position's entry price and take priority over the strategy signal —
  a stop-loss or take-profit exit fires even if the MA signal hasn't flipped yet.

All trading runs in Alpaca **paper mode** only.

## Logging & Monitoring

- `logs/ticks.csv` — every streamed quote (timestamp, symbol, bid/ask)
- `logs/events.csv` — every signal the engine computes and every order it submits
- `logs/trades.csv` — closed round-trip trades with entry/exit price and realized P&L
- The dashboard's **Engine Activity**, **Closed Trades**, and **Engine Performance**
  panels read this same data live (cumulative P&L, max drawdown, trade count, hit
  rate).

## Example Usage

1. `python main.py`, open the dashboard, select a ticker tab to see its live quote
   and MA chart.
2. Click **Start Strategy** — the engine begins polling; BUY/SELL signals and any
   resulting paper orders appear in **Engine Activity** within one poll interval.
3. Watch **Paper Account** and **Closed Trades** update as positions open and close;
   **Engine Performance** tracks cumulative P&L, drawdown, and hit rate as trades
   close.
4. Click **Stop Strategy** to pause new orders at any time.

## Limitations / Possible Improvements

- Signals are computed on **daily** bars re-fetched every cycle (not incrementally
  from the live stream), so a signal changes at most once per day; the live quote is
  used only for stop-loss/take-profit checks and fill-price estimates.
- Single strategy (dual MA), long-only; no portfolio-level risk aggregation across
  tickers, and `MAX_POSITION` is a guardrail rather than a binding limit by default
  (see Risk Controls).
- Orders are polled briefly for their fill state, but the engine does not manage
  long-lived partially-filled orders beyond that window.
- No persistent database — in-memory state plus CSV logs reset on restart, though the
  engine re-seeds a position's entry price from Alpaca's `avg_entry_price` on the next
  cycle so stop-loss/take-profit still work after a restart. Open Alpaca positions
  themselves persist on Alpaca's side.
