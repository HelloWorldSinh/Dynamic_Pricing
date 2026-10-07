import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID


class DemandEvent(Base):
    """Bảng lưu luồng sự kiện clickstream & hành vi khách hàng (PBI-014)."""
    __tablename__ = "demand_events"

    event_id = Column(String(100), primary_key=True)
    fpt_product_id = Column(GUID(), ForeignKey("products.id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)         # view | search_click | cart_add | purchase
    event_ts = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    time_on_page_sec = Column(Integer, default=0, nullable=False)
    scroll_depth_pct = Column(Integer, default=0, nullable=False)
    is_repeat_view = Column(Boolean, default=False, nullable=False)
    is_bounce = Column(Boolean, default=False, nullable=False)
    cart_action = Column(String(50), nullable=True)                     # add | remove | abandon
    search_keyword = Column(String(255), nullable=True)
    exit_url_domain = Column(String(255), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="demand_events")


class DemandHourlyAggregate(Base):
    """Bảng tổng hợp nhu cầu người dùng theo từng giờ cho từng SKU (PBI-014 Optimization)."""
    __tablename__ = "demand_hourly_aggregates"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    fpt_product_id = Column(GUID(), ForeignKey("products.id"), nullable=False, index=True)
    aggregate_hour = Column(DateTime, nullable=False, index=True)
    total_views = Column(Integer, default=0, nullable=False)
    search_clicks = Column(Integer, default=0, nullable=False)
    cart_adds = Column(Integer, default=0, nullable=False)
    purchases = Column(Integer, default=0, nullable=False)
    cvr_pct = Column(Float, default=0.0, nullable=False)
    demand_score = Column(Float, default=0.0, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="demand_hourly_aggregates")
