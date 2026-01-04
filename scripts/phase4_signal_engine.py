import os
import pandas as pd
import MetaTrader5 as mt5
from telegram import Bot
from datetime import datetime

# ==============================
# TELEGRAM CONFIG
# ==============================
API_TOKEN = "8464066633:AAHYBmtQpdJxcURhtW_pgwtzRtlr3l4yNmw"
CHAT_ID = "1271545068"
bot = Bot(token=API_TOKEN)

# ==============================
# DATA FOLDERS
# ==============================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "signals_log.csv")

# ==============================
# MT5 INIT
# ==============================
if not mt5.initialize():
    print("❌ MT5 initialization failed")
    mt5.shutdown()
    quit()
else:
    print("✅ MT5 initialized successfully")

symbol = "XAUUSD"
if not mt5.symbol_select(symbol, True):
    print("❌ XAUUSD not available")
    mt5.shutdown()
    quit()
else:
    print("✅ XAUUSD available")

# ==============================
# FETCH DATA (M15 + H1)
# ==============================
def fetch_candles(symbol, timeframe, count=500):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

df_m15 = fetch_candles(symbol, mt5.TIMEFRAME_M15)
df_h1 = fetch_candles(symbol, mt5.TIMEFRAME_H1)

# ==============================
# INDICATORS
# ==============================
def add_indicators(df):
    df["EMA_50"] = df["close"].ewm(span=50).mean()
    df["EMA_200"] = df["close"].ewm(span=200).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["high_low"] = df["high"] - df["low"]
    df["high_close"] = abs(df["high"] - df["close"].shift())
    df["low_close"] = abs(df["low"] - df["close"].shift())
    df["TR"] = df[["high_low", "high_close", "low_close"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(14).mean()
    return df

df_m15 = add_indicators(df_m15)
df_h1 = add_indicators(df_h1)

# ==============================
# SESSION FILTER
# ==============================
def get_session():
    now = datetime.utcnow()
    london = now.hour >= 7 and now.hour < 16
    newyork = now.hour >= 12 and now.hour < 21
    if london:
        return "LONDON"
    elif newyork:
        return "NEW_YORK"
    else:
        return "NO_SESSION"

current_session = get_session()
if current_session == "NO_SESSION":
    print("❌ Market closed")
    mt5.shutdown()
    quit()

# ==============================
# SIGNAL LOGIC
# ==============================
def generate_signal(df_m15, df_h1):
    last_m15 = df_m15.iloc[-1]
    last_h1 = df_h1.iloc[-1]

    signal = "HOLD"
    # Buy condition: EMA50 > EMA200 on both M15+H1 and RSI < 70
    if last_m15["EMA_50"] > last_m15["EMA_200"] and last_h1["EMA_50"] > last_h1["EMA_200"] and last_m15["RSI"] < 70:
        signal = "BUY"
    elif last_m15["EMA_50"] < last_m15["EMA_200"] and last_h1["EMA_50"] < last_h1["EMA_200"] and last_m15["RSI"] > 30:
        signal = "SELL"
    return signal, last_m15

signal, last = generate_signal(df_m15, df_h1)

# ==============================
# ATR-based SL / TP
# ==============================
atr = last["ATR"]
price = last["close"]

risk_multiplier = 1.2
reward_multiplier = 0.8

if signal == "BUY":
    entry = price
    sl = price - (atr * risk_multiplier)
    tp1 = price + (atr * reward_multiplier)
    tp2 = price + (atr * 1.2)
    tp3 = price + (atr * 1.6)
    tp4 = price + (atr * 2.0)
elif signal == "SELL":
    entry = price
    sl = price + (atr * risk_multiplier)
    tp1 = price - (atr * reward_multiplier)
    tp2 = price - (atr * 1.2)
    tp3 = price - (atr * 1.6)
    tp4 = price - (atr * 2.0)
else:
    entry = sl = tp1 = tp2 = tp3 = tp4 = None
    # ==============================
# CONFIDENCE CALCULATION
# ==============================
confidence = round(abs(last["EMA_50"] - last["EMA_200"]) / last["EMA_200"] * 100, 2)

# ==============================
# LOG SIGNAL
# ==============================
os.makedirs(LOGS_DIR, exist_ok=True)
log_dict = {
    "time": datetime.now(),
    "symbol": symbol,
    "signal": signal,
    "entry": entry,
    "sl": sl,
    "tp1": tp1,
    "tp2": tp2,
    "tp3": tp3,
    "tp4": tp4,
    "session": current_session,
    "confidence": confidence
}

log_df = pd.DataFrame([log_dict])
if os.path.exists(LOG_FILE):
    log_df.to_csv(LOG_FILE, mode="a", header=False, index=False)
else:
    log_df.to_csv(LOG_FILE, index=False)

# ==============================
# SEND TELEGRAM MESSAGE
# ==============================
if signal != "HOLD":
    message = f"""
XAUUSD {signal} NOW
Enter: {entry:.2f}
SL: {sl:.2f}
TP1: {tp1:.2f}
TP2: {tp2:.2f}
TP3: {tp3:.2f}
TP4: {tp4:.2f}
Session: {current_session}
Confidence: {confidence}%
"""
    bot.send_message(chat_id=CHAT_ID, text=message)
    print("✅ Signal sent to Telegram")
else:
    print("No trade signal")

# ==============================
# SHUTDOWN MT5
# ==============================
mt5.shutdown()