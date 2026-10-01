import sys
import os
import json
import logging
import argparse
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

# Đảm bảo UTF-8 cho console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm project root vào sys.path
sys.path.insert(0, os.path.abspath("."))

from app.services.scrapers.factory import ScraperFactory
from app.services.sku_matcher import SkuMatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def convert_scraped_items_to_dict(items: list, source_name: str) -> List[Dict[str, Any]]:
    """Chuyển đổi danh sách ScrapedProductItem sang danh sách dictionary chuẩn."""
    dict_items = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in items:
        specs_summary = item.specifications.get("summary", "N/A") if item.specifications else "N/A"
        dict_items.append({
            "Nguồn": item.source or source_name,
            "Tên sản phẩm cào được": item.product_name,
            "Giá bán đối thủ (VND)": item.current_price,
            "Giá niêm yết (VND)": item.original_price or item.current_price,
            "Còn hàng": "Còn hàng" if item.is_in_stock else "Hết hàng",
            "Thông số kỹ thuật tóm tắt": specs_summary,
            "URL sản phẩm": item.url,
            "Thời gian cào": now_str
        })
    return dict_items


def scrape_cellphones(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Cào toàn bộ sản phẩm Điện thoại & Laptop từ CellphoneS qua GraphQL API."""
    logger.info("=== BẮT ĐẦU CÀO DỮ LIỆU TỪ CELLPHONES ===")
    scraper = ScraperFactory.get_scraper("cellphones")

    phones = scraper.scrape_category("phone", limit=limit)
    laptops = scraper.scrape_category("laptop", limit=limit)
    all_items = phones + laptops

    logger.info(f"[CellphoneS] Tổng số sản phẩm thu thập: {len(all_items)} (Phone: {len(phones)}, Laptop: {len(laptops)})")
    dict_items = convert_scraped_items_to_dict(all_items, "CellphoneS")

    # Lưu cache JSON
    os.makedirs("data", exist_ok=True)
    cache_path = "data/scraped_products_cellphones.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(dict_items, f, ensure_ascii=False, indent=2)
    logger.info(f"[CellphoneS] Đã lưu cache tại: {cache_path}")
    return dict_items


def scrape_hoangha(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Cào sản phẩm Điện thoại & Laptop từ Hoàng Hà Mobile qua HTML Parsing."""
    logger.info("=== BẮT ĐẦU CÀO DỮ LIỆU TỪ HOÀNG HÀ MOBILE ===")
    scraper = ScraperFactory.get_scraper("hoangha")

    phones = scraper.scrape_category("phone", limit=limit)
    laptops = scraper.scrape_category("laptop", limit=limit)

    # Khử trùng lặp URL
    unique_items = []
    seen_urls = set()
    for it in (phones + laptops):
        if it.url not in seen_urls:
            seen_urls.add(it.url)
            unique_items.append(it)

    logger.info(f"[Hoàng Hà] Tổng số sản phẩm thu thập: {len(unique_items)} (Phone: {len(phones)}, Laptop: {len(laptops)})")
    dict_items = convert_scraped_items_to_dict(unique_items, "HOANGHA")

    # Lưu cache JSON
    os.makedirs("data", exist_ok=True)
    cache_path = "data/scraped_products_hoangha.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(dict_items, f, ensure_ascii=False, indent=2)
    logger.info(f"[Hoàng Hà] Đã lưu cache tại: {cache_path}")
    return dict_items


def print_summary_report(excel_path: str):
    """Đọc file Excel kết quả và in bảng báo cáo tổng kết chi tiết."""
    try:
        df_comp = pd.read_excel(excel_path, sheet_name="FPT_Shop_Comparison")
        df_cps = pd.read_excel(excel_path, sheet_name="CellphoneS_Data")
        df_hh = pd.read_excel(excel_path, sheet_name="HoangHa_Data")
    except Exception as e:
        logger.warning(f"Không thể đọc kết quả để in thống kê: {e}")
        return

    total_fpt = len(df_comp)
    cps_approved = len(df_comp[df_comp["Trạng thái CPS"] == "APPROVED"])
    cps_pending = len(df_comp[df_comp["Trạng thái CPS"] == "PENDING"])
    cps_matched = cps_approved + cps_pending

    hh_approved = len(df_comp[df_comp["Trạng thái HH"] == "APPROVED"])
    hh_pending = len(df_comp[df_comp["Trạng thái HH"] == "PENDING"])
    hh_matched = hh_approved + hh_pending

    both_matched = len(df_comp[
        (df_comp["Trạng thái CPS"].isin(["APPROVED", "PENDING"])) &
        (df_comp["Trạng thái HH"].isin(["APPROVED", "PENDING"]))
    ])
    at_least_one = len(df_comp[
        (df_comp["Trạng thái CPS"].isin(["APPROVED", "PENDING"])) |
        (df_comp["Trạng thái HH"].isin(["APPROVED", "PENDING"]))
    ])

    print("\n" + "=" * 90)
    print("           BÁO CÁO TỔNG KẾT ĐỐI SOÁT GIÁ ĐA NGUỒN")
    print("=" * 90)
    print(f" 1. DỮ LIỆU CÀO THỰC TẾ:")
    print(f"    - CellphoneS (Sheet 2) : {len(df_cps):,} sản phẩm")
    print(f"    - Hoàng Hà   (Sheet 3) : {len(df_hh):,} sản phẩm")
    print(f"\n 2. KẾT QUẢ ĐỐI SOÁT MASTER 329 SKU FPT SHOP (Sheet 1):")
    print(f"    - Tổng danh mục FPT Shop          : {total_fpt} SKUs (100%)")
    print(f"    - Khớp với CellphoneS              : {cps_matched}/{total_fpt} SKUs ({cps_matched/total_fpt*100:.1f}%) [APPROVED: {cps_approved}, PENDING: {cps_pending}]")
    print(f"    - Khớp với Hoàng Hà                : {hh_matched}/{total_fpt} SKUs ({hh_matched/total_fpt*100:.1f}%) [APPROVED: {hh_approved}, PENDING: {hh_pending}]")
    print(f"    - Khớp CẢ HAI đối thủ song song    : {both_matched}/{total_fpt} SKUs ({both_matched/total_fpt*100:.1f}%)")
    print(f"    - Khớp ÍT NHẤT 1 đối thủ           : {at_least_one}/{total_fpt} SKUs ({at_least_one/total_fpt*100:.1f}%)")
    print(f"\n 3. FILE XUẤT HOÀN CHỈNH (3 SHEETS):")
    print(f"    -> Đường dẫn: {excel_path}")
    print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="CLI tự động cào dữ liệu từ CellphoneS và Hoàng Hà Mobile, so khớp với 329 SKU FPT và xuất file Excel 3 Sheets."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn số sản phẩm mỗi ngành để test nhanh (mặc định: None = cào toàn bộ các trang)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/crawl_and_sku_mapping_output.xlsx",
        help="Đường dẫn file Excel xuất ra (mặc định: data/crawl_and_sku_mapping_output.xlsx)"
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Bỏ qua bước cào mạng, tái sử dụng dữ liệu JSON trong thư mục data/"
    )
    parser.add_argument(
        "--dim-product",
        type=str,
        default="data/dim_product.xlsx",
        help="Đường dẫn file danh mục SKU chuẩn của FPT Shop"
    )
    parser.add_argument(
        "--demand-events",
        type=str,
        default="data/demand_events_20260723.xlsx",
        help="Đường dẫn file giá tham chiếu của FPT Shop"
    )

    args = parser.parse_args()

    limit_desc = "TOÀN BỘ (tất cả các trang)" if not args.limit else f"Tối đa {args.limit} SP/ngành"
    logger.info(f"=== BẮT ĐẦU PIPELINE CÀO & ĐỐI SOÁT ĐA NGUỒN ===")
    logger.info(f" - Phạm vi cào: {limit_desc}")
    logger.info(f" - File xuất Excel: {args.output}")

    # 1. Thu thập dữ liệu từ CellphoneS và Hoàng Hà Mobile
    cellphones_items = []
    hoangha_items = []

    if args.skip_scrape:
        logger.info("[MODE: SKIP-SCRAPE] Tải dữ liệu từ cache JSON...")
        cps_cache = "data/scraped_products_cellphones.json"
        hh_cache = "data/scraped_products_hoangha.json"

        if os.path.exists(cps_cache):
            with open(cps_cache, "r", encoding="utf-8") as f:
                cellphones_items = json.load(f)
            logger.info(f"Đã nạp {len(cellphones_items)} SP CellphoneS từ {cps_cache}")
        else:
            logger.warning(f"Không tìm thấy cache {cps_cache}. Tiến hành cào mới...")
            cellphones_items = scrape_cellphones(limit=args.limit)

        if os.path.exists(hh_cache):
            with open(hh_cache, "r", encoding="utf-8") as f:
                hoangha_items = json.load(f)
            logger.info(f"Đã nạp {len(hoangha_items)} SP Hoàng Hà từ {hh_cache}")
        else:
            logger.warning(f"Không tìm thấy cache {hh_cache}. Tiến hành cào mới...")
            hoangha_items = scrape_hoangha(limit=args.limit)
    else:
        # Cào mạng thực tế
        cellphones_items = scrape_cellphones(limit=args.limit)
        hoangha_items = scrape_hoangha(limit=args.limit)

    # 2. Khởi tạo SKU Matcher Engine
    logger.info("Đang khởi tạo thuật toán so khớp SKU Matcher Engine...")
    matcher = SkuMatcher(
        dim_product_path=args.dim_product,
        demand_events_path=args.demand_events
    )

    # 3. Tiến hành đối soát đa nguồn và xuất Excel 3 Sheet
    final_excel_path = matcher.match_multi_sources(
        cellphones_items=cellphones_items,
        hoangha_items=hoangha_items,
        output_excel_path=args.output
    )

    # 4. In báo cáo tổng kết chi tiết
    print_summary_report(final_excel_path)


if __name__ == "__main__":
    main()
