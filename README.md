# ◈ CASSANDRA
### Real-Time Order Flow Intelligence for Crypto Markets

> *"Cassandra always told the truth. The tragedy wasn't the signal — it was the silence around it. We built the system that listens."*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-cassandra.samintech.dev-blueviolet?style=for-the-badge)](https://cassandra.samintech.dev)
[![Built with Mistral](https://img.shields.io/badge/Mistral%20AI-AWS%20Bedrock-orange?style=for-the-badge)](https://mistral.ai)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge)](https://react.dev)

---

## The Signal Was There 74 Minutes Before FTX Collapsed. Nobody Was Watching.

On November 7th, 2022, FTX — one of the largest crypto exchanges in the world — began its collapse. Billions were lost. Millions of users were blindsided.

But the signal was already there. Hidden in the order flow. Invisible to the naked eye.

CASSANDRA detected it at **11:46 UTC**. CZ's public tweet came at **13:00 UTC**.

**74 minutes of advance warning. In the data. Waiting to be read.**

---

## What Is CASSANDRA?

CASSANDRA is a real-time market intelligence system that monitors **order flow toxicity** in crypto markets using the **VPIN metric** (Volume-Synchronized Probability of Informed Trading), augmented by a **multi-model Mistral AI agent** that autonomously investigates anomalies and generates professional intelligence briefs.

When informed traders enter the market — insiders, whales, institutions acting on non-public information — they leave a measurable fingerprint in the order flow. CASSANDRA reads that fingerprint in real time, before price moves.

---

## Live Demo

**[cassandra.samintech.dev](https://cassandra.samintech.dev)**

---

## Key Features

- **Real-Time VPIN Engine** — Streams every BTC/USDT trade from Binance via WebSocket and computes order flow toxicity using volume-synchronized buckets
- **Autonomous AI Agent** — Two-model Mistral pipeline (Mixtral 8x7B for triage, Mistral Large for deep analysis) that autonomously selects tools, investigates anomalies, and generates intelligence briefs
- **Live Intelligence Briefs** — Structured professional reports synthesising market data, funding rates, news, and VPIN pattern analysis
- **Natural Language Interface** — Ask CASSANDRA anything about current market conditions in plain English
- **Professional Dashboard** — Real-time React frontend with live charts, alert system, and chat interface

---

## Architecture

```
Binance WebSocket (BTC/USDT)
         │
         ▼
VPIN Calculation Engine
  ├── Volume bucket accumulation
  ├── Order flow imbalance measurement  
  └── Rolling 50-bucket VPIN score
         │
         ▼
Anomaly Detection (threshold breach)
         │
         ▼
Mistral Multi-Agent System
  ├── TriageAgent (Mixtral 8x7B)
  │   ├── Tool: fetch_market_data
  │   ├── Tool: fetch_funding_rate
  │   ├── Tool: fetch_crypto_news
  │   └── Tool: analyse_vpin_pattern
  └── AnalystAgent (Mistral Large)
      └── Intelligence Brief Generation
         │
         ▼
FastAPI Backend (WebSocket broadcast)
         │
         ▼
React Frontend (Live Dashboard)
```

---

## The Science Behind VPIN

CASSANDRA implements the VPIN metric from the seminal academic paper:

> **Easley, D., López de Prado, M., & O'Hara, M. (2012).** *"Flow Toxicity and Liquidity in a High Frequency World."* Review of Financial Studies, 25(5), 1457–1493.

**How it works:**

Instead of measuring time, VPIN measures accumulated volume. Trading activity is divided into *volume buckets* — each bucket represents a fixed quantity of BTC traded. Within each bucket, the algorithm estimates what fraction of volume was buy-initiated versus sell-initiated using trade aggressor flags.

```
VPIN = (1/n) × Σ |Buy_Volume_i - Sell_Volume_i| / Total_Volume_i
```

When informed traders act — because they know something the market doesn't — they trade aggressively on one side. This creates extreme order imbalance within buckets. VPIN captures this imbalance as a probability score between 0 and 1.

**Score interpretation:**
| VPIN Score | Alert Level | Interpretation |
|------------|-------------|----------------|
| 0.00 – 0.50 | NORMAL | Balanced, healthy market flow |
| 0.50 – 0.65 | MODERATE | Slightly elevated activity |
| 0.65 – 0.75 | ELEVATED | Worth monitoring closely |
| 0.75 – 0.85 | HIGH | Strong informed trading signal |
| 0.85 – 1.00 | CRITICAL | Extreme order flow toxicity |

---

## The AI Agent

CASSANDRA's intelligence layer is a two-stage autonomous agent built on Mistral models via AWS Bedrock.

**Stage 1 — Triage (Mixtral 8x7B)**
When VPIN crosses the alert threshold, Mixtral rapidly assesses the situation and selects which investigative tools to deploy based on the signal characteristics. It chooses between investigation paths — liquidity crisis vs. informed accumulation — and executes tool calls accordingly.

**Stage 2 — Analysis (Mistral Large)**
Mistral Large receives all tool outputs and synthesises them into a structured professional intelligence brief covering situation assessment, corroborating signals, pattern classification, risk assessment, and recommended actions.

**Tools available to the agent:**
- `fetch_market_data` — Live price, volume, spread from Binance
- `fetch_funding_rate` — Perpetual futures funding rate and leverage positioning
- `fetch_crypto_news` — Latest headlines from CryptoPanic
- `analyse_vpin_pattern` — Statistical trend analysis and historical crisis comparison

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Source | Binance WebSocket API (free, real-time) |
| VPIN Engine | Python, NumPy, Pandas |
| AI Models | Mistral Large 2402, Mixtral 8x7B via AWS Bedrock |
| Backend | FastAPI, WebSockets, Uvicorn |
| Frontend | React, TailwindCSS, Recharts |
| Containerisation | Docker, Docker Compose |
| Deployment | Railway |
| Domain | Namecheap + Netlify DNS |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional)
- AWS account with Bedrock access
- Mistral models enabled in AWS Bedrock (us-east-1)

### Environment Variables

Create a `.env` file in the project root:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_SESSION_TOKEN=your_session_token        # only for temporary credentials
AWS_REGION=us-east-1
CRYPTOPANIC_API_KEY=your_cryptopanic_key    # optional, free tier available
```

### Run with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Sam-intech/cassandra.git
cd cassandra

# Start everything
docker-compose up --build

# Access the dashboard
open http://localhost:80
```

### Run Manually

**Backend:**
```bash
cd cassandra
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`

### Generate the FTX Backtest Data

```bash
python backend/utils/backtest.py
```

This fetches historical Binance data and generates `data/ftx_vpin_results.csv`. Required for the backtest chart.

---

## Project Structure

```
cassandra/
├── backend/
│   ├── main.py                    ← FastAPI application
│   ├── state.py                   ← Shared application state
│   ├── agent/
│   │   └── cassandra_agent.py     ← Mistral AI agent (triage + analysis)
│   ├── routers/
│   │   ├── streams.py             ← WebSocket + Binance stream
│   │   ├── backtest.py            ← Historical data endpoints
│   │   └── agent.py               ← AI agent endpoints
│   ├── utils/
│   │   ├── vpin_engine.py         ← VPIN calculation engine
│   │   ├── binance_stream.py      ← Binance WebSocket client
│   │   └── backtest.py            ← Historical backtest runner
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                ← Main dashboard layout
│   │   ├── components/
│   │   │   ├── MetricsBar.jsx     ← Live metrics display
│   │   │   ├── LiveChart.jsx      ← Real-time VPIN chart
│   │   │   ├── BacktestChart.jsx  ← FTX historical chart
│   │   │   ├── IntelligenceBrief.jsx ← AI brief display
│   │   │   └── ChatInterface.jsx  ← Natural language interface
│   │   ├── hooks/
│   │   │   ├── useVpinStream.js   ← WebSocket connection
│   │   │   ├── useAgentChat.js    ← Chat state management
│   │   │   ├── useBacktestData.js ← Historical data fetching
│   │   │   └── useStreamStatus.js ← Stream status polling
│   │   └── lib/
│   │       ├── api.js             ← API client
│   │       ├── format.js          ← Display formatters
│   │       └── chart.js           ← Chart utilities
│   ├── nginx.conf
│   └── Dockerfile
├── data/
│   └── ftx_vpin_results.csv       ← Generated by backtest
├── docker-compose.yml
└── .env                           ← Never commit this
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | System health check |
| `GET /stream/status` | GET | Current stream and VPIN status |
| `GET /backtest/ftx` | GET | FTX collapse backtest data |
| `GET /agent/brief` | GET | Latest intelligence brief |
| `POST /agent/chat` | POST | Natural language market query |
| `WS /ws` | WebSocket | Real-time VPIN stream |

---

## Hackathon

Built for the **Mistral AI Worldwide Hackathon 2026** — Track: Mistral AI.

*Build anything with the Mistral API. Create agents, tools, products, experiments — no constraints, just ship something ambitious, creative, and impactful.*

**Track:** Mistral AI
**Models used:** Mistral Large 2402, Mixtral 8x7B Instruct (via AWS Bedrock)

---

## Author

**Samuel Sonowo**
[samintech.dev](https://samintech.dev) · [GitHub](https://github.com/Sam-intech) · [X](https://www.x.com/Sam_intech)

---

<div align="center">
  <sub>CASSANDRA · Order Flow Intelligence · Built with Mistral AI on AWS Bedrock · Binance Market Data</sub>
</div>