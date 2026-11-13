"""Unit & Integration Tests cho API Cào và Đồng bộ Giá Real-Time FPT Shop.

Kiểm thử:
1. POST /api/v1/crawl/trigger với nguồn 'fptshop' và ngành 'all' -> HTTP 202 ACCEPTED + task_id.
2. POST /api/v1/crawl/sync-fpt-prices -> HTTP 202 ACCEPTED + task_id.
3. GET /api/v1/crawl/status/{task_id} -> HTTP 200 OK trả về tiến độ task.
4. Cơ chế Debounce 30s: Kích hoạt 2 lần liên tiếp -> HTTP 429 Too Many Requests.
5. End-to-End Background Job: Cào, lưu kết quả upsert, gọi FptPriceSyncService và cập nhật tiến độ COMPLETED.
6. GET /api/v1/crawl/status/{non_existent_id} -> HTTP 404 NOT FOUND.
"""

import uuid
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.crawl import ScrapedProductItem
from app.services.crawler_service import CrawlerService


@pytest.fixture
def client():
    """Khởi tạo TestClient của FastAPI."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_crawler_state():
    """Đảm bảo cô lập hoàn toàn giữa các bài test: xóa sạch debounce và RAM task store."""
    CrawlerService._last_triggered.clear()
    CrawlerService._tasks.clear()
    yield
    CrawlerService._last_triggered.clear()
    CrawlerService._tasks.clear()


@pytest.fixture
def mock_scraped_items() -> List[ScrapedProductItem]:
    """Dữ liệu giả lập sản phẩm cào từ FPT Shop."""
    return [
        ScrapedProductItem(
            source="FPTSHOP",
            url="https://fptshop.com.vn/dien-thoai/iphone-16-pro-max-256gb",
            product_name="iPhone 16 Pro Max 256GB",
            current_price=33990000,
            original_price=34990000,
            is_in_stock=True,
            specifications={"Bộ nhớ/RAM": "256 GB", "Part Number": "MYWW3VN/A"},
        ),
        ScrapedProductItem(
            source="FPTSHOP",
            url="https://fptshop.com.vn/may-tinh-xach-tay/asus-vivobook-16-x1607ca-mb387w",
            product_name="Laptop Asus Vivobook 16 X1607CA-MB387W",
            current_price=17490000,
            original_price=18990000,
            is_in_stock=True,
            specifications={"Part Number": "X1607CA-MB387W"},
        ),
    ]


def test_trigger_fpt_crawl_success(client, mock_scraped_items):
    """Kiểm tra POST /api/v1/crawl/trigger với source 'fptshop' thành công trả về 202 và task_id."""
    with patch("app.services.scrapers.factory.ScraperFactory.get_scraper") as mock_get_scraper, \
         patch("app.services.fpt_sync_service.FptPriceSyncService.sync_live_prices") as mock_sync:
        mock_scraper = MagicMock()
        mock_scraper.scrape_category.return_value = mock_scraped_items
        mock_get_scraper.return_value = mock_scraper
        mock_sync.return_value = {
            "matched_count": 2,
            "price_updated_count": 1,
            "deactivated_count": 0,
            "recalculated_count": 1,
            "unmatched_skus": [],
        }

        payload = {
            "source": "fptshop",
            "category": "all",
        }
        response = client.post("/api/v1/crawl/trigger", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] in ["PROCESSING", "PENDING", "COMPLETED"]
        assert "FPTSHOP" in data["message"].upper()


def test_sync_fpt_prices_success(client, mock_scraped_items):
    """Kiểm tra POST /api/v1/crawl/sync-fpt-prices thành công trả về 202 và task_id."""
    with patch("app.services.scrapers.factory.ScraperFactory.get_scraper") as mock_get_scraper, \
         patch("app.services.fpt_sync_service.FptPriceSyncService.sync_live_prices") as mock_sync:
        mock_scraper = MagicMock()
        mock_scraper.scrape_category.return_value = mock_scraped_items
        mock_get_scraper.return_value = mock_scraper
        mock_sync.return_value = {
            "matched_count": 5,
            "price_updated_count": 3,
            "deactivated_count": 1,
            "recalculated_count": 3,
            "unmatched_skus": [],
        }

        response = client.post("/api/v1/crawl/sync-fpt-prices")

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] in ["PROCESSING", "PENDING", "COMPLETED"]
        assert "started_at" in data

        # Kiểm tra trạng thái task ngay sau khi kích hoạt
        task_id = data["task_id"]
        status_resp = client.get(f"/api/v1/crawl/status/{task_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["task_id"] == task_id
        assert status_data["status"] == "COMPLETED"
        assert "Đã hoàn tất đồng bộ giá FPT Shop: 5 khớp, 3 cập nhật giá, 1 ngừng kinh doanh." in status_data["message"]


def test_get_crawl_status_existing(client):
    """Kiểm tra GET /api/v1/crawl/status/{task_id} trả về đúng dữ liệu tiến độ."""
    task_id = str(uuid.uuid4())
    CrawlerService._tasks[task_id] = {
        "task_id": task_id,
        "source": "FPTSHOP",
        "category": "ALL",
        "status": "RUNNING",
        "current_page": 2,
        "total_pages": 10,
        "scraped_count": 96,
        "progress_percent": 20,
        "message": "FPT Shop trang 2/10: Đã thu thập 96 sản phẩm...",
        "started_at": "2026-11-02T10:00:00+07:00",
        "completed_at": None,
        "error": None,
    }

    response = client.get(f"/api/v1/crawl/status/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["source"] == "FPTSHOP"
    assert data["status"] == "RUNNING"
    assert data["progress_percent"] == 20
    assert data["scraped_count"] == 96


def test_get_crawl_status_not_found(client):
    """Kiểm tra GET /api/v1/crawl/status/{task_id} với id không tồn tại trả về 404."""
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/crawl/status/{random_id}")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_debounce_trigger_endpoint(client):
    """Kiểm tra debounce trên endpoint /trigger: gọi 2 lần liên tiếp kích hoạt HTTP 429."""
    with patch("app.services.scrapers.factory.ScraperFactory.get_scraper"):
        payload = {"source": "fptshop", "category": "all"}

        # Lần 1: Thành công
        resp1 = client.post("/api/v1/crawl/trigger", json=payload)
        assert resp1.status_code == 202

        # Lần 2 ngay lập tức: Bị chặn debounce (429)
        resp2 = client.post("/api/v1/crawl/trigger", json=payload)
        assert resp2.status_code == 429
        assert "Vui lòng đợi" in resp2.json()["detail"]
        assert "fptshop" in resp2.json()["detail"]


def test_debounce_sync_fpt_prices_endpoint(client):
    """Kiểm tra debounce trên endpoint /sync-fpt-prices: gọi 2 lần liên tiếp kích hoạt HTTP 429."""
    with patch("app.services.scrapers.factory.ScraperFactory.get_scraper"):
        # Lần 1: Thành công
        resp1 = client.post("/api/v1/crawl/sync-fpt-prices")
        assert resp1.status_code == 202

        # Lần 2 ngay lập tức: Bị chặn debounce (429)
        resp2 = client.post("/api/v1/crawl/sync-fpt-prices")
        assert resp2.status_code == 429
        assert "Vui lòng đợi" in resp2.json()["detail"]
        assert "fptshop" in resp2.json()["detail"]


def test_cross_endpoint_debounce(client):
    """Kiểm tra tính liên kết debounce: trigger qua /trigger cũng chặn /sync-fpt-prices."""
    with patch("app.services.scrapers.factory.ScraperFactory.get_scraper"):
        # Gọi /trigger cho fptshop
        resp1 = client.post("/api/v1/crawl/trigger", json={"source": "fptshop", "category": "all"})
        assert resp1.status_code == 202

        # Ngay sau đó gọi /sync-fpt-prices
        resp2 = client.post("/api/v1/crawl/sync-fpt-prices")
        assert resp2.status_code == 429
        assert "fptshop" in resp2.json()["detail"]

