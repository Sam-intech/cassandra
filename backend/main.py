# backend/main.py
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import agent, backtest, streams
from backend.routers.streams import binance_stream_task
from backend.state import app_state

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Binance stream on app startup
    app_state.streaming = True
    stream_task = asyncio.create_task(binance_stream_task())
    print("[CASSANDRA] Binance stream started.")
    yield
    # Cleanup on shutdown
    app_state.streaming = False
    stream_task.cancel()
    await asyncio.gather(stream_task, return_exceptions=True)
    print("[CASSANDRA] Stream stopped.")

app = FastAPI(
    title="CASSANDRA API",
    description="Real-Time Order Flow Intelligence for Crypto Markets",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(streams.router)
app.include_router(backtest.router)
app.include_router(agent.router)

@app.get("/")
def root():
    return {"system": "CASSANDRA", "status": "operational"}
