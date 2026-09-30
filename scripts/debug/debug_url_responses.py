import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

test_urls = [
    "https://cellphones.com.vn/dien-thoai-samsung-galaxy-s26-ultra.html",
    "https://cellphones.com.vn/dien-thoai-oppo-reno16-f.html",
    "https://cellphones.com.vn/dien-thoai-samsung-galaxy-s26-fe.html",
    "https://cellphones.com.vn/dien-thoai-samsung-galaxy-a57.html",
    "https://cellphones.com.vn/dien-thoai-xiaomi-redmi-note-17.html",
    "https://cellphones.com.vn/dien-thoai-samsung-galaxy-s25-ultra.html",
    "https://cellphones.com.vn/samsung-galaxy-s24-ultra.html",
]

for url in test_urls:
    try:
        res = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"Request URL: {url}")
        print(f"Status: {res.status_code} | Final URL: {res.url}")
        soup = BeautifulSoup(res.text, "html.parser")
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else "NO H1"
        print(f"Page title H1: '{title}'")
        price = soup.select_one(".sale-price, .special-price, .product__price--show")
        print(f"Price on page: {price.get_text(strip=True) if price else 'N/A'}")
        print("-" * 50)
    except Exception as e:
        print(f"Error {url}: {e}")
