import json

from fastapi.testclient import TestClient

from backend import database
from backend.app import app, open_catalog


def make_client(tmp_path):
    database.DB_PATH = tmp_path / "test.db"
    database.init_db()
    return TestClient(app)


def test_health_and_chat(tmp_path):
    with make_client(tmp_path) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        response = client.post("/api/chat", json={"user_input": "500 元内防水双肩包", "user_id": "u1", "session_id": "s1"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        sessions = client.get("/api/sessions/u1").json()
        assert sessions[0]["session_id"] == "s1"


def test_vercel_runtime_oidc_header_enables_open_catalog(tmp_path, monkeypatch):
    captured = {}

    def fake_respond(user_input, history, preferences, runtime_oidc_token):
        captured["token"] = runtime_oidc_token
        return {
            "status": "conversation",
            "message": "你好，我可以帮你比较任意消费品类。",
            "mode": "llm-open-chat",
            "model": "openai/gpt-5.4-mini",
        }

    monkeypatch.setattr(open_catalog, "respond", fake_respond)
    headers = {"x-vercel-oidc-token": "test-runtime-token"}
    with make_client(tmp_path) as client:
        health = client.get("/api/health", headers=headers).json()
        response = client.post(
            "/api/original/chat",
            headers=headers,
            json={"user_input": "你好", "user_id": "oidc-user", "session_id": "oidc-session"},
        )

    assert health["open_catalog_enabled"] is True
    assert response.json()["status"] == "conversation"
    assert captured["token"] == "test-runtime-token"


def test_original_week7_chat_endpoint(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/original/chat",
            json={"user_input": "Show me Headphones", "user_id": "original-user", "session_id": "original-session"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["result"]["cat"] == "Headphones"
        assert len(payload["result"]["recs"]) == 3
        assert payload["meta"]["transport"] == "http-json"


def test_original_week7_stream_reports_backend_stages(tmp_path):
    with make_client(tmp_path) as client:
        with client.stream(
            "POST",
            "/api/original/chat/stream",
            json={"user_input": "Show me Keyboard", "user_id": "stream-user", "session_id": "stream-session"},
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/x-ndjson")
            events = [json.loads(line) for line in response.iter_lines() if line]

        stages = [event.get("stage") for event in events]
        assert stages == ["received", "preferences", "category", "reviews", "ranking", "complete"]
        assert events[-1]["type"] == "result"
        payload = events[-1]["payload"]
        assert payload["status"] == "success"
        assert payload["result"]["cat"] == "Keyboard"
        assert payload["meta"]["transport"] == "ndjson-stream"


def test_inline_preferences_keep_serverless_ranking_deterministic(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/original/chat",
            json={
                "user_input": "我想买一双适合日常训练的跑鞋",
                "user_id": "vercel-user",
                "session_id": "vercel-session",
                "preferences": {
                    "brands": [],
                    "avoid_terms": [],
                    "price_sensitivity": 100,
                    "decision_style": "balanced",
                },
            },
        )
        assert response.status_code == 200
        recommendations = response.json()["result"]["recs"]
        assert "ASICS" in recommendations[1]["title"]
        assert "HOKA" in recommendations[2]["title"]
        assert response.json()["result"]["algorithm"]["preferences_applied"] is True


def test_original_chat_returns_contextual_non_catalog_answers(tmp_path):
    with make_client(tmp_path) as client:
        greeting = client.post(
            "/api/original/chat",
            json={"user_input": "hi", "user_id": "chat-user", "session_id": "chat-session-1"},
        )
        cosmetics = client.post(
            "/api/original/chat",
            json={"user_input": "我要买化妆品", "user_id": "chat-user", "session_id": "chat-session-2"},
        )

        assert greeting.status_code == 200
        assert greeting.json()["status"] == "conversation"
        assert cosmetics.status_code == 200
        assert cosmetics.json()["status"] == "unsupported_category"
        assert "化妆品" in cosmetics.json()["message"]


def test_session_history_can_be_deleted_individually_or_all_at_once(tmp_path):
    with make_client(tmp_path) as client:
        for session_id in ("history-1", "history-2"):
            response = client.post(
                "/api/original/chat",
                json={"user_input": "hi", "user_id": "history-user", "session_id": session_id},
            )
            assert response.status_code == 200

        deleted = client.delete("/api/sessions/history-user/history-1")
        assert deleted.status_code == 200
        assert deleted.json() == {"deleted": True}
        assert client.get("/api/sessions/history-user/history-1").status_code == 404
        assert [item["session_id"] for item in client.get("/api/sessions/history-user").json()] == ["history-2"]

        deleted_all = client.delete("/api/sessions/history-user")
        assert deleted_all.status_code == 200
        assert deleted_all.json() == {"deleted": 1}
        assert client.get("/api/sessions/history-user").json() == []
        assert client.get("/api/sessions/history-user/history-2").status_code == 404


def test_preferences_round_trip(tmp_path):
    with make_client(tmp_path) as client:
        payload = {"brands": ["SoundPeak"], "avoid_terms": ["漏音"], "price_sensitivity": 75, "decision_style": "conservative"}
        response = client.put("/api/preferences/u2", json=payload)
        assert response.status_code == 200
        assert client.get("/api/preferences/u2").json() == payload


def test_cart_requires_explicit_authorization(tmp_path):
    with make_client(tmp_path) as client:
        denied = client.post("/api/cart/confirm", json={"user_id": "u3", "session_id": "s3", "product_id": "BP-101", "authorized": False})
        assert denied.status_code == 400
        allowed = client.post("/api/cart/confirm", json={"user_id": "u3", "session_id": "s3", "product_id": "BP-101", "authorized": True})
        assert allowed.status_code == 200
        assert allowed.json()["status"] == "demo_confirmed"
