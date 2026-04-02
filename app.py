import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests

st.set_page_config(page_title="Nifty Advanced Trading App", layout="wide")

st.title("🚀 Nifty 50 Smart Trading Dashboard + Telegram Alerts")

# ===================== TELEGRAM CONFIG =====================
TELEGRAM_TOKEN = st.sidebar.text_input("Telegram Bot Token", type="password")
CHAT_ID = st.sidebar.text_input("Chat ID")

def send_telegram(message):
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=payload)

# ===================== DATA =====================
symbol = "^NSEI"
data = yf.download(symbol, period="6mo", interval="1d")

# ===================== INDICATORS =====================
data['SMA20'] = ta.trend.sma_indicator(data['Close'], window=20)
data['SMA50'] = ta.trend.sma_indicator(data['Close'], window=50)
data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
macd = ta.trend.MACD(data['Close'])
data['MACD'] = macd.macd()
data['MACD_signal'] = macd.macd_signal()

# Support & Resistance
data['Rolling_Max'] = data['High'].rolling(20).max()
data['Rolling_Min'] = data['Low'].rolling(20).min()

latest = data.iloc[-1]

# ===================== SIGNAL ENGINE =====================
signal = "Neutral"
confidence = 0

if latest['Close'] > latest['SMA20'] > latest['SMA50']:
    confidence += 1
if latest['RSI'] > 55:
    confidence += 1
if latest['MACD'] > latest['MACD_signal']:
    confidence += 1

if latest['Close'] < latest['SMA20'] < latest['SMA50']:
    confidence -= 1
if latest['RSI'] < 45:
    confidence -= 1
if latest['MACD'] < latest['MACD_signal']:
    confidence -= 1

if confidence >= 2:
    signal = "Bullish"
elif confidence <= -2:
    signal = "Bearish"

support = latest['Rolling_Min']
resistance = latest['Rolling_Max']

# ===================== DISPLAY =====================
st.subheader("🚦 Trading Signal")
st.write(f"### {signal} (Confidence: {confidence})")

message = f"Nifty Signal: {signal}\nPrice: {round(latest['Close'],2)}\nSupport: {round(support,2)}\nResistance: {round(resistance,2)}"

if signal == "Bullish":
    st.success("📈 Buy on dips")
elif signal == "Bearish":
    st.error("📉 Sell on rise")
else:
    st.warning("⚖️ Sideways")

# ===================== TELEGRAM BUTTON =====================
if st.button("📤 Send Signal to Telegram"):
    send_telegram(message)
    st.success("Signal sent to Telegram!")

# ===================== AUTO ALERT =====================
auto_alert = st.checkbox("Enable Auto Alerts")

if auto_alert:
    send_telegram(message)

# ===================== CHART =====================
st.subheader("📉 Price Chart")
st.line_chart(data[['Close','SMA20','SMA50']])

st.caption("⚠️ Educational purpose only. Not financial advice.")
