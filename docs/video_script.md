# Video Walkthrough — Shooting Outline

**Target:** 10–15 min · Solo narrator · Recorded weekend (market closed)

**Setup before you hit record:**
- `python main.py` running, dashboard open at http://127.0.0.1:5001 (dark mode)
- A terminal window ready (for backtest + tests + a live order)
- VS Code open on the repo to show code
- Have `logs/ticks.csv` from Friday's session on hand (proof the live stream works)

**Recording flow tip:** screen-record the whole thing; narrate as you click. The one
thing you *can't* show live on a weekend is streaming quotes — the outline handles that
by pointing at Friday's tick log instead. Everything else is fully live.

---

## 1 · Intro & Goal — ~0:45
*(On screen: dashboard)*

- "This is our Alpaca paper-trading system — a complete, end-to-end pipeline that pulls
  market data, generates trading signals, runs them through risk checks, and routes
  orders to Alpaca's paper account, all controlled from a web dashboard."
- Name the 5-ticker universe (AAPL, MSFT, GOOG, AMZN, NVDA).
- "Everything runs in **paper mode** — no real money. I'll walk through the architecture,
  each module, a live demo, and then reflect on limitations and what we learned."

## 2 · Architecture Overview — ~1:30
*(On screen: README architecture diagram, or VS Code file tree)*

- Walk the data flow top to bottom: **data → strategy → risk + execution → UI**.
- Stress it's **modular** — each concern is its own package: `data/`, `strategy/`,
  `risk/`, `execution/`, `ui/`, `backtest/`, `tests/`.
- "Two entry points: `main.py` runs the live system + dashboard; `backtest.py` runs the
  same strategy over history."
- Mention the two data paths: **REST** (historical bars, used for signals) and
  **WebSocket** (live quotes, used for monitoring + stop-loss/take-profit).

## 3 · Data Pipeline — ~2:00
*(On screen: VS Code — `data/market_data.py`, `live_stream.py`, `live_store.py`; then `logs/ticks.csv`)*

- `market_data.py`: `get_historical_data()` (REST daily bars) + the streaming handlers
  (`on_quote` / `on_trade`).
- Explain **WebSocket vs webhook**: "We connect out to Alpaca over a persistent
  WebSocket and they push quotes to us — we're the client, no public server needed."
- `live_stream.py` runs the stream in a **background thread**; `live_store.py` is a
  thread-safe store the Flask UI reads from.
- **Market-closed workaround:** open `logs/ticks.csv` — "During Friday's market session
  this captured ~3,000 live quotes across all five tickers. On a weekend the feed is
  idle, so the live panel is quiet, but this is the real logged output."
- Note we use the free **IEX** feed.

## 4 · Strategy Logic — ~1:30
*(On screen: `strategy/moving_average.py`, then the dashboard's Strategy chart)*

- Dual moving-average crossover: short MA (20) vs long MA (50).
- **Intuition:** trend-following — when the short-term average is above the long-term
  average, recent momentum is positive and tends to persist; hold long while that's true.
- Long-only state model: BUY state when short > long, SELL when short < long.
- Point at the chart: "Here's AAPL — blue close, green short MA, orange long MA. Current
  signal is BUY because the short MA sits above the long MA."
- Be honest: "Simple crossover strategies whipsaw in choppy markets — we'll come back to
  that in limitations."

## 5 · Execution & Risk — ~2:00
*(On screen: `execution/trader.py`, `execution/engine.py`, `risk/risk_manager.py`)*

- `trader.py`: wraps Alpaca's `TradingClient` and `submit_order` — `buy()` / `sell()`,
  paper mode, returns order status, catches errors.
- `engine.py`: the **background loop** — every 60s it fetches signals, checks risk, and
  routes orders. This is what the dashboard's **Start/Stop** buttons control.
- `risk_manager.py`: three checks — **max position size** (cumulative, vs what's already
  held), **stop-loss** (5%), **take-profit** (10%). "Stop-loss / take-profit take priority
  over the strategy signal — we exit even if the MAs haven't crossed."
- **Live proof (do this on camera):** in the terminal run
  `python -c "from execution.trader import Trader; print(Trader().buy('AAPL', 1))"`.
  "The market's closed, so Alpaca **accepts and queues** the order — you can see status
  `accepted`. It'll fill at Monday's open. This proves the full submit path end to end."
- Refresh the dashboard → the order appears in **Recent Orders**.

## 6 · UI Demo — ~2:00
*(On screen: dashboard, click through it)*

- Header: **Connected**, **Mode: PAPER**, stream badge, **Strategy: Stopped/Running**.
- Click each **company tab** — strategy chart + metrics update per ticker.
- **Paper Account**: equity $100k, buying power, positions.
- **Recent Orders**: the queued order from step 5.
- Click **Start Strategy** → header flips to Running; explain the engine is now polling.
- **Engine Activity / Closed Trades / Engine Performance**: what they show when trades
  happen (cumulative P&L, drawdown, hit rate).
- Note the live-quotes panel: "This ticks in real time during market hours."

## 7 · Backtest & Tests — ~1:15
*(On screen: terminal)*

- Run `python -m backtest.backtest`. Read the summary: **+38.73% return, −27.85% max
  drawdown, 51.75% hit rate, Sharpe 0.45, 35 trades** on AAPL history.
- "The backtester models the same long-only logic the live engine uses, so the numbers
  correspond to real behavior."
- Run `pytest tests/` → **11 passing** — strategy, risk, backtest, and engine logic
  covered without needing the live API.

## 8 · Reflection — ~1:30
*(On screen: README Limitations section)*

**Limitations**
- Signals on **daily** bars → a signal changes at most once a day; live quotes only drive
  stop-loss/TP and fill estimates.
- Single strategy (dual MA), long-only, no shorting, no cross-ticker portfolio risk.
- `MAX_POSITION` is a guardrail, not routinely binding (TRADE_QTY 5 « MAX 100).
- In-memory state + CSV logs (no database) — resets on restart.

**Improvements**
- Intraday/streaming signals; a second strategy (mean-reversion) and signal blending;
  volatility-based position sizing; a real database; partial-fill handling.

**What we learned**
- Real trading systems are mostly **plumbing** — data reliability, threading (streaming
  can't block the web server), risk checks, and error handling matter more than the
  signal itself.
- The gap between a backtest and live execution: queuing, market hours, order states.
- Value of a modular design — we could build and test each layer independently.

## 9 · Close — ~0:15
- "That's our end-to-end Alpaca paper-trading system. Thanks for watching." Show the repo.

---

### One-line shot list (record in this order)
1. Dashboard intro → 2. README diagram → 3. Code: data files + `ticks.csv` →
4. Code: strategy + chart → 5. Code: trader/engine/risk + live queued order →
6. Full dashboard click-through → 7. Terminal: backtest + pytest →
8. README limitations → 9. Repo + outro.
