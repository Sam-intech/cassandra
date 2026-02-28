# backend/state.py
# Shared application state — one instance, accessed by all routers

from backend.agent.cassandra_agent import CassandraAgent
from backend.utils.vpin_engine import VPINEngine

class AppState:
    def __init__(self):
        self.vpin_engine = VPINEngine(
            bucket_size=1.0,
            window_size=50,
            alert_threshold=0.7
        )
        self.agent = CassandraAgent()
        self.trade_count = 0
        self.latest_price = 0.0
        self.latest_brief: dict | None = None
        self.last_alert_vpin = 0.0
        self.streaming = False
        # Connected WebSocket clients
        self.ws_clients: list = []

# Single global instance
app_state = AppState()
