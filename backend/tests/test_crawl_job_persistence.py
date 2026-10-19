"""Tests for CrawlJob persistence and lifecycle tracking."""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from starlette.datastructures import State
from fastapi import BackgroundTasks

from app.models.crawl_job import CrawlJob
from app.models.crawl_result import CrawlResult
from app.schemas.crawl import CrawlTriggerRequest, SourceEnum, CategoryEnum, ScrapedProductItem
from app.services.crawler_service import CrawlerService


def test_trigger_crawl_creates_crawl_job_in_db(db_session: Session):
    """Kiểm thử khi trigger_crawl được gọi, một bản ghi CrawlJob được lưu ngay vào CSDL."""
    # Reset debounce
    CrawlerService._last_triggered.clear()

    request = CrawlTriggerRequest(
        source=SourceEnum.FULL_PIPELINE,
        category=CategoryEnum.ALL,
        limit=5,
    )
    bg_tasks = BackgroundTasks()

    # Sử dụng db_session_factory trả về db_session
    response = CrawlerService.trigger_crawl(
        request=request,
        background_tasks=bg_tasks,
        db_session_factory=lambda: db_session,
    )

    assert response.task_id is not None
    job_uuid = uuid.UUID(response.task_id)

    # Kiểm tra trong DB có bản ghi CrawlJob với id tương ứng
    job = db_session.query(CrawlJob).filter(CrawlJob.id == job_uuid).first()
    assert job is not None
    assert job.status in ["PENDING", "RUNNING"]
    assert job.source == "FULL_PIPELINE"
    assert job.category == "ALL"
    assert job.trigger_type == "ON_DEMAND"


def test_save_scraped_items_upsert_links_job_id(db_session: Session):
    """Kiểm thử save_scraped_items_upsert gắn đúng khóa ngoại job_id cho CrawlResult."""
    job_id = uuid.uuid4()
    job = CrawlJob(
        id=job_id,
        trigger_type="ON_DEMAND",
        source="CELLPHONES",
        category="PHONE",
        status="RUNNING",
    )
    db_session.add(job)
    db_session.commit()

    item = ScrapedProductItem(
        source="CELLPHONES",
        url="https://cellphones.com.vn/test-job-link-phone",
        product_name="Điện thoại Test Job Link",
        current_price=15_000_000,
        original_price=16_000_000,
        is_in_stock=True,
    )

    # 1. Thêm mới kèm job_id
    stats = CrawlerService.save_scraped_items_upsert([item], db=db_session, job_id=job_id)
    assert stats["inserted"] == 1

    saved = db_session.query(CrawlResult).filter(CrawlResult.url == item.url).first()
    assert saved is not None
    assert saved.job_id == job_id

    # 2. Cập nhật với job_id mới
    new_job_id = uuid.uuid4()
    new_job = CrawlJob(
        id=new_job_id,
        trigger_type="ON_DEMAND",
        source="CELLPHONES",
        category="PHONE",
        status="RUNNING",
    )
    db_session.add(new_job)
    db_session.commit()

    updated_item = ScrapedProductItem(
        source="CELLPHONES",
        url="https://cellphones.com.vn/test-job-link-phone",
        product_name="Điện thoại Test Job Link (Updated)",
        current_price=14_500_000,
        original_price=16_000_000,
        is_in_stock=True,
    )

    stats_up = CrawlerService.save_scraped_items_upsert([updated_item], db=db_session, job_id=new_job_id)
    assert stats_up["updated"] == 1

    updated_rec = db_session.query(CrawlResult).filter(CrawlResult.url == item.url).first()
    assert updated_rec.job_id == new_job_id
    assert updated_rec.raw_name == "Điện thoại Test Job Link (Updated)"


def test_update_crawl_job_record_lifecycle(db_session: Session):
    """Kiểm thử hàm cập nhật vòng đời CrawlJob khi hoàn tất."""
    job_id = uuid.uuid4()
    job = CrawlJob(
        id=job_id,
        trigger_type="ON_DEMAND",
        source="FULL_PIPELINE",
        category="ALL",
        status="RUNNING",
    )
    db_session.add(job)
    db_session.commit()

    # Cập nhật khi hoàn tất
    CrawlerService._update_crawl_job_record(
        db=db_session,
        task_id=str(job_id),
        status="COMPLETED",
        total_items=100,
        success_items=98,
        error_items=2,
    )

    refreshed = db_session.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    assert refreshed.status == "COMPLETED"
    assert refreshed.total_items == 100
    assert refreshed.success_items == 98
    assert refreshed.error_items == 2
    assert refreshed.finished_at is not None


def test_get_task_status_fallback_to_crawl_job_db(db_session: Session):
    """Kiểm thử get_task_status fallback đọc từ bảng crawl_jobs khi RAM store rỗng."""
    job_id = uuid.uuid4()
    job = CrawlJob(
        id=job_id,
        trigger_type="ON_DEMAND",
        source="HOANGHA",
        category="LAPTOP",
        status="COMPLETED",
        total_items=50,
        success_items=50,
        error_items=0,
    )
    db_session.add(job)
    db_session.commit()

    # Xóa khỏi cache RAM
    task_id_str = str(job_id)
    CrawlerService._tasks.pop(task_id_str, None)

    # Gọi get_task_status có truyền db
    status_info = CrawlerService.get_task_status(task_id_str, db=db_session)
    assert status_info is not None
    assert status_info["task_id"] == task_id_str
    assert status_info["status"] == "COMPLETED"
    assert status_info["source"] == "HOANGHA"
    assert status_info["category"] == "LAPTOP"
    assert status_info["scraped_count"] == 50
    assert status_info["progress_percent"] == 100


def test_get_latest_crawl_job_endpoint(db_session: Session):
    """Kiểm thử API GET /api/v1/crawl/jobs/latest trả về đợt cào COMPLETED mới nhất."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    try:
        earlier = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        later = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)

        job_old = CrawlJob(
            id=uuid.uuid4(),
            trigger_type="ON_DEMAND",
            source="FULL_PIPELINE",
            category="ALL",
            status="COMPLETED",
            started_at=earlier,
            finished_at=earlier,
        )
        job_new = CrawlJob(
            id=uuid.uuid4(),
            trigger_type="ON_DEMAND",
            source="FULL_PIPELINE",
            category="ALL",
            status="COMPLETED",
            started_at=later,
            finished_at=later,
        )
        db_session.add_all([job_old, job_new])
        db_session.commit()

        res = client.get("/api/v1/crawl/jobs/latest?status=COMPLETED")
        assert res.status_code == 200
        data = res.json()
        assert data is not None
        assert data["id"] == str(job_new.id)
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_crawl_stats_uses_crawl_job_timestamp(db_session: Session):
    """Kiểm thử API GET /api/v1/crawl/stats ưu tiên lấy mốc thời gian từ CrawlJob COMPLETED."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    try:
        job_time = datetime(2026, 5, 20, 15, 30, 0, tzinfo=timezone.utc)
        job = CrawlJob(
            id=uuid.uuid4(),
            trigger_type="ON_DEMAND",
            source="FULL_PIPELINE",
            category="ALL",
            status="COMPLETED",
            started_at=job_time,
            finished_at=job_time,
        )
        db_session.add(job)
        db_session.commit()

        res = client.get("/api/v1/crawl/stats")
        assert res.status_code == 200
        data = res.json()
        assert data["latest_crawled_at"] is not None
        assert "2026-05-20" in data["latest_crawled_at"]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_crawl_job_stored_with_vietnam_timezone(db_session: Session):
    """Kiểm thử khi CrawlJob được tạo và hoàn tất, thời gian lưu vào DB khớp chuẩn múi giờ Việt Nam (UTC+7)."""
    from app.utils.datetime_utils import get_vietnam_now, VIETNAM_TZ

    CrawlerService._last_triggered.clear()
    now_vn_before = get_vietnam_now()

    request = CrawlTriggerRequest(
        source=SourceEnum.FULL_PIPELINE,
        category=CategoryEnum.ALL,
        limit=2,
    )
    bg_tasks = BackgroundTasks()

    response = CrawlerService.trigger_crawl(
        request=request,
        background_tasks=bg_tasks,
        db_session_factory=lambda: db_session,
    )

    job_uuid = uuid.UUID(response.task_id)
    job = db_session.query(CrawlJob).filter(CrawlJob.id == job_uuid).first()

    assert job is not None
    now_vn_after = get_vietnam_now()

    # started_at trong DB phải nằm trong khoảng thời gian Việt Nam lúc thực hiện
    assert now_vn_before <= job.started_at <= now_vn_after
    # Đảm bảo chênh lệch so với UTC đúng xấp xỉ 7 tiếng (+/- 10s)
    utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    time_diff_hours = (job.started_at - utc_naive).total_seconds() / 3600
    assert abs(time_diff_hours - 7.0) < 0.01

    # Cập nhật hoàn tất và kiểm tra finished_at
    CrawlerService._update_crawl_job_record(
        db=db_session,
        task_id=str(job_uuid),
        status="COMPLETED",
        total_items=10,
        success_items=10,
    )
    db_session.refresh(job)
    assert job.finished_at is not None
    diff_fin_hours = (job.finished_at - utc_naive).total_seconds() / 3600
    assert abs(diff_fin_hours - 7.0) < 0.01


def test_crawl_job_api_serializes_vietnam_iso(db_session: Session):
    """Kiểm thử API trả về chuỗi ISO 8601 kèm múi giờ Việt Nam (+07:00)."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db
    from app.utils.datetime_utils import get_vietnam_now

    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    try:
        now_vn = get_vietnam_now()
        job = CrawlJob(
            id=uuid.uuid4(),
            trigger_type="ON_DEMAND",
            source="CELLPHONES",
            category="PHONE",
            status="COMPLETED",
            started_at=now_vn,
            finished_at=now_vn,
        )
        db_session.add(job)
        db_session.commit()

        res = client.get("/api/v1/crawl/jobs/latest?status=COMPLETED")
        assert res.status_code == 200
        data = res.json()
        assert "+07:00" in data["started_at"]
        assert "+07:00" in data["finished_at"]
    finally:
        app.dependency_overrides.pop(get_db, None)


