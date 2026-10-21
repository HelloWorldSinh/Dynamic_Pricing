from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.models.inventory import InventoryMock
from app.models.pricing import PriceRecommendation
from app.schemas.ai import (
    CompetitorShift,
    InventoryStatus,
    FloorProtection,
    ExplainableFactors,
)


def get_price_discrepancies(
    db: Session,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    competitor: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Truy vấn danh sách sản phẩm FPT Shop đang bán đắt hơn đối thủ cạnh tranh.
    
    Quy tắc nghiệp vụ:
    1. Chỉ xét đối thủ thực tế còn hàng (CrawlResult.is_in_stock == True).
    2. Cặp SKU đã được phê duyệt (status == 'APPROVED') hoặc có confidence_score >= 0.8.
    3. Giá bán FPT Shop lớn hơn giá bán của đối thủ.
    """
    safe_limit = max(1, min(limit, 10))

    query = (
        db.query(Product, CrawlResult, InventoryMock)
        .join(SkuMapping, SkuMapping.fpt_product_id == Product.id)
        .join(CrawlResult, CrawlResult.id == SkuMapping.competitor_crawl_id)
        .outerjoin(InventoryMock, InventoryMock.fpt_product_id == Product.id)
        .filter(
            CrawlResult.is_in_stock == True,
            or_(
                SkuMapping.status == "APPROVED",
                SkuMapping.confidence_score >= 0.8,
            ),
            CrawlResult.current_price.isnot(None),
            Product.base_retail_price > CrawlResult.current_price,
            Product.base_retail_price > 0,
        )
    )

    if category:
        query = query.filter(func.upper(Product.category) == category.strip().upper())
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand.strip()}%"))
    if competitor:
        query = query.filter(func.upper(CrawlResult.source) == competitor.strip().upper())

    # Sắp xếp theo độ chênh lệch tuyệt đối giảm dần
    query = query.order_by((Product.base_retail_price - CrawlResult.current_price).desc())
    items = query.limit(safe_limit).all()

    results: List[Dict[str, Any]] = []
    for prod, crawl, inv in items:
        fpt_price = int(prod.base_retail_price)
        comp_price = int(crawl.current_price)
        diff_amount = fpt_price - comp_price
        diff_pct = round((diff_amount / comp_price) * 100, 1) if comp_price > 0 else 0.0
        doh_val = inv.doh if inv else 0
        comp_label = "CellphoneS" if crawl.source.upper() == "CELLPHONES" else ("Hoàng Hà" if crawl.source.upper() == "HOANGHA" else crawl.source)

        results.append({
            "SKU": prod.sku,
            "Tên sản phẩm": prod.name,
            "Giá FPT": f"{fpt_price:,}đ".replace(",", "."),
            comp_label: f"{comp_price:,}đ".replace(",", "."),
            "Chênh lệch": f"+{diff_amount:,}đ (+{diff_pct}%)".replace(",", "."),
            "DOH": f"{doh_val} ngày",
        })

    return results


def get_inventory_risks(
    db: Session,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    doh_threshold: int = 45,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Tra cứu các sản phẩm có rủi ro lưu kho cao dựa trên chỉ số DOH (Days On Hand).
    
    Quy tắc phân loại:
    - DOH >= 45 ngày: Rủi ro CAO (Cần kích cầu hoặc bám sát đối thủ hạ giá).
    - 30 <= DOH < 45 ngày: Rủi ro TRUNG BÌNH (Theo dõi sát).
    - DOH < 30 ngày: Rủi ro THẤP (Ổn định).
    """
    safe_limit = max(1, min(limit, 10))

    query = (
        db.query(Product, InventoryMock)
        .join(InventoryMock, InventoryMock.fpt_product_id == Product.id)
        .filter(InventoryMock.doh >= doh_threshold)
    )

    if category:
        query = query.filter(func.upper(Product.category) == category.strip().upper())
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand.strip()}%"))

    query = query.order_by(InventoryMock.doh.desc())
    items = query.limit(safe_limit).all()

    results: List[Dict[str, Any]] = []
    for prod, inv in items:
        if inv.doh >= 45:
            risk_label = "CAO (Cần kích cầu)"
        elif inv.doh >= 30:
            risk_label = "TRUNG BÌNH (Theo dõi)"
        else:
            risk_label = "THẤP (Ổn định)"

        results.append({
            "SKU": prod.sku,
            "Dòng máy": prod.name,
            "Tồn kho": inv.stock_quantity,
            "DOH": f"DOH = {inv.doh} ngày",
            "Rủi ro": risk_label,
        })

    return results


def get_sku_explain_factors(db: Session, sku: str) -> Optional[ExplainableFactors]:
    """
    Trích xuất toàn bộ dữ liệu 3 lớp cho một mã SKU cụ thể để phục vụ thẻ ExplainableCard (PBI-018):
    1. Lớp 1: Biến động giá thị trường đối thủ.
    2. Lớp 2: Hiện trạng tồn kho và DOH của FPT Shop.
    3. Lớp 3: Kiểm tra an toàn giá sàn và biên lợi nhuận.
    """
    # 1. Tìm sản phẩm FPT
    prod = db.query(Product).filter(Product.sku == sku.strip()).first()
    if not prod:
        return None

    # 2. Tìm tồn kho
    inv = db.query(InventoryMock).filter(InventoryMock.fpt_product_id == prod.id).first()
    doh = inv.doh if inv else 0
    quantity = inv.stock_quantity if inv else 0
    doh_risk = "HIGH" if doh >= 45 else ("MEDIUM" if doh >= 30 else "LOW")

    # 3. Tìm đề xuất giá gần nhất
    rec = (
        db.query(PriceRecommendation)
        .filter(PriceRecommendation.fpt_product_id == prod.id)
        .order_by(PriceRecommendation.created_at.desc())
        .first()
    )

    # 4. Tìm đối thủ gần nhất qua SkuMapping
    mapping = (
        db.query(SkuMapping, CrawlResult)
        .join(CrawlResult, CrawlResult.id == SkuMapping.competitor_crawl_id)
        .filter(
            SkuMapping.fpt_product_id == prod.id,
            or_(
                SkuMapping.status == "APPROVED",
                SkuMapping.confidence_score >= 0.8,
            ),
        )
        .order_by(CrawlResult.crawled_at.desc())
        .first()
    )

    if mapping:
        _, crawl = mapping
        comp_name = "CellphoneS" if crawl.source.upper() == "CELLPHONES" else ("Hoàng Hà" if crawl.source.upper() == "HOANGHA" else crawl.source)
        comp_new_price = float(crawl.current_price) if crawl.current_price else float(prod.base_retail_price)
        comp_old_price = float(crawl.original_price) if crawl.original_price else None
        if comp_old_price and comp_old_price > comp_new_price:
            price_cut = comp_old_price - comp_new_price
        else:
            price_cut = max(0.0, float(prod.base_retail_price) - comp_new_price)
        is_in_stock = bool(crawl.is_in_stock)
    else:
        comp_name = "CellphoneS"
        comp_new_price = float(rec.competitor_min_price) if rec and rec.competitor_min_price else float(prod.base_retail_price)
        comp_old_price = None
        price_cut = max(0.0, float(prod.base_retail_price) - comp_new_price)
        is_in_stock = True

    # 5. Tính toán kiểm tra giá sàn
    floor_price = float(inv.floor_price if inv and inv.floor_price > 0 else prod.floor_price)
    suggested_price = float(rec.recommended_price if rec and rec.recommended_price > 0 else prod.base_retail_price)
    is_capped = bool(rec.is_floor_capped) if rec else (suggested_price <= floor_price)

    if floor_price > 0:
        safety_margin = round(((suggested_price - floor_price) / floor_price) * 100, 2)
    else:
        safety_margin = 0.0

    return ExplainableFactors(
        competitor_shift=CompetitorShift(
            competitor=comp_name,
            old_price=comp_old_price,
            new_price=comp_new_price,
            price_cut=price_cut,
            is_in_stock=is_in_stock,
        ),
        inventory_status=InventoryStatus(
            sku=prod.sku,
            doh=doh,
            quantity=quantity,
            doh_risk_level=doh_risk,
        ),
        floor_protection=FloorProtection(
            floor_price=floor_price,
            suggested_price=suggested_price,
            safety_margin_percent=safety_margin,
            is_capped=is_capped,
        ),
    )
