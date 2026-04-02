import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Nifty + Sensex Trading Tool", layout="wide")

st.title("📊 Nifty & Sensex Pro Trading Tool")

# ================= TELEGRAM =================
TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= DATA FETCH =================
def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        res = requests.get(url).json()
        return res['quoteResponse']['result'][0]['regularMarketPrice']
    except:
        return None

nifty_price = get_price("^NSEI")
sensex_price = get_price("^BSESN")

# fallback
if nifty_price is None:
    nifty_price = 22500
if sensex_price is None:
    sensex_price = 74000

# ================= SIGNAL LOGIC =================
def generate_signal(price):
    sma20 = price * 0.995
    sma50 = price * 0.99

    signal = "Neutral"

    if price > sma20 and sma20 > sma50:
        signal = "Bullish"
    elif price < sma20 and sma20 < sma50:
        signal = "Bearish"

    return signal, sma20, sma50

nifty_signal, n_sma20, n_sma50 = generate_signal(nifty_price)
sensex_signal, s_sma20, s_sma50 = generate_signal(sensex_price)

# ================= TRADE SETUP =================
def trade_setup(price, signal):
    if signal == "Bullish":
        return price, price + 150, price - 100
    elif signal == "Bearish":
        return price, price - 150, price + 100
    else:
        return price, price + 50, price - 50

# Nifty
n_entry, n_target, n_sl = trade_setup(nifty_price, nifty_signal)

# Sensex
s_entry, s_target, s_sl = trade_setup(sensex_price, sensex_signal)

# ================= DISPLAY =================
st.subheader("📈 Nifty 50")
st.write(f"Price: {nifty_price}")
st.write(f"Signal: {nifty_signal}")
st.write(f"Entry: {n_entry} | Target: {n_target} | SL: {n_sl}")

st.divider()

st.subheader("📊 Sensex")
st.write(f"Price: {sensex_price}")
st.write(f"Signal: {sensex_signal}")
st.write(f"Entry: {s_entry} | Target: {s_target} | SL: {s_sl}")

# ================= TELEGRAM =================
msg = f"""
NIFTY:
Signal: {nifty_signal}
Price: {nifty_price}
Entry: {n_entry}
Target: {n_target}
SL: {n_sl}

SENSEX:
Signal: {sensex_signal}
Price: {sensex_price}
Entry: {s_entry}
Target: {s_target}
SL: {s_sl}
"""

if st.button("Send Alert"):
    send_msg(msg)
    st.success("Alert Sent!")

st.caption("⚠️ Educational use only")
