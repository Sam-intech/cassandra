# backend/routers/agent.py
from fastapi import APIRouter
from pydantic import BaseModel

from backend.state import app_state

router = APIRouter()

class ChatRequest(BaseModel):
    question: str


@router.get("/agent/brief")
def get_latest_brief():
    if not app_state.latest_brief:
        return {"brief": None}
    return {"brief": app_state.latest_brief}


@router.get("/agent/memory")
def get_agent_memory(limit: int = 20):
    return {"memory": app_state.agent.get_memory_snapshot(limit=limit)}


@router.post("/agent/chat")
def chat(request: ChatRequest):
    current_vpin = app_state.vpin_engine.get_current_vpin()
    brief = app_state.latest_brief

    vpin_context = {
        "vpin": current_vpin,
        "alert_level": app_state.vpin_engine.classify_alert(current_vpin),
        "market_data": brief.get("tool_results", {}).get(
            "fetch_market_data", {}
        ) if brief else {}
    }

    response = app_state.agent.chat(request.question, vpin_context)
    return {"response": response}
