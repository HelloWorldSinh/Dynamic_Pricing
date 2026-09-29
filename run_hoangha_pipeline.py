import sys
import os
import json
import logging
from datetime import datetime
import pandas as pd

# Đảm bảo UTF-8 cho console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath("."))

from app.services.scrapers.factory import ScraperFactory
from app.services.sku_matcher import SkuMatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("=== BẮT ĐẦU QUY TRÌNH THU THẬP & SO KHỚP DỮ LIỆU HOÀNG HÀ MOBILE ===")

    # 1. Khởi tạo scraper qua Factory
    hoangha_scraper = ScraperFactory.get_scraper("hoangha")

    # 2. Thu thập sản phẩm: Điện thoại & Laptop (mục tiêu ~70 - 80 sản phẩm)
    logger.info("Đang thu thập sản phẩm từ Hoàng Hà Mobile...")
    phones = hoangha_scraper.scrape_category("phone", limit=38)
    laptops = hoangha_scraper.scrape_category("laptop", limit=38)

    all_scraped = phones + laptops
    logger.info(f"Tổng số sản phẩm cào được từ Hoàng Hà: {len(all_scraped)} (Điện thoại: {len(phones)}, Laptop: {len(laptops)})")

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
    json_path = "data/scraped_products_hoangha.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scraped_dict_items, f, ensure_ascii=False, indent=2)
    logger.info(f"Đã lưu cache dữ liệu cào tại: {json_path}")

    # 4. Khởi chạy SKU Matcher Engine
    matcher = SkuMatcher(
        dim_product_path="data/dim_product.xlsx",
        demand_events_path="data/demand_events_20260723.xlsx"
    )

    output_path = "data/crawl_and_sku_mapping_hoangha.xlsx"
    final_file = matcher.process_and_export_excel(scraped_dict_items, output_excel_path=output_path)
    logger.info(f"Xuất file Excel thành công tại: {final_file}")

    # 5. Đọc thống kê kết quả
    df_map = pd.read_excel(final_file, sheet_name="SKU_Mapping")
    total = len(df_map)
    approved = len(df_map[df_map["Trạng thái (Status)"] == "APPROVED"])
    pending = len(df_map[df_map["Trạng thái (Status)"] == "PENDING"])
    unmatched = len(df_map[df_map["Trạng thái (Status)"] == "UNMATCHED"])

    print("\n" + "=" * 80)
    print("BÁO CÁO KẾT QUẢ CÀO & SO KHỚP HOÀNG HÀ MOBILE:")
    print("=" * 80)
    print(f"Tổng số sản phẩm cào từ Hoàng Hà: {total}")
    print(f" - Khớp tự động (APPROVED): {approved} ({approved/total*100:.1f}%)")
    print(f" - Chờ kiểm duyệt (PENDING): {pending} ({pending/total*100:.1f}%)")
    print(f" - Không tìm thấy (UNMATCHED): {unmatched} ({unmatched/total*100:.1f}%)")
    print(f"\nFile Excel hoàn chỉnh: {final_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
