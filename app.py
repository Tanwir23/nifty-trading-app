import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Pro Trading Tool", layout="wide")

st.title("📊 Nifty & Sensex Intraday Trading Tool")

# ================= TELEGRAM =================
TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= FETCH DATA =================
def get_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"
        res = requests.get(url).json()

        closes = res['chart']['result'][0]['indicators']['quote'][0]['close']
        df = pd.DataFrame(closes, columns=['Close'])
        df.dropna(inplace=True)

        return df
    except:
        return None

# ================= INDICATORS =================
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

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

    signal = "Neutral"

    # 🔥 Scalping Logic
    if latest['RSI'] > 60 and latest['MACD'] > latest['Signal']:
        signal = "BUY (Scalp)"

    elif latest['RSI'] < 40 and latest['MACD'] < latest['Signal']:
        signal = "SELL (Scalp)"

    # ⚡ Breakout logic
    recent_high = df['Close'].rolling(20).max().iloc[-1]
    recent_low = df['Close'].rolling(20).min().iloc[-1]

    if latest['Close'] > recent_high:
        signal = "BREAKOUT BUY 🚀"

    elif latest['Close'] < recent_low:
        signal = "BREAKDOWN SELL 🔻"

    return signal, latest

# ================= TRADE SETUP =================
def trade_setup(price, signal):
    if "BUY" in signal:
        return price, price + 50, price - 30
    elif "SELL" in signal:
        return price, price - 50, price + 30
    else:
        return price, price + 20, price - 20

# ================= RUN =================
nifty_df = get_data("^NSEI")
sensex_df = get_data("^BSESN")

if nifty_df is None or sensex_df is None:
    st.error("⚠️ Data not loading. Try refresh.")
    st.stop()

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

# ================= TELEGRAM =================
msg = f"""
📊 INTRADAY ALERT

NIFTY:
Signal: {n_signal}
Entry: {n_entry}
Target: {n_target}
SL: {n_sl}

SENSEX:
Signal: {s_signal}
Entry: {s_entry}
Target: {s_target}
SL: {s_sl}
"""

if st.button("Send Alert"):
    send_msg(msg)
    st.success("Alert Sent!")

st.caption("⚠️ Intraday scalping system (educational)")
