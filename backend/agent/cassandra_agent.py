# backend/agent/cassandra_agent.py
# CASSANDRA - Autonomous Intelligence Agent

from __future__ import annotations

import json
import os
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

import boto3
from dotenv import load_dotenv

from backend.agent.tools import AgentTools, ToolSpec
# =============================================================================


load_dotenv()


# ── AWS Bedrock Client ─────────────────────────────────────
def _bedrock_client():
    kwargs = {
        "service_name": "bedrock-runtime",
        "region_name": os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1",
    }
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID")
        kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY")
        if os.getenv("AWS_SESSION_TOKEN"):
            kwargs["aws_session_token"] = os.getenv("AWS_SESSION_TOKEN")
    return boto3.client(**kwargs)


bedrock = _bedrock_client()

# ── Model Configuration ────────────────────────────────────
TRIAGE_MODEL = "mistral.mixtral-8x7b-instruct-v0:1"
ANALYST_MODEL = "mistral.mistral-large-2402-v1:0"

ALERT_LEVELS = {"ELEVATED", "HIGH", "CRITICAL"}


@dataclass
class MemoryEvent:
    timestamp: str
    vpin_score: float
    alert_level: str
    trend_tag: str
    alert_streak: int
    investigated: bool
    reason: str
    tools_called: list[str] = field(default_factory=list)


# ── Bedrock Caller ─────────────────────────────────────────
def call_mistral(
    prompt: str,
    model: str,
    max_tokens: int = 1000,
    temperature: float = 0.2,
) -> str:
    response = bedrock.invoke_model(
        modelId=model,
        body=json.dumps(
            {
                "prompt": f"<s>[INST] {prompt} [/INST]",
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        ),
    )
    result = json.loads(response["body"].read())
    return result["outputs"][0]["text"].strip()


class CassandraAgent:
    """
    Autonomous intelligence agent with:
      - Long-running memory
      - Dynamic tool planning (including no-tool decisions)
      - Retry/fallback tool execution
      - Deep-dive follow-up investigations
      - Trend-pattern detection from consecutive alerts
    """

    def __init__(self):
        self.tools = AgentTools()
        self.memory: deque[MemoryEvent] = deque(maxlen=500)
        self.alert_streak = 0

    def reset_memory(self) -> None:
        self.memory.clear()
        self.alert_streak = 0

    def get_memory_snapshot(self, limit: int = 10) -> list[dict[str, Any]]:
        return [asdict(event) for event in list(self.memory)[-max(1, limit) :]]

    def _safe_call_mistral(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str | None:
        try:
            return call_mistral(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as exc:
            print(f"[CASSANDRA AGENT] LLM call failed: {exc}")
            return None

    def _extract_json_array(self, raw_text: str | None) -> list[str] | None:
        if not raw_text:
            return None
        start = raw_text.find("[")
        end = raw_text.rfind("]") + 1
        if start < 0 or end <= start:
            return None
        try:
            parsed = json.loads(raw_text[start:end])
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, list):
            return None
        valid = set(self.tools.names())
        return [item for item in parsed if isinstance(item, str) and item in valid]

    def _is_alert(self, alert_level: str, vpin_score: float) -> bool:
        return alert_level in ALERT_LEVELS or vpin_score >= 0.65

    def _detect_trend_tag(self, vpin_history: list[dict], alert_streak: int) -> str:
        if not vpin_history or len(vpin_history) < 3:
            return "INSUFFICIENT_HISTORY"

        recent = [float(row["vpin"]) for row in vpin_history[-6:]]
        increases = sum(1 for idx in range(1, len(recent)) if recent[idx] > recent[idx - 1])
        decreases = sum(1 for idx in range(1, len(recent)) if recent[idx] < recent[idx - 1])
        variation = max(recent) - min(recent)

        if alert_streak >= 3 and increases >= max(1, len(recent) - 2):
            return "SUSTAINED_TOXICITY_UPTREND"
        if alert_streak >= 3:
            return "PERSISTENT_TOXICITY_REGIME"
        if variation < 0.03:
            return "RANGE_BOUND_FLOW"
        if increases > decreases:
            return "EMERGING_UPTREND"
        if decreases > increases:
            return "MEAN_REVERTING"
        return "MIXED_FLOW"

    def _should_investigate(
        self,
        vpin_score: float,
        alert_level: str,
        trend_tag: str,
    ) -> tuple[bool, str]:
        if not self._is_alert(alert_level, vpin_score):
            return False, "Pattern is within normal VPIN regime."

        if trend_tag == "RANGE_BOUND_FLOW" and self.alert_streak < 3 and vpin_score < 0.72:
            return False, "Elevated but range-bound flow; skipping unnecessary tool calls."

        if self.memory:
            last = self.memory[-1]
            if (
                last.investigated
                and last.trend_tag == trend_tag
                and abs(last.vpin_score - vpin_score) < 0.005
            ):
                return False, "Signal is near-duplicate of latest investigated state."

        return True, "Anomalous or persistent pattern detected."

    def _heuristic_tool_plan(self, alert_level: str, trend_tag: str) -> list[str]:
        plan: list[str] = ["analyse_vpin_pattern", "fetch_market_data"]

        if alert_level in {"HIGH", "CRITICAL"} or "UPTREND" in trend_tag:
            plan.extend(["fetch_order_book_imbalance", "fetch_funding_rate"])
        else:
            plan.append("fetch_funding_rate")

        if alert_level == "CRITICAL" or self.alert_streak >= 3:
            plan.append("fetch_crypto_news")

        # Preserve order while removing duplicates
        deduped: list[str] = []
        for name in plan:
            if name not in deduped:
                deduped.append(name)
        return deduped

    def _llm_tool_plan(self, vpin_score: float, alert_level: str, trend_tag: str) -> list[str] | None:
        prompt = f"""You are an autonomous market-intelligence planner.

Signal context:
- VPIN score: {vpin_score}
- Alert level: {alert_level}
- Detected trend tag: {trend_tag}
- Consecutive alert streak: {self.alert_streak}

Available tools:
{chr(10).join(self.tools.descriptions())}

Return ONLY a JSON array of tool names (use [] if no tool is needed).
Prefer minimal but sufficient evidence collection."""

        triage = self._safe_call_mistral(
            prompt=prompt,
            model=TRIAGE_MODEL,
            max_tokens=120,
            temperature=0.1,
        )
        return self._extract_json_array(triage)

    def _is_tool_result_informative(self, tool_name: str, result: dict) -> bool:
        if not isinstance(result, dict) or result.get("error"):
            return False

        if tool_name == "fetch_crypto_news":
            return int(result.get("count", 0)) > 0
        if tool_name == "fetch_market_data":
            return float(result.get("num_trades_24h", 0)) > 0
        if tool_name == "fetch_funding_rate":
            return len(result.get("history", [])) > 0
        if tool_name == "fetch_order_book_imbalance":
            return "imbalance_ratio" in result
        if tool_name == "analyse_vpin_pattern":
            return "current_vpin" in result

        return True

    def _execute_tool(
        self,
        spec: ToolSpec,
        vpin_history: list[dict],
        parameter_sets: list[dict[str, Any]],
    ) -> tuple[dict, list[dict[str, Any]]]:
        attempts: list[dict[str, Any]] = []
        best_result: dict[str, Any] = {"error": "No attempt executed"}

        for params in parameter_sets:
            try:
                if spec.requires_vpin_history:
                    result = spec.fn(vpin_history=vpin_history, **params)
                else:
                    result = spec.fn(**params)
            except Exception as exc:
                result = {"error": str(exc)}

            informative = self._is_tool_result_informative(spec.name, result)
            attempts.append(
                {
                    "tool": spec.name,
                    "params": params,
                    "informative": informative,
                    "error": result.get("error"),
                }
            )
            best_result = result

            if informative:
                break

        return best_result, attempts

    def _execute_tool_plan(
        self,
        plan: list[str],
        vpin_history: list[dict],
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
        tool_results: dict[str, Any] = {}
        execution_log: list[dict[str, Any]] = []
        tools_called: list[str] = []

        for tool_name in plan:
            spec = self.tools.get(tool_name)
            if spec is None:
                continue

            parameter_sets = [spec.default_params, *spec.fallback_params]
            result, attempts = self._execute_tool(spec, vpin_history, parameter_sets)
            tool_results[tool_name] = result
            execution_log.extend(attempts)
            tools_called.append(tool_name)

        return tool_results, execution_log, tools_called

    def _should_deep_dive(
        self,
        alert_level: str,
        trend_tag: str,
        tool_results: dict[str, Any],
    ) -> tuple[bool, str]:
        errors = sum(1 for result in tool_results.values() if isinstance(result, dict) and result.get("error"))

        if alert_level == "CRITICAL":
            return True, "Critical signal requires deeper evidence."
        if self.alert_streak >= 3:
            return True, "Three or more consecutive alerts detected."
        if errors >= 2:
            return True, "Primary toolset returned insufficient evidence."
        if trend_tag == "SUSTAINED_TOXICITY_UPTREND":
            return True, "Sustained uptrend in toxicity warrants extended analysis."

        return False, "Primary investigation sufficient."

    def _execute_deep_dive(
        self,
        vpin_history: list[dict],
        already_called: list[str],
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
        deep_results: dict[str, Any] = {}
        deep_log: list[dict[str, Any]] = []
        deep_tools: list[str] = []

        follow_up_plan: list[tuple[str, list[dict[str, Any]]]] = []

        if "fetch_market_data" in already_called:
            follow_up_plan.append(("fetch_market_data", [{"symbol": "ETHUSDT", "depth_limit": 20}]))
        else:
            follow_up_plan.append(("fetch_market_data", [{"symbol": "BTCUSDT", "depth_limit": 20}]))

        if "fetch_funding_rate" in already_called:
            follow_up_plan.append(("fetch_funding_rate", [{"symbol": "ETHUSDT", "limit": 6}]))
        else:
            follow_up_plan.append(("fetch_funding_rate", [{"symbol": "BTCUSDT", "limit": 6}]))

        if "fetch_order_book_imbalance" in already_called:
            follow_up_plan.append(("fetch_order_book_imbalance", [{"symbol": "BTCUSDT", "limit": 50}]))
        else:
            follow_up_plan.append(("fetch_order_book_imbalance", [{"symbol": "ETHUSDT", "limit": 50}]))

        follow_up_plan.append(("analyse_vpin_pattern", [{"lookback": 40}]))

        if self.alert_streak >= 3 or "fetch_crypto_news" in already_called:
            follow_up_plan.append(("fetch_crypto_news", [{"symbol": "ETH", "limit": 8}]))

        for tool_name, parameter_sets in follow_up_plan:
            spec = self.tools.get(tool_name)
            if spec is None:
                continue

            result, attempts = self._execute_tool(
                spec=spec,
                vpin_history=vpin_history,
                parameter_sets=parameter_sets,
            )
            deep_results[f"{tool_name}_follow_up"] = result
            deep_log.extend(attempts)
            deep_tools.append(tool_name)

        return deep_results, deep_log, deep_tools

    def _build_fallback_brief(
        self,
        vpin_score: float,
        alert_level: str,
        trend_tag: str,
        tool_results: dict[str, Any],
        deep_dive_reason: str,
    ) -> str:
        error_count = sum(1 for result in tool_results.values() if isinstance(result, dict) and result.get("error"))
        return (
            f"# CASSANDRA ALERT - {alert_level}\n"
            f"VPIN: {vpin_score:.4f}\n"
            f"Trend tag: {trend_tag}\n"
            f"Consecutive alert streak: {self.alert_streak}\n\n"
            f"Situation Assessment:\n"
            f"The agent detected an abnormal order-flow regime and executed autonomous tool checks. "
            f"Tool errors: {error_count}.\n\n"
            f"Pattern Classification:\n"
            f"{trend_tag}.\n\n"
            f"Autonomous Action:\n"
            f"{deep_dive_reason}\n\n"
            f"Risk Assessment:\n"
            f"Elevated probability of informed-flow dominance and short-term liquidity imbalance.\n\n"
            f"Recommended Actions:\n"
            f"- Reduce leverage and tighten invalidation levels.\n"
            f"- Monitor spread/imbalance for continuation vs exhaustion.\n"
            f"- Require confirmation before adding directional risk."
        )

    def _generate_brief(
        self,
        vpin_score: float,
        alert_level: str,
        trend_tag: str,
        decision_reason: str,
        tool_results: dict[str, Any],
        deep_dive_reason: str,
    ) -> str:
        prompt = f"""You are CASSANDRA, an institutional crypto intelligence analyst.

Context:
- VPIN score: {vpin_score}
- Alert level: {alert_level}
- Trend tag: {trend_tag}
- Consecutive alert streak: {self.alert_streak}
- Decision rationale: {decision_reason}
- Deep-dive rationale: {deep_dive_reason}

Tool outputs:
{json.dumps(tool_results, indent=2, default=str)}

Write a concise brief with clear headings and bold heading titles (not markdown asterisks as visible characters).
Use these sections:
1. CASSANDRA ALERT
2. Situation Assessment
3. Corroborating Signals
4. Pattern Classification
5. Risk Assessment
6. Recommended Actions

Be specific and evidence-based."""

        llm_brief = self._safe_call_mistral(
            prompt=prompt,
            model=ANALYST_MODEL,
            max_tokens=900,
            temperature=0.1,
        )

        if llm_brief:
            return llm_brief

        return self._build_fallback_brief(
            vpin_score=vpin_score,
            alert_level=alert_level,
            trend_tag=trend_tag,
            tool_results=tool_results,
            deep_dive_reason=deep_dive_reason,
        )

    def run(self, vpin_score: float, alert_level: str, vpin_history: list[dict]) -> dict:
        """Autonomous entry point for stream alerts."""
        is_alert = self._is_alert(alert_level, vpin_score)
        self.alert_streak = self.alert_streak + 1 if is_alert else 0

        trend_tag = self._detect_trend_tag(vpin_history=vpin_history, alert_streak=self.alert_streak)
        investigate, decision_reason = self._should_investigate(
            vpin_score=vpin_score,
            alert_level=alert_level,
            trend_tag=trend_tag,
        )

        timestamp = datetime.now(timezone.utc).isoformat()

        if not investigate:
            skipped_brief = (
                f"CASSANDRA ALERT: {alert_level}\n"
                f"VPIN: {vpin_score:.4f}\n"
                f"Decision: skipped investigation\n"
                f"Reason: {decision_reason}\n"
                f"Trend tag: {trend_tag}\n"
                f"Consecutive alerts: {self.alert_streak}"
            )
            self.memory.append(
                MemoryEvent(
                    timestamp=timestamp,
                    vpin_score=vpin_score,
                    alert_level=alert_level,
                    trend_tag=trend_tag,
                    alert_streak=self.alert_streak,
                    investigated=False,
                    reason=decision_reason,
                    tools_called=[],
                )
            )
            return {
                "timestamp": timestamp,
                "vpin_score": vpin_score,
                "alert_level": alert_level,
                "trend_tag": trend_tag,
                "alert_streak": self.alert_streak,
                "investigated": False,
                "decision_reason": decision_reason,
                "tools_called": [],
                "tool_results": {},
                "execution_log": [],
                "deep_dive_performed": False,
                "deep_dive_reason": "Investigation skipped.",
                "intelligence_brief": skipped_brief,
                "memory_snapshot": self.get_memory_snapshot(limit=8),
            }

        llm_plan = self._llm_tool_plan(
            vpin_score=vpin_score,
            alert_level=alert_level,
            trend_tag=trend_tag,
        )
        heuristic_plan = self._heuristic_tool_plan(alert_level=alert_level, trend_tag=trend_tag)

        tools_to_call = llm_plan if llm_plan is not None else heuristic_plan
        for tool_name in heuristic_plan:
            if tool_name not in tools_to_call and alert_level == "CRITICAL":
                tools_to_call.append(tool_name)

        tool_results, execution_log, tools_called = self._execute_tool_plan(
            plan=tools_to_call,
            vpin_history=vpin_history,
        )

        do_deep_dive, deep_dive_reason = self._should_deep_dive(
            alert_level=alert_level,
            trend_tag=trend_tag,
            tool_results=tool_results,
        )

        deep_dive_results: dict[str, Any] = {}
        deep_dive_tools: list[str] = []
        if do_deep_dive:
            dive_results, dive_log, dive_tools = self._execute_deep_dive(
                vpin_history=vpin_history,
                already_called=tools_called,
            )
            deep_dive_results = dive_results
            execution_log.extend(dive_log)
            deep_dive_tools = dive_tools
            tool_results.update(deep_dive_results)

        brief = self._generate_brief(
            vpin_score=vpin_score,
            alert_level=alert_level,
            trend_tag=trend_tag,
            decision_reason=decision_reason,
            tool_results=tool_results,
            deep_dive_reason=deep_dive_reason,
        )

        all_tools_called = tools_called + deep_dive_tools
        self.memory.append(
            MemoryEvent(
                timestamp=timestamp,
                vpin_score=vpin_score,
                alert_level=alert_level,
                trend_tag=trend_tag,
                alert_streak=self.alert_streak,
                investigated=True,
                reason=decision_reason,
                tools_called=all_tools_called,
            )
        )

        return {
            "timestamp": timestamp,
            "vpin_score": vpin_score,
            "alert_level": alert_level,
            "trend_tag": trend_tag,
            "alert_streak": self.alert_streak,
            "investigated": True,
            "decision_reason": decision_reason,
            "tools_called": all_tools_called,
            "tool_results": tool_results,
            "execution_log": execution_log,
            "deep_dive_performed": do_deep_dive,
            "deep_dive_reason": deep_dive_reason,
            "intelligence_brief": brief,
            "memory_snapshot": self.get_memory_snapshot(limit=8),
        }

    def chat(self, question: str, vpin_context: dict) -> str:
        """Natural-language interface enhanced with recent agent memory."""
        memory_snapshot = self.get_memory_snapshot(limit=5)

        prompt = f"""You are CASSANDRA, a crypto market intelligence analyst.

Current context:
- VPIN score: {vpin_context.get('vpin', 'N/A')}
- Alert level: {vpin_context.get('alert_level', 'N/A')}
- Market data: {json.dumps(vpin_context.get('market_data', {}), default=str)}
- Recent agent memory: {json.dumps(memory_snapshot, default=str)}

Trader question: {question}

Answer precisely. Use memory to compare current conditions vs recent patterns.
If confidence is low, say what additional evidence is needed."""

        response = self._safe_call_mistral(
            prompt=prompt,
            model=ANALYST_MODEL,
            max_tokens=450,
            temperature=0.2,
        )
        if response:
            return response

        return "I could not reach the reasoning model right now. Check market data and recent memory context, then retry."


if __name__ == "__main__":
    fake_history = [{"vpin": 0.52 + i * 0.01} for i in range(25)]
    fake_history[-1]["vpin"] = 0.79

    agent = CassandraAgent()
    result = agent.run(vpin_score=0.79, alert_level="HIGH", vpin_history=fake_history)

    print("\n" + "=" * 60)
    print("CASSANDRA AUTONOMOUS BRIEF")
    print("=" * 60)
    print(result["intelligence_brief"])
    print("=" * 60)
