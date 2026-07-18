from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).with_name("original_demo_data.json")
DEMO_DATA: dict[str, dict[str, Any]] = json.loads(DATA_PATH.read_text(encoding="utf-8"))

CATEGORY_ALIASES = {
    "backpack": ["kids backpack", "backpack", "school bag", "bag", "书包", "背包", "双肩包"],
    "headphones": ["noise canceling", "noise cancelling", "headphones", "headphone", "headset", "earbuds", "earphone", "耳机", "降噪"],
    "running_shoes": ["running shoes", "running shoe", "sneakers", "sneaker", "jogging", "shoes", "shoe", "跑鞋", "运动鞋", "慢跑"],
    "tablet": ["tablet", "ipad", "kindle", "slate", "平板", "平板电脑"],
    "keyboard": ["mechanical keyboard", "keyboard", "keycap", "typing", "键盘", "机械键盘"],
    "smartwatch": ["smart watch", "smartwatch", "fitness tracker", "wearable", "watch", "智能手表", "手表"],
}


def detect_category(user_input: str) -> str | None:
    lowered = user_input.casefold()
    matches = [
        (len(alias), category)
        for category, aliases in CATEGORY_ALIASES.items()
        for alias in aliases
        if alias.casefold() in lowered
    ]
    return max(matches, default=(0, None))[1]


def _preference_score(product: dict[str, Any], preferences: dict[str, Any]) -> float:
    analytics = product.get("analytics") or {}
    style = str(preferences.get("decision_style") or "balanced").casefold()
    sensitivity = float(preferences.get("price_sensitivity", 50)) / 100

    value = float(analytics.get("value_score", product.get("score", 0)))
    durability = float(analytics.get("durability_score", product.get("score", 0)))
    features = float(analytics.get("feature_score", product.get("score", 0)))
    satisfaction = float(analytics.get("user_satisfaction", product.get("score", 0)))

    if style == "conservative":
        profile_score = durability * 0.55 + satisfaction * 0.45
    elif style == "aggressive":
        profile_score = features * 0.55 + value * 0.45
    else:
        quality = (durability + features + satisfaction) / 3
        profile_score = value * sensitivity + quality * (1 - sensitivity)

    score = float(product.get("score", 0)) * 0.8 + profile_score * 0.2
    searchable = " ".join(
        [
            str(product.get("title", "")),
            str(product.get("pros", "")),
            str(product.get("cons", "")),
            " ".join(analytics.get("top_keywords") or []),
        ]
    ).casefold()

    preferred_brands = [str(value).casefold() for value in preferences.get("brands") or []]
    if any(brand in searchable for brand in preferred_brands):
        score += 4

    avoid_terms = [str(value).casefold() for value in preferences.get("avoid_terms") or []]
    if any(term in searchable for term in avoid_terms):
        score -= 25

    return round(max(0, min(100, score)), 1)


def recommend_original(user_input: str, preferences: dict[str, Any] | None = None) -> dict[str, Any]:
    category = detect_category(user_input)
    if category is None:
        return {
            "status": "needs_clarification",
            "message": "Which product category are you shopping for?",
            "questions": ["Kids Backpack", "Headphones", "Running Shoes", "Tablet", "Keyboard", "Smart Watch"],
        }

    result = deepcopy(DEMO_DATA[category])
    preferences = preferences or {}
    has_custom_preferences = bool(preferences.get("brands") or preferences.get("avoid_terms")) or int(
        preferences.get("price_sensitivity", 50)
    ) != 50 or str(preferences.get("decision_style") or "balanced").casefold() != "balanced"

    if has_custom_preferences:
        for product in result["recs"]:
            product["score"] = _preference_score(product, preferences)
        result["recs"].sort(key=lambda product: product["score"], reverse=True)

    for rank, product in enumerate(result["recs"], start=1):
        product["rank"] = rank

    result.update(
        {
            "status": "success",
            "category": category,
            "query": user_input,
            "mode": "original-week7-backend",
            "algorithm": {
                "name": "Preference-aware multi-criteria ranking",
                "dimensions": ["value", "durability", "features", "user_satisfaction"],
                "preferences_applied": has_custom_preferences,
            },
        }
    )
    return result
