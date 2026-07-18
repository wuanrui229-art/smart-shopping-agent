from __future__ import annotations

import re
from typing import Any, Optional

from .catalog import CATEGORY_ALIASES, CATEGORY_LABELS, PRODUCTS
from .models import Demand


FEATURE_TERMS = [
    "防水", "轻量", "护脊", "电脑隔层", "反光", "扩容", "主动降噪", "降噪", "通透模式",
    "长续航", "双设备", "开放式", "防汗", "低延迟", "缓震", "透气", "耐磨", "宽楦", "回弹",
    "通勤", "运动", "学生", "商务", "性价比",
]
KNOWN_BRANDS = sorted({p["brand"] for p in PRODUCTS})


def _extract_budget(text: str) -> tuple[float, Optional[float]]:
    normalized = text.replace(",", "")
    range_match = re.search(r"(?:预算|价格)?\s*(\d+(?:\.\d+)?)\s*(?:-|到|至|~)\s*(\d+(?:\.\d+)?)\s*(美元|美金|元|块|¥|￥|\$)?", normalized)
    if range_match:
        low, high = float(range_match.group(1)), float(range_match.group(2))
        currency = range_match.group(3) or "元"
        factor = 7.2 if currency in {"美元", "美金", "$"} else 1
        return low * factor, high * factor
    patterns = [
        r"(?:预算|价格|不超过|控制在|最多|以内|低于)\s*(?:约|大约)?\s*[¥￥$]?\s*(\d+(?:\.\d+)?)\s*(美元|美金|元|块)?",
        r"[¥￥$]\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(美元|美金|元|块)(?:以内|以下)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            value = float(match.group(1))
            currency = match.group(2) if match.lastindex and match.lastindex >= 2 else None
            if "$" in match.group(0) or currency in {"美元", "美金"}:
                value *= 7.2
            return 0, value
    return 0, None


def parse_demand_rules(text: str, context: Optional[dict[str, Any]] = None, preferences: Optional[dict[str, Any]] = None) -> Demand:
    lower = text.lower().strip()
    context = context or {}
    preferences = preferences or {}
    category = None
    for key, aliases in CATEGORY_ALIASES.items():
        if any(alias.lower() in lower for alias in aliases):
            category = key
            break
    if not category:
        category = context.get("category")

    budget_min, budget_max = _extract_budget(lower)
    if budget_max is None:
        budget_min = float(context.get("budget_min") or 0)
        budget_max = context.get("budget_max")

    features = [term for term in FEATURE_TERMS if term.lower() in lower]
    if not features and category == context.get("category"):
        features = list(context.get("features") or [])

    preferred = [brand for brand in KNOWN_BRANDS if brand.lower() in lower]
    preferred.extend(preferences.get("brands") or [])
    preferred = list(dict.fromkeys(preferred))

    avoid_terms = list(preferences.get("avoid_terms") or [])
    avoid_match = re.search(r"(?:不要|避开|不想要|避免)([^，。,.]{1,30})", text)
    if avoid_match:
        avoid_terms.extend(re.split(r"[、和与/]", avoid_match.group(1)))
    avoid_terms = [item.strip() for item in dict.fromkeys(avoid_terms) if item.strip()]

    scenario = "日常使用"
    for candidate in ["通勤", "学生", "运动", "跑步", "商务", "旅行", "儿童"]:
        if candidate in lower:
            scenario = candidate
            break

    missing = [] if category else ["category"]
    confidence = 0.45 + (0.3 if category else 0) + (0.1 if budget_max else 0) + (0.1 if features else 0)
    return Demand(
        category=category,
        category_label=CATEGORY_LABELS.get(category, "待确认"),
        budget_min=round(budget_min, 2),
        budget_max=round(float(budget_max), 2) if budget_max is not None else None,
        features=features,
        brand_preferences=preferred,
        avoid_terms=avoid_terms,
        scenario=scenario,
        confidence=min(round(confidence, 2), 0.95),
        source="rules",
        missing_fields=missing,
    )
