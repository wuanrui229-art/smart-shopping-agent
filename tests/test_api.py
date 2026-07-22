import json

from fastapi.testclient import TestClient

from backend import database
from backend.app import app


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
