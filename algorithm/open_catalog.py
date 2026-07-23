from __future__ import annotations

import json
import os
from time import sleep
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from .original_demo import DEMO_DATA, recommend_original


SUPPORTED_CATEGORY_LABELS = {
    "backpack": "Kids Backpack",
    "headphones": "Headphones",
    "running_shoes": "Running Shoes",
    "tablet": "Tablet",
    "keyboard": "Keyboard",
    "smartwatch": "Smart Watch",
}
COLORS = ["#3B82F6", "#10B981", "#F59E0B"]
BADGES = ["Best Overall", "Best Value", "Alternative"]


class OpenCatalogChatClient:
    """Open-ended shopping chat through Kimi, OpenAI, or Vercel AI Gateway."""

    def __init__(self) -> None:
        self.kimi_api_key = (
            os.getenv("MOONSHOT_API_KEY", "").strip()
            or os.getenv("KIMI_API_KEY", "").strip()
        )
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.gateway_api_key = (
            os.getenv("AI_GATEWAY_API_KEY", "").strip()
            or os.getenv("VERCEL_OIDC_TOKEN", "").strip()
        )
        self.requested_provider = os.getenv("LLM_PROVIDER", "").strip().casefold()

        configured = self._resolve_provider()
        self.api_key = configured["api_key"]
        self.provider = configured["provider"]
        self.base_url = configured["base_url"]
        self.model = configured["model"]
        self.uses_gateway = self.provider == "vercel-ai-gateway"

    def _resolve_provider(self, runtime_oidc_token: str = "") -> dict[str, str]:
        providers = {
            "kimi-direct": {
                "provider": "kimi-direct",
                "api_key": self.kimi_api_key,
                "base_url": (
                    os.getenv("MOONSHOT_BASE_URL", "").strip()
                    or os.getenv("KIMI_BASE_URL", "").strip()
                    or "https://api.moonshot.cn/v1"
                ).rstrip("/"),
                "model": (
                    os.getenv("MOONSHOT_MODEL", "").strip()
                    or os.getenv("KIMI_MODEL", "").strip()
                    or "kimi-k3"
                ),
            },
            "openai-direct": {
                "provider": "openai-direct",
                "api_key": self.openai_api_key,
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
                "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip(),
            },
            "vercel-ai-gateway": {
                "provider": "vercel-ai-gateway",
                "api_key": runtime_oidc_token.strip() or self.gateway_api_key,
                "base_url": "https://ai-gateway.vercel.sh/v1",
                "model": os.getenv("AI_GATEWAY_MODEL", "openai/gpt-5.4-mini").strip(),
            },
        }
        aliases = {
            "kimi": "kimi-direct",
            "moonshot": "kimi-direct",
            "openai": "openai-direct",
            "gateway": "vercel-ai-gateway",
            "vercel": "vercel-ai-gateway",
        }
        selected = aliases.get(self.requested_provider, self.requested_provider)
        if selected in providers:
            return providers[selected]
        for provider in ("kimi-direct", "openai-direct", "vercel-ai-gateway"):
            if providers[provider]["api_key"]:
                return providers[provider]
        return {"provider": "", "api_key": "", "base_url": "", "model": ""}

    def describe(self, runtime_oidc_token: str = "") -> dict[str, Any]:
        config = self._resolve_provider(runtime_oidc_token)
        return {
            "enabled": bool(config["api_key"]),
            "provider": config["provider"] or None,
            "model": config["model"] or None,
        }

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _model_candidates(config: dict[str, str]) -> list[str]:
        primary = config["model"]
        if config["provider"] != "kimi-direct":
            return [primary]
        configured = (
            os.getenv("MOONSHOT_FALLBACK_MODELS", "").strip()
            or os.getenv("KIMI_FALLBACK_MODELS", "").strip()
        )
        fallbacks = [item.strip() for item in configured.split(",") if item.strip()]
        if not fallbacks:
            fallbacks = ["kimi-k2.5"]
        return list(dict.fromkeys([primary, *fallbacks]))

    def respond(
        self,
        user_input: str,
        history: Optional[list[dict[str, str]]] = None,
        preferences: Optional[dict[str, Any]] = None,
        runtime_oidc_token: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        config = self._resolve_provider(runtime_oidc_token or "")
        api_key = config["api_key"]
        if not api_key:
            return None
        base_url = config["base_url"]
        model = config["model"]

        safe_history = [
            {"role": item["role"], "content": str(item["content"])[:2000]}
            for item in (history or [])[-8:]
            if item.get("role") in {"user", "assistant"} and item.get("content")
        ]
        system_prompt = (
            "You are Smart Shopping AI, an open-ended bilingual shopping assistant. You may chat naturally and recommend products "
            "from any consumer category. Infer intent from conversation history. For a greeting, complaint, comparison, follow-up, "
            "or ordinary conversation, answer naturally. For a shopping request that lacks essential information, ask exactly one useful "
            "clarifying question. When enough information is available, return exactly three realistic product candidates. "
            "Never claim live browsing, live prices, live stock, exact review counts, or current ratings. Prices are rough USD estimates from "
            "general model knowledge and must be verified. The six curated categories are backpack, headphones, running_shoes, tablet, "
            "keyboard, and smartwatch; set supported_category to one of those only when it truly matches. For every other category, set it "
            "to null and still provide recommendations. Match the user's language. Keep the reply concise and useful."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            *safe_history,
            {
                "role": "user",
                "content": (
                    f"Current preferences: {json.dumps(preferences or {}, ensure_ascii=False)}\n"
                    f"Current user message: {user_input}"
                ),
            },
        ]
        for candidate_model in self._model_candidates(config):
            payload = {
                "model": candidate_model,
                "messages": messages,
                "stream": False,
                "max_tokens": 2000,
                "response_format": {"type": "json_schema", "json_schema": self._response_schema()},
            }
            if config["provider"] == "kimi-direct" and candidate_model.startswith("kimi-k3"):
                # K3 defaults to maximum thinking effort; low is more responsive for a live classroom demo.
                payload["reasoning_effort"] = "low"

            attempts = 2 if config["provider"] == "kimi-direct" else 1
            for attempt in range(1, attempts + 1):
                try:
                    response = self._post(payload, api_key=api_key, base_url=base_url)
                    content = response["choices"][0]["message"]["content"]
                    data = json.loads(content)
                    return self._normalize(
                        data,
                        user_input,
                        preferences or {},
                        model=candidate_model,
                    )
                except HTTPError as error:
                    try:
                        detail = error.read().decode("utf-8", errors="replace")[:500].replace("\n", " ")
                    except Exception:
                        detail = "unavailable"
                    print(
                        "open_catalog_llm_error "
                        f"model={candidate_model} attempt={attempt} status={error.code} detail={detail}"
                    )
                    retryable = error.code == 429 or 500 <= error.code < 600
                    if not retryable:
                        return None
                    if attempt < attempts:
                        sleep(0.6 * attempt)
                except (URLError, TimeoutError) as error:
                    print(
                        "open_catalog_llm_error "
                        f"model={candidate_model} attempt={attempt} type={type(error).__name__}"
                    )
                    if config["provider"] != "kimi-direct":
                        return None
                    break
                except (ValueError, KeyError, TypeError) as error:
                    print(
                        "open_catalog_llm_error "
                        f"model={candidate_model} attempt={attempt} type={type(error).__name__}"
                    )
                    break
        return None

    @staticmethod
    def _post(payload: dict[str, Any], api_key: str, base_url: str) -> dict[str, Any]:
        request = Request(
            f"{base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        # Leave enough time inside Vercel's 45-second function limit to try a backup model.
        with urlopen(request, timeout=16) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        recommendation = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "brand": {"type": "string"},
                "estimated_price_usd": {"type": "number"},
                "fit_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "value_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "durability_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "feature_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "user_satisfaction": {"type": "integer", "minimum": 0, "maximum": 100},
                "rationale": {"type": "string"},
                "pros": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
                "cons": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
                "keywords": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            },
            "required": [
                "title", "brand", "estimated_price_usd", "fit_score", "value_score", "durability_score",
                "feature_score", "user_satisfaction", "rationale", "pros", "cons", "keywords",
            ],
            "additionalProperties": False,
        }
        return {
            "name": "open_shopping_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "intent": {"type": "string", "enum": ["chat", "clarification", "recommendation"]},
                    "language": {"type": "string", "enum": ["zh", "en"]},
                    "reply": {"type": "string"},
                    "category_label": {"type": "string"},
                    "supported_category": {
                        "type": ["string", "null"],
                        "enum": [*SUPPORTED_CATEGORY_LABELS, None],
                    },
                    "demand_summary": {"type": "string"},
                    "budget_label": {"type": "string"},
                    "key_concerns": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                    "market_notes": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
                    "recommendations": {"type": "array", "items": recommendation, "maxItems": 3},
                },
                "required": [
                    "intent", "language", "reply", "category_label", "supported_category", "demand_summary",
                    "budget_label", "key_concerns", "market_notes", "recommendations",
                ],
                "additionalProperties": False,
            },
        }

    def _normalize(
        self,
        data: dict[str, Any],
        user_input: str,
        preferences: dict[str, Any],
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        active_model = model or self.model
        intent = data.get("intent")
        if intent != "recommendation":
            return {
                "status": "conversation" if intent == "chat" else "needs_clarification",
                "message": str(data.get("reply") or "Please tell me a little more about what you need."),
                "mode": "llm-open-chat",
                "model": active_model,
            }

        supported = data.get("supported_category")
        if supported in DEMO_DATA:
            result = recommend_original(user_input, preferences=preferences, category_override=supported)
            result.update(
                {
                    "mode": "llm-routed-curated-catalog",
                    "model": active_model,
                    "message": str(data.get("reply") or result.get("message") or "Here are three recommendations."),
                }
            )
            return result

        recommendations = list(data.get("recommendations") or [])[:3]
        if len(recommendations) != 3:
            return {
                "status": "needs_clarification",
                "message": str(data.get("reply") or "Please share your budget and main use so I can recommend three options."),
                "mode": "llm-open-chat",
                "model": active_model,
            }

        recs = []
        for index, item in enumerate(recommendations):
            title = str(item["title"])
            price = round(max(0, float(item["estimated_price_usd"])), 2)
            recs.append(
                {
                    "rank": index + 1,
                    "title": title,
                    "price": price,
                    "rating": None,
                    "reviews": None,
                    "score": int(item["fit_score"]),
                    "url": f"https://www.amazon.com/s?k={quote_plus(title)}",
                    "pros": ", ".join(item.get("pros") or []),
                    "cons": ", ".join(item.get("cons") or []),
                    "badge": BADGES[index],
                    "color": COLORS[index],
                    "estimated": True,
                    "analytics": {
                        "value_score": int(item["value_score"]),
                        "durability_score": int(item["durability_score"]),
                        "feature_score": int(item["feature_score"]),
                        "user_satisfaction": int(item["user_satisfaction"]),
                        "price_tier": "AI estimate",
                        "top_keywords": list(item.get("keywords") or []),
                        "pros_detail": [str(item.get("rationale") or ""), *[str(v) for v in item.get("pros") or []]],
                        "cons_detail": [str(v) for v in item.get("cons") or []],
                    },
                }
            )

        prices = [item["price"] for item in recs]
        category = str(data.get("category_label") or "Product")
        return {
            "status": "success",
            "cat": category,
            "icon": "🛍️",
            "demand": str(data.get("demand_summary") or user_input),
            "user_profile": {
                "primary_use": str(data.get("demand_summary") or "General use"),
                "age_group": "Not specified",
                "key_concerns": [str(v) for v in data.get("key_concerns") or []],
                "budget_range": str(data.get("budget_label") or "Flexible"),
            },
            "market_analysis": {
                "price_range": f"~${min(prices):.0f} - ${max(prices):.0f}",
                "avg_rating": "Not live",
                "total_reviews_analyzed": 0,
                "key_trends": [str(v) for v in data.get("market_notes") or []],
            },
            "recs": recs,
            "comp": {
                "products": [item["title"][:28] for item in recs],
                "price": prices,
                "match": [item["score"] for item in recs],
                "reputation": [item["analytics"]["user_satisfaction"] for item in recs],
                "value": [item["analytics"]["value_score"] for item in recs],
                "overall": [float(item["score"]) for item in recs],
            },
            "personalized_analysis": {
                "best_overall": f"{recs[0]['title']} — {recommendations[0]['rationale']}",
                "best_value": f"{recs[1]['title']} — estimated at ${recs[1]['price']:.2f}",
                "alternative": f"{recs[2]['title']} — compare features and current availability before purchase",
            },
            "risk_assessment": {
                "data_freshness": "High risk — prices, availability and model details are not live",
                "purchase_check": "Verify the exact model, seller, warranty and return policy before purchase",
                "recommendation_scope": "AI-generated general guidance based on the conversation",
            },
            "category": "open_catalog",
            "query": user_input,
            "mode": "llm-open-catalog",
            "model": active_model,
            "message": str(data.get("reply") or f"Here are three options for {category}."),
            "source_note": "AI-generated shopping guidance. Prices, availability, ratings and specifications are not live data.",
            "algorithm": {
                "name": "LLM-assisted open-category recommendation",
                "dimensions": ["value", "durability", "features", "user_satisfaction"],
                "preferences_applied": bool(preferences),
            },
        }
