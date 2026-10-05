import json
import unittest
from unittest.mock import MagicMock, patch
import requests

from app.services.scrapers.cellphones import CellphonesScraper
from app.schemas.crawl import ScrapedProductItem


class CellphonesScraperTests(unittest.TestCase):
    def setUp(self):
        self.scraper = CellphonesScraper()

    def test_scraper_identity(self):
        self.assertEqual(self.scraper.source_name, "CELLPHONES")
        self.assertEqual(self.scraper.BASE_URL, "https://cellphones.com.vn")

    def test_clean_price(self):
        self.assertEqual(self.scraper._clean_price("24.990.000 ₫"), 24990000)
        self.assertEqual(self.scraper._clean_price("15,500,000"), 15500000)
        self.assertEqual(self.scraper._clean_price(35000000), 35000000)
        self.assertIsNone(self.scraper._clean_price(None))
        self.assertIsNone(self.scraper._clean_price(""))

    def test_extract_storage_from_name(self):
        self.assertEqual(self.scraper._extract_storage_from_name("iPhone 16 Pro 256GB"), "256 GB")
        self.assertEqual(
            self.scraper._extract_storage_from_name("Samsung Galaxy S24 Ultra 12GB 512GB"),
            "12 GB / 512 GB"
        )
        self.assertIsNone(self.scraper._extract_storage_from_name(None))

    def test_graphql_scraper_fetches_and_normalizes_products(self):
        mock_response_data = {
            "data": {
                "products": [
                    {
                        "general": {
                            "product_id": 1001,
                            "name": "Laptop Acer Gaming Aspire 7 A715-59G-57TU",
                            "url_path": "laptop-acer-gaming-aspire-7-a715-59g-57tu.html",
                            "manufacturer": "Acer",
                            "attributes": {
                                "product_condition": "Mới",
                                "laptop_part_number": "A715-59G-57TU",
                                "laptop_cpu": "i5 12450H",
                                "laptop_ram": "16GB",
                            },
                        },
                        "filterable": {
                            "price": 25990000.0,
                            "special_price": 24990000.0,
                            "stock": 10,
                        },
                    },
                    {
                        # Sản phẩm cũ cần bị loại bỏ
                        "general": {
                            "product_id": 1002,
                            "name": "Laptop Acer Gaming Cũ trầy xước",
                            "url_path": "laptop-acer-cu.html",
                            "attributes": {"product_condition": "Cũ"},
                        },
                        "filterable": {"price": 15000000.0, "special_price": 14000000.0, "stock": 1},
                    },
                ]
            }
        }
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = mock_response_data
        mock_res.raise_for_status.return_value = None

        with patch("requests.Session.post", return_value=mock_res):
            items = self.scraper.scrape_category("laptop", limit=5)

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertIsInstance(item, ScrapedProductItem)
        self.assertEqual(item.product_name, "Laptop Acer Gaming Aspire 7 A715-59G-57TU")
        self.assertEqual(item.current_price, 24990000)
        self.assertEqual(item.original_price, 25990000)
        self.assertTrue(item.is_in_stock)
        self.assertEqual(item.specifications.get("Part Number"), "A715-59G-57TU")

    def test_graphql_scraper_retries_on_network_error(self):
        with patch("requests.Session.post", side_effect=requests.exceptions.ConnectionError("Connection failed")):
            with patch("time.sleep", return_value=None):
                items = self.scraper.scrape_category("mobile", limit=5)
        self.assertEqual(items, [])


if __name__ == "__main__":
    unittest.main()
