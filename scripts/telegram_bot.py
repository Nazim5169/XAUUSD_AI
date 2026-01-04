import os
import pandas as pd
from telegram import Bot

# --- TELEGRAM SETUP ---
API_TOKEN = "8464066633:AAHYBmtQpdJxcURhtW_pgwtzRtlr3l4yNmw"
CHAT_ID = "1271545068"  # Replace with your actual Telegram chat ID
bot = Bot(token=API_TOKEN)

# --- LOAD XAUUSD DATA AND CALCULATE SIGNAL ---
base_dir = os.path.dirname(os.path.dirname(__file__))  # FIXED here!
csv_path = os.path.join(base_dir, "data", "xauusd_test.csv")
df = pd.read_csv(csv_path)

# EMA indicators
df["EMA_50"] = df["close"].ewm(span=50).mean()
df["EMA_200"] = df["close"].ewm(span=200).mean()

# RSI calculation
delta = df["close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()
rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))

# Latest candle
last = df.iloc[-1]

# Signal logic
signal = "HOLD"
if last["EMA_50"] > last["EMA_200"] and last["RSI"] < 70:
    signal = "BUY"
elif last["EMA_50"] < last["EMA_200"] and last["RSI"] > 30:
    signal = "SELL"

# --- SEND TELEGRAM MESSAGE ---
message = f"XAUUSD SIGNAL\nPrice: {last['close']}\nEMA50: {last['EMA_50']:.2f}\nEMA200: {last['EMA_200']:.2f}\nRSI: {last['RSI']:.2f}\nSIGNAL: {signal}"
bot.send_message(chat_id=CHAT_ID, text=message)

print("✅ Signal sent to Telegram")