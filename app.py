import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Pro Trading Tool", layout="wide")

st.title("📊 PRO Options Trading System")

# ================= INPUT =================
capital = st.sidebar.number_input("Capital (₹)", value=10000)

TOKEN = st.sidebar.text_input("Telegram Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= EXPIRY =================
def get_expiry():
    today = datetime.today()
    days = 3 - today.weekday()
    if days <= 0:
        days += 7
    return (today + timedelta(days=days)).strftime("%d %b")

# ================= STORAGE =================
FILE = "last.txt"

def get_last():
    return open(FILE).read() if os.path.exists(FILE) else ""

def save_last(s):
    open(FILE, "w").write(s)

# ================= DATA =================
def get_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"
        r = requests.get(url, timeout=5).json()
        c = r['chart']['result'][0]['indicators']['quote'][0]['close']
        df = pd.DataFrame(c, columns=['Close']).dropna()
        if len(df) < 30:
            raise Exception()
        return df
    except:
        base = 22000 if symbol=="^NSEI" else 48000 if symbol=="^NSEBANK" else 73000
        return pd.DataFrame([base+i*20 for i in range(30)], columns=['Close'])

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
def signal_logic(df):
    df = indicators(df)
    l = df.iloc[-1]

    high = df['Close'].rolling(20).max().iloc[-1]
    low = df['Close'].rolling(20).min().iloc[-1]

    # Extra filter: volatility
    volatility = df['Close'].rolling(10).std().iloc[-1]

    if volatility < 10:
        return "NO TRADE", l

    if l['EMA20']>l['EMA50'] and l['RSI']>60 and l['MACD']>l['SIG']:
        return "STRONG BUY 🚀", l

    if l['EMA20']<l['EMA50'] and l['RSI']<40 and l['MACD']<l['SIG']:
        return "STRONG SELL 🔻", l

    if l['Close']>high:
        return "BREAKOUT BUY ⚡", l

    if l['Close']<low:
        return "BREAKDOWN SELL ⚡", l

    return "NO TRADE", l

# ================= OPTION PREMIUM =================
def option_premium(price):
    # simple approximation (ATM)
    return round(price * 0.005, 2)

# ================= TRAILING SL =================
def trailing_sl(entry, current, direction):
    move = abs(current - entry)
    if move > 30:
        if direction == "BUY":
            return entry + move*0.5
        else:
            return entry - move*0.5
    return entry - 20 if direction=="BUY" else entry + 20

# ================= STRATEGY =================
def strategy(price, signal, index, lot):
    strike = round(price/100)*100
    expiry = get_expiry()
    lots = max(1, capital//5000)
    qty = lots * lot

    premium = option_premium(price)

    if "BUY" in signal:
        opt = f"{index} {expiry} {strike} CE"
        tsl = trailing_sl(price, price+40, "BUY")

    elif "SELL" in signal:
        opt = f"{index} {expiry} {strike} PE"
        tsl = trailing_sl(price, price-40, "SELL")

    else:
        opt = "No Trade"
        tsl = price

    return opt, qty, premium, tsl

# ================= RUN =================
symbols = {
    "NIFTY": ("^NSEI", 25),
    "BANKNIFTY": ("^NSEBANK", 15),
    "SENSEX": ("^BSESN", 10)
}

results = {}

for name,(sym,lot) in symbols.items():
    df = get_data(sym)
    sig, last = signal_logic(df)
    opt, qty, prem, tsl = strategy(last['Close'], sig, name, lot)

    results[name] = (sig, opt, qty, prem, tsl)

# ================= DISPLAY =================
for k,v in results.items():
    st.subheader(f"📊 {k}")
    st.write(f"Signal: {v[0]}")
    st.write(f"Trade: {v[1]}")
    st.write(f"Qty: {v[2]}")
    st.write(f"Est Premium: ₹{v[3]}")
    st.write(f"Trailing SL: {round(v[4],2)}")
    st.divider()

# ================= TELEGRAM =================
msg = "🚨 TRADE ALERT 🚨\n\n"
for k,v in results.items():
    msg += f"{k}\n{v[0]}\n{v[1]}\nQty:{v[2]} | Premium:{v[3]}\n\n"

cur = str(results)
if cur != get_last():
    send_msg(msg)
    save_last(cur)

# ================= AUTO REFRESH =================
r = st.sidebar.selectbox("Refresh", [30,60])
time.sleep(r)
st.rerun()
