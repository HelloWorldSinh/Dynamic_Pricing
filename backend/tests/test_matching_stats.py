import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models import Product, CrawlResult, SkuMapping


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_matching_stats_empty_db(client):
    """Kiểm tra thống kê matching khi cơ sở dữ liệu rỗng."""
    response = client.get("/api/v1/matching/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_skus"] == 0
    assert data["matched_skus"] == 0
    assert data["match_rate"] == 0.0
    assert data["pending_queue_count"] == 0
    assert data["approved_count"] == 0
    assert data["rejected_count"] == 0


def test_matching_stats_with_data(client, db_session):
    """Kiểm tra thống kê matching với dữ liệu sản phẩm và SKU mapping thực tế."""
    # 3 active products, 1 inactive product
    prod1 = Product(
        id=uuid.uuid4(),
        sku="SKU-IPHONE-15",
        name="iPhone 15 128GB",
        category="PHONE",
        brand="Apple",
        base_retail_price=20_000_000,
        cost_price=17_000_000,
        floor_price=18_000_000,
        is_active=True,
    )
    prod2 = Product(
        id=uuid.uuid4(),
        sku="SKU-SAMSUNG-S24",
        name="Samsung Galaxy S24",
        category="PHONE",
        brand="Samsung",
        base_retail_price=18_000_000,
        cost_price=15_000_000,
        floor_price=16_000_000,
        is_active=True,
    )
    prod3 = Product(
        id=uuid.uuid4(),
        sku="SKU-MACBOOK-AIR-M2",
        name="MacBook Air M2 8GB 256GB",
        category="LAPTOP",
        brand="Apple",
        base_retail_price=24_000_000,
        cost_price=21_000_000,
        floor_price=22_000_000,
        is_active=True,
    )
    prod_inactive = Product(
        id=uuid.uuid4(),
        sku="SKU-OLD-PRODUCT",
        name="Old Phone Model",
        category="PHONE",
        brand="Apple",
        base_retail_price=5_000_000,
        cost_price=4_000_000,
        floor_price=4_500_000,
        is_active=False,
    )
    db_session.add_all([prod1, prod2, prod3, prod_inactive])
    db_session.flush()

    crawl1 = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/iphone-15.html",
        raw_name="iPhone 15 128GB Chính Hãng",
        current_price=19_500_000,
        is_in_stock=True,
        crawled_at=datetime.now(timezone.utc),
    )
    crawl2 = CrawlResult(
        id=uuid.uuid4(),
        source="HOANGHA",
        url="https://hoanghamobile.com/iphone-15.html",
        raw_name="iPhone 15 128GB VN/A",
        current_price=19_400_000,
        is_in_stock=True,
        crawled_at=datetime.now(timezone.utc),
    )
    crawl3 = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/samsung-s24.html",
        raw_name="Samsung Galaxy S24 8GB 128GB",
        current_price=17_500_000,
        is_in_stock=True,
        crawled_at=datetime.now(timezone.utc),
    )
    db_session.add_all([crawl1, crawl2, crawl3])
    db_session.flush()

    # prod1 matched to 2 competitors (both APPROVED)
    map1 = SkuMapping(
        id=uuid.uuid4(),
        fpt_product_id=prod1.id,
        competitor_crawl_id=crawl1.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=1.0,
        status="APPROVED",
    )
    map2 = SkuMapping(
        id=uuid.uuid4(),
        fpt_product_id=prod1.id,
        competitor_crawl_id=crawl2.id,
        match_type="NORMALIZED_ATTRIBUTE",
        confidence_score=0.9,
        status="APPROVED",
    )
    # prod2 has a PENDING mapping
    map3 = SkuMapping(
        id=uuid.uuid4(),
        fpt_product_id=prod2.id,
        competitor_crawl_id=crawl3.id,
        match_type="NORMALIZED_ATTRIBUTE",
        confidence_score=0.72,
        status="PENDING",
    )
    db_session.add_all([map1, map2, map3])
    db_session.commit()

    response = client.get("/api/v1/matching/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_skus"] == 3
    # prod1 is matched (1 distinct active product)
    assert data["matched_skus"] == 1
    assert data["match_rate"] == 33.3
    assert data["pending_queue_count"] == 1
    assert data["approved_count"] == 2
    assert data["rejected_count"] == 0
