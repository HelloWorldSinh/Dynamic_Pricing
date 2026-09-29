import sys
import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def discover_product_urls(target_count: int = 70) -> list[str]:
    """Khám phá các link sản phẩm thực tế từ CellphoneS qua các thương hiệu chính."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    brand_pages = [
        # Laptop brands
        "https://cellphones.com.vn/laptop/acer.html",
        "https://cellphones.com.vn/laptop/asus.html",
        "https://cellphones.com.vn/laptop/lenovo.html",
        "https://cellphones.com.vn/laptop/dell.html",
        "https://cellphones.com.vn/laptop/hp.html",
        "https://cellphones.com.vn/laptop/mac.html",
        "https://cellphones.com.vn/laptop.html",
        # Mobile brands
        "https://cellphones.com.vn/mobile/apple.html",
        "https://cellphones.com.vn/mobile/samsung.html",
        "https://cellphones.com.vn/mobile/xiaomi.html",
        "https://cellphones.com.vn/mobile/oppo.html",
        "https://cellphones.com.vn/mobile.html"
    ]
    
    collected_urls = []
    seen = set()
    
    logger.info("Đang quét danh mục sản phẩm từ các hãng lớn trên CellphoneS...")
    for page_url in brand_pages:
        if len(collected_urls) >= target_count:
            break
        try:
            res = requests.get(page_url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href.endswith(".html") or any(x in href for x in ["/sforum", "/tin-tuc", "/chinh-sach", "/danh-muc"]):
                    continue
                
                # Link sản phẩm chi tiết
                is_prod = any(k in href for k in ["/laptop-", "dien-thoai", "iphone", "samsung", "xiaomi", "oppo", "macbook", "asus", "acer", "lenovo", "dell", "hp"])
                is_cat = any(href.endswith(c) for c in ["/laptop.html", "/mobile.html", "/apple.html", "/samsung.html", "/xiaomi.html", "/oppo.html", "/acer.html", "/asus.html", "/lenovo.html", "/dell.html", "/hp.html", "/mac.html"])
                
                if is_prod and not is_cat:
                    full_url = href if href.startswith("http") else f"https://cellphones.com.vn{href if href.startswith('/') else '/' + href}"
                    if full_url not in seen:
                        seen.add(full_url)
                        collected_urls.append(full_url)
                        if len(collected_urls) >= target_count:
                            break
        except Exception as e:
            logger.warning(f"Lỗi khi đọc trang {page_url}: {e}")
            continue

    logger.info(f"Đã khám phá thành công {len(collected_urls)} link sản phẩm độc nhất.")
    return collected_urls


def run_collection(target_count: int = 70, max_workers: int = 6):
    logger.info(f"=== BẮT ĐẦU BƯỚC 1: THU THẬP {target_count} SẢN PHẨM TỪ CELLPHONES ===")
    
    urls = discover_product_urls(target_count=target_count)
    scraper = CellphonesScraper()
    
    scraped_items: list[ScrapedProductItem] = []
    
    logger.info(f"Bắt đầu cào song song với {max_workers} luồng...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scraper.scrape_product, u): u for u in urls}
        completed = 0
        for future in as_completed(future_to_url):
            completed += 1
            url = future_to_url[future]
            try:
                item = future.result()
                if item and item.product_name and item.product_name != "N/A" and item.current_price:
                    scraped_items.append(item)
                    if completed % 15 == 0 or completed == len(urls):
                        logger.info(f"Tiến độ: {completed}/{len(urls)} URLs đã xử lý (Thành công: {len(scraped_items)})")
            except Exception as e:
                logger.warning(f"Lỗi khi cào URL {url}: {e}")
                
    logger.info(f"Tổng kết: Đã cào thành công {len(scraped_items)} sản phẩm hợp lệ.")
    
    # Đóng gói DataFrame
    rows = []
    for idx, item in enumerate(scraped_items, 1):
        specs_summary = "; ".join([f"{k}: {v}" for k, v in list(item.specifications.items())[:6]])
        rows.append({
            "STT": idx,
            "Nguồn": item.source,
            "Tên sản phẩm": item.product_name,
            "Giá bán (VND)": item.current_price,
            "Giá niêm yết (VND)": item.original_price if item.original_price else item.current_price,
            "Còn hàng": "Còn hàng" if item.is_in_stock else "Hết hàng",
            "Thông số kỹ thuật tóm tắt": specs_summary if specs_summary else "N/A",
            "URL sản phẩm": item.url,
            "Thời gian cào": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    df = pd.DataFrame(rows)
    
    # Lưu bản JSON dự phòng để không bao giờ mất dữ liệu
    json_path = os.path.join("data", "scraped_products.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    logger.info(f"Đã lưu bản cache JSON vào: {json_path}")
    
    # Lưu file Excel với cơ chế fallback nếu file đang mở
    output_path = os.path.join("data", "scraped_raw_step1.xlsx")
    try:
        df.to_excel(output_path, index=False)
        logger.info(f"Đã lưu {len(df)} sản phẩm vào: {output_path}")
    except PermissionError:
        output_path = os.path.join("data", f"scraped_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(output_path, index=False)
        logger.info(f"File cũ đang mở trong ứng dụng khác, đã lưu sang: {output_path}")
    
    return df


if __name__ == "__main__":
    df = run_collection(target_count=70, max_workers=6)
    print("\n" + "="*80)
    print(f"KẾT QUẢ BƯỚC 1: ĐÃ THU THẬP {len(df)} SẢN PHẨM:")
    print("="*80)
    print(df[["STT", "Nguồn", "Tên sản phẩm", "Giá bán (VND)", "Còn hàng"]].head(15).to_string(index=False))
    print(f"... và {len(df) - 15} sản phẩm tiếp theo.")
