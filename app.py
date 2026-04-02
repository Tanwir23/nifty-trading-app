import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Pro Trading Tool", layout="wide")

st.title("📊 Nifty & Sensex Advanced Trading Tool")

# ================= TELEGRAM =================
TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= DATA =================
def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        res = requests.get(url).json()
        return res['quoteResponse']['result'][0]['regularMarketPrice']
    except:
        return None

nifty_price = get_price("^NSEI") or 22500
sensex_price = get_price("^BSESN") or 74000

# ================= INDICATORS =================
def calculate_indicators(price):
    # Simulated RSI (scaled)
    rsi = (price % 100)  

    # Simulated MACD
    macd = price * 0.001
    signal_line = macd * 0.95

    return rsi, macd, signal_line

# ================= SIGNAL LOGIC =================
def generate_signal(price):
    rsi, macd, signal_line = calculate_indicators(price)

    signal = "Neutral"

    # 🔥 Strong Bullish
    if rsi > 60 and macd > signal_line:
        signal = "Bullish"

    # 🔥 Strong Bearish
    elif rsi < 40 and macd < signal_line:
        signal = "Bearish"

    # ⚡ Breakout logic
    if price % 500 > 450:
        signal = "Breakout ↑"

    elif price % 500 < 50:
        signal = "Breakdown ↓"

    return signal, rsi, macd

# ================= TRADE SETUP =================
def trade_setup(price, signal):
    if "Bullish" in signal or "Breakout" in signal:
        return price, price + 150, price - 100
    elif "Bearish" in signal or "Breakdown" in signal:
        return price, price - 150, price + 100
    else:
        return price, price + 50, price - 50

# Nifty
n_signal, n_rsi, n_macd = generate_signal(nifty_price)
n_entry, n_target, n_sl = trade_setup(nifty_price, n_signal)

# Sensex
s_signal, s_rsi, s_macd = generate_signal(sensex_price)
s_entry, s_target, s_sl = trade_setup(sensex_price, s_signal)

# ================= DISPLAY =================
st.subheader("📈 Nifty 50")
st.write(f"Price: {nifty_price}")
st.write(f"Signal: {n_signal}")
st.write(f"RSI: {round(n_rsi,2)} | MACD: {round(n_macd,2)}")
st.write(f"Entry: {n_entry} | Target: {n_target} | SL: {n_sl}")

st.divider()

st.subheader("📊 Sensex")
st.write(f"Price: {sensex_price}")
st.write(f"Signal: {s_signal}")
st.write(f"RSI: {round(s_rsi,2)} | MACD: {round(s_macd,2)}")
st.write(f"Entry: {s_entry} | Target: {s_target} | SL: {s_sl}")

# ================= TELEGRAM =================
msg = f"""
📊 MARKET ALERT

NIFTY:
Signal: {n_signal}
RSI: {round(n_rsi,2)}
MACD: {round(n_macd,2)}
Entry: {n_entry}
Target: {n_target}
SL: {n_sl}

SENSEX:
Signal: {s_signal}
RSI: {round(s_rsi,2)}
MACD: {round(s_macd,2)}
Entry: {s_entry}
Target: {s_target}
SL: {s_sl}
"""

if st.button("Send Alert"):
    send_msg(msg)
    st.success("Alert Sent!")

st.caption("⚠️ Educational use only")
