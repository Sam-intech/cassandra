# utils/binance_stream.py
# CASSANDRA - Binance WebSocket Trade Stream
# Connects to Binance and streams every BTC/USDT trade in real time

import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime
from collections import deque

# ── Configuration ─────────────────────────────────────────
SYMBOL = "btcusdt"
STREAM_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@aggTrade"

# We keep a rolling window of the last 10,000 trades in memory
# This is our live working dataset for VPIN calculation
MAX_TRADES = 10_000
trade_buffer = deque(maxlen=MAX_TRADES)

# ── Trade Parser ───────────────────────────────────────────
def parse_trade(raw_message: str) -> dict:
    """
    Binance sends each trade as a JSON string.
    We extract only what VPIN needs:
      - timestamp
      - price
      - quantity (volume)
      - is_buyer_maker: True means the SELLER was the aggressor
                        False means the BUYER was the aggressor
    """
    data = json.loads(raw_message)
    
    return {
        "timestamp": datetime.fromtimestamp(data["T"] / 1000),
        "price": float(data["p"]),
        "quantity": float(data["q"]),
        # If buyer is maker, the aggressive side was the SELLER
        # We store 1 for buy-aggressor, 0 for sell-aggressor
        "buy_initiated": 0 if data["m"] else 1
    }

# ── Main Stream Function ───────────────────────────────────
async def stream_trades(callback=None):
    """
    Opens a persistent WebSocket connection to Binance.
    Every trade fires the callback function with parsed trade data.
    This runs forever until you stop the program.
    """
    print(f"[CASSANDRA] Connecting to Binance stream: {SYMBOL.upper()}")
    
    async with websockets.connect(STREAM_URL) as ws:
        print(f"[CASSANDRA] Stream active. Listening for trades...")
        
        async for message in ws:
            trade = parse_trade(message)
            trade_buffer.append(trade)
            
            # If a callback function is provided, call it with each trade
            # This is how the VPIN engine will hook into this stream
            if callback:
                await callback(trade)

# ── Buffer Access ──────────────────────────────────────────
def get_trade_dataframe() -> pd.DataFrame:
    """
    Returns the current trade buffer as a pandas DataFrame.
    The VPIN engine will call this to get fresh data.
    """
    if not trade_buffer:
        return pd.DataFrame()
    return pd.DataFrame(list(trade_buffer))

# ── Test Runner ────────────────────────────────────────────
async def test_stream():
    """
    Prints the first 5 trades then stops.
    Run this file directly to confirm data is flowing.
    """
    count = 0
    
    async def print_trade(trade):
        nonlocal count
        count += 1
        side = "BUY  🟢" if trade["buy_initiated"] else "SELL 🔴"
        print(f"[{trade['timestamp']}] {side} | "
              f"Price: ${trade['price']:,.2f} | "
              f"Volume: {trade['quantity']:.6f} BTC")
        if count >= 10:
            raise KeyboardInterrupt
    
    await stream_trades(callback=print_trade)

if __name__ == "__main__":
    try:
        asyncio.run(test_stream())
    except KeyboardInterrupt:
        print("\n[CASSANDRA] Stream stopped.")