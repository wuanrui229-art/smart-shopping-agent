from algorithm.demand_parser import parse_demand_rules
from algorithm.original_demo import detect_category, recommend_original
from algorithm.pipeline import ShoppingPipeline
from algorithm.review_analyzer import analyze_reviews


def test_parse_complex_chinese_demand():
    demand = parse_demand_rules("想买 500 元以内、适合通勤的防水轻量双肩包")
    assert demand.category == "backpack"
    assert demand.budget_max == 500
    assert "防水" in demand.features
    assert "轻量" in demand.features
    assert demand.scenario == "通勤"


def test_missing_category_requires_clarification():
    result = ShoppingPipeline().run("预算 500 元，要轻一点")
    assert result["status"] == "needs_clarification"
    assert "category" in result["demand"]["missing_fields"]


def test_multi_turn_context_inherits_category():
    context = parse_demand_rules("我想买蓝牙耳机").to_dict()
    demand = parse_demand_rules("预算改为 700 元，还要主动降噪", context=context)
    assert demand.category == "headphones"
    assert demand.budget_max == 700
    assert "主动降噪" in demand.features


def test_duplicate_reviews_lower_credibility():
    normal = [
        {"rating": 5, "text": "音质清晰，连接稳定，续航表现很好。", "verified": True, "days_ago": 3},
        {"rating": 4, "text": "佩戴舒服，通勤降噪效果明显。", "verified": True, "days_ago": 42},
        {"rating": 3, "text": "充电盒容易出现轻微划痕。", "verified": True, "days_ago": 90},
    ]
    spam = [{"rating": 5, "text": "很好很好必须买", "verified": False, "days_ago": 1}] * 3
    assert analyze_reviews(normal).credibility_score > analyze_reviews(spam).credibility_score


def test_pipeline_returns_auditable_top_three():
    result = ShoppingPipeline().run("预算 700 元，想买主动降噪长续航的蓝牙耳机")
    assert result["status"] == "success"
    assert len(result["recommendations"]) == 3
    assert result["recommendations"][0]["role"] == "主推"
    assert result["weights"] == {"credibility": 0.4, "match": 0.3, "price": 0.2, "rating": 0.1}
    assert result["recommendations"][0]["overall_score"] >= result["recommendations"][1]["overall_score"]


def test_original_week7_catalog_supports_all_six_categories():
    queries = ["Kids Backpack", "Headphones", "Running Shoes", "Tablet", "Keyboard", "Smart Watch"]
    for query in queries:
        result = recommend_original(query)
        assert result["status"] == "success"
        assert len(result["recs"]) == 3
        assert result["recs"][0]["rank"] == 1


def test_original_category_detection_is_phrase_aware():
    assert detect_category("I need a smart watch for fitness") == "smartwatch"
    assert detect_category("Recommend running shoes") == "running_shoes"
