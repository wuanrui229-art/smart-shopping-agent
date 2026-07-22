from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = Path("/tmp/shopping_agent.db") if os.getenv("VERCEL") else ROOT / "data" / "shopping_agent.db"
DB_PATH = Path(os.getenv("SHOPPING_DB_PATH", DEFAULT_DB_PATH))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL,
                last_demand TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL, payload TEXT, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT PRIMARY KEY, brands TEXT NOT NULL DEFAULT '[]', avoid_terms TEXT NOT NULL DEFAULT '[]',
                price_sensitivity INTEGER NOT NULL DEFAULT 50, decision_style TEXT NOT NULL DEFAULT 'balanced', updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cart_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, session_id TEXT NOT NULL,
                product_id TEXT NOT NULL, authorized INTEGER NOT NULL, created_at TEXT NOT NULL
            );
            """
        )


def ensure_session(user_id: str, session_id: str, title: str) -> None:
    now = _now()
    with connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO sessions(session_id,user_id,title,created_at,updated_at) VALUES(?,?,?,?,?)",
            (session_id, user_id, title[:40] or "新对话", now, now),
        )


def save_message(session_id: str, role: str, content: str, payload: Optional[dict[str, Any]] = None) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO messages(session_id,role,content,payload,created_at) VALUES(?,?,?,?,?)",
            (session_id, role, content, json.dumps(payload, ensure_ascii=False) if payload else None, _now()),
        )
        db.execute("UPDATE sessions SET updated_at=? WHERE session_id=?", (_now(), session_id))


def set_last_demand(session_id: str, demand: dict[str, Any]) -> None:
    with connect() as db:
        db.execute("UPDATE sessions SET last_demand=?,updated_at=? WHERE session_id=?", (json.dumps(demand, ensure_ascii=False), _now(), session_id))


def get_last_demand(session_id: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT last_demand FROM sessions WHERE session_id=?", (session_id,)).fetchone()
    return json.loads(row["last_demand"]) if row else {}


def list_sessions(user_id: str) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute(
            "SELECT session_id,title,created_at,updated_at FROM sessions WHERE user_id=? ORDER BY updated_at DESC", (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_session(user_id: str, session_id: str) -> Optional[dict[str, Any]]:
    with connect() as db:
        session = db.execute("SELECT * FROM sessions WHERE user_id=? AND session_id=?", (user_id, session_id)).fetchone()
        if not session:
            return None
        rows = db.execute("SELECT role,content,payload,created_at FROM messages WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    messages = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item["payload"]) if item["payload"] else None
        messages.append(item)
    return {"session": dict(session), "messages": messages}


def delete_session(user_id: str, session_id: str) -> bool:
    with connect() as db:
        found = db.execute("SELECT 1 FROM sessions WHERE user_id=? AND session_id=?", (user_id, session_id)).fetchone()
        if not found:
            return False
        db.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        db.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
    return True


def get_preferences(user_id: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT * FROM preferences WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return {"brands": [], "avoid_terms": [], "price_sensitivity": 50, "decision_style": "balanced"}
    return {
        "brands": json.loads(row["brands"]), "avoid_terms": json.loads(row["avoid_terms"]),
        "price_sensitivity": row["price_sensitivity"], "decision_style": row["decision_style"],
    }


def save_preferences(user_id: str, prefs: dict[str, Any]) -> dict[str, Any]:
    with connect() as db:
        db.execute(
            """INSERT INTO preferences(user_id,brands,avoid_terms,price_sensitivity,decision_style,updated_at)
               VALUES(?,?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET brands=excluded.brands,
               avoid_terms=excluded.avoid_terms,price_sensitivity=excluded.price_sensitivity,
               decision_style=excluded.decision_style,updated_at=excluded.updated_at""",
            (user_id, json.dumps(prefs["brands"], ensure_ascii=False), json.dumps(prefs["avoid_terms"], ensure_ascii=False),
             prefs["price_sensitivity"], prefs["decision_style"], _now()),
        )
    return get_preferences(user_id)


def record_cart_action(user_id: str, session_id: str, product_id: str, authorized: bool) -> int:
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO cart_actions(user_id,session_id,product_id,authorized,created_at) VALUES(?,?,?,?,?)",
            (user_id, session_id, product_id, int(authorized), _now()),
        )
        return int(cursor.lastrowid)
