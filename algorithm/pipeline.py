from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .demand_parser import parse_demand_rules
from .llm_client import OpenAIResponsesClient
from .recommender import recommend


class ShoppingPipeline:
    def __init__(self) -> None:
        self.llm = OpenAIResponsesClient()

    def run(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None,
        preferences: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        demand = self.llm.parse_demand(user_input, context)
        if demand is None:
            demand = parse_demand_rules(user_input, context, preferences)
        else:
            preferences = preferences or {}
            demand.brand_preferences = list(dict.fromkeys([*demand.brand_preferences, *(preferences.get("brands") or [])]))
            demand.avoid_terms = list(dict.fromkeys([*demand.avoid_terms, *(preferences.get("avoid_terms") or [])]))

        trace = [
            {"step": "需求解析", "status": "done", "detail": "大模型结构化解析" if demand.source == "openai" else "规则引擎降级解析"},
        ]
        if demand.missing_fields:
            trace.append({"step": "完整性检查", "status": "waiting", "detail": "缺少商品品类"})
            return {
                "status": "needs_clarification",
                "message": "我还需要确认你想购买的商品品类。可以告诉我是双肩包、蓝牙耳机还是跑鞋吗？",
                "questions": ["你想买哪一类商品？", "是否有预算上限？"],
                "demand": demand.to_dict(),
                "trace": trace,
                "mode": "llm" if demand.source == "openai" else "demo",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        trace.extend([
            {"step": "商品检索", "status": "done", "detail": "从演示商品目录筛选候选"},
            {"step": "评论分析", "status": "done", "detail": "计算验证率、重复度、时间分布与情感"},
            {"step": "决策排序", "status": "done", "detail": "可信度 40% + 匹配度 30% + 价格 20% + 评分 10%"},
        ])
        result = recommend(demand)
        if not result["recommendations"]:
            return {
                "status": "no_results", "message": "暂时没有找到匹配商品，请调整品类或预算。",
                "demand": demand.to_dict(), "trace": trace, "mode": "llm" if demand.source == "openai" else "demo",
            }
        primary = result["recommendations"][0]
        result.update({
            "status": "success",
            "message": f"综合评论可信度、需求匹配和价格后，我的主推是「{primary['title']}」，综合得分 {primary['overall_score']:.1f}。",
            "demand": demand.to_dict(),
            "trace": trace,
            "mode": "llm" if demand.source == "openai" else "demo",
            "final_advice": {
                "title": f"主推：{primary['title']}",
                "summary": f"它在评论可信度与需求匹配之间最均衡，当前价格 ¥{primary['price']:.0f}。",
                "authorization_required": True,
                "disclaimer": "演示系统不会真实下单；任何购买动作都必须由用户再次确认。",
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
        return result
