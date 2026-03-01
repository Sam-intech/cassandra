# CASSANDRA

Real-time order-flow intelligence for crypto markets.

The system streams Binance BTCUSDT trades, computes VPIN, pushes live updates over WebSocket, and generates intelligence briefs through an autonomous agent.

## System Architecture

- `backend/` FastAPI API + Binance stream + VPIN engine + agent tooling
- `frontend/` React/Vite dashboard (live VPIN chart, stream controls, chat, briefs)
- `backend/data/` historical FTX backtest datasets

### Data Flow

1. Frontend calls `POST /stream/start`.
2. Backend opens Binance WebSocket (`aggTrade`) and processes trades.
3. VPIN buckets are computed in `VPINEngine`.
4. Backend broadcasts updates on `/ws`.
5. Frontend live chart and metrics update in real time.
6. On elevated conditions, agent tools run and publish intelligence briefs.


## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- For local non-Docker run:
  - Python 3.12+
  - Node 20+

## Environment Variables

Backend reads env vars from `backend/.env`.

Use `backend/.env.example` as a template.

Important variables:

- `AWS_REGION` (or `AWS_DEFAULT_REGION`)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (optional)

Notes:

- Agent model calls use AWS Bedrock.
- If Bedrock is unavailable/misconfigured, the app still runs and falls back to error-safe responses where implemented.

## Run Locally (Without Docker)

### Backend

From repo root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

From repo root:

```bash
cd frontend
npm ci
npm run dev -- --host 0.0.0.0 --port 5173
```

Open:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

## Run With Docker (Recommended)

### Build and Start

From repo root:

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:8080`
- Backend API: `http://localhost:8000`

### Stop

```bash
docker compose down
```

### Rebuild After Code Changes

```bash
docker compose up --build
```

## Container Layout

- `backend/Dockerfile`
  - Base: `python:3.12-slim`
  - Runs: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- `frontend/Dockerfile`
  - Build stage: `node:20-alpine` (`npm ci`, `npm run build`)
  - Runtime stage: `nginx:alpine` serving static `dist/`
- `frontend/nginx.conf`
  - SPA fallback (`try_files ... /index.html`)
- `docker-compose.yml`
  - Orchestrates backend + frontend
  - Frontend build arg `VITE_API_BASE_URL=http://localhost:8000`

## API / Stream Endpoints

Core routes:

- `GET /stream/status`
- `POST /stream/start`
- `POST /stream/stop`
- `POST /system/reset`
- `GET /backtest/ftx`
- `GET /agent/brief`
- `POST /agent/chat`
- `WS /ws`

Compatibility routes also exist under `/api/*` and `/api/v1/*`.

## Troubleshooting

### `ModuleNotFoundError: No module named 'backend'`

- Use current `backend/main.py` (import path fix already applied), or run from repo root with:
  - `uvicorn backend.main:app --reload`

### Frontend shows stream offline / websocket errors

- Confirm backend is running on `localhost:8000`.
- Start stream from UI (`start streaming`).
- Check backend logs for Binance connectivity failures.

### `404` on stream controls

- Verify backend service is reachable.
- Endpoints are available both direct and compatibility paths (`/stream/start`, `/api/stream/start`, etc.).

## Development Notes

- `.dockerignore` and `.gitignore` were expanded to keep local/build artifacts out.
- If you need local packages again after cleanup:
  - `cd frontend && npm ci`

