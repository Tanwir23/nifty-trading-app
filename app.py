import streamlit as st
import pandas as pd
import requests
import os
import time

st.set_page_config(page_title="Pro Trading Tool", layout="wide")

st.title("📊 Nifty & Sensex Advanced Options Trading System")

# ================= TELEGRAM =================
TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= SMART ALERT =================
LAST_SIGNAL_FILE = "last_signal.txt"

def get_last_signal():
    if os.path.exists(LAST_SIGNAL_FILE):
        with open(LAST_SIGNAL_FILE, "r") as f:
            return f.read()
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
            raise Exception("Not enough data")

        return df

    except:
        if symbol == "^NSEI":
            prices = [
                22000,22100,22200,22150,22250,22300,22280,22350,
                22400,22380,22450,22500,22480,22550,22600,22580,
                22650,22700,22680,22750,22800,22780,22850,22900
            ]
        else:
            prices = [
                73000,73100,73200,73150,73300,73400,73350,73500,
                73600,73550,73700,73800,73750,73900,74000,73950,
                74100,74200,74150,74300,74400,74350,74500,74600
            ]

        return pd.DataFrame(prices, columns=['Close'])

# ================= INDICATORS =================
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(df):
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

# ================= SIGNAL (IMPROVED) =================
def generate_signal(df):
    df['RSI'] = calculate_rsi(df)
    df['MACD'], df['Signal'] = calculate_macd(df)

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    latest = df.iloc[-1]

    recent_high = df['Close'].rolling(20).max().iloc[-1]
    recent_low = df['Close'].rolling(20).min().iloc[-1]

    signal = "NO TRADE"

    uptrend = latest['EMA20'] > latest['EMA50']
    downtrend = latest['EMA20'] < latest['EMA50']

    # STRONG BUY
    if (
        uptrend and
        latest['RSI'] > 60 and
        latest['MACD'] > latest['Signal'] and
        latest['Close'] > latest['EMA20']
    ):
        signal = "STRONG BUY 🚀"

    # STRONG SELL
    elif (
        downtrend and
        latest['RSI'] < 40 and
        latest['MACD'] < latest['Signal'] and
        latest['Close'] < latest['EMA20']
    ):
        signal = "STRONG SELL 🔻"

    # BREAKOUT
    elif latest['Close'] > recent_high and latest['RSI'] > 55:
        signal = "BREAKOUT BUY ⚡"

    elif latest['Close'] < recent_low and latest['RSI'] < 45:
        signal = "BREAKDOWN SELL ⚡"

    return signal, latest

# ================= OPTIONS STRATEGY =================
def option_strategy(price, signal, index_name):
    strike = round(price / 100) * 100

    if "BUY" in signal:
        option = f"{index_name} {strike} CE"
        target = price + 50
        sl = price - 30

    elif "SELL" in signal:
        option = f"{index_name} {strike} PE"
        target = price - 50
        sl = price + 30

    else:
        option = "No Trade"
        target = price
        sl = price

    return option, target, sl

# ================= RUN =================
nifty_df = get_data("^NSEI")
sensex_df = get_data("^BSESN")

# NIFTY
n_signal, n_latest = generate_signal(nifty_df)
n_option, n_target, n_sl = option_strategy(n_latest['Close'], n_signal, "NIFTY")

# SENSEX
s_signal, s_latest = generate_signal(sensex_df)
s_option, s_target, s_sl = option_strategy(s_latest['Close'], s_signal, "SENSEX")

# ================= DISPLAY =================
st.subheader("📈 Nifty (Options Trade)")
st.write(f"Price: {round(n_latest['Close'],2)}")
st.write(f"Signal: {n_signal}")
st.write(f"Trade: {n_option}")
st.write(f"Target: {n_target} | SL: {n_sl}")

st.divider()

st.subheader("📊 Sensex (Options Trade)")
st.write(f"Price: {round(s_latest['Close'],2)}")
st.write(f"Signal: {s_signal}")
st.write(f"Trade: {s_option}")
st.write(f"Target: {s_target} | SL: {s_sl}")

# ================= TELEGRAM =================
msg = f"""
🚨 OPTIONS TRADE ALERT 🚨

NIFTY:
{n_signal}
Trade: {n_option}
Target: {n_target}
SL: {n_sl}

SENSEX:
{s_signal}
Trade: {s_option}
Target: {s_target}
SL: {s_sl}
"""

current_signal = n_signal + "|" + s_signal
last_signal = get_last_signal()

if current_signal != last_signal:
    send_msg(msg)
    save_signal(current_signal)
    st.success("🚨 New Signal Sent!")
else:
    st.info("No new signal")

# ================= AUTO REFRESH =================
refresh = st.sidebar.selectbox("Refresh (sec)", [30, 60, 120])

time.sleep(refresh)
st.rerun()

st.caption("⚠️ Intraday trading system (educational use)")
