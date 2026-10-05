import re
import time
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
        # Loại bỏ phần trăm giảm giá (VD: - 17%, -15%)
        cleaned = re.sub(r"-\s*\d+%", "", str(price_str))
        match = re.search(r"(\d[\d\.,]*\d|\d+)", cleaned)
        if match:
            digits = re.sub(r"[^\d]", "", match.group(1))
            val = int(digits) if digits else None
            # Phòng ngừa lỗi dính 2 số phần trăm ở đuôi (VD: 4699000017 -> 46990000)
            if val and val > 500_000_000:
                val_str = str(val)
                if len(val_str) >= 10:
                    val = int(val_str[:-2])
            return val
        return None

    @staticmethod
    def _extract_storage_from_name(name: str) -> Optional[str]:
        """Trích xuất RAM/ROM từ tên sản phẩm.
        Ví dụ: 'iPhone 16 Pro 256GB' -> '256 GB'
               'Samsung Z Fold6 5G 12GB/256GB' -> '12 GB / 256 GB'
        """
        if not name:
            return None
        matches = re.findall(r"\b(\d+\s*(?:GB|TB))\b", name, flags=re.IGNORECASE)
        if matches:
            formatted = [re.sub(r"(\d+)\s*(GB|TB)", r"\1 \2", m, flags=re.IGNORECASE).upper() for m in matches]
            return " / ".join(formatted)
        return None

    def _parse_card_specs(self, specs_list: List[str], product_name: str) -> Dict[str, Any]:
        """Chuẩn hóa danh sách specs ngắn trên thẻ sản phẩm Hoàng Hà thành dict."""
        specs_dict: Dict[str, Any] = {}
        for s in specs_list:
            s_clean = s.strip()
            if not s_clean:
                continue
            if re.search(r"\b\d+\s*mAh\b", s_clean, re.I):
                specs_dict["Pin"] = s_clean
            elif re.search(r"\b\d+\s*(?:GB|TB)\b", s_clean, re.I):
                if "Bộ nhớ/RAM" in specs_dict:
                    specs_dict["Bộ nhớ/RAM"] += f" / {s_clean}"
                else:
                    specs_dict["Bộ nhớ/RAM"] = s_clean
            elif re.search(r"[\d\.,]+\s*(?:\"|inch|inches)", s_clean, re.I):
                specs_dict["Màn hình"] = s_clean
            elif any(k in s_clean.lower() for k in ["chip", "cpu", "snapdragon", "dimensity", "apple a", "intel", "amd", "ryzen", "core i", "core ultra", "m1", "m2", "m3", "m4"]):
                if "CPU/Chip" not in specs_dict:
                    specs_dict["CPU/Chip"] = s_clean

        # Nếu chưa có Bộ nhớ/RAM thì trích xuất từ tên sản phẩm
        if "Bộ nhớ/RAM" not in specs_dict:
            storage_from_name = self._extract_storage_from_name(product_name)
            if storage_from_name:
                specs_dict["Bộ nhớ/RAM"] = storage_from_name

        specs_dict["summary"] = " | ".join([f"{k}: {v}" for k, v in specs_dict.items()])
        return specs_dict

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

        old_price_raw = None
        if old_price_tag:
            strike_tag = old_price_tag.find("strike")
            old_price_raw = strike_tag.get_text(strip=True) if strike_tag else old_price_tag.get_text(strip=True)

        current_price = self._clean_price(price_tag.get_text(strip=True)) if price_tag else None
        original_price = self._clean_price(old_price_raw) if old_price_raw else None

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

        if "summary" not in specifications and specifications:
            specifications["summary"] = " | ".join([f"{k}: {v}" for k, v in list(specifications.items())[:6]])

        return ScrapedProductItem(
            source=self.source_name,
            url=url,
            product_name=product_name,
            current_price=current_price,
            original_price=original_price,
            is_in_stock=is_in_stock,
            specifications=specifications
        )

    def scrape_category(
        self,
        category: str,
        limit: Optional[int] = None,
        on_progress: Optional[Any] = None,
    ) -> List[ScrapedProductItem]:
        if category.lower() == "laptop":
            base_category_url = f"{self.BASE_URL}/laptop"
        else:
            base_category_url = f"{self.BASE_URL}/dien-thoai-di-dong"

        results: List[ScrapedProductItem] = []
        seen_urls = set()
        page = 1
        max_pages = 100

        session = requests.Session()
        session.headers.update(self._get_headers())

        limit_desc = "KHÔNG GIỚI HẠN (tất cả các trang)" if (limit is None or limit <= 0) else f"{limit} sản phẩm"
        logger.info(f"[HoangHa] Bắt đầu cào ngành hàng '{category}' (Mục tiêu: {limit_desc})...")

        while (limit is None or limit <= 0 or len(results) < limit) and page <= max_pages:
            page_url = f"{base_category_url}?p={page}"
            res = None
            for attempt in range(3):
                try:
                    res = session.get(page_url, timeout=20)
                    res.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    logger.warning(f"[HoangHa] Thử lần {attempt + 1}/3 tải trang {page_url} thất bại: {e}")
                    time.sleep(1.5)

            if not res or res.status_code != 200:
                logger.error(f"[HoangHa] Dừng cào: Không thể tải trang {page_url} sau 3 lần thử.")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            container = soup.find(class_="v5-grid-items")
            if not container:
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

                # Khử trùng lặp URL
                if product_url in seen_urls:
                    continue
                seen_urls.add(product_url)

                # Trích xuất giá bán
                price_el = card.select_one(".price-tags .price, .price strong, .price")
                old_price_el = card.select_one(".price.price-last, .price strike")

                old_price_raw = None
                if old_price_el:
                    strike_el = old_price_el.find("strike")
                    old_price_raw = strike_el.get_text(strip=True) if strike_el else old_price_el.get_text(strip=True)

                current_price = self._clean_price(price_el.get_text()) if price_el else None
                original_price = self._clean_price(old_price_raw) if old_price_raw else None

                # Tình trạng kho
                stock_el = card.select_one(".list-conhang, .product-panel_detail")
                is_in_stock = True
                if stock_el:
                    txt = stock_el.get_text().lower()
                    if "hết hàng" in txt or "tạm hết" in txt:
                        is_in_stock = False

                # Thông số tóm tắt
                specs_list = [li.get_text(strip=True) for li in card.select(".specs .spec-item, .specs li, .spec-list li")]
                specs_dict = self._parse_card_specs(specs_list, product_name)

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

                if limit is not None and limit > 0 and len(results) >= limit:
                    break

            logger.info(f"[HoangHa] Trang {page}: Thu thập được {page_items_count} sản phẩm (Tổng hiện tại: {len(results)})")
            if on_progress:
                on_progress(page, None, len(results), f"Hoàng Hà trang {page}: Đã thu thập {len(results)} sản phẩm...")
            if page_items_count == 0:
                logger.info(f"[HoangHa] Không còn sản phẩm mới ở trang {page}. Đã hoàn tất danh mục.")
                break
            time.sleep(0.5)
            page += 1

        logger.info(f"[HoangHa] Hoàn thành cào {len(results)} sản phẩm ngành {category}")
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    scraper = HoanghaScraper()
    print("Kiểm thử cào thử nghiệm 3 sản phẩm Hoàng Hà Mobile...")
    sample_items = scraper.scrape_category("phone", limit=3)
    for it in sample_items:
        print(f"- {it.product_name} | Giá: {it.current_price:,}đ | Còn hàng: {it.is_in_stock}")
