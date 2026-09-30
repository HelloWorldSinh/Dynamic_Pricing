import sys
import os
import json
import logging
from typing import Optional
from datetime import datetime
import pandas as pd

# Đảm bảo UTF-8 cho console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn project vào sys.path
sys.path.insert(0, os.path.abspath("."))

from app.services.scrapers.cellphones import CellphonesScraper
from app.schemas.crawl import ScrapedProductItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_collection(limit: Optional[int] = None):
    """Thu thập toàn bộ dữ liệu sản phẩm từ CellphoneS từ trang đầu đến trang cuối.
    Nếu limit=None hoặc <= 0: cào không giới hạn (tất cả các trang).
    Nếu limit có giá trị: lấy tối đa limit sản phẩm mỗi ngành.
    """
    limit_desc = "KHÔNG GIỚI HẠN (cào từ trang đầu đến cuối)" if (limit is None or limit <= 0) else f"tối đa {limit} SP/ngành"
    logger.info(f"=== BẮT ĐẦU THU THẬP DỮ LIỆU TỪ CELLPHONES ({limit_desc}) ===")

    scraper = CellphonesScraper()

    # 1. Thu thập danh mục Điện thoại
    logger.info("Đang cào toàn bộ danh mục Điện thoại (Mobile)...")
    phones = scraper.scrape_category("phone", limit=limit)

    # 2. Thu thập danh mục Laptop
    logger.info("Đang cào toàn bộ danh mục Laptop...")
    laptops = scraper.scrape_category("laptop", limit=limit)

    # Khử trùng lặp sản phẩm giữa các danh mục
    unique_items = []
    seen_all_urls = set()
    for item in (phones + laptops):
        if item.url not in seen_all_urls:
            seen_all_urls.add(item.url)
            unique_items.append(item)
    scraped_items = unique_items
    logger.info(f"Tổng kết: Đã thu thập {len(scraped_items)} sản phẩm duy nhất từ CellphoneS (Điện thoại: {len(phones)}, Laptop: {len(laptops)}).")

    # 3. Đóng gói DataFrame
    rows = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for idx, item in enumerate(scraped_items, 1):
        specs_summary = item.specifications.get("summary") if item.specifications else "N/A"
        if not specs_summary and item.specifications:
            specs_summary = " | ".join([f"{k}: {v}" for k, v in list(item.specifications.items())[:6]])


        rows.append({
            "STT": idx,
            "Nguồn": item.source,
            "Tên sản phẩm": item.product_name,
            "Giá bán (VND)": item.current_price,
            "Giá niêm yết (VND)": item.original_price if item.original_price else item.current_price,
            "Còn hàng": "Còn hàng" if item.is_in_stock else "Hết hàng",
            "Thông số kỹ thuật tóm tắt": specs_summary or "N/A",
            "URL sản phẩm": item.url,
            "Thời gian cào": now_str
        })

    df = pd.DataFrame(rows)

    # Lưu bản JSON
    os.makedirs("data", exist_ok=True)
    json_path = os.path.join("data", "scraped_products.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    logger.info(f"Đã lưu bản cache JSON vào: {json_path}")

    # Lưu file Excel với cơ chế fallback nếu file đang mở
    output_path = os.path.join("data", "scraped_raw_step1.xlsx")
    try:
        df.to_excel(output_path, index=False)
        logger.info(f"Đã lưu {len(df)} sản phẩm vào file Excel: {output_path}")
    except PermissionError:
        output_path = os.path.join("data", f"scraped_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(output_path, index=False)
        logger.info(f"File cũ đang mở trong ứng dụng khác, đã lưu sang: {output_path}")

    return df


if __name__ == "__main__":
    # Cào không giới hạn từ page đầu đến cuối (limit=None)
    df = run_collection(limit=None)
    print("\n" + "=" * 80)
    print(f"KẾT QUẢ THU THẬP CELLPHONES: TỔNG CỘNG {len(df)} SẢN PHẨM")
    print("=" * 80)
    if len(df) > 0:
        print(df[["STT", "Nguồn", "Tên sản phẩm", "Giá bán (VND)", "Còn hàng"]].head(15).to_string(index=False))
        if len(df) > 15:
            print(f"... và {len(df) - 15} sản phẩm tiếp theo.")
