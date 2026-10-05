from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class GenerateRecommendationsRequest(BaseModel):
    """Yeu cau sinh de xuat gia cho mot san pham hoac toan bo danh muc."""
    fpt_product_id: Optional[UUID] = Field(
        default=None,
        description="ID san pham FPT Shop can tinh toan. Neu null, sinh de xuat cho toan bo san pham active.",
    )
    custom_weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Trong so tuy bien cac tin hieu D (Demand), I (Inventory), C (Competitor). Mac dinh 0.4, 0.35, 0.25.",
    )


class PriceRecommendationResponse(BaseModel):
    """Thong tin chi tiet mot ban ghi de xuat thay doi gia."""
    id: UUID
    fpt_product_id: UUID
    current_fpt_price: int
    competitor_min_price: Optional[int] = None
    recommended_price: int
    price_delta_amount: int
    price_delta_pct: float
    demand_score: float
    inventory_score: float
    competitor_score: float
    composite_score: float
    scenario_name: str
    reasoning_3layers: Dict[str, Any]
    is_floor_capped: bool
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceRecommendationListResponse(BaseModel):
    """Phan hoi danh sach de xuat gia kem tong so ban ghi."""
    total: int
    items: List[PriceRecommendationResponse]

    model_config = ConfigDict(from_attributes=True)


class RecommendationActionRequest(BaseModel):
    """Yeu cau phe duyet hoac tu choi de xuat gia."""
    action: str = Field(description="Hanh dong: APPROVE hoac REJECT")
    reviewed_by: str = Field(description="Nguoi thuc hien kiem duyet")
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Ly do tu choi (bat buoc hoac khuyen nghi khi action la REJECT)",
    )


class PricingAuditLogResponse(BaseModel):
    """Thong tin chi tiet mot ban ghi nhat ky kiem toan gia."""
    id: UUID
    actor: str
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PricingAuditLogListResponse(BaseModel):
    """Phan hoi danh sach nhat ky kiem toan gia."""
    total: int
    items: List[PricingAuditLogResponse]

    model_config = ConfigDict(from_attributes=True)
