import re
import logging
from typing import Optional, List, Dict, Any
import requests
from bs4 import BeautifulSoup
from app.services.scrapers.base import BaseScraper
from app.schemas.crawl import ScrapedProductItem

logger = logging.getLogger(__name__)


class HoanghaScraper(BaseScraper):
    """Scraper thu thập dữ liệu giá và thông số kỹ thuật từ Hoàng Hà Mobile (hoanghamobile.com)."""

    BASE_URL = "https://hoanghamobile.com"

    @property
    def source_name(self) -> str:
        return "HOANGHA"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://hoanghamobile.com/",
        }

    def _clean_price(self, price_str: Optional[str]) -> Optional[int]:
        if not price_str:
            return None
        digits = re.sub(r"[^\d]", "", price_str)
        return int(digits) if digits else None

    def scrape_product(self, url: str) -> Optional[ScrapedProductItem]:
        """Cào chi tiết 1 sản phẩm cụ thể từ Hoàng Hà Mobile."""
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=12)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"[HoangHa] Lỗi khi gửi request tới {url}: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Tên sản phẩm
        title_tag = soup.find("h1")
        product_name = title_tag.get_text(strip=True) if title_tag else "N/A"

        # 2. Giá sản phẩm
        price_tag = soup.select_one(".current-product-price, .product-price, .price strong, .price")
        old_price_tag = soup.select_one(".product-price-through, .price strike, .price-last")

        current_price = self._clean_price(price_tag.get_text(strip=True)) if price_tag else None
        original_price = self._clean_price(old_price_tag.get_text(strip=True)) if old_price_tag else None

        # 3. Trạng thái còn hàng
        is_in_stock = True
        body_text = soup.get_text().lower()
        if "tạm hết hàng" in body_text or "ngừng kinh doanh" in body_text:
            is_in_stock = False

        # 4. Thông số kỹ thuật
        specifications: Dict[str, Any] = {}
        for row in soup.select(".specs-list tr, .technical-content tr"):
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

    def scrape_category(self, category: str, limit: int = 35) -> List[ScrapedProductItem]:
        """Cào danh mục sản phẩm (điện thoại hoặc laptop) từ Hoàng Hà Mobile theo phân trang."""
        if category.lower() == "laptop":
            base_category_url = f"{self.BASE_URL}/laptop"
        else:
            base_category_url = f"{self.BASE_URL}/dien-thoai-di-dong"

        results: List[ScrapedProductItem] = []
        page = 1
        max_pages = 6  # Tối đa 6 trang để đảm bảo số lượng

        logger.info(f"[HoangHa] Bắt đầu cào ngành hàng '{category}' (Mục tiêu: {limit} sản phẩm)...")

        while len(results) < limit and page <= max_pages:
            page_url = f"{base_category_url}?p={page}"
            try:
                res = requests.get(page_url, headers=self._get_headers(), timeout=12)
                res.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.warning(f"[HoangHa] Lỗi khi tải trang {page_url}: {e}")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            container = soup.find(class_="v5-grid-items")
            if not container:
                # Fallback: tìm container sản phẩm khác
                container = soup.select_one(".list-product, .grid-items")
                if not container:
                    break

            cards = container.find_all("div", recursive=False)
            if not cards:
                break

            page_items_count = 0
            for card in cards:
                title_el = card.find("h3") or card.find("h4")
                if not title_el:
                    continue

                a_tag = title_el.find("a")
                product_name = a_tag.get_text(strip=True) if a_tag else title_el.get_text(strip=True)
                if not product_name or len(product_name) < 4:
                    continue

                # Lấy link sản phẩm
                href = a_tag["href"].strip() if a_tag and a_tag.get("href") else ""
                if href and not href.startswith("http"):
                    product_url = f"{self.BASE_URL}{href if href.startswith('/') else '/' + href}"
                else:
                    product_url = href or page_url

                # Trích xuất giá bán
                price_el = card.select_one(".price-tags .price, .price")
                old_price_el = card.select_one(".price.price-last")

                current_price = self._clean_price(price_el.get_text()) if price_el else None
                original_price = self._clean_price(old_price_el.get_text()) if old_price_el else None

                # Tình trạng kho
                stock_el = card.select_one(".list-conhang, .product-panel_detail")
                is_in_stock = True
                if stock_el:
                    txt = stock_el.get_text().lower()
                    if "hết hàng" in txt or "tạm hết" in txt:
                        is_in_stock = False

                # Thông số tóm tắt
                specs_list = [li.get_text(strip=True) for li in card.select(".specs .spec-item")]
                specs_dict = {"summary": " | ".join(specs_list)} if specs_list else {}

                item = ScrapedProductItem(
                    source=self.source_name,
                    url=product_url,
                    product_name=product_name,
                    current_price=current_price,
                    original_price=original_price,
                    is_in_stock=is_in_stock,
                    specifications=specs_dict
                )
                results.append(item)
                page_items_count += 1

                if len(results) >= limit:
                    break

            logger.info(f"[HoangHa] Trang {page}: Thu thập được {page_items_count} sản phẩm (Tổng hiện tại: {len(results)})")
            page += 1

        logger.info(f"[HoangHa] Hoàn thành cào {len(results)} sản phẩm ngành {category}")
        return results
