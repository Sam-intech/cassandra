# utils/test_vpin.py
# Feeds simulated trades into the VPIN engine to verify it calculates correctly

import asyncio
import os
import sys

# Ensure project root is on sys.path so `utils` can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from utils.binance_stream import stream_trades
from utils.vpin_engine import VPINEngine

engine = VPINEngine()
trade_count = 0
bucket_count = 0

async def on_trade(trade):
    global trade_count, bucket_count

    trade_count += 1
    results = engine.process_trade(trade)

    if results:
        for result in results:
            bucket_count += 1
            alert_emoji = "🚨" if result["alert"] else "✅"
            print(
                f"{alert_emoji} Bucket #{result['bucket_id']:04d} | "
                f"VPIN: {result['vpin']:.4f} | "
                f"Level: {result['alert_level']:<10} | "
                f"Imbalance: {result['order_imbalance']:.4f} | "
                f"Trades processed: {trade_count}"
            )

    # Stop after 20 completed buckets
    if bucket_count >= 20:
        raise KeyboardInterrupt

async def main():
    print("[CASSANDRA] VPIN Engine Test — waiting for buckets to fill...")
    print(f"[CASSANDRA] Bucket size: 1.0 BTC | Window: 50 buckets\n")
    await stream_trades(callback=on_trade)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[CASSANDRA] Test complete.")
        print(f"Current VPIN: {engine.get_current_vpin()}")