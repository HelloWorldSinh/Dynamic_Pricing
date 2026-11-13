import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.product import Product
from app.models.inventory import InventoryMock
from app.models.pricing import PriceHistory
from app.schemas.crawl import ScrapedProductItem
from app.services.crawler_service import CrawlerService
from app.services.fpt_sync_service import FptPriceSyncService


@pytest.fixture
def mock_pricing_engine():
    engine = MagicMock()
    engine.generate_for_product.return_value = None
    return engine


def test_sync_live_prices_part_number_match(db_session, mock_pricing_engine):
    """Kiểm tra đối soát Tầng 1: So khớp mã Part-Number chính xác 100%."""
    # 1. Khởi tạo sản phẩm FPT Shop trong CSDL
    prod = Product(
        id=uuid.uuid4(),
        sku="FPT-IPHONE-16PM-256",
        name="iPhone 16 Pro Max 256GB Titan Sa Mạc",
        category="PHONE",
        brand="Apple",
        part_number="MYWV3VN/A",
        base_retail_price=34990000,
        cost_price=int(34990000 * 0.85),
        floor_price=int(34990000 * 0.85 * 1.05),
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    # 2. Dữ liệu cào real-time từ FPT Shop có giá mới giảm còn 33.990.000đ
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/dien-thoai/iphone-16-pro-max",
        product_name="iPhone 16 Pro Max 256GB Titan Sa Mạc (MYWV3VN/A)",
        current_price=33990000,
        original_price=34990000,
        is_in_stock=True,
        specifications={"Part Number": "MYWV3VN/A"},
    )

    sync_service = FptPriceSyncService(pricing_engine=mock_pricing_engine)
    stats = sync_service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    # 3. Xác minh kết quả thống kê
    assert stats["total_catalog"] == 1
    assert stats["matched_count"] == 1
    assert stats["price_updated_count"] == 1
    assert stats["deactivated_count"] == 0

    # 4. Xác minh dữ liệu Product trong CSDL đã được cập nhật
    db_session.refresh(prod)
    assert prod.base_retail_price == 33990000
    assert prod.cost_price == int(33990000 * 0.85)
    assert prod.floor_price == int(int(33990000 * 0.85) * 1.05)
    assert prod.is_active is True

    # 5. Xác minh PriceHistory đã lưu biến động giá
    history = db_session.query(PriceHistory).filter(PriceHistory.fpt_product_id == prod.id).all()
    assert len(history) == 1
    hist = history[0]
    assert hist.source == "FPTSHOP"
    assert hist.old_price == 34990000
    assert hist.new_price == 33990000
    assert hist.price_change == -1000000
    assert hist.status == "SYNCED_POS"

    # 6. Xác minh PricingEngine đã được kích hoạt tái tính toán
    mock_pricing_engine.generate_for_product.assert_called_once_with(db_session, prod.id)


def test_sync_live_prices_fuzzy_match(db_session, mock_pricing_engine):
    """Kiểm tra đối soát Tầng 2: So khớp tên mờ Fuzzy Matching (score >= 75%)."""
    prod = Product(
        id=uuid.uuid4(),
        sku="FPT-SS-S24-ULTRA",
        name="Samsung Galaxy S24 Ultra 12GB 256GB",
        category="PHONE",
        brand="Samsung",
        part_number=None,  # Không có part_number
        base_retail_price=29990000,
        cost_price=int(29990000 * 0.85),
        floor_price=int(29990000 * 0.85 * 1.05),
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    # Dữ liệu cào có tên hơi khác nhưng tỷ lệ trùng khớp cao
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/dien-thoai/samsung-galaxy-s24-ultra",
        product_name="Điện thoại Samsung Galaxy S24 Ultra 12GB 256GB",
        current_price=27990000,
        original_price=29990000,
        is_in_stock=True,
    )

    sync_service = FptPriceSyncService(pricing_engine=mock_pricing_engine)
    stats = sync_service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    assert stats["matched_count"] == 1
    assert stats["price_updated_count"] == 1

    db_session.refresh(prod)
    assert prod.base_retail_price == 27990000


def test_sync_live_prices_unmatched_deactivation(db_session, mock_pricing_engine):
    """Kiểm tra sản phẩm không còn tồn tại trên FPT Shop sẽ bị đánh dấu is_active = False."""
    prod = Product(
        id=uuid.uuid4(),
        sku="FPT-OLD-PHONE",
        name="Nokia 3310 Cổ Điển",
        category="PHONE",
        brand="Nokia",
        part_number="NOK-3310",
        base_retail_price=1000000,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    # Danh sách cào rỗng hoặc không chứa Nokia 3310
    sync_service = FptPriceSyncService(pricing_engine=mock_pricing_engine)
    stats = sync_service.sync_live_prices(
        db=db_session,
        scraped_items=[],
        auto_commit=True,
    )

    assert stats["matched_count"] == 0
    assert stats["deactivated_count"] == 1
    assert "FPT-OLD-PHONE" in stats["unmatched_skus"]

    db_session.refresh(prod)
    assert prod.is_active is False


def test_sync_live_prices_inventory_mock_sync(db_session, mock_pricing_engine):
    """Kiểm tra giá vốn và giá sàn trên bảng InventoryMock được đồng bộ theo Product."""
    prod = Product(
        id=uuid.uuid4(),
        sku="FPT-ASUS-VIVO",
        name="Laptop Asus Vivobook 15",
        category="LAPTOP",
        brand="Asus",
        part_number="X1502ZA",
        base_retail_price=15000000,
        cost_price=12750000,
        floor_price=13387500,
        is_active=True,
    )
    db_session.add(prod)

    inv = InventoryMock(
        id=uuid.uuid4(),
        fpt_product_id=prod.id,
        stock_quantity=20,
        doh=30,
        cost_price=12750000,
        floor_price=13387500,
    )
    db_session.add(inv)
    db_session.commit()

    # FPT Shop cập nhật giá mới: 16.000.000đ
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/may-tinh-xach-tay/asus-vivobook-15",
        product_name="Laptop Asus Vivobook 15 (X1502ZA)",
        current_price=16000000,
        original_price=16000000,
        is_in_stock=True,
        specifications={"Part Number": "X1502ZA"},
    )

    sync_service = FptPriceSyncService(pricing_engine=mock_pricing_engine)
    sync_service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    db_session.refresh(inv)
    expected_cost = int(16000000 * 0.85)
    expected_floor = int(expected_cost * 1.05)
    assert inv.cost_price == expected_cost
    assert inv.floor_price == expected_floor


from fastapi import BackgroundTasks, HTTPException
from app.api.v1.endpoints.crawl import sync_fpt_prices, get_crawl_task_status


def test_api_sync_fpt_prices_and_debounce(db_session):
    """Kiểm tra API controller sync-fpt-prices và cơ chế bảo vệ Debounce 30s."""
    # Reset cache debounce để test độc lập
    CrawlerService._last_triggered["fptshop"] = 0

    bg_tasks = BackgroundTasks()

    # Lần 1: Kích hoạt thành công
    res = sync_fpt_prices(background_tasks=bg_tasks)
    assert res.task_id is not None
    assert res.status in ["PENDING", "PROCESSING", "RUNNING", "COMPLETED"]
    assert "FPTSHOP" in res.message

    # Tra cứu trạng thái tiến độ qua get_crawl_task_status
    status_data = get_crawl_task_status(task_id=res.task_id, db=db_session)
    assert status_data["task_id"] == res.task_id
    assert status_data["source"] == "FPTSHOP"
    assert status_data["status"] in ["PENDING", "PROCESSING", "RUNNING", "COMPLETED"]

    # Lần 2: Kích hoạt ngay lập tức -> Phải bị chặn bởi Debounce 30s (HTTPException 429)
    with pytest.raises(HTTPException) as exc_info:
        sync_fpt_prices(background_tasks=bg_tasks)

    assert exc_info.value.status_code == 429
    err_detail = exc_info.value.detail
    assert "fptshop" in err_detail
    assert "Vui lòng đợi" in err_detail
