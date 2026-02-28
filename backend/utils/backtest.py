# utils/backtest.py
# CASSANDRA - Historical Backtest Engine
# Replays the FTX collapse (Nov 6-9, 2022) through the VPIN engine
# to find the exact moment the signal fired before the crash became public

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
from utils.vpin_engine import VPINEngine

# ── Binance Historical Data Fetcher ───────────────────────
def fetch_historical_trades(
    symbol: str,
    start_time: datetime,
    end_time: datetime,
    max_records: int = 500_000
) -> pd.DataFrame:
    """
    Fetches historical aggregate trades from Binance REST API.
    Free, no API key required.
    Returns a DataFrame identical in structure to our live stream.
    """
    url = "https://api.binance.com/api/v3/aggTrades"

    # Convert datetime to millisecond timestamps
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    all_trades = []
    current_start = start_ms
    request_count = 0

    print(f"[CASSANDRA] Fetching historical data: {start_time.date()} to {end_time.date()}")

    while current_start < end_ms and len(all_trades) < max_records:
        params = {
            "symbol": symbol,
            "startTime": current_start,
            "endTime": min(current_start + 3_600_000, end_ms),  # 1 hour chunks
            "limit": 1000
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"[CASSANDRA] API error: {response.status_code}")
            break

        trades = response.json()

        if not trades:
            current_start += 3_600_000
            continue

        for t in trades:
            all_trades.append({
                "timestamp": datetime.fromtimestamp(t["T"] / 1000, tz=timezone.utc),
                "price": float(t["p"]),
                "quantity": float(t["q"]),
                "buy_initiated": 0 if t["m"] else 1
            })

        current_start = trades[-1]["T"] + 1
        request_count += 1

        # Progress update every 10 requests
        if request_count % 10 == 0:
            print(f"[CASSANDRA] Fetched {len(all_trades):,} trades... "
                  f"({datetime.fromtimestamp(current_start/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')})")

        # Respect Binance rate limits
        time.sleep(0.1)

    df = pd.DataFrame(all_trades)
    print(f"[CASSANDRA] Total trades fetched: {len(df):,}")
    return df


# ── Backtest Runner ────────────────────────────────────────
def run_backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replays all historical trades through the VPIN engine.
    Returns a DataFrame of all VPIN readings with timestamps.
    """
    engine = VPINEngine(
        bucket_size=5.0,   # Larger buckets for historical — 50 BTC per bucket
        window_size=50,
        alert_threshold=0.55
    )

    results = []
    total = len(df)

    print(f"\n[CASSANDRA] Running VPIN backtest on {total:,} trades...")

    for i, trade in df.iterrows():
        vpin_results = engine.process_trade(trade.to_dict())

        if vpin_results:
            for r in vpin_results:
                results.append(r)

        # Progress update
        if i % 50000 == 0 and i > 0:
            pct = (i / total) * 100
            current_vpin = engine.get_current_vpin()
            print(f"[CASSANDRA] Progress: {pct:.1f}% | "
                  f"Buckets: {len(results)} | "
                  f"Current VPIN: {current_vpin}")

    result_df = pd.DataFrame(results)
    print(f"\n[CASSANDRA] Backtest complete. {len(result_df)} VPIN readings generated.")
    return result_df


# ── Key Events Timeline ────────────────────────────────────
FTX_EVENTS = {
    "2022-11-06 22:00": "CoinDesk publishes Alameda balance sheet leak",
    "2022-11-07 13:00": "CZ tweets Binance selling all FTT holdings",
    "2022-11-08 02:00": "FTX halts withdrawals",
    "2022-11-08 22:00": "Binance signs LOI to acquire FTX",
    "2022-11-09 12:00": "Binance walks away from FTX acquisition",
    "2022-11-11 04:00": "FTX files for bankruptcy",
}


# ── Analysis ───────────────────────────────────────────────
def analyse_results(result_df: pd.DataFrame) -> dict:
    """
    Finds the key VPIN signal moments relative to FTX events.
    This is your demo's killer insight.
    """
    if result_df.empty:
        return {}

    result_df["timestamp"] = pd.to_datetime(result_df["timestamp"])

    # Find first VPIN breach above 0.7
    alerts = result_df[result_df["vpin"] >= 0.7]
    first_alert = alerts.iloc[0] if not alerts.empty else None

    # Find peak VPIN
    peak_idx = result_df["vpin"].idxmax()
    peak = result_df.iloc[peak_idx]

    # CZ tweet timestamp — the public "moment of knowledge"
    cz_tweet = pd.Timestamp("2022-11-07 13:00:00", tz="UTC")

    analysis = {
        "total_buckets": len(result_df),
        "peak_vpin": round(peak["vpin"], 4),
        "peak_timestamp": peak["timestamp"],
        "first_alert_timestamp": first_alert["timestamp"] if first_alert is not None else None,
        "first_alert_vpin": round(first_alert["vpin"], 4) if first_alert is not None else None,
    }

    if first_alert is not None:
        first_alert_ts = pd.Timestamp(first_alert["timestamp"])
        if first_alert_ts.tzinfo is None:
            first_alert_ts = first_alert_ts.tz_localize("UTC")
        minutes_before = (cz_tweet - first_alert_ts).total_seconds() / 60
        analysis["minutes_before_public"] = round(minutes_before, 0)
        if minutes_before > 0:
            print(f"\n🚨 [CASSANDRA] SIGNAL FIRED {minutes_before:.0f} MINUTES "
                  f"BEFORE CZ'S PUBLIC TWEET")

    return analysis


# ── Main ───────────────────────────────────────────────────
if __name__ == "__main__":

    # FTX collapse window: Nov 6 to Nov 9, 2022
    start = datetime(2022, 11, 7, 11, 30, 0, tzinfo=timezone.utc)
    end   = datetime(2022, 11, 8, 12, 0, 0, tzinfo=timezone.utc)

    # Step 1: Fetch data
    df = fetch_historical_trades("BTCUSDT", start, end)

    # Step 2: Save raw data so we don't have to re-fetch
    df.to_csv("data/ftx_collapse_trades.csv", index=False)
    print("[CASSANDRA] Raw data saved to data/ftx_collapse_trades.csv")

    # Step 3: Run backtest
    result_df = run_backtest(df)

    # Step 4: Save results
    result_df.to_csv("data/ftx_vpin_results.csv", index=False)
    print("[CASSANDRA] VPIN results saved to data/ftx_vpin_results.csv")

    # Step 5: Analyse
    analysis = analyse_results(result_df)

    print("\n" + "="*60)
    print("CASSANDRA — FTX COLLAPSE BACKTEST RESULTS")
    print("="*60)
    for key, value in analysis.items():
        print(f"  {key:<35} {value}")
    print("="*60)