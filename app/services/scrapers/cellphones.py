import re
import json
import logging
import requests
from typing import Optional, List
from bs4 import BeautifulSoup
from app.services.scrapers.base import BaseScraper
from app.schemas.crawl import ScrapedProductItem

logger = logging.getLogger(__name__)


class CellphonesScraper(BaseScraper):
    """Scraper thu thập dữ liệu giá và thông số kỹ thuật từ CellphoneS."""

    @property
    def source_name(self) -> str:
        return "CELLPHONES"

    def _clean_price(self, price_str: Optional[str]) -> Optional[int]:
        if not price_str:
            return None
        # Loại bỏ các ký tự không phải số
        digits = re.sub(r"[^\d]", "", price_str)
        return int(digits) if digits else None

    def scrape_product(self, url: str) -> Optional[ScrapedProductItem]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            response = requests.get(url, headers=headers, timeout=12)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"[CellphoneS] Lỗi khi gửi request tới {url}: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Trích xuất tên sản phẩm
        title_tag = soup.find("h1")
        product_name = title_tag.get_text(strip=True) if title_tag else "N/A"

        # 2. Trích xuất giá sản phẩm
        price_tag = soup.select_one(".sale-price, .product__price--show, .special-price, .t-price")
        old_price_tag = soup.select_one(".base-price, .product__price--through, .old-price")

        current_price_str = price_tag.get_text(strip=True) if price_tag else None
        old_price_str = old_price_tag.get_text(strip=True) if old_price_tag else None

        # Fallback 1: Trích xuất từ JSON-LD (Schema.org)
        if not current_price_str:
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "Product":
                        offers = data.get("offers", {})
                        if isinstance(offers, dict) and "price" in offers:
                            current_price_str = str(offers["price"])
                            break
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue

        current_price = self._clean_price(current_price_str)
        original_price = self._clean_price(old_price_str)

        # 3. Trạng thái còn hàng (Out of stock check)
        is_in_stock = True
        btn_buy = soup.select_one(".btn-buy, .button__buy")
        if btn_buy:
            btn_text = btn_buy.get_text(strip=True).lower()
            if "hết hàng" in btn_text or "tạm hết hàng" in btn_text or "sắp về hàng" in btn_text:
                is_in_stock = False

        # 4. Trích xuất thông số kỹ thuật
        specifications = {}
        spec_table = soup.find("table")
        if spec_table:
            for row in spec_table.find_all("tr"):
                cols = row.find_all(["td", "th"])
                if len(cols) >= 2:
                    k = cols[0].get_text(strip=True)
                    v = cols[1].get_text(strip=True)
                    specifications[k] = v

        return ScrapedProductItem(
            source=self.source_name,
            url=url,
            product_name=product_name,
            current_price=current_price,
            original_price=original_price,
            is_in_stock=is_in_stock,
            specifications=specifications
        )

    def scrape_category(self, category: str, limit: int = 10) -> List[ScrapedProductItem]:
        """Triển khai mẫu cho cào danh sách sản phẩm theo category."""
        # Danh sách mẫu demo sản phẩm hot phục vụ kiểm thử nhanh
        sample_urls = [
            "https://cellphones.com.vn/iphone-15-pro-max.html",
            "https://cellphones.com.vn/samsung-galaxy-s24-ultra.html",
        ]
        results = []
        for url in sample_urls[:limit]:
            item = self.scrape_product(url)
            if item:
                results.append(item)
        return results
