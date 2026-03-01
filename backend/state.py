# backend/state.py
# Shared application state — one instance, accessed by all routers

import asyncio

from backend.agent.cassandra_agent import CassandraAgent
from backend.utils.vpin_engine import VPINEngine

class AppState:
    def __init__(self):
        self.bucket_size = 1.0
        self.window_size = 50
        self.alert_threshold = 0.7
        self.vpin_engine = VPINEngine(
            bucket_size=self.bucket_size,
            window_size=self.window_size,
            alert_threshold=self.alert_threshold,
        )
        self.agent = CassandraAgent()
        self.trade_count = 0
        self.latest_price = 0.0
        self.latest_brief: dict | None = None
        self.last_alert_vpin = 0.0
        self.streaming = False
        self.stream_task: asyncio.Task | None = None
        # Connected WebSocket clients
        self.ws_clients: list = []

    def reset_runtime(self) -> None:
        self.vpin_engine = VPINEngine(
            bucket_size=self.bucket_size,
            window_size=self.window_size,
            alert_threshold=self.alert_threshold,
        )
        self.trade_count = 0
        self.latest_price = 0.0
        self.latest_brief = None
        self.last_alert_vpin = 0.0
        if hasattr(self.agent, "reset_memory"):
            self.agent.reset_memory()

# Single global instance
app_state = AppState()
