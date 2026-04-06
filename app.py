import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Simple Trading Tool", layout="wide")
st.title("📊 Simple Live Trading System")

# ================= INPUT =================
capital = st.sidebar.number_input("Capital (₹)", value=10000)

# ================= EXPIRY =================
def get_expiry():
    today = datetime.today()
    days = 3 - today.weekday()
    if days <= 0:
        days += 7
    return (today + timedelta(days=days)).strftime("%d %b")

# ================= LIVE PRICE =================
def get_price(symbol):
    try:
        mapping = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "SENSEX": "^BSESN"
        }

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{mapping[symbol]}?interval=1m&range=1d"
        data = requests.get(url, timeout=5).json()

        close = data['chart']['result'][0]['indicators']['quote'][0]['close']
        price = [x for x in close if x is not None][-1]

        return float(price)

    except:
        return 22000 if symbol=="NIFTY" else 48000 if symbol=="BANKNIFTY" else 73000

# ================= DATA =================
def get_df(symbol):
    try:
        mapping = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "SENSEX": "^BSESN"
        }

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{mapping[symbol]}?interval=5m&range=1d"
        data = requests.get(url, timeout=5).json()

        close = data['chart']['result'][0]['indicators']['quote'][0]['close']
        df = pd.DataFrame(close, columns=['Close']).dropna()

        return df

    except:
        base = 22000 if symbol=="NIFTY" else 48000 if symbol=="BANKNIFTY" else 73000
        return pd.DataFrame([base+i*10 for i in range(50)], columns=['Close'])

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
def run_strategy(index, lot):
    price = get_price(index)
    df = get_df(index)

    signal = get_signal(df)
    strike = round(price/100)*100
    expiry = get_expiry()

    lots = max(1, capital//5000)
    qty = lots * lot

    if "BUY" in signal:
        option = f"{index} {expiry} {strike} CE"
        entry = price
        target = price + 50
        sl = price - 30

    elif "SELL" in signal:
        option = f"{index} {expiry} {strike} PE"
        entry = price
        target = price - 50
        sl = price + 30

    else:
        option = "No Trade"
        entry = price
        target = price
        sl = price

    return signal, option, qty, entry, target, sl, df

# ================= RUN =================
data = {
    "NIFTY": run_strategy("NIFTY", 25),
    "BANKNIFTY": run_strategy("BANKNIFTY", 15),
    "SENSEX": run_strategy("SENSEX", 10)
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
refresh = st.sidebar.selectbox("Refresh (sec)", [30, 60])
time.sleep(refresh)
st.rerun()
