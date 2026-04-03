import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Pro Trading Tool", layout="wide")

st.title("📊 Advanced Options Trading System")

# ================= USER INPUT =================
capital = st.sidebar.number_input("Capital (₹)", value=10000)

TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= EXPIRY =================
def get_next_expiry():
    today = datetime.today()
    days_ahead = 3 - today.weekday()  # Thursday
    if days_ahead <= 0:
        days_ahead += 7
    expiry = today + timedelta(days=days_ahead)
    return expiry.strftime("%d %b")

# ================= SMART ALERT =================
LAST_SIGNAL_FILE = "last_signal.txt"

def get_last_signal():
    if os.path.exists(LAST_SIGNAL_FILE):
        return open(LAST_SIGNAL_FILE).read()
    return ""

def save_signal(signal):
    with open(LAST_SIGNAL_FILE, "w") as f:
        f.write(signal)

# ================= DATA =================
def get_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"
        res = requests.get(url, timeout=5).json()

        closes = res['chart']['result'][0]['indicators']['quote'][0]['close']
        df = pd.DataFrame(closes, columns=['Close'])
        df.dropna(inplace=True)

        if len(df) < 30:
            raise Exception()

        return df
    except:
        if symbol == "^NSEI":
            prices = [22000,22100,22200,22300,22400,22500,22600,22700,22800]
        elif symbol == "^NSEBANK":
            prices = [48000,48200,48400,48600,48800,49000,49200,49400]
        else:
            prices = [73000,73200,73400,73600,73800,74000,74200]

        return pd.DataFrame(prices, columns=['Close'])

# ================= INDICATORS =================
def calculate_rsi(df):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(df):
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

# ================= SIGNAL =================
def generate_signal(df):
    df['RSI'] = calculate_rsi(df)
    df['MACD'], df['Signal'] = calculate_macd(df)

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    latest = df.iloc[-1]

    recent_high = df['Close'].rolling(20).max().iloc[-1]
    recent_low = df['Close'].rolling(20).min().iloc[-1]

    signal = "NO TRADE"

    if latest['EMA20'] > latest['EMA50'] and latest['RSI'] > 60 and latest['MACD'] > latest['Signal']:
        signal = "STRONG BUY 🚀"

    elif latest['EMA20'] < latest['EMA50'] and latest['RSI'] < 40 and latest['MACD'] < latest['Signal']:
        signal = "STRONG SELL 🔻"

    elif latest['Close'] > recent_high:
        signal = "BREAKOUT BUY ⚡"

    elif latest['Close'] < recent_low:
        signal = "BREAKDOWN SELL ⚡"

    return signal, latest

# ================= OPTIONS =================
def option_strategy(price, signal, index, lot_size):
    strike = round(price / 100) * 100
    expiry = get_next_expiry()

    lots = max(1, capital // 5000)
    qty = lots * lot_size

    if "BUY" in signal:
        option = f"{index} {expiry} {strike} CE"
    elif "SELL" in signal:
        option = f"{index} {expiry} {strike} PE"
    else:
        option = "No Trade"

    return option, qty

# ================= RUN =================
nifty_df = get_data("^NSEI")
bank_df = get_data("^NSEBANK")
sensex_df = get_data("^BSESN")

# NIFTY
n_signal, n_latest = generate_signal(nifty_df)
n_option, n_qty = option_strategy(n_latest['Close'], n_signal, "NIFTY", 25)

# BANK NIFTY
b_signal, b_latest = generate_signal(bank_df)
b_option, b_qty = option_strategy(b_latest['Close'], b_signal, "BANKNIFTY", 15)

# SENSEX
s_signal, s_latest = generate_signal(sensex_df)
s_option, s_qty = option_strategy(s_latest['Close'], s_signal, "SENSEX", 10)

# ================= DISPLAY =================
st.subheader("📈 NIFTY")
st.write(n_signal, "|", n_option, "| Qty:", n_qty)

st.subheader("🏦 BANK NIFTY")
st.write(b_signal, "|", b_option, "| Qty:", b_qty)

st.subheader("📊 SENSEX")
st.write(s_signal, "|", s_option, "| Qty:", s_qty)

# ================= TELEGRAM =================
msg = f"""
🚨 TRADE ALERT 🚨

NIFTY:
{n_signal}
{n_option}
Qty: {n_qty}

BANKNIFTY:
{b_signal}
{b_option}
Qty: {b_qty}

SENSEX:
{s_signal}
{s_option}
Qty: {s_qty}
"""

current_signal = n_signal + b_signal + s_signal
last_signal = get_last_signal()

if current_signal != last_signal:
    send_msg(msg)
    save_signal(current_signal)
    st.success("🚨 New Signal Sent!")
else:
    st.info("No new signal")

# ================= AUTO REFRESH =================
refresh = st.sidebar.selectbox("Refresh (sec)", [30, 60])

time.sleep(refresh)
st.rerun()
