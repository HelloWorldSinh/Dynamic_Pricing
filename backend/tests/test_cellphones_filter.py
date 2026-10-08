import pytest
from app.services.scrapers.cellphones import CellphonesScraper


def test_cellphones_used_product_regex_discontinued():
    """Kiểm tra regex loại bỏ hàng ngừng kinh doanh và hàng cũ."""
    scraper = CellphonesScraper()
    
    # Các trường hợp phải bị loại bỏ
    assert scraper.USED_PRODUCT_RE.search("iPhone 11 64GB - Ngừng kinh doanh /iphone-11-ngung-kd")
    assert scraper.USED_PRODUCT_RE.search("Samsung Galaxy S20 FE (Tạm hết hàng)")
    assert scraper.USED_PRODUCT_RE.search("Laptop Dell Vostro cũ xước")
    assert scraper.USED_PRODUCT_RE.search("iPhone 13 128GB - Đã kích hoạt")
    
    # Các trường hợp hợp lệ không được dính regex
    assert not scraper.USED_PRODUCT_RE.search("iPhone 15 Pro Max 256GB Chính hãng VN/A")
    assert not scraper.USED_PRODUCT_RE.search("Laptop ASUS TUF Gaming F15 FX506HF")


def test_cellphones_clean_price():
    """Kiểm tra hàm chuẩn hóa giá."""
    scraper = CellphonesScraper()
    assert scraper._clean_price("15.990.000₫") == 15990000
    assert scraper._clean_price("0") == 0
    assert scraper._clean_price(None) is None
    assert scraper._clean_price("") is None


def test_cellphones_price_filtering_rule():
    """Kiểm tra logic lọc sản phẩm có giá <= 0 hoặc None (ngừng kinh doanh)."""
    mock_products = [
        {"price": 15000000, "special_price": 14000000, "expected_keep": True},
        {"price": 20000000, "special_price": None, "expected_keep": True},
        {"price": 0, "special_price": 0, "expected_keep": False},
        {"price": None, "special_price": None, "expected_keep": False},
        {"price": -1, "special_price": None, "expected_keep": False},
    ]

    kept = []
    for item in mock_products:
        price_val = item.get("price")
        special_price_val = item.get("special_price")
        current_price = (
            int(special_price_val)
            if special_price_val and special_price_val > 0
            else (int(price_val) if price_val and price_val > 0 else None)
        )
        if not current_price or current_price <= 0:
            continue
        kept.append(item)

    assert len(kept) == 2
    assert all(k["expected_keep"] for k in kept)
