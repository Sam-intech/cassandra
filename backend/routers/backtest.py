# backend/routers/backtest.py
from pathlib import Path

import pandas as pd
from fastapi import APIRouter

router = APIRouter()

BACKTEST_RESULTS_PATH = Path(__file__).resolve().parents[1] / "data" / "ftx_vpin_results.csv"
CWD_RESULTS_PATH = Path.cwd() / "data" / "ftx_vpin_results.csv"


@router.get("/backtest/ftx")
def get_ftx_backtest():
    source_path = None
    for candidate in (BACKTEST_RESULTS_PATH, CWD_RESULTS_PATH):
        if candidate.exists():
            source_path = candidate
            break

    if source_path is None:
        return {
            "error": "Backtest data not found. Run utils/backtest.py first.",
            "searched_paths": [
                str(BACKTEST_RESULTS_PATH),
                str(CWD_RESULTS_PATH),
            ],
        }

    df = pd.read_csv(source_path)
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

    chart_df = df[["timestamp", "vpin", "alert_level", "alert"]].copy()
    chart_df["timestamp"] = chart_df["timestamp"].map(lambda ts: ts.isoformat())

    return {
        "data": chart_df.to_dict(orient="records"),
        "events": events,
        "summary": {
            "total_buckets": len(df),
            "peak_vpin": round(df["vpin"].max(), 4),
            "first_alert": "2022-11-07T11:46:22+00:00",
            "minutes_before_public": 74,
            "peak_timestamp": df.loc[df["vpin"].idxmax(), "timestamp"].isoformat(),
            "source_file": str(source_path),
        },
    }
