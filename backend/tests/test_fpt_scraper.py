import json
from unittest.mock import MagicMock, patch
import pytest

from app.schemas.crawl import ScrapedProductItem, SourceEnum
from app.services.scrapers.factory import ScraperFactory
from app.services.scrapers.fpt import FptShopScraper


@pytest.fixture
def scraper():
    return FptShopScraper()


@pytest.fixture
def sample_api_phone_response():
    return {
        "totalCount": 2,
        "items": [
            {
                "name": "iPhone 16 Pro Max 256GB",
                "displayName": "iPhone 16 Pro Max 256GB",
                "slug": "dien-thoai/iphone-16-pro-max-256gb",
                "code": "00889901",
                "price": 34990000,
                "currentPrice": 32990000,
                "originalPrice": 34990000,
                "brand": {"name": "Apple"},
                "keySellingPoints": [
                    {"title": "Màn hình 6.9 inch OLED"},
                    {"title": "Chip Apple A18 Pro"},
                    {"title": "Pin 4685 mAh"},
                ],
                "skus": [
                    {
                        "sku": "00889901-1",
                        "statusOnWeb": {"code": 11, "displayName": "Mua ngay"},
                        "qtyAvailable": 5,
                    }
                ],
            },
            {
                "name": "Samsung Galaxy S24 Ultra 12GB 256GB",
                "displayName": "Samsung Galaxy S24 Ultra 12GB 256GB",
                "slug": "dien-thoai/samsung-galaxy-s24-ultra",
                "code": "00889902",
                "price": 29990000,
                "currentPrice": 27990000,
                "originalPrice": 29990000,
                "brand": {"name": "Samsung"},
                "keySellingPoints": [
                    {"title": "Màn hình 6.8 inch Dynamic AMOLED 2X"},
                    {"title": "Snapdragon 8 Gen 3 for Galaxy"},
                    {"title": "Pin 5000 mAh"},
                ],
                "skus": [
                    {
                        "sku": "00889902-1",
                        "statusOnWeb": {"code": 11, "displayName": "Mua ngay"},
                        "qtyAvailable": 10,
                    }
                ],
            },
        ],
    }


@pytest.fixture
def sample_api_laptop_response():
    return {
        "totalCount": 1,
        "items": [
            {
                "name": "Asus Vivobook 16 X1607CA-MB387W Ultra 5 225H 16GB 512GB",
                "displayName": "Asus Vivobook 16 X1607CA-MB387W",
                "slug": "may-tinh-xach-tay/asus-vivobook-16-x1607ca-mb387w",
                "code": "00778899",
                "price": 19990000,
                "currentPrice": 18490000,
                "originalPrice": 19990000,
                "brand": {"name": "Asus"},
                "keySellingPoints": [
                    {"title": "Màn hình 16.0 inch WUXGA"},
                    {"title": "Intel Core Ultra 5 225H"},
                ],
                "skus": [
                    {
                        "sku": "00778899-1",
                        "statusOnWeb": {"code": 11, "displayName": "Mua ngay"},
                        "qtyAvailable": 3,
                    }
                ],
            }
        ],
    }


def test_factory_registration():
    """Kiểm tra ScraperFactory đã đăng ký FptShopScraper dưới SourceEnum.FPTSHOP."""
    assert SourceEnum.FPTSHOP.value == "fptshop"

    scraper = ScraperFactory.get_scraper("fptshop")
    assert isinstance(scraper, FptShopScraper)
    assert scraper.source_name == "FPTSHOP"

    # Case-insensitive
    scraper_upper = ScraperFactory.get_scraper("FPTSHOP")
    assert isinstance(scraper_upper, FptShopScraper)


def test_extract_storage_and_part_number(scraper):
    """Kiểm tra trích xuất dung lượng và part number từ tên sản phẩm."""
    assert scraper._extract_storage_from_name("iPhone 16 Pro 256GB") == "256 GB"
    assert (
        scraper._extract_storage_from_name("Samsung Galaxy Z Fold6 12GB 512GB")
        == "12 GB / 512 GB"
    )
    assert scraper._extract_storage_from_name("Không có bộ nhớ") is None

    # Part number
    pn = scraper._extract_part_number("Asus Vivobook 16 X1607CA-MB387W Ultra 5")
    assert pn == "X1607CA-MB387W"

    pn2 = scraper._extract_part_number("Acer Nitro 5 AN515-58-773Y i7")
    assert pn2 == "AN515-58-773Y"


def test_parse_api_item(scraper, sample_api_phone_response):
    """Kiểm tra chuẩn hóa item từ FPT Shop API thành ScrapedProductItem."""
    raw_item = sample_api_phone_response["items"][0]
    parsed = scraper._parse_api_item(raw_item)

    assert parsed is not None
    assert isinstance(parsed, ScrapedProductItem)
    assert parsed.source == "FPTSHOP"
    assert parsed.product_name == "iPhone 16 Pro Max 256GB"
    assert parsed.url == "https://fptshop.com.vn/dien-thoai/iphone-16-pro-max-256gb"
    assert parsed.current_price == 32990000
    assert parsed.original_price == 34990000
    assert parsed.is_in_stock is True
    assert parsed.specifications.get("Hãng") == "Apple"
    assert parsed.specifications.get("Code") == "00889901"
    assert parsed.specifications.get("Bộ nhớ/RAM") == "256 GB"
    assert "Apple A18 Pro" in parsed.specifications.get("CPU/Chip", "")
    assert "summary" in parsed.specifications


def test_parse_api_item_out_of_stock(scraper):
    """Kiểm tra sản phẩm hết hàng hoặc ngừng kinh doanh."""
    item_out = {
        "name": "iPhone 11 64GB",
        "slug": "dien-thoai/iphone-11",
        "currentPrice": 0,
        "price": 0,
        "skus": [{"statusOnWeb": {"displayName": "Ngừng kinh doanh"}}],
    }
    parsed = scraper._parse_api_item(item_out)
    assert parsed is not None
    assert parsed.is_in_stock is False

    # Trường hợp skus chỉ có "Hết hàng"
    item_out_2 = {
        "name": "iPhone 12 64GB",
        "slug": "dien-thoai/iphone-12",
        "currentPrice": 9990000,
        "price": 9990000,
        "skus": [{"statusOnWeb": {"displayName": "Tạm hết hàng"}}],
    }
    parsed_2 = scraper._parse_api_item(item_out_2)
    assert parsed_2 is not None
    assert parsed_2.is_in_stock is False


def test_scrape_category_phone(scraper, sample_api_phone_response):
    """Kiểm tra cào category 'phone' gửi slug 'dien-thoai' và parse đầy đủ kết quả."""
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_api_phone_response
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        progress_calls = []

        def on_progress(page, total_pages, count, msg):
            progress_calls.append((page, total_pages, count, msg))

        items = scraper.scrape_category("phone", on_progress=on_progress)

        assert len(items) == 2
        assert items[0].product_name == "iPhone 16 Pro Max 256GB"
        assert items[1].product_name == "Samsung Galaxy S24 Ultra 12GB 256GB"

        # Kiểm tra payload
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["slug"] == "dien-thoai"
        assert payload["maxResultCount"] == 48

        # Kiểm tra callback tiến độ
        assert len(progress_calls) >= 1
        page, total, count, msg = progress_calls[0]
        assert page == 1
        assert count == 2


def test_scrape_category_laptop(scraper, sample_api_laptop_response):
    """Kiểm tra cào category 'laptop' gửi slug 'may-tinh-xach-tay'."""
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_api_laptop_response
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        items = scraper.scrape_category("laptop")
        assert len(items) == 1
        assert "Asus Vivobook" in items[0].product_name
        assert items[0].specifications.get("Part Number") == "X1607CA-MB387W"

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["slug"] == "may-tinh-xach-tay"


def test_scrape_category_limit(scraper, sample_api_phone_response):
    """Kiểm tra giới hạn số lượng sản phẩm cào (limit)."""
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_api_phone_response
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        items = scraper.scrape_category("phone", limit=1)
        assert len(items) == 1
        assert items[0].product_name == "iPhone 16 Pro Max 256GB"


def test_scrape_category_pagination(scraper):
    """Kiểm tra cơ chế phân trang tự động khi totalCount > 48."""
    # Tạo 48 items cho trang 1, và 10 items cho trang 2
    items_page_1 = [
        {
            "name": f"Phone Model {i}",
            "slug": f"dien-thoai/phone-{i}",
            "currentPrice": 10000000 + i * 100000,
        }
        for i in range(48)
    ]
    items_page_2 = [
        {
            "name": f"Phone Model {i}",
            "slug": f"dien-thoai/phone-{i}",
            "currentPrice": 10000000 + i * 100000,
        }
        for i in range(48, 58)
    ]

    resp_1 = MagicMock()
    resp_1.json.return_value = {"totalCount": 58, "items": items_page_1}
    resp_1.raise_for_status.return_value = None

    resp_2 = MagicMock()
    resp_2.json.return_value = {"totalCount": 58, "items": items_page_2}
    resp_2.raise_for_status.return_value = None

    with patch("httpx.Client.post", side_effect=[resp_1, resp_2]) as mock_post:
        items = scraper.scrape_category("phone")
        assert len(items) == 58
        assert mock_post.call_count == 2
        # Kiểm tra skipCount tăng dần
        first_payload = mock_post.call_args_list[0][1]["json"]
        second_payload = mock_post.call_args_list[1][1]["json"]
        assert first_payload["skipCount"] == 0
        assert second_payload["skipCount"] == 48


def test_scrape_category_all(scraper, sample_api_phone_response, sample_api_laptop_response):
    """Kiểm tra category 'all' cào cả phone và laptop."""
    resp_phone = MagicMock()
    resp_phone.json.return_value = sample_api_phone_response
    resp_phone.raise_for_status.return_value = None

    resp_laptop = MagicMock()
    resp_laptop.json.return_value = sample_api_laptop_response
    resp_laptop.raise_for_status.return_value = None

    with patch("httpx.Client.post", side_effect=[resp_phone, resp_laptop]) as mock_post:
        items = scraper.scrape_category("all")
        assert len(items) == 3
        assert mock_post.call_count == 2
        slugs_called = [call[1]["json"]["slug"] for call in mock_post.call_args_list]
        assert "dien-thoai" in slugs_called
        assert "may-tinh-xach-tay" in slugs_called


def test_scrape_product_ld_json(scraper):
    """Kiểm tra scrape_product qua schema.org Product ld+json."""
    html_mock = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@type": "Product",
          "name": "Xiaomi Redmi Note 17 4GB 128GB",
          "mpn": "24116RN10I",
          "sku": "344851327977",
          "brand": {"name": "Xiaomi"},
          "offers": {
            "@type": "Offer",
            "price": 6190000,
            "availability": "https://schema.org/InStock"
          },
          "additionalProperty": [
            {"name": "Dung lượng pin", "value": "7700 mAh"},
            {"name": "Màn hình", "value": "6.9 inch"}
          ]
        }
        </script>
      </head>
      <body>
        <h1>Xiaomi Redmi Note 17 4GB 128GB</h1>
      </body>
    </html>
    """
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = html_mock
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        item = scraper.scrape_product("https://fptshop.com.vn/dien-thoai/xiaomi-redmi-note-17")

        assert item is not None
        assert item.product_name == "Xiaomi Redmi Note 17 4GB 128GB"
        assert item.current_price == 6190000
        assert item.is_in_stock is True
        assert item.specifications.get("Hãng") == "Xiaomi"
        assert item.specifications.get("Part Number") == "24116RN10I"
        assert item.specifications.get("Code") == "344851327977"
        assert item.specifications.get("Dung lượng pin") == "7700 mAh"
        assert item.specifications.get("Bộ nhớ/RAM") == "4 GB / 128 GB"

