import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey, String, Boolean, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID


class InventoryMock(Base):
    """Bảng lưu dữ liệu tồn kho giả lập của FPT Shop (PBI-009)."""
    __tablename__ = "inventory_mock"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    fpt_product_id = Column(GUID(), ForeignKey("products.id"), unique=True, nullable=False, index=True)

    stock_quantity = Column(Integer, default=0, nullable=False)   # Lượng tồn kho
    doh = Column(Integer, default=0, nullable=False)              # Days On Hand (Số ngày tồn kho)
    cost_price = Column(BigInteger, nullable=False)               # Giá vốn (VND)
    floor_price = Column(BigInteger, nullable=False)              # Giá sàn bảo vệ (VND)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="inventory")


class Warehouse(Base):
    """Danh mục trung tâm kho hàng chính (Hà Nội, TP.HCM, Đà Nẵng)."""
    __tablename__ = "warehouses"

    warehouse_id = Column(String(50), primary_key=True)                 # WH-HN-01 | WH-HCM-01 | WH-DN-01
    warehouse_name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)                         # NORTH | SOUTH | CENTRAL

    # Relationships
    snapshots = relationship("InventorySnapshot", back_populates="warehouse", cascade="all, delete-orphan")


class InventorySnapshot(Base):
    """Ảnh chụp tồn kho chi tiết phục vụ tính toán DOH và rủi ro tồn kho (PBI-009 Multi-warehouse)."""
    __tablename__ = "inventory_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    fpt_product_id = Column(GUID(), ForeignKey("products.id"), nullable=False, index=True)
    warehouse_id = Column(String(50), ForeignKey("warehouses.warehouse_id"), nullable=False, index=True)
    snapshot_ts = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    qty_on_hand = Column(Integer, default=0, nullable=False)            # Tồn kho vật lý
    qty_reserved = Column(Integer, default=0, nullable=False)           # Hàng đã khóa (cọc/chờ giao)
    qty_available = Column(Integer, default=0, nullable=False)          # Hàng khả dụng (on_hand - reserved)
    target_stock = Column(Integer, default=0, nullable=False)           # Tồn kho mục tiêu
    safety_stock = Column(Integer, default=0, nullable=False)           # Tồn kho an toàn
    reorder_level = Column(Integer, default=0, nullable=False)          # Ngưỡng đặt hàng lại
    stock_cover_days = Column(Integer, default=0, nullable=False)       # DOH (Days On Hand)
    is_obsolescence_risk = Column(Boolean, default=False, nullable=False, index=True)  # Cảnh báo rủi ro lỗi thời
    holding_cost_pct_monthly = Column(Float, default=1.5, nullable=False)              # Chi phí lưu kho %
    competitor_oos_count = Column(Integer, default=0, nullable=False)                  # Số đối thủ hết hàng

    # Relationships
    product = relationship("Product", back_populates="inventory_snapshots")
    warehouse = relationship("Warehouse", back_populates="snapshots")

