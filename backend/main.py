# backend/main.py
import os
import sys

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure absolute imports like `from backend...` work when running
# `uvicorn main:app` from within the `backend` directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.routers import agent, backtest, streams
from backend.routers.streams import stop_streaming_task
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do not auto-start stream; wait for explicit API call from frontend.
    yield
    # Cleanup on shutdown
    await stop_streaming_task()

app = FastAPI(
    title="CASSANDRA API",
    description="Real-Time Order Flow Intelligence for Crypto Markets",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(streams.router)
app.include_router(backtest.router)
app.include_router(agent.router)

# Compatibility routes (same endpoints under /api/*)
app.include_router(streams.router, prefix="/api")
app.include_router(backtest.router, prefix="/api")
app.include_router(agent.router, prefix="/api")

# Compatibility routes for deployments using versioned API prefixes.
app.include_router(streams.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"system": "CASSANDRA", "status": "operational"}
