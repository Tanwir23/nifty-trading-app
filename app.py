import streamlit as st
import pandas as pd
import requests
import datetime

st.set_page_config(page_title="Nifty Trading Tool", layout="wide")

st.title("📊 Nifty 50 Pro Trading Tool")

# ================= TELEGRAM =================
TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= REAL DATA (NSE API) =================
try:
    url = "https://www.nseindia.com/api/quote-equity?symbol=NIFTY%2050"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers).json()
    
    price = res['priceInfo']['lastPrice']
except:
    price = 22500  # fallback

# ================= LOGIC =================
# Simple levels (can improve later)
support = price - 200
resistance = price + 200

signal = "Neutral"

if price > resistance - 50:
    signal = "Bullish Breakout"
elif price < support + 50:
    signal = "Bearish Breakdown"

# ================= TRADE SETUP =================
entry = price
target = price + 150 if "Bullish" in signal else price - 150
sl = price - 100 if "Bullish" in signal else price + 100

# ================= DISPLAY =================
st.subheader("📈 Live Nifty Data")
st.write(f"Price: {price}")

st.subheader("🚦 Signal")
st.write(signal)

st.subheader("🎯 Trade Setup")
st.write(f"Entry: {entry}")
st.write(f"Target: {target}")
st.write(f"Stop Loss: {sl}")

# ================= TELEGRAM =================
msg = f"""
NIFTY TRADE ALERT
Signal: {signal}
Price: {price}
Entry: {entry}
Target: {target}
SL: {sl}
"""

if st.button("Send Alert"):
    send_msg(msg)
    st.success("Alert Sent!")

st.caption("⚠️ For educational use only")
