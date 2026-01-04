import os
import MetaTrader5 as mt5
import pandas as pd

# Initialize MT5
if not mt5.initialize():
    print("MT5 initialization failed")
    mt5.shutdown()
    quit()

print("MT5 initialized successfully")

# Select XAUUSD symbol
symbol = "XAUUSD"
if not mt5.symbol_select(symbol, True):
    print("XAUUSD not available")
    mt5.shutdown()
    quit()

print("XAUUSD available")

# Get last 500 M15 candles
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 500)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Create data folder safely
base_dir = os.path.dirname(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

# Save CSV (NO 'file' variable anywhere)
csv_path = os.path.join(data_dir, "xauusd_test.csv")
df.to_csv(csv_path, index=False)

print("Data saved successfully")

# Shutdown MT5
mt5.shutdown()