from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Demand:
    category: Optional[str] = None
    category_label: str = "待确认"
    budget_min: float = 0
    budget_max: Optional[float] = None
    features: list[str] = field(default_factory=list)
    brand_preferences: list[str] = field(default_factory=list)
    avoid_terms: list[str] = field(default_factory=list)
    scenario: str = "日常使用"
    confidence: float = 0.55
    source: str = "rules"
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewAnalysis:
    credibility_score: float
    risk_level: str
    verified_ratio: float
    duplicate_ratio: float
    sentiment: dict[str, float]
    pros: list[str]
    cons: list[str]
    risk_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
