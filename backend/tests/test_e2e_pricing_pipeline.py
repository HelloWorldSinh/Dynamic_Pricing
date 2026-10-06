"""End-to-End Pipeline Integration Test (Task 3).

Kiểm thử toàn trình từ nạp Catalog -> Khớp SKU đối thủ -> Sinh đề xuất giá qua Pricing Engine -> Phê duyệt đề xuất & Audit Log.
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.models.pricing import PriceRecommendation, PricingAuditLog
from app.services.seeder import seed_catalog_and_inventory
from app.services.matching_persistence import run_sku_matching_and_persist
from app.services.pricing import PricingEngine


def test_e2e_pricing_pipeline(db_session: Session):
    """Kiểm thử luồng toàn trình từ Catalog -> Matching -> Pricing Engine -> Audit Log."""
    # 1. Nạp danh mục chuẩn và tồn kho (10 sản phẩm mẫu)
    seed_counts = seed_catalog_and_inventory(db_session, limit=10)
    assert seed_counts["products"] == 10
    assert seed_counts["warehouses"] >= 3

    products = db_session.query(Product).all()
    assert len(products) == 10

    # 2. Tạo kết quả cào đối thủ tương ứng với sản phẩm đầu tiên
    p1 = products[0]
    crawl_p1 = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/test-p1",
        raw_name=p1.name,
        current_price=int(p1.base_retail_price * 0.95),  # Đối thủ rẻ hơn 5%
        is_in_stock=True,
        crawled_at=datetime.utcnow(),
    )
    db_session.add(crawl_p1)
    db_session.commit()

    # 3. Kích hoạt module SKU Matching Persistence
    matched_count = run_sku_matching_and_persist(db_session)
    assert matched_count >= 1

    # Kiểm tra mapping được lưu
    mapping = db_session.query(SkuMapping).filter(
        SkuMapping.fpt_product_id == p1.id,
        SkuMapping.competitor_crawl_id == crawl_p1.id,
    ).first()
    assert mapping is not None
    assert mapping.status in ["APPROVED", "PENDING"]

    # 4. Kích hoạt Pricing Engine sinh đề xuất giá hàng loạt
    engine = PricingEngine()
    recs = engine.generate_batch(db_session)
    assert len(recs) == 10

    # 5. Kiểm tra tính toàn vẹn của đề xuất giá trong database
    db_recs = db_session.query(PriceRecommendation).all()
    assert len(db_recs) == 10

    rec_p1 = db_session.query(PriceRecommendation).filter(
        PriceRecommendation.fpt_product_id == p1.id
    ).first()
    assert rec_p1 is not None
    assert rec_p1.status == "PENDING"
    assert rec_p1.current_fpt_price == p1.base_retail_price
    assert rec_p1.recommended_price > 0
    assert rec_p1.scenario_name is not None
    assert rec_p1.reasoning_3layers is not None
    assert rec_p1.competitor_min_price == crawl_p1.current_price

    # Đảm bảo giá đề xuất không vi phạm giá sàn (Floor Price)
    assert rec_p1.recommended_price >= p1.floor_price

    # 6. Mô phỏng quy trình phê duyệt đề xuất giá (Approval & Audit Log)
    rec_p1.status = "APPROVED"
    rec_p1.reviewed_by = "Pricing Director"
    rec_p1.reviewed_at = datetime.now(timezone.utc)

    audit_entry = PricingAuditLog(
        actor="Pricing Director",
        action="APPROVE_PRICE",
        entity_type="price_recommendations",
        entity_id=rec_p1.id,
        old_value={"status": "PENDING"},
        new_value={
            "status": "APPROVED",
            "recommended_price": rec_p1.recommended_price,
        },
    )
    db_session.add(audit_entry)
    db_session.commit()

    # Kiểm tra Audit Log đã được lưu trong DB
    audit_logs = db_session.query(PricingAuditLog).filter(
        PricingAuditLog.entity_id == rec_p1.id
    ).all()
    assert len(audit_logs) == 1
    assert audit_logs[0].actor == "Pricing Director"
    assert audit_logs[0].action == "APPROVE_PRICE"
