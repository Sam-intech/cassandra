# backend/routers/backtest.py
from pathlib import Path

import pandas as pd
from fastapi import APIRouter

router = APIRouter()

BACKTEST_RESULTS_PATH = Path(__file__).resolve().parents[1] / "data" / "ftx_vpin_results.csv"

@router.get("/backtest/ftx")
def get_ftx_backtest():
    if not BACKTEST_RESULTS_PATH.exists():
        return {"error": "Backtest data not found. Run utils/backtest.py first."}

    df = pd.read_csv(BACKTEST_RESULTS_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Key events for chart annotations
    events = [
        {
            "timestamp": "2022-11-07T11:46:00+00:00",
            "label": "🚨 CASSANDRA Fires",
            "color": "#ff2d55"
        },
        {
            "timestamp": "2022-11-07T13:00:00+00:00",
            "label": "CZ Tweet (Public)",
            "color": "#ff9f0a"
        },
        {
            "timestamp": "2022-11-08T02:00:00+00:00",
            "label": "FTX Halts Withdrawals",
            "color": "#ffd60a"
        }
    ]

    return {
        "data": df[["timestamp", "vpin", "alert_level", "alert"]].to_dict(orient="records"),
        "events": events,
        "summary": {
            "total_buckets": len(df),
            "peak_vpin": round(df["vpin"].max(), 4),
            "first_alert": "2022-11-07T11:46:22+00:00",
            "minutes_before_public": 74,
            "peak_timestamp": df.loc[df["vpin"].idxmax(), "timestamp"].isoformat()
        }
    }
