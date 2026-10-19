import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.schemas.crawl import ScrapedProductItem
from app.models.crawl_result import CrawlResult
from app.models.product import Product
from app.models.sku_mapping import SkuMapping
from app.models.pricing import PriceHistory
from app.services.crawler_service import CrawlerService
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

client = TestClient(app)


def test_upsert_prevents_duplicate_records_and_updates_in_place(db_session):
    """Kiểm tra: Cào cùng 1 URL nhiều lần thì không được tạo bản ghi mới,
    mà phải UPDATE tại chỗ (giữ nguyên ID) để tránh phình to database.
    """
    item1 = ScrapedProductItem(
        source="cellphones",
        url="https://cellphones.com.vn/laptop-asus-test.html",
        product_name="Laptop Asus Test V1",
        current_price=15000000,
        original_price=16000000,
        is_in_stock=True,
        specifications={"CPU": "Core i5"},
    )

    # 1. Lần cào đầu tiên: Phải thêm mới (INSERT)
    stats1 = CrawlerService.save_scraped_items_upsert([item1], db=db_session)
    assert stats1["inserted"] == 1
    assert stats1["updated"] == 0

    record = db_session.query(CrawlResult).filter_by(url=item1.url).first()
    assert record is not None
    assert record.current_price == 15000000
    first_id = record.id

    # 2. Lần cào thứ 2: Cùng URL nhưng đổi giá xuống 14.500.000 VND và đổi kho
    item2 = ScrapedProductItem(
        source="cellphones",
        url="https://cellphones.com.vn/laptop-asus-test.html",
        product_name="Laptop Asus Test V2 - Giảm giá",
        current_price=14500000,
        original_price=16000000,
        is_in_stock=False,
        specifications={"CPU": "Core i5", "RAM": "16GB"},
    )

    stats2 = CrawlerService.save_scraped_items_upsert([item2], db=db_session)
    assert stats2["inserted"] == 0
    assert stats2["updated"] == 1

    # Tổng số bản ghi trong bảng vẫn CHỈ LÀ 1 (Không được tạo dòng thứ 2)
    all_records = db_session.query(CrawlResult).all()
    assert len(all_records) == 1

    # Bản ghi đó giữ nguyên ID ban đầu (để bảo vệ SkuMapping) nhưng giá và cấu hình đã cập nhật
    updated_record = all_records[0]
    assert updated_record.id == first_id
    assert updated_record.current_price == 14500000
    assert updated_record.is_in_stock is False
    assert updated_record.raw_specs.get("RAM") == "16GB"


def test_upsert_logs_to_price_history_when_price_changes_and_mapped(db_session):
    """Kiểm tra: Nếu giá đối thủ thay đổi VÀ sản phẩm đã được ghép với SKU FPT,
    hệ thống tự động ghi 1 dòng log vào price_history để phục vụ vẽ biểu đồ.
    """
    # 1. Tạo sản phẩm FPT Shop
    fpt_prod = Product(
        id=uuid.uuid4(),
        sku="FPT-ASUS-TEST",
        name="Laptop Asus Baseline FPT",
        category="LAPTOP",
        cost_price=12000000,
        base_retail_price=16000000,
    )
    db_session.add(fpt_prod)
    db_session.commit()

    # 2. Tạo CrawlResult ban đầu
    crawl_rec = CrawlResult(
        id=uuid.uuid4(),
        source="HOANGHA",
        url="https://hoanghamobile.com/laptop-asus-test.html",
        raw_name="Asus Test Hoàng Hà",
        current_price=15000000,
        original_price=16000000,
        is_in_stock=True,
    )
    db_session.add(crawl_rec)
    db_session.commit()

    # 3. Tạo SkuMapping ghép nối sản phẩm đối thủ với FPT Product
    mapping = SkuMapping(
        id=uuid.uuid4(),
        fpt_product_id=fpt_prod.id,
        competitor_crawl_id=crawl_rec.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=1.0,
        status="APPROVED",
    )
    db_session.add(mapping)
    db_session.commit()

    # 4. Cào lại cùng URL với giá mới (14.200.000 VND - đổi giá)
    item_new_price = ScrapedProductItem(
        source="HOANGHA",
        url="https://hoanghamobile.com/laptop-asus-test.html",
        product_name="Asus Test Hoàng Hà Mới",
        current_price=14200000,
        original_price=16000000,
        is_in_stock=True,
        specifications={},
    )
    CrawlerService.save_scraped_items_upsert([item_new_price], db=db_session)

    # Phải có 1 log được ghi vào price_history
    histories = db_session.query(PriceHistory).filter_by(fpt_product_id=fpt_prod.id).all()
    assert len(histories) == 1
    assert histories[0].price == 14200000
    assert histories[0].source == "HOANGHA"

    # 5. Cào lại LẦN NỮA với CÙNG MỨC GIÁ (14.200.000 VND - giá không đổi)
    CrawlerService.save_scraped_items_upsert([item_new_price], db=db_session)

    # Số lượng log trong price_history KHÔNG ĐƯỢC TĂNG THÊM (chống spam log)
    histories_after = db_session.query(PriceHistory).filter_by(fpt_product_id=fpt_prod.id).all()
    assert len(histories_after) == 1


def test_cleanup_stale_crawl_results(db_session):
    """Kiểm tra: Retention Cleanup xóa các sản phẩm đối thủ cũ (> 7 ngày)
    mà CHƯA TỪNG ĐƯỢC MAP vào SKU FPT nào, nhưng BẢO TOÀN các sản phẩm đã map.
    """
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(days=10)
    fresh_time = now - timedelta(days=2)

    # 1. Record A: Cũ (> 7 ngày) + CHƯA MAP -> PHẢI BỊ XÓA
    rec_a = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/stale-unmapped.html",
        raw_name="Sản phẩm cũ chưa map",
        current_price=5000000,
        crawled_at=old_time,
    )

    # 2. Record B: Cũ (> 7 ngày) + ĐÃ MAP -> KHÔNG ĐƯỢC XÓA (BẢO TOÀN)
    fpt_prod = Product(
        id=uuid.uuid4(),
        sku="FPT-PROD-B",
        name="FPT Product B",
        category="PHONE",
        cost_price=4000000,
        base_retail_price=6000000,
    )
    db_session.add(fpt_prod)
    db_session.flush()

    rec_b = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/stale-mapped.html",
        raw_name="Sản phẩm cũ đã map",
        current_price=5500000,
        crawled_at=old_time,
    )
    db_session.add(rec_b)
    db_session.flush()

    mapping_b = SkuMapping(
        id=uuid.uuid4(),
        fpt_product_id=fpt_prod.id,
        competitor_crawl_id=rec_b.id,
        match_type="EXACT_PART_NUMBER",
        status="APPROVED",
        confidence_score=0.95,
    )
    db_session.add(mapping_b)

    # 3. Record C: Mới (2 ngày trước) + CHƯA MAP -> KHÔNG ĐƯỢC XÓA (CÒN TƯƠI)
    rec_c = CrawlResult(
        id=uuid.uuid4(),
        source="HOANGHA",
        url="https://hoanghamobile.com/fresh-unmapped.html",
        raw_name="Sản phẩm mới chưa map",
        current_price=7000000,
        crawled_at=fresh_time,
    )

    db_session.add_all([rec_a, rec_c])
    db_session.commit()

    # Thực hiện dọn dẹp với ngưỡng mặc định (7 ngày)
    deleted_count = CrawlerService.cleanup_stale_crawl_results(days=7, db=db_session)
    assert deleted_count == 1

    remaining_urls = {r.url for r in db_session.query(CrawlResult).all()}
    assert rec_a.url not in remaining_urls
    assert rec_b.url in remaining_urls
    assert rec_c.url in remaining_urls


def test_cleanup_api_endpoint(db_session):
    """Kiểm tra API endpoint POST /api/v1/crawl/cleanup hoạt động chính xác."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        res = client.post("/api/v1/crawl/cleanup?days=7")
        assert res.status_code == 200
        data = res.json()
        assert "deleted_count" in data
        assert "message" in data
    finally:
        app.dependency_overrides.clear()
