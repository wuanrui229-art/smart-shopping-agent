from algorithm.demand_parser import parse_demand_rules
from algorithm.open_catalog import OpenCatalogChatClient
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


def test_original_demo_handles_conversation_and_catalog_boundaries():
    greeting = recommend_original("hi")
    assert greeting["status"] == "conversation"
    assert "Smart Shopping AI" in greeting["message"]

    unsupported = recommend_original("我要买化妆品")
    assert unsupported["status"] == "unsupported_category"
    assert "模型服务当前不可用" in unsupported["message"]

    broad_bag = recommend_original("i want to buy a bag")
    assert broad_bag["status"] == "needs_clarification"
    assert "Kids Backpack" in broad_bag["message"]

    frustrated = recommend_original("you are so stupid")
    assert frustrated["status"] == "conversation"
    assert "Sorry" in frustrated["message"]


def test_open_catalog_normalizes_any_category_into_three_estimated_options():
    client = OpenCatalogChatClient()
    raw = {
        "intent": "recommendation",
        "language": "zh",
        "reply": "根据你的预算和通勤需求，我整理了三款咖啡机。",
        "category_label": "Coffee Machine",
        "supported_category": None,
        "demand_summary": "预算 200 美元，适合办公室使用",
        "budget_label": "$100–$200",
        "key_concerns": ["清洁方便", "出杯速度"],
        "market_notes": ["胶囊机操作更简单"],
        "recommendations": [
            {
                "title": f"Demo Coffee Machine {index}",
                "brand": "Demo",
                "estimated_price_usd": 99 + index * 20,
                "fit_score": 90 - index,
                "value_score": 88 - index,
                "durability_score": 84 - index,
                "feature_score": 86 - index,
                "user_satisfaction": 87 - index,
                "rationale": "适合办公室快速制作咖啡",
                "pros": ["操作简单"],
                "cons": ["价格需要核验"],
                "keywords": ["快捷", "易清洁"],
            }
            for index in range(3)
        ],
    }

    result = client._normalize(raw, "推荐办公室咖啡机", {})

    assert result["status"] == "success"
    assert result["mode"] == "llm-open-catalog"
    assert len(result["recs"]) == 3
    assert all(item["estimated"] is True for item in result["recs"])
    assert "not live data" in result["source_note"]


def test_explicit_openai_key_overrides_vercel_runtime_oidc(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "test-vercel-oidc")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")
    client = OpenCatalogChatClient()
    captured = {}

    def fake_post(payload, api_key, base_url):
        captured.update({"model": payload["model"], "api_key": api_key, "base_url": base_url})
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"intent":"chat","language":"zh","reply":"你好！","category_label":"","supported_category":null,"demand_summary":"","budget_label":"","key_concerns":[],"market_notes":[],"recommendations":[]}'
                    }
                }
            ]
        }

    monkeypatch.setattr(client, "_post", fake_post)
    result = client.respond("你好", runtime_oidc_token="request-oidc-token")

    assert result["status"] == "conversation"
    assert captured == {
        "model": "gpt-5-mini",
        "api_key": "test-openai-key",
        "base_url": "https://api.openai.com/v1",
    }


def test_kimi_key_enables_open_catalog_and_overrides_vercel_oidc(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "kimi")
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-kimi-key")
    monkeypatch.setenv("MOONSHOT_MODEL", "kimi-k3")
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "test-vercel-oidc")
    client = OpenCatalogChatClient()
    captured = {}

    def fake_post(payload, api_key, base_url):
        captured.update({
            "model": payload["model"],
            "api_key": api_key,
            "base_url": base_url,
            "response_format": payload["response_format"],
            "reasoning_effort": payload.get("reasoning_effort"),
        })
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"intent":"chat","language":"zh","reply":"你好，我可以自由聊天并推荐任意消费品类。","category_label":"","supported_category":null,"demand_summary":"","budget_label":"","key_concerns":[],"market_notes":[],"recommendations":[]}'
                    }
                }
            ]
        }

    monkeypatch.setattr(client, "_post", fake_post)
    result = client.respond("你好", runtime_oidc_token="request-oidc-token")

    assert result["status"] == "conversation"
    assert client.describe("request-oidc-token") == {
        "enabled": True,
        "provider": "kimi-direct",
        "model": "kimi-k3",
    }
    assert captured["model"] == "kimi-k3"
    assert captured["api_key"] == "test-kimi-key"
    assert captured["base_url"] == "https://api.moonshot.ai/v1"
    assert captured["response_format"]["type"] == "json_schema"
    assert captured["reasoning_effort"] == "low"


def test_price_sensitivity_reorders_running_shoe_alternatives():
    query = "我想买一双适合日常训练的跑鞋"
    default = recommend_original(query, {"price_sensitivity": 50, "decision_style": "balanced"})
    price_focused = recommend_original(query, {"price_sensitivity": 100, "decision_style": "balanced"})

    assert "HOKA" in default["recs"][1]["title"]
    assert "ASICS" in default["recs"][2]["title"]
    assert "ASICS" in price_focused["recs"][1]["title"]
    assert "HOKA" in price_focused["recs"][2]["title"]
    assert price_focused["algorithm"]["preferences_applied"] is True
