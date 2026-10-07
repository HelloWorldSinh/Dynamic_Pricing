import uuid
from sqlalchemy import Column, String, Boolean, JSON, BigInteger, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class Product(Base, TimestampMixin):
    """Bảng danh mục sản phẩm chuẩn của FPT Shop (Ground Truth Catalog)."""
    __tablename__ = "products"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # PHONE | LAPTOP
    brand = Column(String(100), nullable=True, index=True)      # Apple, Asus, Dell, Samsung...
    part_number = Column(String(100), nullable=True, index=True)  # Mã Part hãng (vd: 83JC00LVVN)
    specs = Column(JSON, nullable=True)                        # CPU, RAM, Ổ cứng, Màu sắc...
    is_active = Column(Boolean, default=True, nullable=False)

    # Các trường giá phục vụ định giá động (PBI-009 & PBI-010)
    cost_price = Column(BigInteger, default=0, nullable=False)                 # Giá vốn (VND)
    min_margin_pct = Column(Float, default=5.0, nullable=False)                # Biên lợi nhuận tối thiểu (%)
    floor_price = Column(BigInteger, default=0, nullable=False)                # Giá sàn bảo vệ (VND)
    base_retail_price = Column(BigInteger, default=0, nullable=False)          # Giá niêm yết bán lẻ gốc (VND)

    # Relationships
    inventory = relationship("InventoryMock", back_populates="product", uselist=False, cascade="all, delete-orphan")
    inventory_snapshots = relationship("InventorySnapshot", back_populates="product", cascade="all, delete-orphan")
    mappings = relationship("SkuMapping", back_populates="product", cascade="all, delete-orphan")
    demand_events = relationship("DemandEvent", back_populates="product", cascade="all, delete-orphan")
    demand_hourly_aggregates = relationship("DemandHourlyAggregate", back_populates="product", cascade="all, delete-orphan")
    price_recommendations = relationship("PriceRecommendation", back_populates="product", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

