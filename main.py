# Entry point
#
# Launches the trading dashboard (Flask UI) and starts the live data stream.
# Run:  python main.py   ->   open http://127.0.0.1:5000

from ui.app import app, start_background_services


def main():
    print("=" * 50)
    print("Alpaca Trading System")
    print("=" * 50)
    print("Starting live data stream + dashboard...")
    print("Open http://127.0.0.1:5001 in your browser")
    print("=" * 50)

    # Start the WebSocket stream in the background
    start_background_services()

    # Serve the UI (blocking). debug=False so the reloader does not
    # open a second WebSocket connection. Port 5001 avoids macOS AirPlay.
    app.run(host="127.0.0.1", port=5001, debug=False)


if __name__ == "__main__":
    main()
