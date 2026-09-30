import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import json
from app.services.scrapers.cellphones import CellphonesScraper

scraper = CellphonesScraper()

# Pick some Android URLs from scraped_products.json
json_path = os.path.join(BASE_DIR, "data", "scraped_products.json")
with open(json_path, "r", encoding="utf-8") as f:
    items = json.load(f)

android_items = [it for it in items if any(k in it.get("URL sản phẩm", "").lower() for k in ["samsung", "oppo", "xiaomi", "redmi", "vivo"])]

print(f"Total android items in json: {len(android_items)}")
for it in android_items[:10]:
    url = it.get("URL sản phẩm")
    print(f"\n--- Testing URL: {url} ---")
    print(f"JSON Name: {it.get('Tên sản phẩm')}")
    res = scraper.scrape_product(url)
    if res:
        print(f"scrape_product Name: {res.product_name}")
        print(f"scrape_product Price: {res.current_price}")
        if "iphone" in res.product_name.lower():
            print(f"!!! CRITICAL: scrape_product returned iPhone for an Android URL: {url} -> {res.product_name}")
