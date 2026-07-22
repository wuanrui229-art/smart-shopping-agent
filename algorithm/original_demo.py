from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).with_name("original_demo_data.json")
DEMO_DATA: dict[str, dict[str, Any]] = json.loads(DATA_PATH.read_text(encoding="utf-8"))

CATEGORY_ALIASES = {
    "backpack": ["kids backpack", "backpack", "school bag", "书包", "背包", "双肩包"],
    "headphones": ["noise canceling", "noise cancelling", "headphones", "headphone", "headset", "earbuds", "earphone", "耳机", "降噪"],
    "running_shoes": ["running shoes", "running shoe", "sneakers", "sneaker", "jogging", "跑鞋", "运动鞋", "慢跑"],
    "tablet": ["tablet", "ipad", "kindle", "slate", "平板", "平板电脑"],
    "keyboard": ["mechanical keyboard", "keyboard", "keycap", "typing", "键盘", "机械键盘"],
    "smartwatch": ["smart watch", "smartwatch", "fitness tracker", "wearable", "watch", "智能手表", "手表"],
}

SUPPORTED_CATEGORIES_ZH = "儿童书包、耳机、跑鞋、平板、键盘和智能手表"
SUPPORTED_CATEGORIES_EN = "Kids Backpack, Headphones, Running Shoes, Tablet, Keyboard, and Smart Watch"
UNSUPPORTED_CATEGORY_ALIASES = {
    "化妆品": ["化妆品", "美妆", "护肤品", "口红", "粉底", "眼影", "makeup", "cosmetic", "lipstick", "skincare"],
    "服装": ["衣服", "服装", "外套", "裤子", "裙子", "clothes", "clothing", "shirt", "jacket"],
    "手机": ["手机", "智能手机", "phone", "smartphone", "iphone"],
}
GREETING_TERMS = {"hi", "hello", "hey", "你好", "您好", "嗨", "在吗"}
FRUSTRATION_TERMS = ["stupid", "idiot", "dumb", "瞎", "笨", "傻", "不对", "答非所问", "牛头不对马嘴"]


def _uses_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _catalog_boundary_response(user_input: str) -> dict[str, Any]:
    normalized = user_input.casefold().strip(" \t\r\n!?！？。,.，")
    chinese = _uses_chinese(user_input)

    unsupported_label = next(
        (
            label
            for label, aliases in UNSUPPORTED_CATEGORY_ALIASES.items()
            if any(alias.casefold() in normalized for alias in aliases)
        ),
        None,
    )
    if unsupported_label:
        message = (
            f"抱歉，开放品类的大模型服务当前不可用，所以暂时无法为{unsupported_label}生成可靠建议。"
            f"六个内置数据品类仍可离线推荐：{SUPPORTED_CATEGORIES_ZH}。模型服务恢复后，其他品类也可以使用。"
            if chinese
            else f"Sorry, the open-category model service is currently unavailable, so I cannot generate reliable {unsupported_label} guidance. "
            f"The six offline catalog categories still work: {SUPPORTED_CATEGORIES_EN}. Other categories work when the model service is available."
        )
        return {"status": "unsupported_category", "message": message, "questions": list(DEMO_DATA)}

    if any(term in normalized for term in FRUSTRATION_TERMS):
        message = (
            f"抱歉，刚才的回答没有解决你的问题。开放品类模型服务当前不可用；"
            f"现在仍可离线推荐{SUPPORTED_CATEGORIES_ZH}，模型恢复后其他品类也可以使用。"
            if chinese
            else f"Sorry, that response did not solve your problem. The open-category model service is currently unavailable. "
            f"The offline catalog still supports {SUPPORTED_CATEGORIES_EN}, and other categories return when the model service is restored."
        )
        return {"status": "conversation", "message": message}

    if normalized in GREETING_TERMS:
        message = (
            f"你好！我是 Smart Shopping AI。开放式对话服务当前不可用，但仍可离线推荐{SUPPORTED_CATEGORIES_ZH}。"
            if chinese
            else f"Hi! I am Smart Shopping AI. Open chat is currently unavailable, but the offline catalog still supports {SUPPORTED_CATEGORIES_EN}."
        )
        return {"status": "conversation", "message": message}

    if normalized in {"bag", "a bag", "buy a bag", "i want to buy a bag", "鞋", "鞋子", "shoes", "shoe"}:
        message = (
            f"你说的商品比较宽泛。请确认是儿童书包还是跑鞋；当前还支持{SUPPORTED_CATEGORIES_ZH}。"
            if chinese
            else "That category is a little broad. Do you mean Kids Backpack or Running Shoes? "
            f"The demo currently supports {SUPPORTED_CATEGORIES_EN}."
        )
        return {"status": "needs_clarification", "message": message, "questions": list(DEMO_DATA)}

    message = (
        f"开放式大模型服务当前不可用。六个内置数据品类仍可离线推荐：{SUPPORTED_CATEGORIES_ZH}。"
        if chinese
        else f"The open-chat model service is currently unavailable. The offline catalog still supports {SUPPORTED_CATEGORIES_EN}."
    )
    return {"status": "needs_clarification", "message": message, "questions": list(DEMO_DATA)}


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


def recommend_original(
    user_input: str,
    preferences: dict[str, Any] | None = None,
    category_override: str | None = None,
) -> dict[str, Any]:
    category = category_override or detect_category(user_input)
    if category is None:
        return _catalog_boundary_response(user_input)

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
