from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=500)
    user_id: str = Field(min_length=1, max_length=80)
    session_id: str = Field(min_length=1, max_length=80)


class PreferenceRequest(BaseModel):
    brands: list[str] = Field(default_factory=list, max_length=10)
    avoid_terms: list[str] = Field(default_factory=list, max_length=10)
    price_sensitivity: int = Field(default=50, ge=0, le=100)
    decision_style: str = Field(default="balanced", pattern="^(conservative|balanced|aggressive)$")


class CartRequest(BaseModel):
    user_id: str
    session_id: str
    product_id: str
    authorized: bool = False
