from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from uuid import UUID


@dataclass
class SignalScores:
    """Điểm số 3 nhóm tín hiệu thị trường D, I, C (-2.0 đến +2.0)."""
    demand_score: float
    inventory_score: float
    competitor_score: float

    def composite(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Tính điểm tổng hợp Composite Score."""
        w = weights or {"D": 0.40, "I": 0.35, "C": 0.25}
        w_d = w.get("D", 0.40)
        w_i = w.get("I", 0.35)
        w_c = w.get("C", 0.25)
        raw_score = (self.demand_score * w_d) + (self.inventory_score * w_i) + (self.competitor_score * w_c)
        return round(raw_score, 2)


@dataclass
class ScenarioMatch:
    """Kết quả ánh xạ kịch bản và dải hành động."""
    scenario_name: str
    target_delta_pct: float
    action_type: str
    rationale: str


@dataclass
class GuardrailResult:
    """Kết quả sau khi áp dụng các rào cản an toàn (Margin floor, Rate cap, Predatory filter)."""
    final_price: int
    price_delta_amount: int
    price_delta_pct: float
    is_floor_capped: bool
    guardrail_notes: List[str] = field(default_factory=list)


@dataclass
class PricingRecommendationDTO:
    """DTO chứa toàn bộ kết quả đề xuất giá trước khi lưu DB."""
    product_id: UUID
    current_fpt_price: int
    competitor_min_price: Optional[int]
    recommended_price: int
    price_delta_amount: int
    price_delta_pct: float
    demand_score: float
    inventory_score: float
    competitor_score: float
    composite_score: float
    scenario_name: str
    action_type: str
    reasoning_3layers: Dict[str, Any]
    is_floor_capped: bool
