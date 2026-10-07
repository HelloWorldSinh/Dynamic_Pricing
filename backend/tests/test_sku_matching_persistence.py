"""Tests for Two-Tiered SKU Matching Persistence (Task 2)."""

import uuid
from datetime import datetime
import pytest
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.services.seeder import seed_catalog_and_inventory
from app.services.matching_persistence import run_sku_matching_and_persist


def test_sku_matching_and_persistence(db_session: Session):
    """Kiểm thử quy trình so khớp 2 tầng và lưu kết quả vào bảng sku_mappings."""
    # 1. Nạp catalog FPT mẫu
    counts = seed_catalog_and_inventory(db_session, limit=10)
    assert counts["products"] == 10
    prods = db_session.query(Product).all()
    sample_prod = prods[0]

    # 2. Tạo crawl results đối thủ giả lập
    # Case A: Trùng tên / part number của sample_prod
    crawl_exact = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/sample-exact",
        raw_name=sample_prod.name,
        current_price=sample_prod.base_retail_price - 500_000,
        is_in_stock=True,
        crawled_at=datetime.utcnow(),
    )
    # Case B: Không khớp với sản phẩm nào
    crawl_unmatched = CrawlResult(
        id=uuid.uuid4(),
        source="HOANGHA",
        url="https://hoanghamobile.com/unmatched-item",
        raw_name="Sản phẩm vu vơ không có trong danh mục FPT 9999XYZ",
        current_price=10_000_000,
        is_in_stock=True,
        crawled_at=datetime.utcnow(),
    )
    db_session.add_all([crawl_exact, crawl_unmatched])
    db_session.commit()

    # 3. Kích hoạt so khớp và lưu trữ
    mapped_count = run_sku_matching_and_persist(db_session)
    assert mapped_count >= 1

    # 4. Kiểm tra dữ liệu trong bảng sku_mappings
    mappings = db_session.query(SkuMapping).all()
    assert len(mappings) >= 1

    matched_exact = db_session.query(SkuMapping).filter(
        SkuMapping.competitor_crawl_id == crawl_exact.id
    ).first()
    assert matched_exact is not None
    assert matched_exact.fpt_product_id == sample_prod.id
    assert matched_exact.status in ["APPROVED", "PENDING"]
    assert matched_exact.confidence_score >= 0.60
    assert matched_exact.product.sku == sample_prod.sku

    # Crawl unmatched không được lưu hoặc không có match
    matched_none = db_session.query(SkuMapping).filter(
        SkuMapping.competitor_crawl_id == crawl_unmatched.id
    ).first()
    assert matched_none is None
