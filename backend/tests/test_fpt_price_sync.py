import uuid
from unittest.mock import MagicMock
import pytest
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import InventoryMock
from app.models.pricing import PriceHistory
from app.schemas.crawl import ScrapedProductItem
from app.services.fpt_sync_service import FptPriceSyncService


@pytest.fixture
def sample_laptop_product(db_session: Session) -> Product:
    prod = Product(
        id=uuid.uuid4(),
        sku="FPT-LAPTOP-LENOVO-01",
        name="Laptop Lenovo IdeaPad Slim 3 15IAH8",
        category="LAPTOP",
        brand="Lenovo",
        part_number="83JC00LVVN",
        base_retail_price=14000000,
        cost_price=11900000,
        floor_price=12495000,
        is_active=False,  # Bắt đầu bằng False để test chuyển thành True khi match
    )
    db_session.add(prod)
    db_session.flush()

    inv = InventoryMock(
        id=uuid.uuid4(),
        fpt_product_id=prod.id,
        cost_price=prod.cost_price,
        floor_price=prod.floor_price,
        stock_quantity=15,
        doh=25,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(prod)
    return prod


@pytest.fixture
def sample_phone_product(db_session: Session) -> Product:
    prod = Product(
        id=uuid.uuid4(),
        sku="FPT-IPHONE-16PM-256",
        name="iPhone 16 Pro Max 256GB",
        category="PHONE",
        brand="Apple",
        part_number=None,
        base_retail_price=34990000,
        cost_price=29741500,
        floor_price=31228575,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    return prod


def test_sync_live_prices_part_number_matching(db_session: Session, sample_laptop_product: Product):
    """Kiểm tra đối soát Tầng 1: So khớp chính xác Part-Number trong tên."""
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/may-tinh-xach-tay/lenovo-ideapad-slim-3",
        product_name="Laptop Lenovo IdeaPad Slim 3 15IAH8 83JC00LVVN i5 12450H 16GB",
        current_price=15000000,
        specifications={"part_number": "83JC00LVVN"},
        is_in_stock=True,
    )

    mock_pricing_engine = MagicMock()
    service = FptPriceSyncService(pricing_engine=mock_pricing_engine)

    result = service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    # 1. Kiểm tra thống kê trả về
    assert result["total_catalog"] == 1
    assert result["matched_count"] == 1
    assert result["price_updated_count"] == 1
    assert result["deactivated_count"] == 0
    assert result["recalculated_count"] == 1
    assert result["unmatched_skus"] == []

    # 2. Kiểm tra cập nhật trên Product
    db_session.refresh(sample_laptop_product)
    assert sample_laptop_product.is_active is True
    assert sample_laptop_product.base_retail_price == 15000000
    expected_cost = int(15000000 * 0.85)  # 12,750,000
    expected_floor = int(expected_cost * 1.05)  # 13,387,500
    assert sample_laptop_product.cost_price == expected_cost
    assert sample_laptop_product.floor_price == expected_floor

    # 3. Kiểm tra InventoryMock được đồng bộ
    inv = db_session.query(InventoryMock).filter(InventoryMock.fpt_product_id == sample_laptop_product.id).first()
    assert inv is not None
    assert inv.cost_price == expected_cost
    assert inv.floor_price == expected_floor

    # 4. Kiểm tra PriceHistory được ghi vết đầy đủ
    hist = db_session.query(PriceHistory).filter(PriceHistory.fpt_product_id == sample_laptop_product.id).first()
    assert hist is not None
    assert hist.source == "FPTSHOP"
    assert hist.old_price == 14000000
    assert hist.new_price == 15000000
    assert hist.price_change == 1000000
    assert hist.price_change_percent == round(((15000000 - 14000000) / 14000000) * 100, 2)
    assert hist.cost_price == expected_cost
    assert hist.floor_price == expected_floor
    assert hist.change_type == "REALTIME_CRAWL"
    assert hist.status == "SYNCED_POS"

    # 5. Kiểm tra PricingEngine được gọi tái tính toán
    mock_pricing_engine.generate_for_product.assert_called_once_with(db_session, sample_laptop_product.id)


def test_sync_live_prices_part_number_in_specs_only(db_session: Session, sample_laptop_product: Product):
    """Kiểm tra đối soát Tầng 1: Part-Number nằm trong specifications (không có trong tên)."""
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/may-tinh-xach-tay/lenovo-ideapad-slim-3",
        product_name="Laptop Lenovo IdeaPad Slim 3 15 inch Core i5 Gen 12",  # Tên không chứa 83JC00LVVN
        current_price=14500000,
        specifications={"part_number": "83JC00LVVN", "cpu": "i5-12450H"},
        is_in_stock=True,
    )

    mock_pricing_engine = MagicMock()
    service = FptPriceSyncService(pricing_engine=mock_pricing_engine)

    result = service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    assert result["matched_count"] == 1
    assert result["price_updated_count"] == 1
    db_session.refresh(sample_laptop_product)
    assert sample_laptop_product.base_retail_price == 14500000
    assert sample_laptop_product.is_active is True


def test_sync_live_prices_fuzzy_name_matching(db_session: Session, sample_phone_product: Product):
    """Kiểm tra đối soát Tầng 2: So khớp Fuzzy Matching tên sản phẩm >= 75%."""
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/dien-thoai/iphone-16-pro-max-256gb",
        product_name="iPhone 16 Pro Max 256GB Titan Sa Mạc",
        current_price=33990000,
        specifications={},
        is_in_stock=True,
    )

    mock_pricing_engine = MagicMock()
    service = FptPriceSyncService(pricing_engine=mock_pricing_engine)

    result = service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    assert result["matched_count"] == 1
    assert result["price_updated_count"] == 1
    assert result["deactivated_count"] == 0

    db_session.refresh(sample_phone_product)
    assert sample_phone_product.is_active is True
    assert sample_phone_product.base_retail_price == 33990000
    expected_cost = int(33990000 * 0.85)
    expected_floor = int(expected_cost * 1.05)
    assert sample_phone_product.cost_price == expected_cost
    assert sample_phone_product.floor_price == expected_floor


def test_sync_live_prices_unmatched_deactivated_option_b(db_session: Session, sample_phone_product: Product):
    """Kiểm tra Phương án B: Sản phẩm không còn xuất hiện trên web FPT Shop bị đánh dấu is_active = False."""
    # Thêm 1 sản phẩm không khớp vào DB
    unmatched_prod = Product(
        id=uuid.uuid4(),
        sku="FPT-OLD-FEATURE-PHONE",
        name="Điện thoại Nokia 105 4G Cũ",
        category="PHONE",
        brand="Nokia",
        part_number="NK105-4G",
        base_retail_price=650000,
        cost_price=500000,
        floor_price=525000,
        is_active=True,
    )
    db_session.add(unmatched_prod)
    db_session.commit()

    # Cào chỉ khớp sample_phone_product, không có Nokia 105
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/dien-thoai/iphone-16-pro-max-256gb",
        product_name="iPhone 16 Pro Max 256GB",
        current_price=34990000,
        specifications={},
        is_in_stock=True,
    )

    mock_pricing_engine = MagicMock()
    service = FptPriceSyncService(pricing_engine=mock_pricing_engine)

    result = service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    assert result["total_catalog"] == 2
    assert result["matched_count"] == 1
    assert result["deactivated_count"] == 1
    assert "FPT-OLD-FEATURE-PHONE" in result["unmatched_skus"]

    # Xác nhận sản phẩm không khớp bị deactive
    db_session.refresh(unmatched_prod)
    assert unmatched_prod.is_active is False

    # Xác nhận sản phẩm khớp vẫn active
    db_session.refresh(sample_phone_product)
    assert sample_phone_product.is_active is True


def test_sync_live_prices_invalid_price_treated_as_unmatched(db_session: Session, sample_phone_product: Product):
    """Kiểm tra: Nếu sản phẩm khớp tên nhưng giá <= 0 hoặc None thì coi như không hợp lệ -> deactive."""
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/dien-thoai/iphone-16-pro-max-256gb",
        product_name="iPhone 16 Pro Max 256GB",
        current_price=0,  # Giá không hợp lệ
        specifications={},
        is_in_stock=False,
    )

    mock_pricing_engine = MagicMock()
    service = FptPriceSyncService(pricing_engine=mock_pricing_engine)

    result = service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    assert result["matched_count"] == 0
    assert result["deactivated_count"] == 1
    db_session.refresh(sample_phone_product)
    assert sample_phone_product.is_active is False


def test_sync_live_prices_price_unchanged(db_session: Session, sample_phone_product: Product):
    """Kiểm tra trường hợp giá không đổi: Không tạo PriceHistory nhưng vẫn tính lại gợi ý giá."""
    current_price = sample_phone_product.base_retail_price

    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/dien-thoai/iphone-16-pro-max-256gb",
        product_name="iPhone 16 Pro Max 256GB",
        current_price=current_price,  # Giá y hệt DB
        specifications={},
        is_in_stock=True,
    )

    mock_pricing_engine = MagicMock()
    service = FptPriceSyncService(pricing_engine=mock_pricing_engine)

    result = service.sync_live_prices(
        db=db_session,
        scraped_items=[scraped_item],
        auto_commit=True,
    )

    assert result["matched_count"] == 1
    assert result["price_updated_count"] == 0
    assert result["recalculated_count"] == 1

    # Không sinh bản ghi PriceHistory
    hist_count = db_session.query(PriceHistory).filter(PriceHistory.fpt_product_id == sample_phone_product.id).count()
    assert hist_count == 0

    # Vẫn gọi PricingEngine cho sản phẩm matched
    mock_pricing_engine.generate_for_product.assert_called_once_with(db_session, sample_phone_product.id)


def test_sync_live_prices_scraper_fallback(db_session: Session, sample_phone_product: Product):
    """Kiểm tra khi scraped_items là None, tự động gọi FptShopScraper.scrape_category('all')."""
    mock_scraper = MagicMock()
    mock_scraper.scrape_category.return_value = [
        ScrapedProductItem(
            source="FPTSHOP",
            url="https://fptshop.com.vn/dien-thoai/iphone-16-pro-max-256gb",
            product_name="iPhone 16 Pro Max 256GB",
            current_price=33500000,
            specifications={},
            is_in_stock=True,
        )
    ]

    mock_pricing_engine = MagicMock()
    service = FptPriceSyncService(scraper=mock_scraper, pricing_engine=mock_pricing_engine)

    result = service.sync_live_prices(db=db_session, scraped_items=None)

    mock_scraper.scrape_category.assert_called_once_with("all")
    assert result["matched_count"] == 1
    assert result["price_updated_count"] == 1


def test_sync_live_prices_pricing_engine_failure_handled(db_session: Session, sample_phone_product: Product):
    """Kiểm tra xử lý ngoại lệ an toàn nếu PricingEngine gặp lỗi."""
    scraped_item = ScrapedProductItem(
        source="FPTSHOP",
        url="https://fptshop.com.vn/dien-thoai/iphone-16-pro-max-256gb",
        product_name="iPhone 16 Pro Max 256GB",
        current_price=32000000,
        specifications={},
        is_in_stock=True,
    )

    mock_pricing_engine = MagicMock()
    mock_pricing_engine.generate_for_product.side_effect = RuntimeError("Engine calculation error")

    service = FptPriceSyncService(pricing_engine=mock_pricing_engine)
    result = service.sync_live_prices(db=db_session, scraped_items=[scraped_item])

    assert result["matched_count"] == 1
    assert result["price_updated_count"] == 1
    assert result["recalculated_count"] == 0  # Lỗi nên không tăng recalculated_count


def test_sync_live_prices_empty_catalog(db_session: Session):
    """Kiểm tra khi catalog trống không xảy ra lỗi."""
    service = FptPriceSyncService()
    result = service.sync_live_prices(db=db_session, scraped_items=[])
    assert result["total_catalog"] == 0
    assert result["matched_count"] == 0
    assert result["deactivated_count"] == 0
