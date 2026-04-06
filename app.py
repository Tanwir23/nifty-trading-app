import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from kiteconnect import KiteConnect

st.set_page_config(page_title="Pro Trading Tool", layout="wide")

st.title("📊 Zerodha Live Trading System")

# ================= USER INPUT =================
capital = st.sidebar.number_input("Capital (₹)", value=10000)

# Zerodha Login
api_key = st.sidebar.text_input("Zerodha API Key")
api_secret = st.sidebar.text_input("API Secret", type="password")
request_token = st.sidebar.text_input("Request Token")

# Telegram
TOKEN = st.sidebar.text_input("Telegram Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

# ================= TELEGRAM =================
def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= ZERODHA CONNECT =================
kite = None

if api_key and api_secret and request_token:
    try:
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(request_token, api_secret=api_secret)
        kite.set_access_token(data["access_token"])
        st.success("✅ Zerodha Connected")
    except:
        st.error("❌ Login Failed")

# ================= EXPIRY =================
def get_expiry():
    today = datetime.today()
    days = 3 - today.weekday()
    if days <= 0:
        days += 7
    return (today + timedelta(days=days)).strftime("%d %b")

# ================= STORAGE =================
FILE = "last_signal.txt"

def get_last():
    return open(FILE).read() if os.path.exists(FILE) else ""

def save_last(s):
    open(FILE, "w").write(s)

# ================= LIVE PRICE =================
def get_price(symbol):
    try:
        if kite:
            mapping = {
                "NIFTY": "NSE:NIFTY 50",
                "BANKNIFTY": "NSE:NIFTY BANK",
                "SENSEX": "BSE:SENSEX"
            }
            data = kite.ltp(mapping[symbol])
            return list(data.values())[0]['last_price']
    except:
        pass

    # fallback
    return 22000 if symbol=="NIFTY" else 48000 if symbol=="BANKNIFTY" else 73000

# ================= FAKE SERIES FOR INDICATORS =================
def build_df(price):
    return pd.DataFrame([price + i for i in range(50)], columns=['Close'])

# ================= INDICATORS =================
def indicators(df):
    df['RSI'] = 100 - (100/(1+(df['Close'].diff().clip(lower=0).rolling(14).mean() /
                             -df['Close'].diff().clip(upper=0).rolling(14).mean())))
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['SIG'] = df['MACD'].ewm(span=9).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return df

# ================= SIGNAL =================
def get_signal(df):
    df = indicators(df)
    l = df.iloc[-1]

    if l['EMA20'] > l['EMA50'] and l['RSI'] > 60 and l['MACD'] > l['SIG']:
        return "STRONG BUY 🚀"

    if l['EMA20'] < l['EMA50'] and l['RSI'] < 40 and l['MACD'] < l['SIG']:
        return "STRONG SELL 🔻"

    return "NO TRADE"

# ================= OPTION PRICE =================
def get_option_price(index, strike, opt_type):
    try:
        if kite:
            symbol_map = {
                "NIFTY": "NFO:NIFTY",
                "BANKNIFTY": "NFO:BANKNIFTY"
            }

            tradingsymbol = f"{symbol_map[index]}{strike}{opt_type}"
            data = kite.ltp(tradingsymbol)

            return list(data.values())[0]['last_price']
    except:
        pass

    return 0

# ================= STRATEGY =================
def strategy(index, lot):
    price = get_price(index)
    df = build_df(price)

    signal = get_signal(df)
    strike = round(price / 100) * 100
    expiry = get_expiry()

    lots = max(1, capital // 5000)
    qty = lots * lot

    if "BUY" in signal:
        opt = f"{index} {expiry} {strike} CE"
        premium = get_option_price(index, strike, "CE")

    elif "SELL" in signal:
        opt = f"{index} {expiry} {strike} PE"
        premium = get_option_price(index, strike, "PE")

    else:
        opt = "No Trade"
        premium = 0

    tsl = price - 20 if "BUY" in signal else price + 20

    return signal, opt, qty, premium, tsl, df

# ================= RUN =================
data = {
    "NIFTY": strategy("NIFTY", 25),
    "BANKNIFTY": strategy("BANKNIFTY", 15),
    "SENSEX": strategy("SENSEX", 10)
}

# ================= DISPLAY =================
for k,v in data.items():
    st.subheader(f"📊 {k}")
    st.write(f"Signal: {v[0]}")
    st.write(f"Trade: {v[1]}")
    st.write(f"Qty: {v[2]}")
    st.write(f"Premium: ₹{v[3]}")
    st.write(f"Trailing SL: {round(v[4],2)}")

    st.line_chart(v[5]['Close'])
    st.divider()

# ================= TELEGRAM =================
msg = "🚨 TRADE ALERT 🚨\n\n"

for k,v in data.items():
    msg += f"{k}\n{v[0]}\n{v[1]}\nQty:{v[2]} Premium:{v[3]}\n\n"

cur = str(data)

if cur != get_last():
    send_msg(msg)
    save_last(cur)

# ================= AUTO REFRESH =================
r = st.sidebar.selectbox("Refresh", [30,60])

time.sleep(r)
st.rerun()
