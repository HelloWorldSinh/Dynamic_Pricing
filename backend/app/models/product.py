import uuid
from sqlalchemy import Column, String, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class Product(Base, TimestampMixin):
    """Bảng danh mục sản phẩm chuẩn của FPT Shop."""
    __tablename__ = "products"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # PHONE | LAPTOP
    brand = Column(String(100), nullable=True, index=True)      # Apple, Asus, Dell, Samsung...
    part_number = Column(String(100), nullable=True, index=True)  # Mã Part hãng (vd: 83JC00LVVN)
    specs = Column(JSON, nullable=True)                        # CPU, RAM, Ổ cứng, Màu sắc...
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    inventory = relationship("InventoryMock", back_populates="product", uselist=False, cascade="all, delete-orphan")
    mappings = relationship("SkuMapping", back_populates="product", cascade="all, delete-orphan")
