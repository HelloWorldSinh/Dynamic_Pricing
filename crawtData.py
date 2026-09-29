import json
import requests
from bs4 import BeautifulSoup


def scrape_cellphones_product(url: str):
    # 1. Bắt buộc gắn User-Agent để không bị chặn mã 403 Forbidden
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi yêu cầu tới website: {e}")
        return None

    # 2. Khởi tạo cây DOM bằng BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # 3. Trích xuất tên sản phẩm (thẻ h1 chính của trang)
    title_tag = soup.find("h1")
    product_name = title_tag.get_text(strip=True) if title_tag else "N/A"

    # 4. Trích xuất giá sản phẩm
    # CellphoneS sử dụng class '.sale-price' cho giá hiện tại và '.base-price' cho giá niêm yết cũ
    price_tag = soup.select_one(".sale-price, .product__price--show, .special-price, .t-price")
    old_price_tag = soup.select_one(".base-price, .product__price--through, .old-price")

    current_price = price_tag.get_text(strip=True) if price_tag else None
    old_price = old_price_tag.get_text(strip=True) if old_price_tag else None

    # Fallback 1: Trích xuất từ JSON-LD (Schema.org) nếu không tìm thấy qua CSS selector
    if not current_price:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    offers = data.get("offers", {})
                    if isinstance(offers, dict) and "price" in offers:
                        raw_price = int(offers["price"])
                        current_price = f"{raw_price:,}".replace(",", ".") + "đ"
                        break
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

    if not current_price:
        current_price = "Liên hệ"

    # 5. Trích xuất bảng thông số kỹ thuật
    specifications = {}
    spec_table = soup.find("table")
    if spec_table:
        rows = spec_table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True)
                val = cols[1].get_text(strip=True)
                specifications[key] = val

    return {
        "url": url,
        "product_name": product_name,
        "current_price": current_price,
        "old_price": old_price,
        "specifications": specifications,
    }


if __name__ == "__main__":
    # URL sản phẩm mẫu trên CellphoneS
    target_url = "https://cellphones.com.vn/iphone-15-pro-max.html"

    print("Đang cào dữ liệu từ CellphoneS...")
    data = scrape_cellphones_product(target_url)

    if data:
        print("\n--- KẾT QUẢ CÀO DỮ LIỆU ---")
        print(f"Tên sản phẩm: {data['product_name']}")
        print(f"Giá hiện tại: {data['current_price']}")
        if data["old_price"]:
            print(f"Giá niêm yết: {data['old_price']}")

        print(f"\nThông số kỹ thuật ({len(data['specifications'])} mục):")
        # In thử 5 thông số đầu tiên
        for idx, (k, v) in enumerate(data["specifications"].items()):
            if idx >= 10:
                break
            print(f" - {k}: {v}")