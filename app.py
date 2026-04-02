import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Nifty App", layout="wide")

st.title("📊 Nifty 50 Trading App")

# Telegram setup
TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ✅ STATIC DATA (No crash guaranteed)
data = pd.DataFrame({
    "Close": [22000, 22100, 22250, 22180, 22300, 22400, 22350]
})

# Indicators
data['SMA20'] = data['Close'].rolling(2).mean()
data['SMA50'] = data['Close'].rolling(3).mean()

data = data.dropna()

latest = data.iloc[-1]

# Signal
signal = "Neutral"

if latest['Close'] > latest['SMA20']:
    signal = "Bullish"
elif latest['Close'] < latest['SMA20']:
    signal = "Bearish"
else:
    signal = "Neutral"

# Output
st.subheader("Signal")
st.write(signal)

price = float(latest['Close'])

msg = f"Nifty: {signal} | Price: {price}"

if st.button("Send Telegram"):
    send_msg(msg)
    st.success("Sent!")

# Chart
st.line_chart(data[['Close','SMA20','SMA50']])
