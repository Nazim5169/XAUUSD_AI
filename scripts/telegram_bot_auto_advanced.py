import MetaTrader5 as mt5
import pandas as pd
import time
from telegram import Bot

# ---------- TELEGRAM CONFIG ----------
API_TOKEN = "8464066633:AAHYBmtQpdJxcURhtW_pgwtzRtlr3l4yNmw"
CHAT_ID = "1271545068"
bot = Bot(token=API_TOKEN)

# ---------- MT5 CONNECT ----------
if not mt5.initialize():
    print("❌ MT5 not initialized")
    quit()

symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_M15

print("✅ MT5 Connected. Bot running...")

# ---------- MAIN LOOP ----------
while True:
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 300)
    df = pd.DataFrame(rates)

    df["EMA50"] = df["close"].ewm(span=50).mean()
    df["EMA200"] = df["close"].ewm(span=200).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]
    price = round(last["close"], 2)

    signal = None

    if last["EMA50"] > last["EMA200"] and last["RSI"] < 70:
        signal = "BUY"
        sl = price - 12
        tps = [price + 3, price + 7, price + 10, price + 40]

    elif last["EMA50"] < last["EMA200"] and last["RSI"] > 30:
        signal = "SELL"
        sl = price + 12
        tps = [price - 3, price - 7, price - 10, price - 40]

    if signal:
        message = (
            f"XAUUSD {signal} NOW\n\n"
            f"Entry: {price}\n"
            f"Stop Loss: {round(sl,2)}\n"
            f"TP1: {round(tps[0],2)}\n"
            f"TP2: {round(tps[1],2)}\n"
            f"TP3: {round(tps[2],2)}\n"
            f"TP4: {round(tps[3],2)}\n\n"
            f"Timeframe: M15\n"
            f"Confidence: High"
        )

        bot.send_message(chat_id=CHAT_ID, text=message)
        print("✅ Signal sent to Telegram")

        time.sleep(900)  # 15 minutes cooldown

    time.sleep(60)