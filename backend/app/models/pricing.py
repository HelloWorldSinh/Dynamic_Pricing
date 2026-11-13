import uuid
from sqlalchemy import Column, String, BigInteger, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID
from app.utils.datetime_utils import get_vietnam_now


class PriceRecommendation(Base):
    """Bảng đề xuất thay đổi giá tự động từ Dynamic Pricing Engine (PBI-010, PBI-011, PBI-012)."""
    __tablename__ = "price_recommendations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    fpt_product_id = Column(GUID(), ForeignKey("products.id"), nullable=False, index=True)

    current_fpt_price = Column(BigInteger, nullable=False)               # Giá hiện tại của FPT Shop (VND)
    competitor_min_price = Column(BigInteger, nullable=True)            # Giá đối thủ thấp nhất còn hàng (VND)
    recommended_price = Column(BigInteger, nullable=False)              # Giá đề xuất điều chỉnh (VND)
    price_delta_amount = Column(BigInteger, nullable=False)             # Mức chênh lệch tiền tuyệt đối
    price_delta_pct = Column(Float, nullable=False)                     # Mức chênh lệch % (-15% đến +15%)

    demand_score = Column(Float, nullable=False)                        # Điểm nhu cầu (-2.0 đến +2.0)
    inventory_score = Column(Float, nullable=False)                     # Điểm tồn kho (-2.0 đến +2.0)
    competitor_score = Column(Float, nullable=False)                    # Điểm đối thủ (-2.0 đến +2.0)
    composite_score = Column(Float, nullable=False, index=True)         # Điểm tổng hợp 0.4D + 0.35I + 0.25C

    scenario_name = Column(String(100), nullable=False)                 # Tên kịch bản (Strong Raise, Clearance, Hold...)
    reasoning_3layers = Column(JSON, nullable=False)                    # {competitor_factor, inventory_factor, floor_protection_factor}
    is_floor_capped = Column(Boolean, default=False, nullable=False)    # Cờ cảnh báo giá chạm sàn

    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING | APPROVED | REJECTED
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_vietnam_now, nullable=False, index=True)

    # Relationships
    product = relationship("Product", back_populates="price_recommendations")
    audit_logs = relationship(
        "PricingAuditLog",
        primaryjoin="and_(PricingAuditLog.entity_id == PriceRecommendation.id, PricingAuditLog.entity_type == 'price_recommendations')",
        foreign_keys="PricingAuditLog.entity_id",
        cascade="all, delete-orphan",
    )


class PriceHistory(Base):
    """Bảng lưu lịch sử biến động giá theo thời gian phục vụ vẽ biểu đồ (PBI-013)."""
    __tablename__ = "price_history"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    fpt_product_id = Column(GUID(), ForeignKey("products.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)             # FPTSHOP | CELLPHONES | HOANGHA
    price = Column(BigInteger, nullable=True)                          # Giá ghi nhận (VND)
    is_in_stock = Column(Boolean, default=True, nullable=False)         # Tình trạng còn hàng
    recorded_at = Column(DateTime, default=get_vietnam_now, nullable=False, index=True)

    # Các trường mở rộng lưu chi tiết biến động giá và đồng bộ
    old_price = Column(BigInteger, nullable=True)
    new_price = Column(BigInteger, nullable=True)
    price_change = Column(BigInteger, nullable=True)
    price_change_percent = Column(Float, nullable=True)
    cost_price = Column(BigInteger, nullable=True)
    floor_price = Column(BigInteger, nullable=True)
    change_type = Column(String(50), nullable=True)
    scenario = Column(String(255), nullable=True)
    changed_by = Column(String(100), nullable=True)
    changed_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="price_history")

    def __init__(self, **kwargs):
        if "price" not in kwargs and "new_price" in kwargs:
            kwargs["price"] = kwargs["new_price"]
        super().__init__(**kwargs)


class PricingAuditLog(Base):
    """Bảng ghi vết kiểm toán các thao tác của chuyên viên giá (PBI-016)."""
    __tablename__ = "pricing_audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    actor = Column(String(100), nullable=False)                         # Tên người dùng thao tác
    action = Column(String(50), nullable=False)                         # APPROVE_PRICE | REJECT_PRICE | TRIGGER_CRAWL | APPROVE_MAPPING
    entity_type = Column(String(50), nullable=False)                    # price_recommendations | sku_mappings
    entity_id = Column(GUID(), nullable=True, index=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=get_vietnam_now, nullable=False)

    # Relationships
    price_recommendation = relationship(
        "PriceRecommendation",
        primaryjoin="and_(PricingAuditLog.entity_id == PriceRecommendation.id, PricingAuditLog.entity_type == 'price_recommendations')",
        foreign_keys=[entity_id],
        overlaps="audit_logs",
    )
