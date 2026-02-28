# backend/routers/streams.py
import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.state import app_state
from backend.utils.binance_stream import stream_trades

router = APIRouter()

def _remove_client(client: WebSocket) -> None:
    if client in app_state.ws_clients:
        app_state.ws_clients.remove(client)


async def _broadcast(payload: str) -> None:
    disconnected_clients: list[WebSocket] = []
    for client in list(app_state.ws_clients):
        try:
            await client.send_text(payload)
        except Exception:
            disconnected_clients.append(client)

    for client in disconnected_clients:
        _remove_client(client)


async def _broadcast_message(message_type: str, data: Any) -> None:
    payload = json.dumps({"type": message_type, "data": data}, default=str)
    await _broadcast(payload)


def _should_trigger_agent(result: dict) -> bool:
    return result["alert"] and result["vpin"] > app_state.last_alert_vpin + 0.02


async def trigger_agent(result: dict) -> None:
    """Run the agent in the background without blocking the stream callback."""
    try:
        vpin_history = list(app_state.vpin_engine.vpin_history)
        brief = await asyncio.to_thread(
            app_state.agent.run,
            vpin_score=result["vpin"],
            alert_level=result["alert_level"],
            vpin_history=vpin_history,
        )
        app_state.latest_brief = brief
        await _broadcast_message("intelligence_brief", brief)
    except Exception as exc:
        print(f"[CASSANDRA] Agent error: {exc}")


# ── Background stream task ─────────────────────────────────
async def binance_stream_task() -> None:
    """
    Runs forever in the background.
    Processes every trade, computes VPIN, and broadcasts bucket updates.
    """
    async def on_trade(trade: dict) -> None:
        app_state.trade_count += 1
        app_state.latest_price = trade["price"]

        results = app_state.vpin_engine.process_trade(trade)
        if not results:
            return

        for result in results:
            await _broadcast_message(
                "vpin_update",
                {
                    "timestamp": result["timestamp"].isoformat(),
                    "vpin": result["vpin"],
                    "alert_level": result["alert_level"],
                    "alert": result["alert"],
                    "buy_volume": result["buy_volume"],
                    "sell_volume": result["sell_volume"],
                    "order_imbalance": result["order_imbalance"],
                    "bucket_id": result["bucket_id"],
                    "trade_count": app_state.trade_count,
                    "latest_price": app_state.latest_price,
                },
            )

            if _should_trigger_agent(result):
                app_state.last_alert_vpin = result["vpin"]
                asyncio.create_task(trigger_agent(result))

    await stream_trades(callback=on_trade)


# ── WebSocket endpoint ─────────────────────────────────────
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    app_state.ws_clients.append(websocket)
    print(f"[CASSANDRA] Client connected. Total: {len(app_state.ws_clients)}")

    # Send current state immediately on connect
    vpin_df = app_state.vpin_engine.get_vpin_dataframe()
    if not vpin_df.empty:
        history = vpin_df.tail(100).to_dict(orient="records")
        await websocket.send_text(
            json.dumps({"type": "history", "data": history}, default=str)
        )

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("[CASSANDRA] Client disconnected.")
    finally:
        _remove_client(websocket)


# ── Stream status endpoint ─────────────────────────────────
@router.get("/stream/status")
def stream_status():
    return {
        "streaming": app_state.streaming,
        "trade_count": app_state.trade_count,
        "latest_price": app_state.latest_price,
        "current_vpin": app_state.vpin_engine.get_current_vpin(),
        "connected_clients": len(app_state.ws_clients)
    }
