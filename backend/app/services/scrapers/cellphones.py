import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

import requests

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
    Hỗ trợ cào toàn bộ danh mục và sản phẩm đơn lẻ 100% qua GraphQL API (không cào DOM HTML).
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

    def _parse_product_dict(
        self,
        p: Dict[str, Any],
        seen_urls: Optional[set] = None
    ) -> Optional[ScrapedProductItem]:
        """Chuẩn hóa một item sản phẩm từ GraphQL API của CellphoneS thành ScrapedProductItem."""
        gen = p.get("general") or {}
        filt = p.get("filterable") or {}
        attrs = gen.get("attributes") or {}

        name = (gen.get("name") or "").strip()
        if not name or name == "N/A":
            return None

        url_path = (gen.get("url_path") or "").strip()
        full_url = url_path if url_path.startswith("http") else f"{self.BASE_URL}/{url_path.lstrip('/')}"

        # Khử trùng lặp sản phẩm giữa các trang phân trang
        if seen_urls is not None and full_url in seen_urls:
            return None

        # Lọc bỏ hàng cũ, hàng trưng bày, đã kích hoạt
        cond = attrs.get("product_condition")
        if cond and cond != "Mới":
            return None
        if self.USED_PRODUCT_RE.search(f"{name} {url_path}"):
            return None

        if seen_urls is not None:
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
            return None

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

        return ScrapedProductItem(
            source=self.source_name,
            url=full_url,
            product_name=name,
            current_price=current_price,
            original_price=original_price,
            is_in_stock=is_in_stock,
            specifications=specs
        )

    def scrape_product(self, url: str) -> Optional[ScrapedProductItem]:
        """Cào thông tin chi tiết một sản phẩm cụ thể qua GraphQL API của CellphoneS (không cào DOM HTML)."""
        url_clean = url.split("?")[0].rstrip("/")
        url_path = url_clean.replace("https://cellphones.com.vn/", "").replace("http://cellphones.com.vn/", "").lstrip("/")

        paths = [url_path]
        if url_path.endswith(".html"):
            paths.append(url_path[:-5])
        else:
            paths.append(f"{url_path}.html")

        paths_json = json.dumps(paths)
        query = f"""
        query getProductByUrl {{
            products(
                filter: {{
                    static: {{
                        url_path: {paths_json}
                        province_id: 30
                    }}
                }}
                page: 1
                size: 1
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
                }}
            }}
        }}
        """

        headers = self._get_api_headers()
        try:
            res = requests.post(self.GRAPHQL_URL, json={"query": query}, headers=headers, timeout=12)
            res.raise_for_status()
            data = res.json()
            products = data.get("data", {}).get("products", [])
            if not products:
                logger.info(f"[CellphoneS] Không tìm thấy sản phẩm qua API cho URL: {url}")
                return None
            return self._parse_product_dict(products[0])
        except Exception as e:
            logger.error(f"[CellphoneS] Lỗi khi gọi GraphQL API cho URL {url}: {e}")
            return None

    def get_category_product_urls(self, category: str, limit: Optional[int] = None) -> List[str]:
        """Lấy danh sách link sản phẩm từ CellphoneS qua GraphQL API."""
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
        """Cào danh mục sản phẩm từ CellphoneS qua GraphQL API."""
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
                item = self._parse_product_dict(p, seen_urls=seen_urls)
                if not item:
                    continue

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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    scraper = CellphonesScraper()
    print("Kiểm thử cào thử nghiệm 3 sản phẩm CellphoneS...")
    sample_items = scraper.scrape_category("phone", limit=3)
    for it in sample_items:
        print(f"- {it.product_name} | Giá: {it.current_price:,}đ | Còn hàng: {it.is_in_stock} | Specs: {it.specifications.get('summary', '')[:60]}...")
