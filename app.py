import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests

st.set_page_config(page_title="Nifty Trading App", layout="wide")

st.title("🚀 Nifty 50 Dashboard + Telegram Alerts")

# Telegram
TELEGRAM_TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_telegram(msg):
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# Data
symbol = "^NSEI"
data = yf.download(symbol, period="6mo", interval="1d")

# 🔴 FIX: Prevent crash
if data.empty:
    st.error("⚠️ Data not loading. Try again later.")
    st.stop()

# Indicators
data['SMA20'] = ta.trend.sma_indicator(data['Close'], window=20)
data['SMA50'] = ta.trend.sma_indicator(data['Close'], window=50)
data['RSI'] = ta.momentum.rsi(data['Close'], window=14)

latest = data.iloc[-1]

# Signal
signal = "Neutral"

if latest['Close'] > latest['SMA20'] > latest['SMA50']:
    signal = "Bullish"
elif latest['Close'] < latest['SMA20'] < latest['SMA50']:
    signal = "Bearish"

# Output
st.subheader("Signal")
st.write(signal)

msg = f"Nifty Signal: {signal} | Price: {round(latest['Close'],2)}"

if st.button("Send to Telegram"):
    send_telegram(msg)
    st.success("Sent!")

# Chart
st.line_chart(data[['Close','SMA20','SMA50']])
