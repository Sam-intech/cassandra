# utils/vpin_engine.py
# CASSANDRA - VPIN Calculation Engine
# Based on Easley, Lopez de Prado & O'Hara (2012)
# "Flow Toxicity and Liquidity in a High Frequency World"

import numpy as np
import pandas as pd
from collections import deque
from dataclasses import dataclass
from datetime import datetime

# ── Configuration ─────────────────────────────────────────
# Volume bucket size: how much BTC volume fills one bucket
# We use 1.0 BTC per bucket — each bucket represents a meaningful
# chunk of market activity, not just a few small retail trades
BUCKET_SIZE_BTC = 1.0

# How many buckets we use to calculate VPIN at any moment
# 50 is the standard from the academic paper
WINDOW_SIZE = 50

# Alert threshold — above this, informed trading is likely
VPIN_ALERT_THRESHOLD = 0.7

# ── Data Structures ────────────────────────────────────────
@dataclass
class VolumeBucket:
    """
    A volume bucket is the core unit of VPIN.
    Instead of measuring time, we measure accumulated volume.
    When enough volume fills a bucket, we close it and measure
    the imbalance between buy and sell volume inside it.
    """
    bucket_id: int
    start_time: datetime
    end_time: datetime = None
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    total_volume: float = 0.0
    vpin_contribution: float = 0.0  # |buy - sell| / total

    @property
    def order_imbalance(self) -> float:
        """
        The key metric inside each bucket.
        1.0 = all volume was buy-initiated (maximum informed buying)
        0.0 = all volume was sell-initiated (maximum informed selling)
        0.5 = perfectly balanced (no informed trading signal)
        """
        if self.total_volume == 0:
            return 0.5
        return self.buy_volume / self.total_volume


# ── VPIN Engine ────────────────────────────────────────────
class VPINEngine:
    def __init__(
        self,
        bucket_size: float = BUCKET_SIZE_BTC,
        window_size: int = WINDOW_SIZE,
        alert_threshold: float = VPIN_ALERT_THRESHOLD
    ):
        self.bucket_size = bucket_size
        self.window_size = window_size
        self.alert_threshold = alert_threshold

        # Completed buckets — we keep a rolling window
        self.completed_buckets = deque(maxlen=window_size * 2)

        # Internal counters
        self._bucket_count = 0
        self._overflow_buy = 0.0
        self._overflow_sell = 0.0

        # The bucket currently being filled
        self.current_bucket = self._new_bucket()

        # Rolling VPIN history for the dashboard
        self.vpin_history = deque(maxlen=500)

    def _new_bucket(self) -> VolumeBucket:
        self._bucket_count += 1
        return VolumeBucket(
            bucket_id=self._bucket_count,
            start_time=datetime.now()
        )

    def process_trade(self, trade: dict) -> list[dict] | None:
        """
        The main entry point. Feed every trade here.
        Returns a VPIN result dict every time a bucket completes.
        Returns None if the bucket is still filling.

        A trade looks like:
        {
            "timestamp": datetime,
            "price": float,
            "quantity": float,       ← volume in BTC
            "buy_initiated": 1 or 0
        }
        """
        volume = trade["quantity"]
        is_buy = trade["buy_initiated"]

        # Add any overflow from the previous bucket first
        remaining_volume = volume + self._overflow_buy + self._overflow_sell
        self._overflow_buy = 0.0
        self._overflow_sell = 0.0

        results = []

        while remaining_volume > 0:
            # How much space is left in the current bucket?
            space_left = self.bucket_size - self.current_bucket.total_volume

            if remaining_volume <= space_left:
                # This trade fits entirely in the current bucket
                if is_buy:
                    self.current_bucket.buy_volume += remaining_volume
                else:
                    self.current_bucket.sell_volume += remaining_volume
                self.current_bucket.total_volume += remaining_volume
                remaining_volume = 0

            else:
                # This trade overflows — fill current bucket and close it
                if is_buy:
                    self.current_bucket.buy_volume += space_left
                else:
                    self.current_bucket.sell_volume += space_left
                self.current_bucket.total_volume += space_left
                remaining_volume -= space_left

                # Close this bucket
                result = self._close_bucket(trade["timestamp"])
                if result:
                    results.append(result)

                # Start a fresh bucket
                self.current_bucket = self._new_bucket()

        return results if results else None

    def _close_bucket(self, timestamp: datetime) -> dict:
        """
        Closes the current bucket, calculates its contribution,
        and computes the new rolling VPIN score.
        """
        bucket = self.current_bucket
        bucket.end_time = timestamp
        bucket.vpin_contribution = (
            abs(bucket.buy_volume - bucket.sell_volume) / bucket.total_volume
            if bucket.total_volume > 0 else 0
        )

        self.completed_buckets.append(bucket)

        # We need at least window_size buckets to compute VPIN
        if len(self.completed_buckets) < self.window_size:
            return None

        # VPIN = average order imbalance over the last N buckets
        recent_buckets = list(self.completed_buckets)[-self.window_size:]
        vpin_score = np.mean([b.vpin_contribution for b in recent_buckets])

        result = {
            "timestamp": timestamp,
            "vpin": round(float(vpin_score), 4),
            "bucket_id": bucket.bucket_id,
            "buy_volume": round(bucket.buy_volume, 6),
            "sell_volume": round(bucket.sell_volume, 6),
            "order_imbalance": round(bucket.order_imbalance, 4),
            "alert": vpin_score >= self.alert_threshold,
            "alert_level": self.classify_alert(vpin_score)
        }

        self.vpin_history.append(result)
        return result

    def classify_alert(self, vpin: float | None) -> str:
        """
        Human-readable classification of the VPIN score.
        These thresholds are calibrated to crypto market conditions.
        """
        if vpin is None:
            return "NORMAL"
        if vpin >= 0.85:
            return "CRITICAL"    # Extreme informed trading detected
        elif vpin >= 0.75:
            return "HIGH"        # Strong signal — high conviction
        elif vpin >= 0.65:
            return "ELEVATED"    # Worth watching
        elif vpin >= 0.50:
            return "MODERATE"    # Normal elevated activity
        else:
            return "NORMAL"      # Healthy balanced flow

    def get_current_vpin(self) -> float:
        """Returns the most recent VPIN score."""
        if self.vpin_history:
            return self.vpin_history[-1]["vpin"]
        return None

    def get_vpin_dataframe(self) -> pd.DataFrame:
        """Returns full VPIN history as a DataFrame for the dashboard."""
        if not self.vpin_history:
            return pd.DataFrame()
        return pd.DataFrame(list(self.vpin_history))
