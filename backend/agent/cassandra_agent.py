# agents/cassandra_agent.py
# CASSANDRA - Mistral Intelligence Agent
# When VPIN spikes, this agent investigates autonomously using multiple tools
# and generates a professional intelligence brief for the trader

import boto3
import json
import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ── AWS Bedrock Client ─────────────────────────────────────
def _bedrock_client():
    kwargs = {
        "service_name": "bedrock-runtime",
        "region_name": os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1",
    }
    # Use explicit credentials from env when set (including session token for temporary creds)
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID")
        kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY")
        if os.getenv("AWS_SESSION_TOKEN"):
            kwargs["aws_session_token"] = os.getenv("AWS_SESSION_TOKEN")
    return boto3.client(**kwargs)


bedrock = _bedrock_client()

# ── Model Configuration ────────────────────────────────────
TRIAGE_MODEL  = "mistral.mixtral-8x7b-instruct-v0:1"   # Fast first assessment
ANALYST_MODEL = "mistral.mistral-large-2402-v1:0"       # Deep reasoning


# ══════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# These are the real-world data sources the agent can call
# ══════════════════════════════════════════════════════════

def tool_fetch_crypto_news(symbol: str = "BTC") -> dict:
    """
    Tool 1: Fetch latest crypto news from CryptoPanic.
    Free tier — no key needed for public feed.
    """
    try:
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token=free&currencies={symbol}&kind=news&public=true"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return {"error": f"News API returned {response.status_code}"}
        
        data = response.json()
        articles = data.get("results", [])[:5]  # Top 5 most recent
        
        news_items = []
        for article in articles:
            news_items.append({
                "title": article.get("title", ""),
                "source": article.get("source", {}).get("title", ""),
                "published": article.get("published_at", ""),
                "url": article.get("url", "")
            })
        
        return {"symbol": symbol, "news": news_items, "count": len(news_items)}
    
    except Exception as e:
        return {"error": str(e)}


def tool_fetch_binance_market_data(symbol: str = "BTCUSDT") -> dict:
    """
    Tool 2: Fetch current market snapshot from Binance.
    Price, 24h change, volume, bid/ask spread.
    Free, no API key required.
    """
    try:
        # 24hr ticker
        ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        ticker = requests.get(ticker_url, timeout=5).json()

        # Current order book top level
        book_url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5"
        book = requests.get(book_url, timeout=5).json()

        best_bid = float(book["bids"][0][0])
        best_ask = float(book["asks"][0][0])
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100

        return {
            "symbol": symbol,
            "price": float(ticker["lastPrice"]),
            "price_change_24h_pct": float(ticker["priceChangePercent"]),
            "volume_24h_btc": float(ticker["volume"]),
            "high_24h": float(ticker["highPrice"]),
            "low_24h": float(ticker["lowPrice"]),
            "bid": best_bid,
            "ask": best_ask,
            "spread_pct": round(spread_pct, 4),
            "num_trades_24h": int(ticker["count"])
        }
    
    except Exception as e:
        return {"error": str(e)}


def tool_fetch_funding_rate(symbol: str = "BTCUSDT") -> dict:
    """
    Tool 3: Fetch perpetual futures funding rate from Binance.
    Funding rate is a powerful signal — extreme positive = overleveraged longs,
    extreme negative = overleveraged shorts. Both precede violent moves.
    """
    try:
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=3"
        response = requests.get(url, timeout=5)
        data = response.json()

        if not data or isinstance(data, dict):
            return {"error": "No funding data available"}

        rates = []
        for item in data:
            rates.append({
                "funding_rate": float(item["fundingRate"]),
                "funding_rate_pct": round(float(item["fundingRate"]) * 100, 4),
                "time": datetime.fromtimestamp(
                    item["fundingTime"] / 1000, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M UTC")
            })

        latest_rate = rates[0]["funding_rate_pct"] if rates else 0
        
        # Interpret the funding rate
        if latest_rate > 0.1:
            interpretation = "EXTREME_LONG_BIAS — high liquidation risk for longs"
        elif latest_rate > 0.05:
            interpretation = "ELEVATED_LONG_BIAS — market overleveraged long"
        elif latest_rate < -0.05:
            interpretation = "ELEVATED_SHORT_BIAS — market overleveraged short"
        elif latest_rate < -0.1:
            interpretation = "EXTREME_SHORT_BIAS — high liquidation risk for shorts"
        else:
            interpretation = "NEUTRAL — balanced leverage"

        return {
            "symbol": symbol,
            "latest_funding_rate_pct": latest_rate,
            "interpretation": interpretation,
            "history": rates
        }
    
    except Exception as e:
        return {"error": str(e)}


def tool_analyse_vpin_pattern(vpin_history: list) -> dict:
    """
    Tool 4: Statistical analysis of recent VPIN pattern.
    Computes trend, acceleration, and compares to historical baselines.
    """
    if not vpin_history or len(vpin_history) < 5:
        return {"error": "Insufficient VPIN history"}

    recent = [r["vpin"] for r in vpin_history[-20:]]  # Last 20 readings
    current = recent[-1]
    mean = sum(recent) / len(recent)
    
    # Trend: is VPIN rising or falling?
    first_half = sum(recent[:len(recent)//2]) / (len(recent)//2)
    second_half = sum(recent[len(recent)//2:]) / (len(recent)//2)
    trend = "RISING" if second_half > first_half else "FALLING"
    trend_magnitude = abs(second_half - first_half)

    # How long has it been elevated?
    elevated_count = sum(1 for v in recent if v >= 0.55)
    
    # Historical crisis comparison
    crisis_profiles = {
        "FTX_collapse": {"peak": 0.73, "duration_buckets": 180, "pattern": "sustained_rise"},
        "LUNA_collapse": {"peak": 0.81, "duration_buckets": 240, "pattern": "spike_and_sustain"},
        "March_2020_crash": {"peak": 0.69, "duration_buckets": 120, "pattern": "sudden_spike"},
    }

    closest_crisis = None
    closest_distance = float("inf")
    for crisis, profile in crisis_profiles.items():
        distance = abs(current - profile["peak"])
        if distance < closest_distance:
            closest_distance = distance
            closest_crisis = crisis

    return {
        "current_vpin": round(current, 4),
        "mean_vpin_recent": round(mean, 4),
        "trend": trend,
        "trend_magnitude": round(trend_magnitude, 4),
        "elevated_buckets_of_last_20": elevated_count,
        "closest_historical_pattern": closest_crisis,
        "pattern_similarity_score": round(1 - closest_distance, 4)
    }


# ══════════════════════════════════════════════════════════
# BEDROCK CALLER
# ══════════════════════════════════════════════════════════

def call_mistral(prompt: str, model: str, max_tokens: int = 1000, temperature: float = 0.2) -> str:
    """
    Calls a Mistral model through AWS Bedrock.
    Returns the text response.
    """
    response = bedrock.invoke_model(
        modelId=model,
        body=json.dumps({
            "prompt": f"<s>[INST] {prompt} [/INST]",
            "max_tokens": max_tokens,
            "temperature": temperature
        })
    )
    result = json.loads(response['body'].read())
    return result['outputs'][0]['text'].strip()


# ══════════════════════════════════════════════════════════
# THE AGENT
# ══════════════════════════════════════════════════════════

class CassandraAgent:
    """
    A two-stage autonomous agent.

    Stage 1 — TRIAGE (Mixtral 8x7B, fast):
        Receives the VPIN spike alert.
        Decides which tools to call and in what order.

    Stage 2 — ANALYSIS (Mistral Large, deep):
        Receives all tool outputs.
        Synthesises everything into a professional intelligence brief.
    """

    def __init__(self):
        self.tool_registry = {
            "fetch_crypto_news":     tool_fetch_crypto_news,
            "fetch_market_data":     tool_fetch_binance_market_data,
            "fetch_funding_rate":    tool_fetch_funding_rate,
            "analyse_vpin_pattern":  tool_analyse_vpin_pattern,
        }

    def run(self, vpin_score: float, alert_level: str, vpin_history: list) -> dict:
        """
        Main agent entry point. Called whenever VPIN crosses threshold.
        Returns a structured intelligence brief.
        """
        print(f"\n[CASSANDRA AGENT] Alert triggered — VPIN: {vpin_score} | Level: {alert_level}")
        print(f"[CASSANDRA AGENT] Stage 1: Triage assessment...")

        # ── Stage 1: Triage ───────────────────────────────
        triage_prompt = f"""You are CASSANDRA, an AI system that monitors crypto market order flow toxicity.

A VPIN alert has been triggered:
- Current VPIN Score: {vpin_score}
- Alert Level: {alert_level}
- VPIN measures order flow toxicity — high values indicate informed trading activity

You have access to these tools:
1. fetch_crypto_news — latest BTC news headlines
2. fetch_market_data — current price, volume, spread
3. fetch_funding_rate — futures funding rate and leverage positioning  
4. analyse_vpin_pattern — statistical analysis of the VPIN trend

Which tools should be called to investigate this alert? 
Respond with ONLY a JSON array of tool names in the order they should be called.
Example: ["fetch_market_data", "fetch_funding_rate", "fetch_crypto_news", "analyse_vpin_pattern"]"""

        triage_response = call_mistral(triage_prompt, TRIAGE_MODEL, max_tokens=100)
        
        # Parse tool selection
        try:
            # Extract JSON array from response
            start = triage_response.find("[")
            end = triage_response.rfind("]") + 1
            tools_to_call = json.loads(triage_response[start:end])
        except:
            # Default tool order if parsing fails
            tools_to_call = ["fetch_market_data", "fetch_funding_rate", 
                           "fetch_crypto_news", "analyse_vpin_pattern"]

        print(f"[CASSANDRA AGENT] Tools selected: {tools_to_call}")

        # ── Execute Tools ──────────────────────────────────
        tool_results = {}
        for tool_name in tools_to_call:
            if tool_name in self.tool_registry:
                print(f"[CASSANDRA AGENT] Running tool: {tool_name}...")
                tool_fn = self.tool_registry[tool_name]
                
                # Pass vpin_history to the pattern analysis tool
                if tool_name == "analyse_vpin_pattern":
                    tool_results[tool_name] = tool_fn(vpin_history)
                else:
                    tool_results[tool_name] = tool_fn()

        # ── Stage 2: Deep Analysis ─────────────────────────
        print(f"[CASSANDRA AGENT] Stage 2: Generating intelligence brief...")

        tool_summary = json.dumps(tool_results, indent=2, default=str)

        analysis_prompt = f"""You are CASSANDRA, a professional crypto market intelligence system used by institutional traders.

A significant order flow toxicity alert has been detected:
- VPIN Score: {vpin_score} (Alert Level: {alert_level})
- Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

Your intelligence tools have returned the following data:
{tool_summary}

Generate a concise, professional intelligence brief with these exact sections:

## CASSANDRA ALERT — {alert_level}
**VPIN Score:** {vpin_score} | **Time:** {datetime.now(timezone.utc).strftime('%H:%M UTC')}

### Situation Assessment
[2-3 sentences: what the VPIN signal means in context of current market conditions]

### Corroborating Signals  
[Bullet points: what the other data sources confirm or contradict]

### Pattern Classification
[Which historical event this most resembles and why]

### Risk Assessment
[Specific, concrete risks a trader should be aware of right now]

### Recommended Actions
[3 specific, actionable steps for a trader seeing this alert]

Be direct. Be specific. Use the actual numbers from the data. No generic statements."""

        brief = call_mistral(analysis_prompt, ANALYST_MODEL, max_tokens=800, temperature=0.1)

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vpin_score": vpin_score,
            "alert_level": alert_level,
            "tools_called": tools_to_call,
            "tool_results": tool_results,
            "intelligence_brief": brief
        }

        print(f"[CASSANDRA AGENT] Intelligence brief generated.")
        return result


    def chat(self, question: str, vpin_context: dict) -> str:
        """
        Natural language interface.
        Allows a trader to ask questions about the current market state.
        """
        prompt = f"""You are CASSANDRA, a crypto market intelligence analyst.

Current market context:
- VPIN Score: {vpin_context.get('vpin', 'N/A')}
- Alert Level: {vpin_context.get('alert_level', 'N/A')}
- Recent market data: {json.dumps(vpin_context.get('market_data', {}), default=str)}

Trader question: {question}

Answer concisely and precisely using the market data available. 
If you don't have enough data to answer definitively, say so clearly."""

        return call_mistral(prompt, ANALYST_MODEL, max_tokens=400, temperature=0.2)


# ── Test Runner ────────────────────────────────────────────
if __name__ == "__main__":
    
    # Simulate a VPIN spike alert
    fake_history = [{"vpin": 0.5 + i * 0.01} for i in range(20)]
    fake_history[-1]["vpin"] = 0.74

    agent = CassandraAgent()
    
    result = agent.run(
        vpin_score=0.74,
        alert_level="HIGH",
        vpin_history=fake_history
    )

    print("\n" + "="*60)
    print("CASSANDRA INTELLIGENCE BRIEF")
    print("="*60)
    print(result["intelligence_brief"])
    print("="*60)

    # Test the chat interface
    print("\n[Testing chat interface...]")
    response = agent.chat(
        question="Is this spike more consistent with a liquidation cascade or informed accumulation?",
        vpin_context={
            "vpin": 0.74,
            "alert_level": "HIGH",
            "market_data": result["tool_results"].get("fetch_market_data", {})
        }
    )
    print(f"\nChat response:\n{response}")