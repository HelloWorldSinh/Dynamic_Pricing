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

    # Enriched product and inventory fields for Frontend consumption
    sku: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    cost_price: Optional[int] = None
    floor_price: Optional[int] = None
    current_price: Optional[int] = None
    suggested_price: Optional[int] = None
    is_floor_protected: Optional[bool] = None
    doh: Optional[int] = None
    inventory_quantity: Optional[int] = None
    min_competitor_price: Optional[int] = None
    competitor_name: Optional[str] = None
    competitor_in_stock: Optional[bool] = None
    cellphones_price: Optional[int] = None
    cellphones_in_stock: Optional[bool] = None
    hoangha_price: Optional[int] = None
    hoangha_in_stock: Optional[bool] = None
    scenario: Optional[str] = None
    margin_impact_percent: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class PriceRecommendationListResponse(BaseModel):
    """Phan hoi danh sach de xuat gia kem tong so ban ghi."""
    total: int
    items: List[PriceRecommendationResponse]

    model_config = ConfigDict(from_attributes=True)


class ApplyCustomPriceRequest(BaseModel):
    """Yeu cau ap dung muc gia tuy bien."""
    custom_price: int = Field(gt=0, description="Muc gia moi tuy chinh (VND)")
    change_type: str = Field(default="MANUAL_CONFIG", description="Loai thay doi: MANUAL_CONFIG hoac AI_RECOMMENDED")
    reviewed_by: str = Field(default="Pricing Analyst", description="Nguoi thuc hien ap dung gia")


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


class MatrixSimulationRequest(BaseModel):
    """Yeu cau mo phong tinh toan goi y gia theo ma tran tin hieu."""
    demand_score: float = Field(ge=-2.0, le=2.0, description="Diem nhu cau (-2.0 den +2.0)")
    inventory_score: float = Field(ge=-2.0, le=2.0, description="Diem ton kho (-2.0 den +2.0)")
    competitor_score: float = Field(ge=-2.0, le=2.0, description="Diem doi thu (-2.0 den +2.0)")
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Trong so tuy bien D, I, C. Mac dinh 0.40, 0.35, 0.25",
    )
    current_price: int = Field(gt=0, description="Gia ban hien tai FPT Shop (VND)")
    cost_price: int = Field(ge=0, description="Gia von nhap kho (VND)")
    floor_price: int = Field(ge=0, description="Gia san toi thieu cho phep (VND)")
    competitor_price: Optional[int] = Field(default=None, description="Gia thap nhat cua doi thu canh tranh (VND)")
    max_rate_cap: float = Field(default=0.10, gt=0, le=0.50, description="Tran bien do thay doi toi da (mac dinh 0.10)")


class MatrixSimulationResponse(BaseModel):
    """Ket qua phan tich mo phong ma tran dinh gia."""
    demand_score: float
    inventory_score: float
    competitor_score: float
    composite_score: float
    scenario_name: str
    action_type: str
    target_delta_pct: float
    current_price: int
    recommended_price: int
    price_delta_amount: int
    price_delta_pct: float
    is_floor_capped: bool
    guardrail_notes: List[str]
    rationale: str


class CompetitorPriceInfo(BaseModel):
    """Thong tin gia doi thu canh tranh duoc map."""
    source: str
    price: int
    url: str
    is_in_stock: bool
    product_name: str
    matched_at: Optional[str] = None


class PriceComparisonItem(BaseModel):
    """Ban ghi ma tran so sanh gia 3 ben FPT Shop, CellphoneS, Hoang Ha."""
    id: str
    sku: str
    name: str
    category: str
    brand: str
    part_number: Optional[str] = None
    fpt_price: int
    cellphones: Optional[CompetitorPriceInfo] = None
    hoangha: Optional[CompetitorPriceInfo] = None
    min_competitor_price: int
    price_diff: int
    price_diff_percent: float
    confidence_score: float
    match_tier: str
    doh: int
    inventory_quantity: int
    cost_price: int
    floor_price: int
    status: str


class PriceChangeHistoryItem(BaseModel):
    """Ban ghi lich su thay doi gia phuc vu Frontend."""
    id: str
    sku: str
    product_name: str
    category: str
    old_price: int
    new_price: int
    price_change: int
    price_change_percent: float
    cost_price: int
    floor_price: int
    margin_percent: float
    change_type: str
    scenario: str
    changed_by: str
    changed_at: str
    status: str


