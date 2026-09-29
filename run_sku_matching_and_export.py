import sys
import os
import json
import logging
import pandas as pd

# Đảm bảo UTF-8 cho console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn project vào sys.path
sys.path.insert(0, os.path.abspath("."))

from app.services.sku_matcher import SkuMatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    json_path = os.path.join("data", "scraped_products.json")
    if not os.path.exists(json_path):
        logger.error(f"Không tìm thấy file dữ liệu cào: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        scraped_items = json.load(f)

    logger.info(f"Đã đọc {len(scraped_items)} sản phẩm từ {json_path}")
    
    matcher = SkuMatcher(
        dim_product_path="data/dim_product.xlsx",
        demand_events_path="data/demand_events_20260723.xlsx"
    )
    
    output_path = os.path.join("data", "crawl_and_sku_mapping_output.xlsx")
    matcher.process_and_export_excel(scraped_items, output_excel_path=output_path)
    
    # Đọc lại và in thống kê
    df_map = pd.read_excel(output_path, sheet_name="SKU_Mapping")
    total = len(df_map)
    approved = len(df_map[df_map["Trạng thái (Status)"] == "APPROVED"])
    pending = len(df_map[df_map["Trạng thái (Status)"] == "PENDING"])
    unmatched = len(df_map[df_map["Trạng thái (Status)"] == "UNMATCHED"])
    
    print("\n" + "="*80)
    print("BÁO CÁO KẾT QUẢ SO KHỚP SKU (BƯỚC 2 & BƯỚC 3):")
    print("="*80)
    print(f"Tổng số sản phẩm cào về: {total}")
    print(f" - Khớp tự động (APPROVED): {approved} ({approved/total*100:.1f}%)")
    print(f" - Cần duyệt lại (PENDING):  {pending} ({pending/total*100:.1f}%)")
    print(f" - Không khớp (UNMATCHED):   {unmatched} ({unmatched/total*100:.1f}%)")
    print(f"\nFile Excel hoàn chỉnh đã được tạo tại: {output_path}")
    print("\nTop 10 dòng mẫu từ Sheet 'SKU_Mapping':")
    cols_to_print = ["STT", "Mã SKU FPT", "Tên sản phẩm chuẩn (FPT Shop)", "Giá đối thủ (VND)", "Độ tin cậy (Confidence)", "Trạng thái (Status)"]
    print(df_map[cols_to_print].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
