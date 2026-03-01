from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import unescape
import re
from typing import Any, Callable

import requests


@dataclass
class ToolSpec:
    name: str
    description: str
    fn: Callable[..., dict]
    default_params: dict[str, Any] = field(default_factory=dict)
    fallback_params: list[dict[str, Any]] = field(default_factory=list)
    requires_vpin_history: bool = False


def _get_json(url: str, timeout: int = 5, params: dict[str, Any] | None = None) -> dict | list:
    response = requests.get(url, timeout=timeout, params=params)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {url}")
    return response.json()


def _clean_html_text(raw_html: str) -> str:
    # Strip script/style blocks and simple tags for lightweight article extraction.
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw_html)
    text = re.sub(r"(?is)<br\s*/?>", " ", text)
    text = re.sub(r"(?is)</p>", "\n", text)
    text = re.sub(r"(?is)<.*?>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _scrape_url_excerpt(url: str, max_chars: int = 420) -> str:
    try:
        response = requests.get(
            url,
            timeout=6,
            headers={"User-Agent": "CASSANDRA-Agent/1.0 (+market-intel)"},
        )
        if response.status_code != 200:
            return ""

        html_doc = response.text
        title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html_doc)
        title = _clean_html_text(title_match.group(1)) if title_match else ""

        paragraphs = re.findall(r"(?is)<p[^>]*>(.*?)</p>", html_doc)
        paragraph_text = " ".join(_clean_html_text(p) for p in paragraphs[:4])
        merged = f"{title}. {paragraph_text}".strip(". ").strip()
        return merged[:max_chars] if merged else ""
    except Exception:
        return ""


def tool_fetch_crypto_news(symbol: str = "BTC", limit: int = 5) -> dict:
    """Fetch latest crypto news from CryptoPanic public feed."""
    try:
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {
            "auth_token": "free",
            "currencies": symbol,
            "kind": "news",
            "public": "true",
        }
        data = _get_json(url, timeout=5, params=params)
        articles = data.get("results", [])[:limit]
        news_items = [
            {
                "title": article.get("title", ""),
                "source": article.get("source", {}).get("title", ""),
                "published": article.get("published_at", ""),
                "url": article.get("url", ""),
            }
            for article in articles
        ]
        return {"symbol": symbol, "news": news_items, "count": len(news_items)}
    except Exception as exc:
        return {"error": str(exc), "symbol": symbol}


def tool_scrape_web_context(query: str = "bitcoin market liquidity stress", limit: int = 5) -> dict:
    """
    Pull recent internet context and scrape short excerpts from article pages.
    Source search list from the public GDELT document API.
    """
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": max(1, min(limit, 10)),
            "sort": "HybridRel",
        }
        payload = _get_json(url, timeout=8, params=params)

        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        if not articles:
            return {"query": query, "count": 0, "results": []}

        results = []
        for article in articles[:limit]:
            article_url = article.get("url", "")
            excerpt = _scrape_url_excerpt(article_url) if article_url else ""
            results.append(
                {
                    "title": article.get("title", ""),
                    "url": article_url,
                    "domain": article.get("domain", ""),
                    "published": article.get("seendate", ""),
                    "language": article.get("language", ""),
                    "excerpt": excerpt,
                }
            )

        return {
            "query": query,
            "count": len(results),
            "results": results,
        }
    except Exception as exc:
        return {"error": str(exc), "query": query}


def tool_fetch_binance_market_data(symbol: str = "BTCUSDT", depth_limit: int = 5) -> dict:
    """Fetch current market snapshot from Binance spot API."""
    try:
        ticker_url = "https://api.binance.com/api/v3/ticker/24hr"
        ticker = _get_json(ticker_url, timeout=5, params={"symbol": symbol})

        book_url = "https://api.binance.com/api/v3/depth"
        book = _get_json(book_url, timeout=5, params={"symbol": symbol, "limit": depth_limit})

        bids = book.get("bids") or []
        asks = book.get("asks") or []
        if not bids or not asks:
            return {"error": "No order book data available", "symbol": symbol}

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100 if best_bid else 0.0

        return {
            "symbol": symbol,
            "price": float(ticker["lastPrice"]),
            "price_change_24h_pct": float(ticker["priceChangePercent"]),
            "volume_24h": float(ticker["volume"]),
            "high_24h": float(ticker["highPrice"]),
            "low_24h": float(ticker["lowPrice"]),
            "bid": best_bid,
            "ask": best_ask,
            "spread_pct": round(spread_pct, 4),
            "num_trades_24h": int(ticker["count"]),
            "depth_levels": depth_limit,
        }
    except Exception as exc:
        return {"error": str(exc), "symbol": symbol}


def tool_fetch_order_book_imbalance(symbol: str = "BTCUSDT", limit: int = 20) -> dict:
    """Measure near-touch order book imbalance as a microstructure confirmation signal."""
    try:
        book_url = "https://api.binance.com/api/v3/depth"
        book = _get_json(book_url, timeout=5, params={"symbol": symbol, "limit": limit})

        bids = book.get("bids") or []
        asks = book.get("asks") or []
        if not bids or not asks:
            return {"error": "No order book data available", "symbol": symbol}

        bid_volume = sum(float(level[1]) for level in bids)
        ask_volume = sum(float(level[1]) for level in asks)
        total = bid_volume + ask_volume
        imbalance = ((bid_volume - ask_volume) / total) if total else 0.0

        if imbalance > 0.2:
            interpretation = "STRONG_BID_DOMINANCE"
        elif imbalance < -0.2:
            interpretation = "STRONG_ASK_DOMINANCE"
        else:
            interpretation = "BALANCED_BOOK"

        return {
            "symbol": symbol,
            "levels_used": limit,
            "bid_volume": round(bid_volume, 6),
            "ask_volume": round(ask_volume, 6),
            "imbalance_ratio": round(imbalance, 4),
            "interpretation": interpretation,
        }
    except Exception as exc:
        return {"error": str(exc), "symbol": symbol}


def tool_fetch_funding_rate(symbol: str = "BTCUSDT", limit: int = 3) -> dict:
    """Fetch futures funding rate history from Binance futures API."""
    try:
        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        rows = _get_json(url, timeout=5, params={"symbol": symbol, "limit": limit})

        if not rows or isinstance(rows, dict):
            return {"error": "No funding data available", "symbol": symbol}

        history = []
        for row in rows:
            rate = float(row["fundingRate"])
            history.append(
                {
                    "funding_rate": rate,
                    "funding_rate_pct": round(rate * 100, 4),
                    "time": datetime.fromtimestamp(row["fundingTime"] / 1000, tz=timezone.utc).isoformat(),
                }
            )

        latest_rate_pct = history[0]["funding_rate_pct"] if history else 0.0
        if latest_rate_pct > 0.1:
            interpretation = "EXTREME_LONG_BIAS"
        elif latest_rate_pct > 0.05:
            interpretation = "ELEVATED_LONG_BIAS"
        elif latest_rate_pct < -0.1:
            interpretation = "EXTREME_SHORT_BIAS"
        elif latest_rate_pct < -0.05:
            interpretation = "ELEVATED_SHORT_BIAS"
        else:
            interpretation = "NEUTRAL"

        return {
            "symbol": symbol,
            "latest_funding_rate_pct": latest_rate_pct,
            "interpretation": interpretation,
            "history": history,
        }
    except Exception as exc:
        return {"error": str(exc), "symbol": symbol}


def tool_analyse_vpin_pattern(vpin_history: list[dict], lookback: int = 20) -> dict:
    """Analyse VPIN trend statistics and compare with historical stress templates."""
    if not vpin_history or len(vpin_history) < 5:
        return {"error": "Insufficient VPIN history"}

    lookback = max(5, min(lookback, len(vpin_history)))
    recent = [float(row["vpin"]) for row in vpin_history[-lookback:]]
    current = recent[-1]
    mean_recent = sum(recent) / len(recent)

    half = len(recent) // 2
    first_half = sum(recent[:half]) / max(half, 1)
    second_half = sum(recent[half:]) / max(len(recent) - half, 1)
    trend = "RISING" if second_half > first_half else "FALLING"
    trend_magnitude = abs(second_half - first_half)

    elevated_count = sum(1 for value in recent if value >= 0.55)

    crisis_profiles = {
        "FTX_COLLAPSE": 0.73,
        "LUNA_COLLAPSE": 0.81,
        "MARCH_2020_CRASH": 0.69,
    }

    closest_pattern = "UNKNOWN"
    closest_distance = float("inf")
    for name, peak in crisis_profiles.items():
        distance = abs(current - peak)
        if distance < closest_distance:
            closest_distance = distance
            closest_pattern = name

    return {
        "lookback": lookback,
        "current_vpin": round(current, 4),
        "mean_vpin_recent": round(mean_recent, 4),
        "trend": trend,
        "trend_magnitude": round(trend_magnitude, 4),
        "elevated_buckets": elevated_count,
        "closest_historical_pattern": closest_pattern,
        "pattern_similarity_score": round(1 - closest_distance, 4),
    }


class AgentTools:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {
            "fetch_market_data": ToolSpec(
                name="fetch_market_data",
                description="Current market snapshot: price, change, volume, spread.",
                fn=tool_fetch_binance_market_data,
                default_params={"symbol": "BTCUSDT", "depth_limit": 5},
                fallback_params=[
                    {"symbol": "BTCUSDT", "depth_limit": 20},
                    {"symbol": "ETHUSDT", "depth_limit": 20},
                ],
            ),
            "fetch_order_book_imbalance": ToolSpec(
                name="fetch_order_book_imbalance",
                description="Order-book imbalance signal for microstructure confirmation.",
                fn=tool_fetch_order_book_imbalance,
                default_params={"symbol": "BTCUSDT", "limit": 20},
                fallback_params=[
                    {"symbol": "BTCUSDT", "limit": 50},
                    {"symbol": "ETHUSDT", "limit": 50},
                ],
            ),
            "fetch_funding_rate": ToolSpec(
                name="fetch_funding_rate",
                description="Perpetual futures funding and leverage-bias readout.",
                fn=tool_fetch_funding_rate,
                default_params={"symbol": "BTCUSDT", "limit": 3},
                fallback_params=[
                    {"symbol": "BTCUSDT", "limit": 6},
                    {"symbol": "ETHUSDT", "limit": 6},
                ],
            ),
            "fetch_crypto_news": ToolSpec(
                name="fetch_crypto_news",
                description="Recent headlines to detect event-driven catalysts.",
                fn=tool_fetch_crypto_news,
                default_params={"symbol": "BTC", "limit": 5},
                fallback_params=[
                    {"symbol": "ETH", "limit": 5},
                    {"symbol": "BTC", "limit": 10},
                ],
            ),
            "scrape_web_context": ToolSpec(
                name="scrape_web_context",
                description="Scrape recent internet context and article excerpts for macro/micro catalysts.",
                fn=tool_scrape_web_context,
                default_params={"query": "bitcoin market liquidity stress", "limit": 5},
                fallback_params=[
                    {"query": "btc exchange risk liquidity", "limit": 5},
                    {"query": "eth crypto market contagion", "limit": 5},
                ],
            ),
            "analyse_vpin_pattern": ToolSpec(
                name="analyse_vpin_pattern",
                description="Quant analysis of VPIN trend, acceleration, and crisis similarity.",
                fn=tool_analyse_vpin_pattern,
                default_params={"lookback": 20},
                fallback_params=[{"lookback": 40}],
                requires_vpin_history=True,
            ),
        }

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def descriptions(self) -> list[str]:
        return [f"- {spec.name}: {spec.description}" for spec in self._tools.values()]
