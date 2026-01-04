import os
import time
import pandas as pd
import MetaTrader5 as mt5
from telegram import Bot
from datetime import datetime

# ================= TELEGRAM =================
API_TOKEN = "8464066633:AAHYBmtQpdJxcURhtW_pgwtzRtlr3l4yNmw"
CHAT_IDS = ["1271545068"]
bot = Bot(token=API_TOKEN)

# ================= PATHS =================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "xauusd_test.csv")
HISTORY_PATH = os.path.join(BASE_DIR, "data", "signals_history.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "error.log")
LAST_SIGNAL_FILE = os.path.join(BASE_DIR, "data", "last_signal.txt")

os.makedirs(LOG_DIR, exist_ok=True)

def log_error(err):
    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.now()} | {err}\n")

def run_bot():
    try:
        if not mt5.initialize():
            raise Exception("MT5 initialization failed")

        symbol = "XAUUSD"
        mt5.symbol_select(symbol, True)

        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 500)
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.to_csv(DATA_PATH, index=False)

        # Indicators
        df["EMA50"] = df["close"].ewm(span=50).mean()
        df["EMA200"] = df["close"].ewm(span=200).mean()

        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + rs))

        # ATR
        df["H-L"] = df["high"] - df["low"]
        df["H-C"] = abs(df["high"] - df["close"].shift())
        df["L-C"] = abs(df["low"] - df["close"].shift())
        df["TR"] = df[["H-L", "H-C", "L-C"]].max(axis=1)
        df["ATR"] = df["TR"].rolling(14).mean()

        last = df.iloc[-1]

        # Signal logic
        signal = "HOLD"
        if last["EMA50"] > last["EMA200"] and last["RSI"] < 70:
            signal = "BUY"
        elif last["EMA50"] < last["EMA200"] and last["RSI"] > 30:
            signal = "SELL"

        if os.path.exists(LAST_SIGNAL_FILE):
            with open(LAST_SIGNAL_FILE, "r") as f:
                if f.read() == signal:
                    mt5.shutdown()
                    return

        with open(LAST_SIGNAL_FILE, "w") as f:
            f.write(signal)

        entry = last["close"]
        atr = last["ATR"]

        if signal == "BUY":
            sl = entry - (1.5 * atr)
            tp1 = entry + (0.5 * atr)
            tp2 = entry + (1.0 * atr)
            tp3 = entry + (1.5 * atr)
            tp4 = entry + (2.5 * atr)
        elif signal == "SELL":
            sl = entry + (1.5 * atr)
            tp1 = entry - (0.5 * atr)
            tp2 = entry - (1.0 * atr)
            tp3 = entry - (1.5 * atr)
            tp4 = entry - (2.5 * atr)
        else:
            mt5.shutdown()
            return

        message = (
            f"🔥 XAUUSD {signal}\n\n"
            f"Entry: {entry:.2f}\n"
            f"SL: {sl:.2f}\n\n"
            f"TP1: {tp1:.2f}\n"
            f"TP2: {tp2:.2f}\n"
            f"TP3: {tp3:.2f}\n"
            f"TP4: {tp4:.2f}\n\n"
            f"⏱ Timeframe: M15"
        )

        for chat in CHAT_IDS:
            bot.send_message(chat_id=chat, text=message)

        pd.DataFrame([{
            "time": datetime.now(),
            "signal": signal,
            "entry": entry,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "tp4": tp4
        }]).to_csv(HISTORY_PATH, mode="a", header=not os.path.exists(HISTORY_PATH), index=False)

        mt5.shutdown()

    except Exception as e:
        log_error(e)

print("🚀 PHASE 3 PRO BOT STARTED")
while True:
    run_bot()
    time.sleep(900)