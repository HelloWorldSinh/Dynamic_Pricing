import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.crawler_service import CrawlerService

client = TestClient(app)


from unittest.mock import patch


def test_get_progress_not_found():
    """Tra cứu một task_id không tồn tại phải trả về 404."""
    response = client.get("/api/v1/crawl/status/invalid-uuid-1234")
    assert response.status_code == 404
    assert "Không tìm thấy" in response.json()["detail"]


@patch.object(CrawlerService, "execute_crawl_job")
def test_trigger_and_check_progress(mock_execute):
    """Kích hoạt cào và kiểm tra trạng thái tiến độ qua API."""
    # Reset debounce cho test
    CrawlerService._last_triggered.clear()

    payload = {
        "source": "cellphones",
        "category": "phone",
        "limit": 5
    }
    trigger_res = client.post("/api/v1/crawl/trigger", json=payload)
    assert trigger_res.status_code == 202
    data = trigger_res.json()
    task_id = data["task_id"]
    assert task_id is not None

    # Tra cứu ngay trạng thái của task_id
    status_res = client.get(f"/api/v1/crawl/status/{task_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()

    assert status_data["task_id"] == task_id
    assert status_data["status"] in ["PENDING", "RUNNING", "COMPLETED"]
    assert "progress_percent" in status_data
    assert "scraped_count" in status_data
    assert "message" in status_data


@patch.object(CrawlerService, "execute_full_pipeline_job")
def test_trigger_full_pipeline_and_check_progress(mock_execute):
    """Kích hoạt Full Pipeline và kiểm tra trạng thái ban đầu."""
    CrawlerService._last_triggered.clear()
    payload = {
        "source": "full_pipeline",
        "category": "all"
    }
    trigger_res = client.post("/api/v1/crawl/trigger", json=payload)
    assert trigger_res.status_code == 202
    data = trigger_res.json()
    task_id = data["task_id"]
    assert task_id is not None

    status_res = client.get(f"/api/v1/crawl/status/{task_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["source"] == "FULL_PIPELINE"
    assert status_data["status"] in ["PENDING", "RUNNING", "COMPLETED"]

