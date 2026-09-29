from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductOut

router = APIRouter()


@router.get(
    "",
    response_model=List[ProductOut],
    summary="Danh sách sản phẩm chuẩn FPT Shop",
    description="Lấy danh mục sản phẩm chuẩn của FPT Shop dùng làm mốc so sánh giá với các đối thủ."
)
def list_products(
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category.upper())
    return query.limit(limit).all()


@router.post(
    "",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm sản phẩm FPT Shop mới",
    description="Thêm một sản phẩm chuẩn vào danh mục để theo dõi đối soát giá."
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db)
):
    product = Product(
        sku=product_in.sku,
        name=product_in.name,
        category=product_in.category.upper(),
        brand=product_in.brand,
        part_number=product_in.part_number,
        specs=product_in.specs
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
