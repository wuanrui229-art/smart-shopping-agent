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
