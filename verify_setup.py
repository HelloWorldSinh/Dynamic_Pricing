import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.crawl_result import CrawlResult

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print(" [PASS] Health check OK:", data)

def test_docs():
    response = client.get("/docs")
    assert response.status_code == 200
    print(" [PASS] Swagger UI docs (/docs) OK!")

def test_trigger_crawl():
    # 1. Gọi lần 1 -> Thành công (202 Accepted)
    payload = {
        "source": "cellphones",
        "category": "phone",
        "target_url": "https://cellphones.com.vn/iphone-15-pro-max.html"
    }
    response = client.post("/api/v1/crawl/trigger", json=payload)
    assert response.status_code == 202
    data = response.json()
    print(" [PASS] Kích hoạt cào lần 1 OK:", data)

    # 2. Gọi ngay lần 2 -> Bị debounce 30s chặn lại (429 Too Many Requests)
    response_debounce = client.post("/api/v1/crawl/trigger", json=payload)
    assert response_debounce.status_code == 429
    print(" [PASS] Cơ chế Debounce 30s hoạt động chuẩn xác (429 Too Many Requests):", response_debounce.json())

if __name__ == "__main__":
    print("--- BẮT ĐẦU KIỂM THỬ HỆ THỐNG FASTAPI + CSDL + DEBOUNCE ---")
    test_health()
    test_docs()
    test_trigger_crawl()
    print("--- TOÀN BỘ KIỂM THỬ THÀNH CÔNG RỰC RỠ! ---")
