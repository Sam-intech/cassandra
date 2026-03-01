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
    if not result["alert"]:
        return False

    if result["vpin"] > app_state.last_alert_vpin + 0.02:
        return True

    recent = list(app_state.vpin_engine.vpin_history)[-3:]
    return len(recent) == 3 and all(item.get("alert") for item in recent)


async def start_streaming_task() -> bool:
    task = app_state.stream_task
    if app_state.streaming and task is not None and not task.done():
        return False

    app_state.streaming = True
    app_state.stream_task = asyncio.create_task(binance_stream_task())
    print("[CASSANDRA] Binance stream started.")
    return True


async def stop_streaming_task() -> bool:
    was_streaming = app_state.streaming
    app_state.streaming = False

    task = app_state.stream_task
    if task is not None and not task.done():
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        print("[CASSANDRA] Binance stream stopped.")

    app_state.stream_task = None
    return was_streaming


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


@router.get("/streaming/status")
def stream_status_legacy():
    return stream_status()


@router.get("/streams/status")
def stream_status_legacy_alt():
    return stream_status()


@router.post("/stream/start")
async def start_stream():
    started = await start_streaming_task()
    return {
        "started": started,
        "streaming": app_state.streaming,
    }


@router.post("/stream/resume")
async def resume_stream():
    return await start_stream()


@router.post("/streaming/start")
async def start_stream_legacy():
    return await start_stream()


@router.post("/streams/start")
async def start_stream_legacy_alt():
    return await start_stream()


@router.post("/start-stream")
async def start_stream_legacy_dash():
    return await start_stream()


@router.post("/start_stream")
async def start_stream_legacy_snake():
    return await start_stream()


@router.post("/stream/stop")
async def stop_stream():
    stopped = await stop_streaming_task()
    return {
        "stopped": stopped,
        "streaming": app_state.streaming,
    }


@router.post("/streaming/stop")
async def stop_stream_legacy():
    return await stop_stream()


@router.post("/streams/stop")
async def stop_stream_legacy_alt():
    return await stop_stream()


@router.post("/stop-stream")
async def stop_stream_legacy_dash():
    return await stop_stream()


@router.post("/stop_stream")
async def stop_stream_legacy_snake():
    return await stop_stream()


@router.post("/system/reset")
async def reset_system(start_stream: bool = False):
    await stop_streaming_task()
    app_state.reset_runtime()

    if start_stream:
        await start_streaming_task()

    await _broadcast_message(
        "system_reset",
        {
            "streaming": app_state.streaming,
            "trade_count": app_state.trade_count,
            "latest_price": app_state.latest_price,
            "current_vpin": app_state.vpin_engine.get_current_vpin(),
        },
    )

    return {
        "reset": True,
        "streaming": app_state.streaming,
    }


@router.post("/reset")
async def reset_system_legacy(start_stream: bool = False):
    return await reset_system(start_stream=start_stream)
