from __future__ import annotations

import json
import os
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import Demand


class OpenAIResponsesClient:
    """Optional OpenAI Responses API adapter. The system remains runnable without a key."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def parse_demand(self, text: str, context: Optional[dict[str, Any]] = None) -> Optional[Demand]:
        if not self.enabled:
            return None
        schema = {
            "type": "object",
            "properties": {
                "category": {"type": ["string", "null"], "enum": ["backpack", "headphones", "running_shoes", None]},
                "category_label": {"type": "string"},
                "budget_min": {"type": "number"},
                "budget_max": {"type": ["number", "null"]},
                "features": {"type": "array", "items": {"type": "string"}},
                "brand_preferences": {"type": "array", "items": {"type": "string"}},
                "avoid_terms": {"type": "array", "items": {"type": "string"}},
                "scenario": {"type": "string"},
                "confidence": {"type": "number"},
            },
            "required": ["category", "category_label", "budget_min", "budget_max", "features", "brand_preferences", "avoid_terms", "scenario", "confidence"],
            "additionalProperties": False,
        }
        prompt = (
            "你是购物需求解析器。把用户输入解析为结构化条件；金额统一换算成人民币，美元按 1:7.2；"
            "仅支持 backpack、headphones、running_shoes 三个演示品类。不要编造用户未表达的品牌或功能。\n"
            f"历史上下文：{json.dumps(context or {}, ensure_ascii=False)}\n用户输入：{text}"
        )
        payload = {
            "model": self.model,
            "input": prompt,
            "text": {"format": {"type": "json_schema", "name": "shopping_demand", "strict": True, "schema": schema}},
        }
        try:
            data = self._post(payload)
            parsed = json.loads(self._output_text(data))
            parsed["source"] = "openai"
            parsed["missing_fields"] = [] if parsed.get("category") else ["category"]
            return Demand(**parsed)
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.base_url}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=18) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _output_text(data: dict[str, Any]) -> str:
        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    return content["text"]
        raise ValueError("Responses API did not return output text")
