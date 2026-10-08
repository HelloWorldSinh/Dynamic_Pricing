import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Đảm bảo import được app.* kể cả khi chạy trực tiếp file này
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.schemas.crawl import ScrapedProductItem  # noqa: E402
from app.services.scrapers.base import BaseScraper  # noqa: E402

logger = logging.getLogger(__name__)


class CellphonesScraper(BaseScraper):
    """Scraper thu thập dữ liệu giá và thông số kỹ thuật từ CellphoneS (cellphones.com.vn).
    Hỗ trợ cào toàn bộ danh mục từ trang đầu đến trang cuối (không giới hạn) qua GraphQL API.
    """

    GRAPHQL_URL = "https://api.cellphones.com.vn/v2/graphql/query"
    BASE_URL = "https://cellphones.com.vn"

    # Regex nhận diện và loại bỏ hàng cũ, hàng trưng bày, đã kích hoạt, ngừng kinh doanh
    USED_PRODUCT_RE = re.compile(
        r"da kich hoat|đã kích hoạt|hang cu|hàng cũ|doi tra|đổi trả|cu xuoc|cũ xước|cu tray|cũ trầy|"
        r"trung bay|trưng bày|refurbished|cu dep|cũ đẹp|da qua su dung|đã qua sử dụng|"
        r"ngung kinh doanh|ngừng kinh doanh|tam het|tạm hết|dung kinh doanh|dừng kinh doanh|"
        r"khong con kinh doanh|không còn kinh doanh",
        re.IGNORECASE,
    )

    # Ánh xạ category name sang Category ID của CellphoneS
    CATEGORY_ID_MAP = {
        "phone": "3",
        "mobile": "3",
        "dien-thoai": "3",
        "laptop": "380",
        "may-tinh-xach-tay": "380",
    }

    @property
    def source_name(self) -> str:
        return "CELLPHONES"

    def _get_api_headers(self, category: str = "phone") -> Dict[str, str]:
        referer = f"{self.BASE_URL}/laptop.html" if category.lower() in ["laptop", "may-tinh-xach-tay"] else f"{self.BASE_URL}/mobile.html"
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Origin": self.BASE_URL,
            "Referer": referer,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _clean_price(self, price_str: Optional[str]) -> Optional[int]:
        if not price_str:
            return None
        digits = re.sub(r"[^\d]", "", str(price_str))
        return int(digits) if digits else None

    def _clean_html_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        # Đổi thẻ <br> thành dấu phẩy, tránh dùng | để không làm gãy cấu trúc các trường thông số
        clean = re.sub(r"<br\s*/?>", ", ", str(text), flags=re.IGNORECASE)
        # Loại bỏ các tag HTML còn lại
        clean = re.sub(r"<[^>]+>", "", clean)
        # Chuẩn hóa khoảng trắng
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    @staticmethod
    def _extract_storage_from_name(name: str) -> Optional[str]:
        """Trích xuất RAM/ROM từ tên sản phẩm nếu API thiếu trường storage.
        Ví dụ: 'iPhone 18 Pro 256GB' -> '256 GB'
               'Samsung S26 Ultra 12GB 256GB' -> '12 GB / 256 GB'
        """
        if not name:
            return None
        matches = re.findall(r"\b(\d+\s*(?:GB|TB))\b", name, flags=re.IGNORECASE)
        if matches:
            formatted = [re.sub(r"(\d+)\s*(GB|TB)", r"\1 \2", m, flags=re.IGNORECASE).upper() for m in matches]
            return " / ".join(formatted)
        return None

    def scrape_product(self, url: str) -> Optional[ScrapedProductItem]:
        """Cào thông tin chi tiết một sản phẩm cụ thể từ URL HTML."""
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

        # Lọc bỏ sản phẩm ngừng kinh doanh (không có giá bán hợp lệ hoặc giá <= 0)
        if not current_price or current_price <= 0:
            logger.info(f"[CellphoneS] Bỏ qua sản phẩm ngừng kinh doanh (không có giá hợp lệ): {url}")
            return None

        # 3. Trạng thái còn hàng (Out of stock check)
        is_in_stock = True
        btn_buy = soup.select_one(".btn-buy, .button__buy")
        if btn_buy:
            btn_text = btn_buy.get_text(strip=True).lower()
            if "hết hàng" in btn_text or "tạm hết hàng" in btn_text or "sắp về hàng" in btn_text:
                is_in_stock = False

        # 4. Trích xuất thông số kỹ thuật
        specifications: Dict[str, Any] = {}
        spec_table = soup.find("table")
        if spec_table:
            for row in spec_table.find_all("tr"):
                cols = row.find_all(["td", "th"])
                if len(cols) >= 2:
                    k = cols[0].get_text(strip=True)
                    v = cols[1].get_text(strip=True)
                    specifications[k] = v

        if specifications:
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

    def get_category_product_urls(self, category: str, limit: Optional[int] = None) -> List[str]:
        """Lấy danh sách link sản phẩm từ CellphoneS.
        Nếu limit=None hoặc <= 0, lấy toàn bộ link sản phẩm từ trang đầu đến trang cuối.
        """
        cate_id = self.CATEGORY_ID_MAP.get(category.lower(), "3")
        headers = self._get_api_headers(category)
        session = requests.Session()
        session.headers.update(headers)

        urls: List[str] = []
        page = 1
        page_size = 50

        while True:
            query = f"""
            query filterByCateAndFilter {{
                products(
                    filter: {{
                        static: {{
                            is_parent: ["true"]
                            categories: "{cate_id}"
                            province_id: 30
                        }}
                    }}
                    page: {page}
                    sort: [{{view: desc}}]
                    size: {page_size}
                ) {{
                    general {{
                        url_path
                    }}
                }}
            }}
            """
            try:
                res = session.post(self.GRAPHQL_URL, json={"query": query, "variables": {}}, timeout=12)
                res.raise_for_status()
                data = res.json()
                prods = data.get("data", {}).get("products")
                if not prods:
                    break

                for p in prods:
                    gen = p.get("general") or {}
                    url_path = (gen.get("url_path") or "").strip()
                    if url_path:
                        full_url = url_path if url_path.startswith("http") else f"{self.BASE_URL}/{url_path.lstrip('/')}"
                        urls.append(full_url)
                        if limit is not None and limit > 0 and len(urls) >= limit:
                            return urls[:limit]

                if len(prods) < page_size:
                    break
                page += 1
            except Exception as e:
                logger.warning(f"[CellphoneS] Lỗi khi lấy URLs trang {page} cho category '{category}': {e}")
                break

        return urls

    def scrape_category(
        self,
        category: str,
        limit: Optional[int] = None,
        on_progress: Optional[Any] = None,
    ) -> List[ScrapedProductItem]:
        cate_id = self.CATEGORY_ID_MAP.get(category.lower(), "3")
        headers = self._get_api_headers(category)
        session = requests.Session()
        session.headers.update(headers)

        results: List[ScrapedProductItem] = []
        seen_urls = set()
        page = 1
        page_size = 100

        limit_desc = "KHÔNG GIỚI HẠN (từ trang đầu đến cuối)" if (limit is None or limit <= 0) else f"tối đa {limit} sản phẩm"
        logger.info(f"[CellphoneS] Bắt đầu cào ngành '{category}' (Category ID: {cate_id}, Mục tiêu: {limit_desc})...")

        while True:
            # Kiểm tra nếu đã đạt giới hạn mong muốn
            if limit is not None and limit > 0 and len(results) >= limit:
                break

            query = f"""
            query filterByCateAndFilter {{
                products(
                    filter: {{
                        static: {{
                            is_parent: ["true"]
                            categories: "{cate_id}"
                            province_id: 30
                        }}
                    }}
                    page: {page}
                    sort: [{{view: desc}}]
                    size: {page_size}
                ) {{
                    general {{
                        product_id
                        name
                        attributes
                        url_path
                    }}
                    filterable {{
                        price
                        special_price
                        stock
                        stock_available_id
                    }}
                }}
            }}
            """

            data = None
            for attempt in range(3):
                try:
                    res = session.post(self.GRAPHQL_URL, json={"query": query, "variables": {}}, timeout=15)
                    res.raise_for_status()
                    data = res.json()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        logger.warning(f"[CellphoneS] Lỗi mạng khi tải trang {page} (lần {attempt + 1}/3): {e}. Đang thử lại sau {2 * (attempt + 1)}s...")
                        time.sleep(2 * (attempt + 1))
                    else:
                        logger.warning(f"[CellphoneS] Lỗi mạng khi tải trang {page} sau 3 lần thử: {e}. Đang dừng phân trang.")
                        break

            if not data:
                break

            products = data.get("data", {}).get("products")
            if not products or len(products) == 0:
                logger.info(f"[CellphoneS] Đã duyệt đến trang cuối cùng (Trang {page} không còn sản phẩm).")
                break

            page_items_count = 0
            for p in products:
                gen = p.get("general") or {}
                filt = p.get("filterable") or {}
                attrs = gen.get("attributes") or {}

                name = (gen.get("name") or "").strip()
                if not name or name == "N/A":
                    continue

                url_path = (gen.get("url_path") or "").strip()
                full_url = url_path if url_path.startswith("http") else f"{self.BASE_URL}/{url_path.lstrip('/')}"

                # Khử trùng lặp sản phẩm giữa các trang phân trang
                if full_url in seen_urls:
                    continue

                # Lọc bỏ hàng cũ, hàng trưng bày, đã kích hoạt
                cond = attrs.get("product_condition")
                if cond and cond != "Mới":
                    continue
                if self.USED_PRODUCT_RE.search(f"{name} {url_path}"):
                    continue

                seen_urls.add(full_url)

                # Giá bán & Giá niêm yết
                price_val = filt.get("price")
                special_price_val = filt.get("special_price")

                # current_price ưu tiên special_price nếu > 0, ngược lại lấy price
                current_price = (
                    int(special_price_val)
                    if special_price_val and special_price_val > 0
                    else (int(price_val) if price_val and price_val > 0 else None)
                )
                original_price = int(price_val) if price_val and price_val > 0 else current_price

                # Lọc bỏ sản phẩm ngừng kinh doanh (không có giá bán hợp lệ hoặc giá <= 0)
                if not current_price or current_price <= 0:
                    continue

                # Tình trạng kho
                stock = filt.get("stock", 0)
                is_in_stock = bool(stock and stock > 0)

                # Thông số kỹ thuật
                specs: Dict[str, Any] = {}
                cpu_chip = attrs.get("chipset") or attrs.get("cpu")
                if cpu_chip:
                    specs["CPU/Chip"] = self._clean_html_text(str(cpu_chip))
                if attrs.get("ram"):
                    specs["RAM"] = self._clean_html_text(str(attrs.get("ram")))
                if attrs.get("storage"):
                    specs["Bộ nhớ/RAM"] = self._clean_html_text(str(attrs.get("storage")))
                else:
                    storage_from_name = self._extract_storage_from_name(name)
                    if storage_from_name:
                        specs["Bộ nhớ/RAM"] = storage_from_name
                screen = attrs.get("display_size") or attrs.get("screen_size")
                if screen:
                    specs["Màn hình"] = self._clean_html_text(str(screen))
                if attrs.get("display_resolution"):
                    specs["Độ phân giải"] = self._clean_html_text(str(attrs.get("display_resolution")))
                if attrs.get("battery"):
                    specs["Pin"] = self._clean_html_text(str(attrs.get("battery")))
                os_ver = attrs.get("operating_system") or attrs.get("os_version")
                if os_ver:
                    specs["HĐH"] = self._clean_html_text(str(os_ver))
                if attrs.get("manufacturer"):
                    specs["Hãng"] = str(attrs.get("manufacturer"))
                part_num = attrs.get("laptop_part_number") or attrs.get("model") or attrs.get("part_number")
                if part_num:
                    specs["Part Number"] = str(part_num)

                # Chuỗi summary hỗ trợ SKU Matcher
                specs["summary"] = " | ".join([f"{k}: {v}" for k, v in specs.items() if k != "summary"])

                item = ScrapedProductItem(
                    source=self.source_name,
                    url=full_url,
                    product_name=name,
                    current_price=current_price,
                    original_price=original_price,
                    is_in_stock=is_in_stock,
                    specifications=specs
                )
                results.append(item)
                page_items_count += 1

                if limit is not None and limit > 0 and len(results) >= limit:
                    break

            logger.info(f"[CellphoneS] Trang {page}: Thu thập được {page_items_count} sản phẩm (Tổng tích lũy: {len(results)})")
            if on_progress:
                on_progress(page, None, len(results), f"CellphoneS trang {page}: Đã thu thập {len(results)} sản phẩm...")

            # Nếu trang hiện tại trả về ít hơn page_size thì đây là trang cuối
            if len(products) < page_size:
                logger.info(f"[CellphoneS] Đã cào đến trang cuối cùng của danh mục '{category}'.")
                break

            page += 1
            time.sleep(0.05)

        logger.info(f"[CellphoneS] Hoàn tất cào {len(results)} sản phẩm ngành '{category}' từ trang 1 đến trang {page}.")
        return results


if __name__ == "__main__":
    from collect_sample_data import run_collection
    # Chạy thu thập toàn bộ dữ liệu CellphoneS (không giới hạn)
    run_collection(limit=None)
