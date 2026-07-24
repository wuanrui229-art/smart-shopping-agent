from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from algorithm import ShoppingPipeline
from algorithm.open_catalog import OpenCatalogChatClient
from algorithm.original_demo import detect_category, recommend_original
from backend import database
from backend.schemas import CartRequest, ChatRequest, PreferenceRequest


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
pipeline = ShoppingPipeline()
open_catalog = OpenCatalogChatClient()
DEMO_CATEGORY_NAMES = {
    "backpack": "Kids Backpack",
    "headphones": "Headphones",
    "running_shoes": "Running Shoes",
    "tablet": "Tablet",
    "keyboard": "Keyboard",
    "smartwatch": "Smart Watch",
}


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


def _runtime_oidc_token(request: Request) -> str:
    return request.headers.get("x-vercel-oidc-token", "").strip()


@app.get("/api/health")
def health(request: Request) -> dict:
    catalog = open_catalog.describe(_runtime_oidc_token(request))
    return {
        "status": "ok",
        "service": "shopping-agent",
        "llm_enabled": catalog["enabled"] or pipeline.llm.enabled,
        "model": catalog["model"] if catalog["enabled"] else (pipeline.llm.model if pipeline.llm.enabled else None),
        "open_catalog_enabled": catalog["enabled"],
        "model_provider": catalog["provider"] if catalog["enabled"] else None,
    }


def _finish_original_chat(
    request: ChatRequest,
    result: dict,
    request_id: str,
    started_at: float,
    transport: str,
) -> dict:
    if result["status"] != "success":
        message = result["message"]
    else:
        top = result["recs"][0]
        message = result.get("message") or (
            f"Found {len(result['recs'])} great options for {result['cat']}! "
            f"Top Pick: {top['title']} — ${top['price']:.2f}, score {top['score']:.1f}."
        )
        database.set_last_demand(request.session_id, {"category": result["category"], "query": request.user_input})
    payload = {
        "status": result["status"],
        "message": message,
        "result": result,
        "meta": {
            "request_id": request_id,
            "elapsed_ms": round((perf_counter() - started_at) * 1000, 1),
            "transport": transport,
        },
    }
    database.save_message(request.session_id, "assistant", message, payload)
    return payload


def _request_preferences(request: ChatRequest) -> dict:
    if request.preferences is not None:
        return request.preferences.model_dump()
    return database.get_preferences(request.user_id)


def _recommend_for_request(request: ChatRequest, preferences: dict, runtime_oidc_token: str = "") -> dict:
    history = [item.model_dump() for item in request.history]
    llm_result = open_catalog.respond(
        request.user_input,
        history=history,
        preferences=preferences,
        runtime_oidc_token=runtime_oidc_token,
    )
    return llm_result or recommend_original(request.user_input, preferences=preferences)


@app.post("/api/original/chat")
def original_chat(request: ChatRequest, http_request: Request) -> dict:
    started_at = perf_counter()
    request_id = uuid4().hex[:10]
    database.ensure_session(request.user_id, request.session_id, request.user_input)
    database.save_message(request.session_id, "user", request.user_input)
    preferences = _request_preferences(request)
    result = _recommend_for_request(request, preferences, _runtime_oidc_token(http_request))
    return _finish_original_chat(request, result, request_id, started_at, "http-json")


def _ndjson_event(event_type: str, request_id: str, **data: object) -> bytes:
    return (json.dumps({"type": event_type, "request_id": request_id, **data}, ensure_ascii=False) + "\n").encode("utf-8")


@app.post("/api/original/chat/stream")
async def original_chat_stream(request: ChatRequest, http_request: Request) -> StreamingResponse:
    async def generate():
        started_at = perf_counter()
        request_id = uuid4().hex[:10]
        try:
            yield _ndjson_event("stage", request_id, stage="received", message="FastAPI received the shopping request")
            database.ensure_session(request.user_id, request.session_id, request.user_input)
            database.save_message(request.session_id, "user", request.user_input)

            preferences = _request_preferences(request)
            yield _ndjson_event(
                "stage",
                request_id,
                stage="preferences",
                message=f"Loaded preferences · {preferences['decision_style']} decision style",
            )

            category = detect_category(request.user_input)
            category_name = DEMO_CATEGORY_NAMES.get(category, "needs clarification")
            yield _ndjson_event(
                "stage",
                request_id,
                stage="category",
                message=f"Detected category · {category_name}",
            )

            result = _recommend_for_request(request, preferences, _runtime_oidc_token(http_request))
            if result["status"] == "success":
                if result.get("mode") == "llm-open-catalog":
                    yield _ndjson_event(
                        "stage",
                        request_id,
                        stage="candidates",
                        message="Prepared open-category candidates with estimate labels",
                    )
                else:
                    yield _ndjson_event(
                        "stage",
                        request_id,
                        stage="reviews",
                        message="Loaded review statistics from the demo dataset",
                    )
                yield _ndjson_event(
                    "stage",
                    request_id,
                    stage="ranking",
                    message=f"Scored 4 dimensions and ranked {len(result['recs'])} products",
                )

            payload = _finish_original_chat(request, result, request_id, started_at, "ndjson-stream")
            yield _ndjson_event(
                "result",
                request_id,
                stage="complete",
                message="Backend pipeline complete",
                payload=payload,
            )
        except Exception:
            yield _ndjson_event(
                "error",
                request_id,
                stage="failed",
                message="The backend pipeline failed",
                code="INTERNAL_ERROR",
                detail="Please retry the request or use the standard JSON endpoint.",
                retryable=True,
            )

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict:
    database.ensure_session(request.user_id, request.session_id, request.user_input)
    database.save_message(request.session_id, "user", request.user_input)
    context = database.get_last_demand(request.session_id)
    preferences = _request_preferences(request)
    result = pipeline.run(request.user_input, context=context, preferences=preferences)
    database.set_last_demand(request.session_id, result.get("demand") or context)
    database.save_message(request.session_id, "assistant", result["message"], result)
    return result


@app.get("/api/sessions/{user_id}")
def sessions(user_id: str) -> list[dict]:
    return database.list_sessions(user_id)


@app.delete("/api/sessions/{user_id}")
def sessions_delete_all(user_id: str) -> dict:
    return {"deleted": database.delete_all_sessions(user_id)}


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
