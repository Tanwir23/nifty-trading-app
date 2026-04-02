import streamlit as st
import pandas as pd
import requests
import os
import time

st.set_page_config(page_title="Pro Trading Tool", layout="wide")

st.title("📊 Nifty & Sensex Intraday Trading System")

# ================= TELEGRAM =================
TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= SMART ALERT STORAGE =================
LAST_SIGNAL_FILE = "last_signal.txt"

def get_last_signal():
    if os.path.exists(LAST_SIGNAL_FILE):
        with open(LAST_SIGNAL_FILE, "r") as f:
            return f.read()
    return ""

def save_signal(signal):
    with open(LAST_SIGNAL_FILE, "w") as f:
        f.write(signal)

# ================= FETCH DATA =================
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
    if symbol == "^NSEI":  # NIFTY
        prices = [
            22000,22100,22200,22150,22250,22300,22280,22350,
            22400,22380,22450,22500,22480,22550,22600,22580,
            22650,22700,22680,22750,22800,22780,22850,22900
        ]
    else:  # SENSEX
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

# ================= SIGNAL =================
def generate_signal(df):
    df['RSI'] = calculate_rsi(df)
    df['MACD'], df['Signal'] = calculate_macd(df)

    latest = df.iloc[-1]

    recent_high = df['Close'].rolling(20).max().iloc[-1]
    recent_low = df['Close'].rolling(20).min().iloc[-1]

    signal = "Neutral"

    # Strong signals
    if latest['RSI'] > 65 and latest['MACD'] > latest['Signal']:
        signal = "STRONG BUY 🚀"

    elif latest['RSI'] < 35 and latest['MACD'] < latest['Signal']:
        signal = "STRONG SELL 🔻"

    # Breakouts
    elif latest['Close'] > recent_high:
        signal = "BREAKOUT BUY ⚡"

    elif latest['Close'] < recent_low:
        signal = "BREAKDOWN SELL ⚡"

    return signal, latest

# ================= TRADE SETUP =================
def trade_setup(price, signal):
    risk = 30
    reward = 60

    if "BUY" in signal:
        return price, price + reward, price - risk
    elif "SELL" in signal:
        return price, price - reward, price + risk
    else:
        return price, price + 20, price - 20

# ================= RUN =================
nifty_df = get_data("^NSEI")
sensex_df = get_data("^BSESN")

# NIFTY
n_signal, n_latest = generate_signal(nifty_df)
n_entry, n_target, n_sl = trade_setup(n_latest['Close'], n_signal)

# SENSEX
s_signal, s_latest = generate_signal(sensex_df)
s_entry, s_target, s_sl = trade_setup(s_latest['Close'], s_signal)

# ================= DISPLAY =================
st.subheader("📈 Nifty (5-min Scalping)")
st.write(f"Price: {round(n_latest['Close'],2)}")
st.write(f"Signal: {n_signal}")
st.write(f"Entry: {n_entry} | Target: {n_target} | SL: {n_sl}")

st.divider()

st.subheader("📊 Sensex (5-min Scalping)")
st.write(f"Price: {round(s_latest['Close'],2)}")
st.write(f"Signal: {s_signal}")
st.write(f"Entry: {s_entry} | Target: {s_target} | SL: {s_sl}")

# ================= TELEGRAM ALERT =================
msg = f"""
🚨 INTRADAY TRADE ALERT 🚨

NIFTY:
{n_signal}
Entry: {round(n_entry,2)}
Target: {round(n_target,2)}
SL: {round(n_sl,2)}

SENSEX:
{s_signal}
Entry: {round(s_entry,2)}
Target: {round(s_target,2)}
SL: {round(s_sl,2)}
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

st.caption("⚠️ Intraday system for learning purposes")
