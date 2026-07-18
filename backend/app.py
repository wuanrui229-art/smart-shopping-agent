from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from algorithm import ShoppingPipeline
from backend import database
from backend.schemas import CartRequest, ChatRequest, PreferenceRequest


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
pipeline = ShoppingPipeline()


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="智选 AI 购物决策系统",
    description="课程作业：前端、后端与大语言模型/可解释算法三层应用",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "shopping-agent", "llm_enabled": pipeline.llm.enabled, "model": pipeline.llm.model if pipeline.llm.enabled else None}


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict:
    database.ensure_session(request.user_id, request.session_id, request.user_input)
    database.save_message(request.session_id, "user", request.user_input)
    context = database.get_last_demand(request.session_id)
    preferences = database.get_preferences(request.user_id)
    result = pipeline.run(request.user_input, context=context, preferences=preferences)
    database.set_last_demand(request.session_id, result.get("demand") or context)
    database.save_message(request.session_id, "assistant", result["message"], result)
    return result


@app.get("/api/sessions/{user_id}")
def sessions(user_id: str) -> list[dict]:
    return database.list_sessions(user_id)


@app.get("/api/sessions/{user_id}/{session_id}")
def session_detail(user_id: str, session_id: str) -> dict:
    result = database.get_session(user_id, session_id)
    if not result:
        raise HTTPException(404, "会话不存在")
    return result


@app.delete("/api/sessions/{user_id}/{session_id}")
def session_delete(user_id: str, session_id: str) -> dict:
    if not database.delete_session(user_id, session_id):
        raise HTTPException(404, "会话不存在")
    return {"deleted": True}


@app.get("/api/preferences/{user_id}")
def preferences_get(user_id: str) -> dict:
    return database.get_preferences(user_id)


@app.put("/api/preferences/{user_id}")
def preferences_put(user_id: str, request: PreferenceRequest) -> dict:
    return database.save_preferences(user_id, request.model_dump())


@app.post("/api/cart/confirm")
def cart_confirm(request: CartRequest) -> dict:
    action_id = database.record_cart_action(request.user_id, request.session_id, request.product_id, request.authorized)
    if not request.authorized:
        raise HTTPException(400, "必须获得用户明确授权后才能执行加购")
    return {
        "status": "demo_confirmed", "action_id": action_id, "product_id": request.product_id,
        "message": "已记录演示加购授权；系统不会连接真实支付或创建真实订单。",
    }


app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
