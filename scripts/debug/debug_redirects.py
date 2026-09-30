import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import json
import requests

json_path = os.path.join(BASE_DIR, "data", "scraped_products.json")
with open(json_path, "r", encoding="utf-8") as f:
    items = json.load(f)

# Pick Android products
android_items = [it for it in items if any(k in it.get("URL sản phẩm", "").lower() for k in ["samsung", "oppo", "xiaomi", "redmi", "realme", "vivo"])]

print(f"Total android items: {len(android_items)}")

# Check redirects for 50 items
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
})

redirects = []
for it in android_items[:50]:
    url = it.get("URL sản phẩm")
    try:
        res = session.get(url, timeout=5, allow_redirects=False)
        if res.status_code in [301, 302, 307, 308]:
            loc = res.headers.get("Location")
            redirects.append((url, res.status_code, loc))
            print(f"REDIRECT {res.status_code}: {url} -> {loc}")
    except Exception as e:
        pass

print(f"Total redirects among 50 items: {len(redirects)}")
