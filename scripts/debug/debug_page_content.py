import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

url = "https://cellphones.com.vn/dien-thoai-samsung-galaxy-s26-ultra.html"
res = requests.get(url, headers=headers, timeout=10)
print("Status code:", res.status_code)
print("Final URL:", res.url)
soup = BeautifulSoup(res.text, "html.parser")
h1 = soup.find("h1")
print("H1 tag:", h1.get_text(strip=True) if h1 else "No H1")
title = soup.find("title")
print("Title tag:", title.get_text(strip=True) if title else "No title")

# What products are featured or shown on this page?
links = soup.find_all("a", href=True)
print("Total links:", len(links))
for a in links[:20]:
    if "iphone" in a["href"].lower():
        print("iPhone link on page:", a["href"], a.get_text(strip=True))
