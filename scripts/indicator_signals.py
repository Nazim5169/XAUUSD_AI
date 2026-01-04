import pandas as pd

# Load data
import os

base_dir = os.path.dirname(os.path.dirname(__file__))
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

# Last candle
last = df.iloc[-1]

# Signal logic
signal = "HOLD"

if last["EMA_50"] > last["EMA_200"] and last["RSI"] < 70:
    signal = "BUY"
elif last["EMA_50"] < last["EMA_200"] and last["RSI"] > 30:
    signal = "SELL"

# Print output
print("XAUUSD SIGNAL")
print("--------------")
print("Price:", last["close"])
print("EMA 50:", round(last["EMA_50"], 2))
print("EMA 200:", round(last["EMA_200"], 2))
print("RSI:", round(last["RSI"], 2))
print("SIGNAL:", signal)