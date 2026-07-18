from __future__ import annotations

from collections import Counter

from .models import ReviewAnalysis


POSITIVE_TERMS = ["防水", "舒适", "稳定", "轻", "耐用", "透气", "方便", "顺滑", "扎实", "均衡", "回弹", "保护"]
NEGATIVE_TERMS = ["断连", "进水", "异味", "偏重", "闷", "划痕", "漏音", "不耐脏", "抓地一般", "价格偏高", "故障"]


def analyze_reviews(reviews: list[dict]) -> ReviewAnalysis:
    if not reviews:
        return ReviewAnalysis(40, "中风险", 0, 0, {"positive": 0, "neutral": 100, "negative": 0}, [], [], ["评论样本不足"])
    normalized = ["".join(str(r.get("text", "")).lower().split()) for r in reviews]
    counts = Counter(normalized)
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    duplicate_ratio = duplicate_count / len(reviews)
    verified_ratio = sum(bool(r.get("verified")) for r in reviews) / len(reviews)
    detailed_ratio = sum(len(str(r.get("text", ""))) >= 14 for r in reviews) / len(reviews)
    time_diversity = min(len({r.get("days_ago") for r in reviews}) / len(reviews), 1)
    credibility = 100 * (
        0.35 * verified_ratio
        + 0.25 * (1 - duplicate_ratio)
        + 0.20 * detailed_ratio
        + 0.20 * time_diversity
    )
    ratings = [float(r.get("rating", 3)) for r in reviews]
    positive = sum(r >= 4 for r in ratings)
    negative = sum(r <= 2 for r in ratings)
    neutral = len(ratings) - positive - negative
    sentiment = {
        "positive": round(positive / len(ratings) * 100, 1),
        "neutral": round(neutral / len(ratings) * 100, 1),
        "negative": round(negative / len(ratings) * 100, 1),
    }
    joined = " ".join(str(r.get("text", "")) for r in reviews)
    pros = [term for term in POSITIVE_TERMS if term in joined][:3] or ["整体口碑稳定"]
    cons = [term for term in NEGATIVE_TERMS if term in joined][:3] or ["未发现集中性严重问题"]
    flags = []
    if duplicate_ratio >= 0.3:
        flags.append("重复评论比例偏高")
    if verified_ratio < 0.6:
        flags.append("已验证购买占比较低")
    if time_diversity < 0.6:
        flags.append("评论发布时间过于集中")
    if negative / len(ratings) >= 0.3:
        flags.append("低分评论占比偏高")
    score = round(max(0, min(100, credibility)), 1)
    risk = "低风险" if score >= 70 else "中风险" if score >= 40 else "高风险"
    return ReviewAnalysis(score, risk, round(verified_ratio * 100, 1), round(duplicate_ratio * 100, 1), sentiment, pros, cons, flags)
