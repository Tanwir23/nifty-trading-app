import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from kiteconnect import KiteConnect

st.set_page_config(page_title="Pro Trading Tool", layout="wide")
st.title("📊 FULL AUTO TRADING SYSTEM (ZERODHA)")

# ================= INPUT =================
capital = st.sidebar.number_input("Capital (₹)", value=10000)

api_key = st.sidebar.text_input("Zerodha API Key")
api_secret = st.sidebar.text_input("API Secret", type="password")
request_token = st.sidebar.text_input("Request Token")

TOKEN = st.sidebar.text_input("Telegram Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

auto_trade = st.sidebar.checkbox("Enable Auto Trading")

# ================= TELEGRAM =================
def send_msg(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ================= ZERODHA =================
kite = None
if api_key and api_secret and request_token:
    try:
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(request_token, api_secret=api_secret)
        kite.set_access_token(data["access_token"])
        st.success("✅ Zerodha Connected")
    except:
        st.error("❌ Login Failed")

# ================= STORAGE =================
FILE = "last_signal.txt"

def get_last():
    return open(FILE).read() if os.path.exists(FILE) else ""

def save_last(s):
    open(FILE, "w").write(s)

# ================= EXPIRY =================
def get_expiry():
    today = datetime.today()
    days = 3 - today.weekday()
    if days <= 0:
        days += 7
    return (today + timedelta(days=days)).strftime("%d%b").upper()

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

    return 22000 if symbol=="NIFTY" else 48000 if symbol=="BANKNIFTY" else 73000

# ================= BUILD DF =================
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

# ================= SYMBOL =================
def build_symbol(index, strike, opt_type):
    expiry = get_expiry()
    return f"{index}{expiry}{strike}{opt_type}"

# ================= ORDER =================
def place_order(symbol, qty, transaction):
    try:
        if kite and symbol != "":
            return kite.place_order(
                variety=kite.VARIETY_REGULAR,
                exchange=kite.EXCHANGE_NFO,
                tradingsymbol=symbol,
                transaction_type=transaction,
                quantity=qty,
                product=kite.PRODUCT_MIS,
                order_type=kite.ORDER_TYPE_MARKET
            )
    except Exception as e:
        return str(e)

# ================= STRATEGY =================
def run_strategy(index, lot):
    price = get_price(index)
    df = build_df(price)

    signal = get_signal(df)
    strike = round(price/100)*100
    expiry = get_expiry()

    lots = max(1, capital//5000)
    qty = lots * lot

    symbol = ""
    option_text = ""

    if "BUY" in signal:
        symbol = build_symbol(index, strike, "CE")
        option_text = f"{index} {expiry} {strike} CE"

    elif "SELL" in signal:
        symbol = build_symbol(index, strike, "PE")
        option_text = f"{index} {expiry} {strike} PE"

    tsl = price - 20 if "BUY" in signal else price + 20

    return signal, option_text, qty, tsl, df, symbol

# ================= RUN =================
data = {
    "NIFTY": run_strategy("NIFTY", 25),
    "BANKNIFTY": run_strategy("BANKNIFTY", 15),
    "SENSEX": run_strategy("SENSEX", 10)
}

# ================= DISPLAY =================
for k,v in data.items():
    st.subheader(f"📊 {k}")
    st.write("Signal:", v[0])
    st.write("Trade:", v[1])
    st.write("Qty:", v[2])
    st.write("Trailing SL:", round(v[3],2))

    col1, col2 = st.columns(2)

    if col1.button(f"BUY {k}"):
        order = place_order(v[5], v[2], "BUY")
        st.success(order)

    if col2.button(f"SELL {k}"):
        order = place_order(v[5], v[2], "SELL")
        st.success(order)

    st.line_chart(v[4]['Close'])
    st.divider()

# ================= TELEGRAM =================
msg = "🚨 TRADE ALERT 🚨\n\n"
for k,v in data.items():
    msg += f"{k}\n{v[0]}\n{v[1]}\nQty:{v[2]}\n\n"

cur = str(data)

if cur != get_last():
    send_msg(msg)
    save_last(cur)

# ================= AUTO TRADE =================
if auto_trade and cur != get_last():
    for k,v in data.items():
        if "BUY" in v[0]:
            place_order(v[5], v[2], "BUY")
        elif "SELL" in v[0]:
            place_order(v[5], v[2], "SELL")

# ================= REFRESH =================
r = st.sidebar.selectbox("Refresh", [30,60])

time.sleep(r)
st.rerun()
