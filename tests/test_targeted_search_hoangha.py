import os
import sys
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.services.sku_matcher import SkuMatcher

matcher = SkuMatcher(
    dim_product_path=os.path.join(BASE_DIR, "data", "dim_product.xlsx"),
    demand_events_path=os.path.join(BASE_DIR, "data", "demand_events_20260723.xlsx")
)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
})

def extract_search_keyword(sku_name: str) -> str:
    """Trích xuất từ khóa tối ưu để gửi vào thanh tìm kiếm của Hoàng Hà."""
    clean = re.sub(r'^(Laptop|Điện thoại|ĐTDĐ)\s+', '', sku_name, flags=re.IGNORECASE).strip()
    
    # 1. Tìm Part-Number (đối với laptop: AL14-52M-52UU, A715-59G, FA506NCG-HN329W...)
    part_match = re.search(r'\b([A-Za-z0-9]{3,8}-[A-Za-z0-9]{2,8}(?:-[A-Za-z0-9]{2,8})?)\b', clean)
    if part_match:
        return part_match.group(1).strip()
    
    # 2. Lenovo mã 8x (ví dụ 83ER00EVVN)
    lenovo_match = re.search(r'\b(8[0-9][A-Za-z0-9]{6,8})\b', clean)
    if lenovo_match:
        return lenovo_match.group(1).strip()

    # 3. Điện thoại: Lấy tên máy đến dung lượng GB/TB (iPhone 16e 128GB, Galaxy S24 Ultra 256GB)
    storage_match = re.search(r'^(.*?(\d+\s*(?:GB|TB)))', clean, flags=re.IGNORECASE)
    if storage_match:
        return storage_match.group(1).strip()
        
    return ' '.join(clean.split()[:4])

def search_and_match(sku_id: str, sku_name: str):
    kwd = extract_search_keyword(sku_name)
    url = f"https://hoanghamobile.com/tim-kiem?kwd={quote(kwd)}"
    
    res_req = None
    for attempt in range(3):
        try:
            res_req = session.get(url, timeout=20)
            res_req.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            time.sleep(2.0)
            
    if not res_req or res_req.status_code != 200:
        return kwd, None
        
    soup = BeautifulSoup(res_req.text, 'html.parser')
    cards = soup.select('.pj16-item-info')
    
    best_match = None
    for c in cards:
        # Bóc tách tên sản phẩm
        title_el = c.select_one('h3 a, a.text-limit')
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            a_tag = c.find('a', title=True)
            if a_tag:
                title = a_tag.get('title', '').strip()
                
        if not title:
            continue
            
        href = ""
        link_el = c.find('a', href=True)
        if link_el:
            href = link_el.get('href', '')
            
        # Bỏ qua hàng cũ / máy đổi trả
        if '/kho-san-pham-cu/' in href or 'máy cũ' in title.lower() or 'tbh' in title.lower():
            continue
            
        price_el = c.select_one('.price strong, strong')
        price_val = None
        if price_el:
            digits = re.sub(r'[^\d]', '', price_el.get_text(strip=True))
            price_val = int(digits) if digits else None
            
        # Xác thực xem card này có khớp với sku_id này không
        match_res = matcher.match_single_item(title, price_val)
        if match_res['fpt_sku_id'] == sku_id and match_res['status'] in ['APPROVED', 'PENDING']:
            full_url = href if href.startswith('http') else f"https://hoanghamobile.com{href}"
            best_match = {
                "competitor_name": title,
                "competitor_price": price_val,
                "url": full_url,
                "status": match_res['status'],
                "confidence": match_res['confidence_score']
            }
            break # Lấy kết quả khớp chính xác đầu tiên
            
    return kwd, best_match

if __name__ == '__main__':
    test_skus = [
        ('SKU0007', 'Laptop Acer Aspire Lite 14 AL14-52M-52UU i5 1335U/16GB/512GB/14" 2.2K/Win11'),
        ('SKU0001', 'Laptop Acer Aspire 7 Gaming A715-59G-57TU i5 12450H/16GB/512GB/15.6"FHD/Nvidia Geforce RTX3050 6GB/Win11'),
        ('SKU0190', 'iPhone 16e 128GB'),
        ('SKU0294', 'Samsung Galaxy Z Fold7 5G 12GB 256GB'),
        ('SKU0055', 'Laptop Asus Vivobook Go 15 E1504FA-BQ340W R5 7520U/16GB/512GB/15.6"FHD/Win11'),
    ]

    print("=" * 80)
    print("KIỂM TRA CÀO THEO TỪNG SKU FPT (TARGETED SEARCH)")
    print("=" * 80)
    for sid, sname in test_skus:
        kwd, match = search_and_match(sid, sname)
        print(f"[{sid}] {sname[:45]} -> Từ khóa search: '{kwd}'")
        if match and isinstance(match, dict):
            print(f"   => KHỚP ĐƯỢC: {match['competitor_name']}")
            print(f"      Giá: {match['competitor_price']:,} ₫ | Trạng thái: {match['status']} ({match['confidence']*100:.1f}%) | Link: {match['url']}")
        else:
            print("   => KHÔNG TÌM THẤY (Hoàng Hà không kinh doanh mã này)")
        time.sleep(1.0)
    print("=" * 80)
