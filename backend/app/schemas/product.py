from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    sku: str = Field(description="Mã SKU FPT Shop")
    name: str = Field(description="Tên sản phẩm chuẩn")
    category: str = Field(description="Ngành hàng (PHONE / LAPTOP)")
    brand: Optional[str] = None
    part_number: Optional[str] = None
    specs: Optional[Dict[str, Any]] = None


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
