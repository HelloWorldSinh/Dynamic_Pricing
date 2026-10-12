import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models import Product, CrawlResult, SkuMapping, InventoryMock


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


def test_pricing_matrix_prioritizes_in_stock_competitor(client, db_session):
    """Kiểm tra khi 1 SKU có nhiều mapping CellphoneS (1 còn hàng, 1 hết hàng), 
    ma trận giá BẮT BUỘC phải ưu tiên chọn bản ghi còn hàng và có giá hợp lệ,
    không được để bản ghi hết hàng ghi đè.
    """
    prod = Product(
        id=uuid.uuid4(),
        sku="TEST-LAPTOP-001",
        name="Laptop ASUS Vivobook 15 Core i5",
        category="LAPTOP",
        brand="ASUS",
        base_retail_price=18_000_000,
        cost_price=15_000_000,
        floor_price=16_000_000,
        is_active=True,
    )
    db_session.add(prod)

    # 1. Bản ghi còn hàng
    c_in_stock = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/laptop-asus-in-stock.html",
        raw_name="Laptop ASUS Vivobook 15 Core i5 (Chính hãng)",
        current_price=17_500_000,
        original_price=19_000_000,
        is_in_stock=True,
    )
    # 2. Bản ghi hết hàng (ra sau)
    c_oos = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/laptop-asus-oos.html",
        raw_name="Laptop ASUS Vivobook 15 Cũ Hết Hàng",
        current_price=None,
        original_price=None,
        is_in_stock=False,
    )
    db_session.add_all([c_in_stock, c_oos])
    db_session.commit()

    # Tạo 2 mapping: map c_in_stock trước, c_oos sau
    m1 = SkuMapping(
        id=uuid.uuid4(),
        fpt_product_id=prod.id,
        competitor_crawl_id=c_in_stock.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=1.0,
        status="APPROVED",
    )
    m2 = SkuMapping(
        id=uuid.uuid4(),
        fpt_product_id=prod.id,
        competitor_crawl_id=c_oos.id,
        match_type="NORMALIZED_ATTRIBUTE",
        confidence_score=0.75,
        status="PENDING",
    )
    db_session.add_all([m1, m2])
    db_session.commit()

    res = client.get("/api/v1/pricing/matrix?category=LAPTOP")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    item = data[0]

    # CellphoneS phải hiển thị bản ghi còn hàng
    assert item["cellphones"] is not None
    assert item["cellphones"]["is_in_stock"] is True
    assert item["cellphones"]["price"] == 17_500_000
    assert item["min_competitor_price"] == 17_500_000


def test_crawl_results_category_filter(client, db_session):
    """Kiểm tra endpoint /crawl/results lọc đúng theo category (laptop vs phone)."""
    c_laptop = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/laptop-dell.html",
        raw_name="Laptop Dell Inspiron 15 3520",
        current_price=14_000_000,
        is_in_stock=True,
    )
    c_phone = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/iphone-16.html",
        raw_name="iPhone 16 128GB Chính hãng",
        current_price=21_000_000,
        is_in_stock=True,
    )
    db_session.add_all([c_laptop, c_phone])
    db_session.commit()

    # Lọc category=LAPTOP
    res_laptop = client.get("/api/v1/crawl/results?category=LAPTOP")
    assert res_laptop.status_code == 200
    laptop_items = res_laptop.json()["items"]
    assert any("laptop" in it["raw_name"].lower() for it in laptop_items)
    assert not any("iphone" in it["raw_name"].lower() for it in laptop_items)

    # Lọc category=PHONE
    res_phone = client.get("/api/v1/crawl/results?category=PHONE")
    assert res_phone.status_code == 200
    phone_items = res_phone.json()["items"]
    assert any("iphone" in it["raw_name"].lower() for it in phone_items)
    assert not any("laptop" in it["raw_name"].lower() for it in phone_items)
