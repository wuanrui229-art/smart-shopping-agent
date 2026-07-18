from __future__ import annotations

from statistics import mean
from typing import Any

from .catalog import PRODUCTS
from .models import Demand
from .review_analyzer import analyze_reviews


WEIGHTS = {"credibility": 0.40, "match": 0.30, "price": 0.20, "rating": 0.10}


def _match_score(product: dict, demand: Demand) -> float:
    searchable = " ".join([product["title"], *product["features"]]).lower()
    if demand.features:
        feature_score = sum(feature.lower() in searchable for feature in demand.features) / len(demand.features) * 80
    else:
        feature_score = 65
    if demand.brand_preferences:
        feature_score += 15 if product["brand"] in demand.brand_preferences else -5
    for term in demand.avoid_terms:
        if term.lower() in searchable:
            feature_score -= 30
    if demand.scenario != "日常使用" and demand.scenario.lower() in searchable:
        feature_score += 10
    return round(max(0, min(100, feature_score)), 1)


def recommend(demand: Demand) -> dict[str, Any]:
    candidates = [p for p in PRODUCTS if p["category"] == demand.category]
    notes: list[str] = []
    if demand.budget_max is not None:
        within_budget = [p for p in candidates if demand.budget_min <= p["price"] <= demand.budget_max]
        if len(within_budget) >= 3:
            candidates = within_budget
        else:
            notes.append("预算内不足 3 款，已保留最接近预算的候选并明确标注价格差异。")
    if not candidates:
        return {"recommendations": [], "comparison": [], "market": {}, "notes": ["当前演示目录中没有匹配商品。"]}

    prices = [p["price"] for p in candidates]
    low, high = min(prices), max(prices)
    scored = []
    for product in candidates:
        review = analyze_reviews(product["reviews"])
        match = _match_score(product, demand)
        price = 85 if high == low else 55 + 40 * (high - product["price"]) / (high - low)
        if demand.budget_max and product["price"] > demand.budget_max:
            price = max(0, price - min(50, (product["price"] - demand.budget_max) / demand.budget_max * 100))
        rating = product["rating"] / 5 * 100
        overall = (
            review.credibility_score * WEIGHTS["credibility"]
            + match * WEIGHTS["match"]
            + price * WEIGHTS["price"]
            + rating * WEIGHTS["rating"]
        )
        score_detail = {
            "credibility": review.credibility_score,
            "match": round(match, 1),
            "price": round(price, 1),
            "rating": round(rating, 1),
        }
        reasons = [
            f"评论可信度 {review.credibility_score:.0f} 分（权重 40%）",
            f"需求匹配度 {match:.0f} 分（权重 30%）",
            f"价格竞争力 {price:.0f} 分（权重 20%）",
        ]
        risk_text = "；".join(review.risk_flags) if review.risk_flags else "未发现集中性评论风险"
        scored.append({
            "id": product["id"], "title": product["title"], "brand": product["brand"],
            "price": product["price"], "rating": product["rating"], "review_count": product["review_count"],
            "features": product["features"], "overall_score": round(overall, 1), "score_detail": score_detail,
            "review_analysis": review.to_dict(), "reasons": reasons, "risk_warning": risk_text,
            "purchase_url": f"https://www.amazon.com/s?k={product['id']}",
        })
    scored.sort(key=lambda item: item["overall_score"], reverse=True)
    top = scored[:3]
    for index, item in enumerate(top, start=1):
        item["rank"] = index
        item["role"] = "主推" if index == 1 else "备选"
    comparison = [
        {
            "title": item["title"], "price": item["price"], "rating": item["rating"],
            "credibility": item["score_detail"]["credibility"], "match": item["score_detail"]["match"],
            "overall": item["overall_score"],
        }
        for item in top
    ]
    return {
        "recommendations": top,
        "comparison": comparison,
        "market": {
            "candidate_count": len(candidates), "price_min": low, "price_max": high,
            "average_rating": round(mean(p["rating"] for p in candidates), 2),
            "reviews_analyzed": sum(len(p["reviews"]) for p in candidates),
        },
        "notes": notes,
        "weights": WEIGHTS,
    }
