from datetime import datetime, timezone
import json
import random
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.scrapers.cellphones import (
    CellphoneSScraper,
    CrawlConfig,
    CrawlError,
    ScrapedProduct,
)

CAPTURED_AT = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


class ConfigTests(unittest.TestCase):
    def test_default_config_is_valid(self):
        config = CrawlConfig(category="mobile")
        self.assertEqual(config.category, "mobile")
        self.assertEqual(config.max_products, 4000)

    def test_rejects_unsupported_category(self):
        with self.assertRaises(ValueError):
            CrawlConfig(category="tablet")

    def test_rejects_reversed_delay_range(self):
        with self.assertRaises(ValueError):
            CrawlConfig(min_delay_seconds=5.0, max_delay_seconds=2.0)

    def test_rejects_invalid_limits(self):
        with self.assertRaises(ValueError):
            CrawlConfig(max_products=0)


class GraphQLScraperTests(unittest.IsolatedAsyncioTestCase):
    async def test_graphql_scraper_fetches_and_normalizes_products(self):
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
                        # Used product that should be filtered out
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
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False

        config = CrawlConfig(
            category="laptop",
            max_products=10,
            min_delay_seconds=0.01,
            max_delay_seconds=0.02,
        )
        sleeper = AsyncMock()
        sink = MagicMock()
        sink.append_products = AsyncMock()
        scraper = CellphoneSScraper(config, sleeper=sleeper, rng=random.Random(42))

        with patch("urllib.request.urlopen", return_value=mock_resp):
            report = await scraper.scrape(sink=sink)

        self.assertEqual(report.parsed_count, 1)
        self.assertEqual(report.rejected_count, 1)
        self.assertEqual(len(report.products), 1)

        product = report.products[0]
        self.assertEqual(product.name, "Laptop Acer Gaming Aspire 7 A715-59G-57TU")
        self.assertEqual(product.price_vnd, 24990000)
        self.assertEqual(product.original_price_vnd, 25990000)
        self.assertEqual(product.raw_status, "Còn hàng")
        self.assertEqual(product.part_number, "A715-59G-57TU")
        self.assertEqual(product.manufacturer, "Acer")

        sink.append_products.assert_awaited_once_with(report.products)

    async def test_graphql_scraper_retries_on_network_error(self):
        config = CrawlConfig(
            category="mobile",
            max_retries=1,
            min_delay_seconds=0.01,
            max_delay_seconds=0.02,
        )
        sleeper = AsyncMock()
        scraper = CellphoneSScraper(config, sleeper=sleeper)

        with patch("urllib.request.urlopen", side_effect=Exception("Connection reset")):
            with self.assertRaises(CrawlError):
                await scraper.scrape()


if __name__ == "__main__":
    unittest.main()
