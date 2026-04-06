import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="Trading Tool", layout="wide")
st.title("📊 Trading System (Stable Version)")

# ================= INPUT =================
capital = st.sidebar.number_input("Capital (₹)", value=10000)

# ================= EXPIRY =================
def get_expiry():
    today = datetime.today()
    days = 3 - today.weekday()
    if days <= 0:
        days += 7
    return (today + timedelta(days=days)).strftime("%d %b")

# ================= MANUAL BASE PRICE =================
nifty_base = st.sidebar.number_input("NIFTY Base Price", value=22500)
bank_base = st.sidebar.number_input("BANKNIFTY Base Price", value=49000)
sensex_base = st.sidebar.number_input("SENSEX Base Price", value=75000)

# ================= LIVE SIMULATION =================
def get_price(base):
    return base + random.uniform(-20, 20)

# ================= DATA =================
def get_df(base):
    prices = [base + random.uniform(-30, 30) for _ in range(50)]
    return pd.DataFrame(prices, columns=['Close'])

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

# ================= STRATEGY =================
def run_strategy(name, base, lot):
    price = get_price(base)
    df = get_df(base)

    signal = get_signal(df)
    strike = round(price/100)*100
    expiry = get_expiry()

    lots = max(1, capital//5000)
    qty = lots * lot

    if "BUY" in signal:
        option = f"{name} {expiry} {strike} CE"
        target = price + 50
        sl = price - 30

    elif "SELL" in signal:
        option = f"{name} {expiry} {strike} PE"
        target = price - 50
        sl = price + 30

    else:
        option = "No Trade"
        target = price
        sl = price

    return signal, option, qty, price, target, sl, df

# ================= RUN =================
data = {
    "NIFTY": run_strategy("NIFTY", nifty_base, 25),
    "BANKNIFTY": run_strategy("BANKNIFTY", bank_base, 15),
    "SENSEX": run_strategy("SENSEX", sensex_base, 10)
}

# ================= DISPLAY =================
for k,v in data.items():
    st.subheader(f"📊 {k}")

    st.write("Price:", round(v[3],2))
    st.write("Signal:", v[0])
    st.write("Trade:", v[1])
    st.write("Qty:", v[2])
    st.write("Target:", v[4], "| Stop Loss:", v[5])

    st.line_chart(v[6]['Close'])
    st.divider()

# ================= REFRESH =================
refresh = st.sidebar.selectbox("Refresh (sec)", [10, 30])
time.sleep(refresh)
st.rerun()
