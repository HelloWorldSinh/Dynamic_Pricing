import sys
import os
import json
import logging
from datetime import datetime
import pandas as pd

# Đảm bảo UTF-8 cho console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

# Thêm backend root vào sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
DATA_DIR = BACKEND_DIR / "data"

from app.services.scrapers.factory import ScraperFactory  # noqa: E402
from app.services.sku_matcher import SkuMatcher  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main(limit: int = None):
    """Quy trình tự động thu thập toàn bộ dữ liệu CellphoneS (không giới hạn, từ trang đầu đến cuối)
    và so khớp SKU với danh mục sản phẩm FPT Shop.
    """
    limit_desc = "KHÔNG GIỚI HẠN (tất cả các trang)" if (limit is None or limit <= 0) else f"tối đa {limit} SP/ngành"
    logger.info(f"=== BẮT ĐẦU QUY TRÌNH THU THẬP & SO KHỚP CELLPHONES ({limit_desc}) ===")

    # 1. Khởi tạo scraper qua Factory
    cellphones_scraper = ScraperFactory.get_scraper("cellphones")

    # 2. Thu thập sản phẩm: Điện thoại & Laptop từ trang 1 đến trang cuối
    logger.info("Đang thu thập toàn bộ danh mục Điện thoại từ CellphoneS...")
    phones = cellphones_scraper.scrape_category("phone", limit=limit)

    logger.info("Đang thu thập toàn bộ danh mục Laptop từ CellphoneS...")
    laptops = cellphones_scraper.scrape_category("laptop", limit=limit)

    all_scraped = phones + laptops
    logger.info(f"Tổng số sản phẩm cào được từ CellphoneS: {len(all_scraped)} (Điện thoại: {len(phones)}, Laptop: {len(laptops)})")

    # 3. Chuyển đổi dữ liệu sang định dạng chuẩn dictionary
    scraped_dict_items = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in all_scraped:
        specs_summary = item.specifications.get("summary", "N/A") if item.specifications else "N/A"
        scraped_dict_items.append({
            "Nguồn": item.source,
            "Tên sản phẩm": item.product_name,
            "Giá bán (VND)": item.current_price,
            "Giá niêm yết (VND)": item.original_price or item.current_price,
            "Còn hàng": "Còn hàng" if item.is_in_stock else "Hết hàng",
            "Thông số kỹ thuật tóm tắt": specs_summary,
            "URL sản phẩm": item.url,
            "Thời gian cào": now_str
        })

    # Lưu cache JSON
    os.makedirs(DATA_DIR, exist_ok=True)
    json_path = DATA_DIR / "scraped_products_cellphones.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scraped_dict_items, f, ensure_ascii=False, indent=2)
    logger.info(f"Đã lưu cache dữ liệu cào tại: {json_path}")

    # Đồng bộ lưu vào file cache chung nếu cần cho các script khác
    common_json_path = DATA_DIR / "scraped_products.json"
    with open(common_json_path, "w", encoding="utf-8") as f:
        json.dump(scraped_dict_items, f, ensure_ascii=False, indent=2)

    # 4. Khởi chạy SKU Matcher Engine
    logger.info("Đang khởi động thuật toán so khớp SKU Matcher...")
    matcher = SkuMatcher(
        dim_product_path=str(DATA_DIR / "dim_product.xlsx"),
        demand_events_path=str(DATA_DIR / "demand_events_20260723.xlsx")
    )

    output_path = str(DATA_DIR / "crawl_and_sku_mapping_cellphones.xlsx")
    final_file = matcher.process_and_export_excel(scraped_dict_items, output_excel_path=output_path)
    logger.info(f"Xuất file Excel thành công tại: {final_file}")

    # 5. Đọc thống kê kết quả
    df_map = pd.read_excel(final_file, sheet_name="SKU_Mapping")
    total = len(df_map)
    approved = len(df_map[df_map["Trạng thái (Status)"] == "APPROVED"])
    pending = len(df_map[df_map["Trạng thái (Status)"] == "PENDING"])
    unmatched = len(df_map[df_map["Trạng thái (Status)"] == "UNMATCHED"])

    print("\n" + "=" * 80)
    print("BÁO CÁO KẾT QUẢ CÀO & SO KHỚP CELLPHONES (FULL PAGES):")
    print("=" * 80)
    print(f"Tổng số sản phẩm cào từ CellphoneS: {total}")
    if total > 0:
        print(f" - Khớp tự động (APPROVED): {approved} ({approved/total*100:.1f}%)")
        print(f" - Chờ kiểm duyệt (PENDING): {pending} ({pending/total*100:.1f}%)")
        print(f" - Không tìm thấy (UNMATCHED): {unmatched} ({unmatched/total*100:.1f}%)")
    print(f"\nFile Excel hoàn chỉnh: {final_file}")
    print("=" * 80)


if __name__ == "__main__":
    # Cào không giới hạn từ trang đầu đến trang cuối
    main(limit=None)
