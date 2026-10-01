import sys
import os
import json
import logging
from datetime import datetime
from typing import Optional
import pandas as pd


# Đảm bảo UTF-8 cho console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath("."))

from app.services.scrapers.factory import ScraperFactory  # noqa: E402
from app.services.sku_matcher import SkuMatcher  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main(limit: Optional[int] = None, filter_by_dim: bool = True):
    mode_desc = "CHỈ LẤY SẢN PHẨM THUỘC DIM_PRODUCT FPT" if filter_by_dim else "TOÀN BỘ SẢN PHẨM TRÊN KỆ"
    limit_desc = "KHÔNG GIỚI HẠN (tất cả các trang từ đầu đến cuối)" if (limit is None or limit <= 0) else f"tối đa {limit} SP/ngành"
    logger.info("=== BẮT ĐẦU QUY TRÌNH THU THẬP & SO KHỚP HOÀNG HÀ MOBILE ===")
    logger.info(f" - Chế độ cào: {mode_desc}")
    logger.info(f" - Phạm vi: {limit_desc}")

    # 1. Khởi tạo scraper qua Factory
    hoangha_scraper = ScraperFactory.get_scraper("hoangha")

    # 2. Thu thập sản phẩm: Điện thoại & Laptop
    logger.info("Đang thu thập sản phẩm từ Hoàng Hà Mobile...")
    phones = hoangha_scraper.scrape_category("phone", limit=limit)
    laptops = hoangha_scraper.scrape_category("laptop", limit=limit)

    # Khử trùng lặp sản phẩm giữa các danh mục
    unique_items = []
    seen_all_urls = set()
    for item in (phones + laptops):
        if item.url not in seen_all_urls:
            seen_all_urls.add(item.url)
            unique_items.append(item)

    all_scraped = unique_items
    logger.info(f"Tổng số sản phẩm cào được trên kệ Hoàng Hà: {len(all_scraped)} (Điện thoại: {len(phones)}, Laptop: {len(laptops)})")

    # 3. Khởi tạo SKU Matcher để đối soát với danh mục chuẩn FPT
    matcher = SkuMatcher(
        dim_product_path="data/dim_product.xlsx",
        demand_events_path="data/demand_events_20260723.xlsx"
    )

    # 4. Chuyển đổi và lọc dữ liệu (theo mindset chỉ lấy SP trong dim_product FPT)
    scraped_dict_items = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    excluded_count = 0

    for idx, item in enumerate(all_scraped, 1):
        match_res = matcher.match_single_item(item.product_name, item.current_price)
        status = match_res["status"]

        # Nếu kích hoạt filter_by_dim, bỏ qua những sản phẩm UNMATCHED (ngoài danh mục FPT)
        if filter_by_dim and status not in ["APPROVED", "PENDING"]:
            excluded_count += 1
            continue

        specs_summary = item.specifications.get("summary", "N/A") if item.specifications else "N/A"
        scraped_dict_items.append({
            "STT": len(scraped_dict_items) + 1,
            "Nguồn": item.source,
            "Tên sản phẩm": item.product_name,
            "Giá bán (VND)": item.current_price,
            "Giá niêm yết (VND)": item.original_price or item.current_price,
            "Còn hàng": "Còn hàng" if item.is_in_stock else "Hết hàng",
            "Thông số kỹ thuật tóm tắt": specs_summary,
            "URL sản phẩm": item.url,
            "Thời gian cào": now_str
        })

    logger.info(f"Sau khi lọc: Giữ lại {len(scraped_dict_items)} SP thuộc FPT (Đã loại bỏ {excluded_count} SP ngoài luồng).")

    # 5. Lưu cache JSON sạch
    os.makedirs("data", exist_ok=True)
    json_path = "data/scraped_products_hoangha.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scraped_dict_items, f, ensure_ascii=False, indent=2)
    logger.info(f"Đã lưu cache dữ liệu cào tại: {json_path}")

    # 6. Lưu file raw Excel chuẩn
    raw_excel_path = "data/scraped_raw_hoangha.xlsx"
    try:
        pd.DataFrame(scraped_dict_items).to_excel(raw_excel_path, index=False)
        logger.info(f"Đã lưu bảng raw vào: {raw_excel_path}")
    except Exception as e:
        logger.warning(f"Không thể lưu file {raw_excel_path}: {e}")

    # 7. Xuất file kết quả 2 sheet hoàn chỉnh (Scraped_All_Data & SKU_Mapping 329 Master SKU FPT)
    output_path = "data/crawl_and_sku_mapping_hoangha.xlsx"
    final_file = matcher.process_and_export_excel(
        scraped_dict_items,
        output_excel_path=output_path,
        master_by_fpt=True
    )
    logger.info(f"Xuất file Excel thành công tại: {final_file}")

    # 8. Đọc thống kê kết quả từ bảng Master 329 SKU FPT
    df_map = pd.read_excel(final_file, sheet_name="SKU_Mapping")
    total_fpt = len(df_map)
    approved = len(df_map[df_map["Trạng thái (Status)"] == "APPROVED"])
    pending = len(df_map[df_map["Trạng thái (Status)"] == "PENDING"])
    not_found = len(df_map[df_map["Trạng thái (Status)"] == "NOT_FOUND"])
    matched_fpt = approved + pending

    print("\n" + "=" * 80)
    print("BÁO CÁO KẾT QUẢ ĐỐI SOÁT GIÁ HOÀNG HÀ THEO MASTER 329 SKU FPT SHOP:")
    print("=" * 80)
    print(f" - Tổng SKU chuẩn của FPT Shop          : {total_fpt} SKU (100% Master Table)")
    print(f" - Số SKU đối thủ Hoàng Hà CÓ HÀNG      : {matched_fpt} SKU ({matched_fpt/total_fpt*100:.1f}%)")
    print(f"     + Khớp chính xác (APPROVED)        : {approved} SKU ({approved/total_fpt*100:.1f}%)")
    print(f"     + Chờ kiểm duyệt (PENDING)         : {pending} SKU ({pending/total_fpt*100:.1f}%)")
    print(f" - Số SKU đối thủ Hoàng Hà KHÔNG CÓ HÀNG: {not_found} SKU ({not_found/total_fpt*100:.1f}%) -> Điền 'N/A'")
    print(f"\nSheet 1 (Scraped_All_Data): Lưu toàn bộ {len(scraped_dict_items)} sản phẩm thực tế cào từ Hoàng Hà.")
    print("Sheet 2 (SKU_Mapping)    : Bảng chuẩn 329 SKU FPT đối soát sang giá Hoàng Hà.")
    print(f"\nFile Excel hoàn chỉnh: {final_file}")
    print(f"File Raw Excel sạch  : {raw_excel_path}")
    print("=" * 80)


if __name__ == "__main__":
    # Hỗ trợ truyền limit từ command line: python run_hoangha_pipeline.py [limit]
    # Mặc định cào và lọc theo dim_product của FPT Shop (limit=None cào toàn bộ)
    cli_limit = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        cli_limit = int(sys.argv[1])
    main(limit=cli_limit, filter_by_dim=True)
