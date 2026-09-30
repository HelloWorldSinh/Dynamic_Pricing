import os
import sys
import re
import time
import logging
from datetime import datetime
from urllib.parse import quote
from typing import Optional, List, Dict, Any, Tuple

# Đảm bảo import được app.* kể cả khi chạy file trực tiếp
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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
        # Tìm cụm số tiền đầu tiên (VD: 46,990,000 hoặc 46.990.000)
        match = re.search(r"(\d[\d\.,]*\d|\d+)", cleaned)
        if match:
            digits = re.sub(r"[^\d]", "", match.group(1))
            val = int(digits) if digits else None
            # Phòng ngừa lỗi dính 2 số phần trăm ở đuôi (ví dụ: 4699000017 -> 46990000)
            if val and val > 500_000_000:
                val_str = str(val)
                if len(val_str) >= 10:
                    val = int(val_str[:-2])
            return val
        return None

    @staticmethod
    def _extract_storage_from_name(name: str) -> Optional[str]:
        """Trích xuất RAM/ROM từ tên sản phẩm.
        Ví dụ: 'iPhone 18 Pro 256GB' -> '256 GB'
               'Samsung Z Fold7 5G 12GB/256GB' -> '12 GB / 256 GB'
        """
        if not name:
            return None
        matches = re.findall(r"\b(\d+\s*(?:GB|TB))\b", name, flags=re.IGNORECASE)
        if matches:
            formatted = [re.sub(r"(\d+)\s*(GB|TB)", r"\1 \2", m, flags=re.IGNORECASE).upper() for m in matches]
            return " / ".join(formatted)
        return None

    def _parse_card_specs(self, specs_list: List[str], product_name: str) -> Tuple[Dict[str, Any], str]:
        """Chuẩn hóa danh sách specs ngắn trên thẻ sản phẩm Hoàng Hà thành dict và chuỗi summary."""
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
            else:
                if "CPU/Chip" not in specs_dict:
                    specs_dict["CPU/Chip"] = s_clean

        # Nếu chưa có Bộ nhớ/RAM thì trích xuất từ tên sản phẩm
        if "Bộ nhớ/RAM" not in specs_dict:
            storage_from_name = self._extract_storage_from_name(product_name)
            if storage_from_name:
                specs_dict["Bộ nhớ/RAM"] = storage_from_name

        summary = " | ".join([f"{k}: {v}" for k, v in specs_dict.items()])
        specs_dict["summary"] = summary
        return specs_dict, summary

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

        strike_tag = old_price_tag.find("strike") if old_price_tag else None
        old_price_raw = strike_tag.get_text(strip=True) if strike_tag else (old_price_tag.get_text(strip=True) if old_price_tag else None)

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

    def scrape_category(self, category: str, limit: Optional[int] = None) -> List[ScrapedProductItem]:
        """Cào danh mục sản phẩm (điện thoại hoặc laptop) từ Hoàng Hà Mobile theo phân trang.
        Nếu limit=None hoặc <= 0, cào toàn bộ các trang.
        """
        if category.lower() == "laptop":
            base_category_url = f"{self.BASE_URL}/laptop"
        else:
            base_category_url = f"{self.BASE_URL}/dien-thoai-di-dong"

        results: List[ScrapedProductItem] = []
        seen_urls = set()
        page = 1
        max_pages = 100  # Duyệt đến khi hết toàn bộ sản phẩm của danh mục


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

                # Khử trùng lặp URL
                if product_url in seen_urls:
                    continue
                seen_urls.add(product_url)

                # Trích xuất giá bán
                price_el = card.select_one(".price-tags .price, .price strong, .price")
                old_price_el = card.select_one(".price.price-last, .price strike")

                strike_el = old_price_el.find("strike") if old_price_el else None
                old_price_raw = strike_el.get_text(strip=True) if strike_el else (old_price_el.get_text(strip=True) if old_price_el else None)

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
                specs_dict, specs_summary = self._parse_card_specs(specs_list, product_name)

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
            if page_items_count == 0:
                logger.info(f"[HoangHa] Không còn sản phẩm mới ở trang {page}. Đã hoàn tất danh mục.")
                break
            time.sleep(0.5)  # Tránh nghẽn server và chống rate-limit
            page += 1


        logger.info(f"[HoangHa] Hoàn thành cào {len(results)} sản phẩm ngành {category}")
        return results

    @staticmethod
    def _extract_search_keyword(sku_name: str) -> str:
        """Trích xuất từ khóa tìm kiếm tối ưu từ tên sản phẩm FPT Shop để search trên Hoàng Hà.
        - Laptop: Lấy mã Part-Number (VD: AL14-52M-52UU, A715-59G, FA506NCG-HN329W)
        - Lenovo: Mã 8x (VD: 83ER00EVVN)
        - Điện thoại: Tên máy + dung lượng GB/TB (VD: iPhone 16e 128GB, Galaxy S24 Ultra 256GB)
        """
        clean = re.sub(r'^(Laptop|Điện thoại|ĐTDĐ)\s+', '', str(sku_name), flags=re.IGNORECASE).strip()
        
        # 1. Tìm Part-Number (dạng ABC-123 hoặc ABC-123-XYZ)
        part_match = re.search(r'\b([A-Za-z0-9]{3,8}-[A-Za-z0-9]{2,8}(?:-[A-Za-z0-9]{2,8})?)\b', clean)
        if part_match:
            return part_match.group(1).strip()
        
        # 2. Lenovo mã 8x (ví dụ 83ER00EVVN)
        lenovo_match = re.search(r'\b(8[0-9][A-Za-z0-9]{6,8})\b', clean)
        if lenovo_match:
            return lenovo_match.group(1).strip()

        # 3. Điện thoại: Lấy tên máy đến dung lượng GB/TB
        storage_match = re.search(r'^(.*?(\d+\s*(?:GB|TB)))', clean, flags=re.IGNORECASE)
        if storage_match:
            return storage_match.group(1).strip()
            
        return ' '.join(clean.split()[:4])

    def search_competitor_product(
        self,
        sku_id: str,
        sku_name: str,
        session: requests.Session,
        matcher: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Gửi request tìm kiếm trực tiếp 1 SKU của FPT lên thanh Search của Hoàng Hà Mobile."""
        keyword = self._extract_search_keyword(sku_name)
        search_url = f"{self.BASE_URL}/tim-kiem?kwd={quote(keyword)}"
        
        res = None
        for attempt in range(3):
            try:
                res = session.get(search_url, timeout=20)
                res.raise_for_status()
                break
            except requests.exceptions.RequestException:
                time.sleep(1.5)
                
        if not res or res.status_code != 200:
            return keyword, None
            
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select(".pj16-item-info")
        
        for c in cards:
            title_el = c.select_one("h3 a, a.text-limit")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                a_tag = c.find("a", title=True)
                if a_tag:
                    title = a_tag.get("title", "").strip()
                    
            if not title:
                continue
                
            href = ""
            link_el = c.find("a", href=True)
            if link_el:
                href = link_el.get("href", "")
                
            # Loại bỏ máy cũ, trầy xước, đổi bảo hành
            if "/kho-san-pham-cu/" in href or "máy cũ" in title.lower() or "tbh" in title.lower():
                continue
                
            price_el = c.select_one(".price strong, strong")
            price_val = None
            if price_el:
                digits = re.sub(r"[^\d]", "", price_el.get_text(strip=True))
                price_val = int(digits) if digits else None
                
            # Kiểm tra xác thực xem kết quả search có đúng là sku_id này không
            match_res = matcher.match_single_item(title, price_val)
            if match_res["fpt_sku_id"] == sku_id and match_res["status"] in ["APPROVED", "PENDING"]:
                full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                return keyword, {
                    "fpt_sku_id": sku_id,
                    "fpt_sku_name": sku_name,
                    "source": self.source_name,
                    "competitor_name": title,
                    "competitor_price": price_val,
                    "url": full_url,
                    "match_type": match_res["match_type"],
                    "confidence_score": match_res["confidence_score"],
                    "status": match_res["status"]
                }
                
        return keyword, None

    def scrape_by_fpt_search(
        self,
        dim_product_path: str = "data/dim_product.xlsx",
        limit: Optional[int] = None,
        delay: float = 0.5
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
        """Quy trình cào THỰC SỰ THEO DANH MỤC FPT (Targeted Search Crawl):
        1. Đọc từng sản phẩm trong dim_product của FPT Shop.
        2. Tạo từ khóa và gửi request tìm kiếm trực tiếp trên Hoàng Hà Mobile.
        3. Bóc tách sản phẩm khớp và lưu lại bảng so sánh Master.
        """
        import pandas as pd
        from app.services.sku_matcher import SkuMatcher

        if not os.path.exists(dim_product_path):
            raise FileNotFoundError(f"Không tìm thấy file danh mục chuẩn: {dim_product_path}")

        df_dim = pd.read_excel(dim_product_path)
        if limit is not None and limit > 0:
            df_dim = df_dim.head(limit)

        matcher = SkuMatcher(dim_product_path=dim_product_path)
        session = requests.Session()
        session.headers.update(self._get_headers())

        logger.info(f"[HoangHa] Bắt đầu cào tìm kiếm trực tiếp theo {len(df_dim)} SKU của FPT...")

        scraped_raw_items = []
        master_rows = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        stats = {
            "total_fpt_skus": len(df_dim),
            "matched_found": 0,
            "approved": 0,
            "pending": 0,
            "not_found": 0
        }

        for idx, (_, row) in enumerate(df_dim.iterrows(), 1):
            sku_id = str(row["sku_id"])
            sku_name = str(row["sku_name"])
            fpt_ref_price = matcher.fpt_prices.get(sku_id)

            keyword, match = self.search_competitor_product(sku_id, sku_name, session, matcher)

            if match:
                c_price = match["competitor_price"]
                diff_vnd = fpt_ref_price - c_price if (fpt_ref_price and c_price) else None
                diff_pct = round((diff_vnd / fpt_ref_price) * 100, 1) if (fpt_ref_price and diff_vnd) else None

                scraped_raw_items.append({
                    "STT": len(scraped_raw_items) + 1,
                    "Nguồn": self.source_name,
                    "Mã SKU FPT": sku_id,
                    "Tên sản phẩm FPT": sku_name,
                    "Tên sản phẩm cào được": match["competitor_name"],
                    "Giá bán đối thủ (VND)": c_price,
                    "Giá niêm yết (VND)": c_price,
                    "Còn hàng": "Còn hàng",
                    "URL sản phẩm": match["url"],
                    "Thời gian cào": now_str
                })

                master_rows.append({
                    "STT": idx,
                    "Mã SKU FPT": sku_id,
                    "Tên sản phẩm chuẩn (FPT Shop)": sku_name,
                    "Nguồn đối thủ": self.source_name,
                    "Tên sản phẩm đối thủ cào về": match["competitor_name"],
                    "Giá đối thủ (VND)": c_price,
                    "Giá tham chiếu FPT (VND)": fpt_ref_price if fpt_ref_price else "Chưa có giá",
                    "Chênh lệch giá (FPT - ĐT)": diff_vnd if diff_vnd is not None else "N/A",
                    "Chênh lệch (%)": f"{diff_pct}%" if diff_pct is not None else "N/A",
                    "Loại khớp (Match Type)": match["match_type"],
                    "Độ tin cậy (Confidence)": match["confidence_score"],
                    "Trạng thái (Status)": match["status"],
                })

                stats["matched_found"] += 1
                if match["status"] == "APPROVED":
                    stats["approved"] += 1
                else:
                    stats["pending"] += 1
                logger.info(f"[{idx}/{len(df_dim)}] {sku_id} -> KHỚP: {match['competitor_name'][:35]} | Giá: {c_price:,} đ" if c_price else f"[{idx}/{len(df_dim)}] {sku_id} -> KHỚP: {match['competitor_name'][:35]}")
            else:
                master_rows.append({
                    "STT": idx,
                    "Mã SKU FPT": sku_id,
                    "Tên sản phẩm chuẩn (FPT Shop)": sku_name,
                    "Nguồn đối thủ": self.source_name,
                    "Tên sản phẩm đối thủ cào về": "N/A (Hoàng Hà không có hàng)",
                    "Giá đối thủ (VND)": "N/A",
                    "Giá tham chiếu FPT (VND)": fpt_ref_price if fpt_ref_price else "Chưa có giá",
                    "Chênh lệch giá (FPT - ĐT)": "N/A",
                    "Chênh lệch (%)": "N/A",
                    "Loại khớp (Match Type)": "NOT_FOUND",
                    "Độ tin cậy (Confidence)": 0.0,
                    "Trạng thái (Status)": "NOT_FOUND",
                })
                stats["not_found"] += 1
                logger.info(f"[{idx}/{len(df_dim)}] {sku_id} -> KHÔNG TÌM THẤY (KWD: '{keyword}')")

            time.sleep(delay)

        return scraped_raw_items, master_rows, stats

    def scrape_by_fpt_dim(
        self,
        dim_product_path: str = "data/dim_product.xlsx",
        limit: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Thu thập sản phẩm từ Hoàng Hà Mobile theo catalog rồi lọc theo FPT."""
        logger.info(f"[HoangHa] Bắt đầu cào dữ liệu catalog và lọc theo danh mục FPT: {dim_product_path}")
        phones = self.scrape_category("phone", limit=limit)
        laptops = self.scrape_category("laptop", limit=limit)

        unique_items: List[ScrapedProductItem] = []
        seen = set()
        for item in (phones + laptops):
            if item.url not in seen:
                seen.add(item.url)
                unique_items.append(item)

        from app.services.sku_matcher import SkuMatcher
        matcher = SkuMatcher(dim_product_path=dim_product_path)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filtered_rows = []
        matched_idx = 1
        stats = {
            "total_crawled": len(unique_items),
            "matched_fpt": 0,
            "approved": 0,
            "pending": 0,
            "excluded_unmatched": 0,
        }

        for item in unique_items:
            match_res = matcher.match_single_item(item.product_name, item.current_price)
            status = match_res["status"]

            if status in ["APPROVED", "PENDING"]:
                specs_summary = item.specifications.get("summary", "N/A") if item.specifications else "N/A"
                filtered_rows.append({
                    "STT": matched_idx,
                    "Mã SKU FPT": match_res["fpt_sku_id"],
                    "Tên chuẩn FPT": match_res["fpt_sku_name"],
                    "Nguồn": item.source,
                    "Tên sản phẩm đối thủ": item.product_name,
                    "Giá bán (VND)": item.current_price,
                    "Giá niêm yết (VND)": item.original_price or item.current_price,
                    "Giá tham chiếu FPT (VND)": match_res["fpt_price"] if match_res["fpt_price"] else "Chưa có giá",
                    "Độ tin cậy": match_res["confidence_score"],
                    "Trạng thái khớp": status,
                    "Còn hàng": "Còn hàng" if item.is_in_stock else "Hết hàng",
                    "Thông số kỹ thuật tóm tắt": specs_summary,
                    "URL sản phẩm": item.url,
                    "Thời gian cào": now_str
                })
                matched_idx += 1
                stats["matched_fpt"] += 1
                if status == "APPROVED":
                    stats["approved"] += 1
                else:
                    stats["pending"] += 1
            else:
                stats["excluded_unmatched"] += 1

        return filtered_rows, stats


if __name__ == "__main__":
    import json
    import pandas as pd

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    scraper = HoanghaScraper()
    print("=" * 80)
    print("=== CHẠY CÀO TÌM KIẾM TRỰC TIẾP THEO TỪNG SKU FPT (TARGETED SEARCH) ===")
    print("=" * 80)

    # Chạy thử nghiệm cào theo danh mục FPT (mặc định thử nghiệm 20 sản phẩm đầu để phản hồi nhanh)
    # Muốn chạy toàn bộ 329 SKU, truyền limit=None
    limit_test = 60;
    scraped_raw, master_rows, stats = scraper.scrape_by_fpt_search(
        dim_product_path="data/dim_product.xlsx",
        limit=limit_test,
        delay=0.6
    )

    os.makedirs("data", exist_ok=True)
    json_path = "data/scraped_products_hoangha.json"
    excel_path = "data/scraped_raw_hoangha.xlsx"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scraped_raw, f, ensure_ascii=False, indent=2)

    pd.DataFrame(scraped_raw).to_excel(excel_path, index=False)

    print("\n" + "=" * 80)
    print("KẾT QUẢ CÀO TRỰC TIẾP THEO TỪNG SKU FPT TRÊN HOÀNG HÀ MOBILE:")
    print("=" * 80)
    print(f" - Tổng SKU FPT đã tìm kiếm               : {stats['total_fpt_skus']}")
    print(f" - Số SKU tìm thấy trên Hoàng Hà           : {stats['matched_found']} (LƯU VÀO DATASET)")
    print(f"     + Khớp chính xác (APPROVED)          : {stats['approved']}")
    print(f"     + Chờ kiểm duyệt (PENDING)           : {stats['pending']}")
    print(f" - Số SKU đối thủ không có hàng (N/A)     : {stats['not_found']}")
    print(f"\n - Đã lưu cache JSON sạch                  : {json_path}")
    print(f" - Đã lưu bảng Excel raw                   : {excel_path}")
    print("=" * 80)


