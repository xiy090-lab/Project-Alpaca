# Streamlit UI
import streamlit as st
import pandas as pd

from data.market_data import MarketData
from strategy.moving_average import MovingAverageStrategy
from config.config import Config

st.set_page_config(
    page_title="Alpaca Trading System",
    layout="wide"
)

st.title("📈 Alpaca Trading Dashboard")

st.sidebar.header("System")

symbol = st.sidebar.selectbox(
    "Ticker",
    Config.TICKERS
)

st.sidebar.write("Mode")
st.sidebar.success("Paper Trading")

market = MarketData()

strategy = MovingAverageStrategy(
    Config.SHORT_WINDOW,
    Config.LONG_WINDOW
)

df = market.get_historical_data(symbol)

result = strategy.generate_signals(df)

signal = strategy.latest_signal(result)

latest_price = result.iloc[-1]["close"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Latest Price",
        f"${latest_price:.2f}"
    )

with col2:
    st.metric(
        "Current Signal",
        signal
    )

with col3:
    st.metric(
        "Short MA",
        f"{result.iloc[-1]['short_ma']:.2f}"
    )

st.subheader("Price Chart")

chart = result.set_index("timestamp")[[
    "close",
    "short_ma",
    "long_ma"
]]

st.line_chart(chart)

st.subheader("Recent Data")

st.dataframe(
    result.tail(10),
    use_container_width=True
)

st.subheader("System Status")

st.success("Connected to Alpaca Paper Trading")

col1, col2 = st.columns(2)

with col1:
    if st.button("Start Strategy"):
        st.success("Strategy Started")

with col2:
    if st.button("Stop Strategy"):
        st.warning("Strategy Stopped")
