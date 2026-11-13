import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from app.schemas.crawl import ScrapedProductItem
from app.services.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class FptShopScraper(BaseScraper):
    """Scraper thu thập dữ liệu giá và thông số kỹ thuật từ FPT Shop (fptshop.com.vn).
    Sử dụng FPT Shop Public API để cào danh mục với hiệu năng và độ ổn định cao.
    """

    API_URL = "https://papi.fptshop.com.vn/gw/v1/public/fulltext-search-service/category"
    BASE_URL = "https://fptshop.com.vn"

    CATEGORY_SLUG_MAP = {
        "phone": "dien-thoai",
        "dien-thoai": "dien-thoai",
        "mobile": "dien-thoai",
        "laptop": "may-tinh-xach-tay",
        "may-tinh-xach-tay": "may-tinh-xach-tay",
    }

    @property
    def source_name(self) -> str:
        return "FPTSHOP"

    def _get_api_headers(self) -> Dict[str, str]:
        return {
            "order-channel": "1",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

    @staticmethod
    def _extract_storage_from_name(name: str) -> Optional[str]:
        """Trích xuất RAM/ROM từ tên sản phẩm.
        Ví dụ: 'iPhone 16 Pro 256GB' -> '256 GB'
               'Samsung S24 Ultra 12GB 256GB' -> '12 GB / 256 GB'
        """
        if not name:
            return None
        matches = re.findall(r"\b(\d+\s*(?:GB|TB))\b", name, flags=re.IGNORECASE)
        if matches:
            formatted = [re.sub(r"(\d+)\s*(GB|TB)", r"\1 \2", m, flags=re.IGNORECASE).upper() for m in matches]
            return " / ".join(formatted)
        return None

    @staticmethod
    def _extract_part_number(name: str) -> Optional[str]:
        """Trích xuất mã Part-Number từ tên sản phẩm (đặc biệt là laptop).
        Ví dụ: 'Asus Vivobook 16 X1607CA-MB387W Ultra 5' -> 'X1607CA-MB387W'
               'Acer Nitro 5 AN515-58-773Y i7' -> 'AN515-58-773Y'
        """
        if not name:
            return None
        matches = re.findall(r"\b([A-Za-z0-9]{2,}-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\b", name)
        for m in matches:
            m_upper = m.upper()
            if re.match(r"^(I[3579]|R[3579])-\d+", m_upper):
                continue
            if m_upper in ["WI-FI", "TYPE-C"]:
                continue
            if any(c.isdigit() for c in m) and any(c.isalpha() for c in m) and len(m) >= 5:
                return m_upper
        return None

    def _parse_api_item(self, raw_item: Dict[str, Any]) -> Optional[ScrapedProductItem]:
        """Chuẩn hóa một item từ FPT Shop category API thành ScrapedProductItem."""
        if not isinstance(raw_item, dict):
            return None

        name = (raw_item.get("name") or raw_item.get("displayName") or "").strip()
        if not name:
            return None

        # 1. URL
        slug = (raw_item.get("slug") or "").strip()
        if slug.startswith("http://") or slug.startswith("https://"):
            url = slug
        elif slug:
            url = f"{self.BASE_URL}/{slug.lstrip('/')}"
        else:
            url = f"{self.BASE_URL}/san-pham/{raw_item.get('code', '')}"

        # 2. Giá sản phẩm
        raw_current = raw_item.get("currentPrice") or raw_item.get("price")
        raw_original = raw_item.get("originalPrice") or raw_item.get("price") or raw_current

        current_price: Optional[int] = None
        if raw_current is not None:
            try:
                current_price = int(raw_current)
            except (ValueError, TypeError):
                current_price = None

        original_price: Optional[int] = None
        if raw_original is not None:
            try:
                original_price = int(raw_original)
            except (ValueError, TypeError):
                original_price = None

        if current_price is not None and original_price is None:
            original_price = current_price
        if original_price is not None and current_price is None:
            current_price = original_price

        # 3. Tình trạng kho
        is_in_stock = True
        if not current_price or current_price <= 0:
            is_in_stock = False
        else:
            skus = raw_item.get("skus") or []
            if skus:
                all_out = True
                for s in skus:
                    st = (s.get("statusOnWeb") or {}).get("displayName", "").lower()
                    if any(w in st for w in ["mua ngay", "đặt hàng", "còn hàng", "order", "nhận thông tin"]):
                        all_out = False
                        break
                    elif any(w in st for w in ["hết hàng", "ngừng kinh doanh", "tạm hết"]):
                        continue
                    else:
                        all_out = False
                        break
                if all_out:
                    is_in_stock = False

        # 4. Thông số kỹ thuật
        specifications: Dict[str, Any] = {}
        brand_info = raw_item.get("brand") or {}
        brand_name = brand_info.get("name") if isinstance(brand_info, dict) else str(brand_info)
        if brand_name:
            specifications["Hãng"] = brand_name

        code = raw_item.get("code")
        if code:
            specifications["Code"] = str(code)

        storage = self._extract_storage_from_name(name)
        if storage:
            specifications["Bộ nhớ/RAM"] = storage

        part_number = self._extract_part_number(name)
        if part_number:
            specifications["Part Number"] = part_number

        key_points = raw_item.get("keySellingPoints") or []
        if isinstance(key_points, list):
            for kp in key_points:
                if not isinstance(kp, dict):
                    continue
                title = (kp.get("title") or "").strip()
                if not title:
                    continue
                t_lower = title.lower()
                if "pin" in t_lower:
                    specifications["Pin"] = title
                elif any(w in t_lower for w in ["snapdragon", "apple a", "chip", "core i", "ryzen", "helio", "dimensity", "intel", "amd"]):
                    specifications["CPU/Chip"] = title
                elif "màn hình" in t_lower or ('"' in title and any(c.isdigit() for c in title)):
                    specifications["Màn hình"] = title

        if specifications:
            summary_parts = [f"{k}: {v}" for k, v in specifications.items() if k != "summary"]
            specifications["summary"] = " | ".join(summary_parts)

        return ScrapedProductItem(
            source=self.source_name,
            url=url,
            product_name=name,
            current_price=current_price,
            original_price=original_price,
            is_in_stock=is_in_stock,
            specifications=specifications,
        )

    def _scrape_single_category(
        self,
        category: str,
        limit: Optional[int] = None,
        on_progress: Optional[Any] = None,
    ) -> List[ScrapedProductItem]:
        """Cào một ngành hàng cụ thể ('phone' hoặc 'laptop')."""
        slug = self.CATEGORY_SLUG_MAP.get(category.lower(), "dien-thoai")
        page_size = 48
        skip = 0
        results: List[ScrapedProductItem] = []
        seen_urls = set()
        page = 1

        limit_desc = "KHÔNG GIỚI HẠN (tất cả các trang)" if (limit is None or limit <= 0) else f"{limit} sản phẩm"
        logger.info(f"[FptShop] Bắt đầu cào ngành '{category}' (Slug: {slug}, Mục tiêu: {limit_desc})...")

        with httpx.Client(timeout=15.0) as client:
            while True:
                if limit is not None and limit > 0 and len(results) >= limit:
                    break

                payload = {
                    "skipCount": skip,
                    "maxResultCount": page_size,
                    "sortMethod": "noi-bat",
                    "slug": slug,
                    "categoryType": "category",
                    "location": {},
                }

                data = None
                for attempt in range(3):
                    try:
                        resp = client.post(self.API_URL, headers=self._get_api_headers(), json=payload)
                        resp.raise_for_status()
                        data = resp.json()
                        break
                    except (httpx.RequestError, httpx.HTTPStatusError) as e:
                        if attempt < 2:
                            logger.warning(
                                f"[FptShop] Lỗi mạng khi tải trang {page} (lần {attempt + 1}/3): {e}. Thử lại..."
                            )
                            time.sleep(1.0 * (attempt + 1))
                        else:
                            logger.error(f"[FptShop] Thất bại khi tải trang {page} sau 3 lần thử: {e}")
                            break

                if not data or not isinstance(data, dict):
                    break

                items = data.get("items") or []
                total_count = data.get("totalCount", 0)
                total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

                if not items:
                    logger.info(f"[FptShop] Không còn sản phẩm ở trang {page} (skip={skip}). Dừng phân trang.")
                    break

                page_items_count = 0
                for raw_item in items:
                    parsed = self._parse_api_item(raw_item)
                    if not parsed:
                        continue
                    if parsed.url in seen_urls:
                        continue
                    seen_urls.add(parsed.url)
                    results.append(parsed)
                    page_items_count += 1

                    if limit is not None and limit > 0 and len(results) >= limit:
                        break

                logger.info(
                    f"[FptShop] Trang {page}/{total_pages}: Thu thập {page_items_count} sản phẩm (Tổng tích lũy: {len(results)})"
                )
                if on_progress:
                    on_progress(
                        page,
                        total_pages,
                        len(results),
                        f"FPT Shop trang {page}/{total_pages}: Đã thu thập {len(results)} sản phẩm...",
                    )

                skip += len(items)
                page += 1

                if skip >= total_count or len(items) < page_size:
                    logger.info(f"[FptShop] Đã duyệt đến trang cuối cùng của ngành '{category}'.")
                    break

                time.sleep(0.05)

        logger.info(f"[FptShop] Hoàn tất cào {len(results)} sản phẩm ngành '{category}'.")
        return results

    def scrape_category(
        self,
        category: str,
        limit: Optional[int] = None,
        on_progress: Optional[Any] = None,
    ) -> List[ScrapedProductItem]:
        """Cào danh mục sản phẩm từ FPT Shop.
        Hỗ trợ: 'phone' (dien-thoai), 'laptop' (may-tinh-xach-tay), 'all' (cả hai).
        """
        cat_lower = (category or "").lower().strip()

        if cat_lower in ["all", "tat-ca"]:
            results: List[ScrapedProductItem] = []
            for c in ["phone", "laptop"]:
                sub_limit = None if (limit is None or limit <= 0) else (limit - len(results))
                if sub_limit is not None and sub_limit <= 0:
                    break
                items = self._scrape_single_category(c, limit=sub_limit, on_progress=on_progress)
                results.extend(items)
            return results

        return self._scrape_single_category(cat_lower, limit=limit, on_progress=on_progress)

    def scrape_product(self, url: str) -> Optional[ScrapedProductItem]:
        """Cào thông tin chi tiết một sản phẩm cụ thể từ URL của FPT Shop."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                html_text = resp.text
        except Exception as e:
            logger.error(f"[FptShop] Lỗi khi gửi request tới {url}: {e}")
            return None

        soup = BeautifulSoup(html_text, "html.parser")

        # 1. Trích xuất từ schema.org Product ld+json
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                ld_data = json.loads(script.string)
                if isinstance(ld_data, dict) and ld_data.get("@type") == "Product":
                    name = ld_data.get("name") or "N/A"
                    offers = ld_data.get("offers") or {}
                    raw_price = offers.get("price")
                    current_price = int(raw_price) if raw_price is not None else None
                    original_price = current_price
                    avail = str(offers.get("availability", ""))
                    is_in_stock = ("InStock" in avail) if avail else (current_price is not None and current_price > 0)

                    specs: Dict[str, Any] = {}
                    brand = ld_data.get("brand") or {}
                    if isinstance(brand, dict) and brand.get("name"):
                        specs["Hãng"] = brand["name"]
                    if ld_data.get("mpn"):
                        specs["Part Number"] = str(ld_data["mpn"])
                    if ld_data.get("sku"):
                        specs["Code"] = str(ld_data["sku"])

                    for prop in ld_data.get("additionalProperty") or []:
                        if isinstance(prop, dict) and prop.get("name") and prop.get("value"):
                            specs[prop["name"]] = str(prop["value"])

                    storage = self._extract_storage_from_name(name)
                    if storage and "Bộ nhớ/RAM" not in specs:
                        specs["Bộ nhớ/RAM"] = storage

                    if specs:
                        specs["summary"] = " | ".join([f"{k}: {v}" for k, v in specs.items() if k != "summary"])

                    return ScrapedProductItem(
                        source=self.source_name,
                        url=url,
                        product_name=name,
                        current_price=current_price,
                        original_price=original_price,
                        is_in_stock=is_in_stock,
                        specifications=specs,
                    )
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

        # 2. Fallback sang DOM HTML
        title_tag = soup.find("h1")
        product_name = title_tag.get_text(strip=True) if title_tag else "N/A"

        price_tag = soup.select_one(".price, .special-price, .product-price, .t-price")
        old_price_tag = soup.select_one(".strike-price, .old-price, .original-price")

        def _clean_price(p_str: Optional[str]) -> Optional[int]:
            if not p_str:
                return None
            digits = re.sub(r"[^\d]", "", p_str)
            return int(digits) if digits else None

        current_price = _clean_price(price_tag.get_text(strip=True)) if price_tag else None
        original_price = _clean_price(old_price_tag.get_text(strip=True)) if old_price_tag else current_price

        if not current_price or current_price <= 0:
            return None

        is_in_stock = True
        out_of_stock_el = soup.select_one(".btn-out-of-stock, .tam-het-hang, .ngung-kinh-doanh")
        if out_of_stock_el:
            is_in_stock = False

        specs = {}
        storage = self._extract_storage_from_name(product_name)
        if storage:
            specs["Bộ nhớ/RAM"] = storage
        part_num = self._extract_part_number(product_name)
        if part_num:
            specs["Part Number"] = part_num

        return ScrapedProductItem(
            source=self.source_name,
            url=url,
            product_name=product_name,
            current_price=current_price,
            original_price=original_price,
            is_in_stock=is_in_stock,
            specifications=specs,
        )
