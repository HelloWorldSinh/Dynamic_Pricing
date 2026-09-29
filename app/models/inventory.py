import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey
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
