# Flask UI
import os
import sys

# Allow running as "python ui/app.py" by adding the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, render_template, jsonify

from data.market_data import MarketData
from strategy.moving_average import MovingAverageStrategy
from config.config import Config

# Optional: read-only account / positions view from the paper account
try:
    from alpaca.trading.client import TradingClient

    _trading_client = TradingClient(
        Config.API_KEY,
        Config.API_SECRET,
        paper=Config.PAPER,
    ) if Config.API_KEY and Config.API_SECRET else None
except Exception:
    _trading_client = None


app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
)

market = MarketData()
strategy = MovingAverageStrategy(Config.SHORT_WINDOW, Config.LONG_WINDOW)

# Simple in-memory system state toggled by the Start/Stop buttons
STATE = {"running": False, "mode": "PAPER" if Config.PAPER else "LIVE"}


@app.route("/")
def index():
    return render_template(
        "index.html",
        tickers=Config.TICKERS,
        short_window=Config.SHORT_WINDOW,
        long_window=Config.LONG_WINDOW,
    )


@app.route("/api/data/<symbol>")
def api_data(symbol):
    """Return latest price, signal and chart series for a symbol."""
    df = market.get_historical_data(symbol)
    result = strategy.generate_signals(df)

    latest = result.iloc[-1]

    # Keep the chart light: last ~180 rows
    tail = result.tail(180)

    def clean(x):
        # NaN check without importing numpy/math
        return None if x != x else round(float(x), 2)

    chart = {
        "labels": [str(t)[:10] for t in tail["timestamp"]],
        "close": [round(float(x), 2) for x in tail["close"]],
        "short_ma": [clean(x) for x in tail["short_ma"]],
        "long_ma": [clean(x) for x in tail["long_ma"]],
    }

    recent = (
        result.tail(10)[["timestamp", "close", "short_ma", "long_ma", "signal"]]
        .assign(timestamp=lambda d: d["timestamp"].astype(str).str[:10])
        .round(2)
        .to_dict(orient="records")
    )

    return jsonify(
        {
            "symbol": symbol,
            "price": round(float(latest["close"]), 2),
            "signal": strategy.latest_signal(result),
            "short_ma": clean(latest["short_ma"]),
            "long_ma": clean(latest["long_ma"]),
            "chart": chart,
            "recent": recent,
        }
    )


@app.route("/api/account")
def api_account():
    """Return paper account equity and open positions, if connected."""
    if _trading_client is None:
        return jsonify({"connected": False, "positions": []})

    try:
        account = _trading_client.get_account()
        positions = _trading_client.get_all_positions()

        return jsonify(
            {
                "connected": True,
                "equity": round(float(account.equity), 2),
                "cash": round(float(account.cash), 2),
                "buying_power": round(float(account.buying_power), 2),
                "positions": [
                    {
                        "symbol": p.symbol,
                        "qty": float(p.qty),
                        "avg_price": round(float(p.avg_entry_price), 2),
                        "market_value": round(float(p.market_value), 2),
                        "unrealized_pl": round(float(p.unrealized_pl), 2),
                    }
                    for p in positions
                ],
            }
        )
    except Exception as e:
        return jsonify({"connected": False, "error": str(e), "positions": []})


@app.route("/api/orders")
def api_orders():
    """Return the 5 most recent orders from the paper account."""
    if _trading_client is None:
        return jsonify({"connected": False, "orders": []})

    try:
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus

        req = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=5)
        orders = _trading_client.get_orders(filter=req)

        def val(x):
            return x.value if hasattr(x, "value") else str(x)

        return jsonify(
            {
                "connected": True,
                "orders": [
                    {
                        "symbol": o.symbol,
                        "side": val(o.side),
                        "qty": float(o.qty) if o.qty else None,
                        "type": val(o.order_type),
                        "status": val(o.status),
                        "filled_qty": float(o.filled_qty) if o.filled_qty else 0,
                        "submitted_at": str(o.submitted_at)[:19] if o.submitted_at else "",
                    }
                    for o in orders
                ],
            }
        )
    except Exception as e:
        return jsonify({"connected": False, "error": str(e), "orders": []})


@app.route("/api/status")
def api_status():
    return jsonify(STATE)


@app.route("/api/start", methods=["POST"])
def api_start():
    STATE["running"] = True
    return jsonify(STATE)


@app.route("/api/stop", methods=["POST"])
def api_stop():
    STATE["running"] = False
    return jsonify(STATE)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
