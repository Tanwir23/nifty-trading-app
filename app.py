import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="Nifty App", layout="wide")

st.title("📊 Nifty 50 Trading App")

# Telegram
TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# Fetch data
data = yf.download("^NSEI", period="3mo", interval="1d")

# FIX: check data
if data is None or data.empty:
    st.error("Data not loading. Try later.")
    st.stop()

# FIX: reset index (very important)
data = data.reset_index()

# Simple Moving Averages (no ta library)
data['SMA20'] = data['Close'].rolling(20).mean()
data['SMA50'] = data['Close'].rolling(50).mean()

latest = data.iloc[-1]

# Signal logic (simple + stable)
signal = "Neutral"

if latest['Close'] > latest['SMA20'] > latest['SMA50']:
    signal = "Bullish"
elif latest['Close'] < latest['SMA20'] < latest['SMA50']:
    signal = "Bearish"

# Show output
st.subheader("Signal")
st.write(signal)

price = float(latest['Close'])

msg = f"Nifty: {signal} | Price: {round(price,2)}"

if st.button("Send Telegram"):
    send_msg(msg)
    st.success("Sent!")

# Chart
st.line_chart(data[['Close','SMA20','SMA50']])
