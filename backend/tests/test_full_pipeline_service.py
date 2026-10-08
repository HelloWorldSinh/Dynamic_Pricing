import uuid
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.schemas.crawl import CrawlTriggerRequest, SourceEnum, ScrapedProductItem
from app.services.crawler_service import CrawlerService
from app.services.seeder import seed_catalog_and_inventory
from app.services.scrapers.factory import ScraperFactory


def test_execute_full_pipeline_job(db_session: Session):
    """Kiểm thử toàn bộ luồng execute_full_pipeline_job từ cào, lưu DB, đối soát SKU đến xuất Excel."""
    # 1. Nạp catalog FPT vào db_session
    seed_catalog_and_inventory(db_session, limit=10)
    prods = db_session.query(Product).all()
    sample_prod = prods[0]

    # 2. Tạo mock ScrapedProductItem khớp với sample_prod
    mock_cps_item = ScrapedProductItem(
        source="CELLPHONES",
        product_name=sample_prod.name,
        current_price=sample_prod.base_retail_price - 100_000,
        original_price=sample_prod.base_retail_price,
        url="https://cellphones.com.vn/test-sample-item",
        specifications={"storage": "128GB"},
        is_in_stock=True,
    )

    mock_hh_item = ScrapedProductItem(
        source="HOANGHA",
        product_name="Sản phẩm khác không khớp 999XYZ",
        current_price=15_000_000,
        original_price=16_000_000,
        url="https://hoanghamobile.com/test-hh-item",
        specifications={},
        is_in_stock=True,
    )

    # 3. Tạo mock scrapers
    mock_cps = MagicMock()
    mock_cps.scrape_category.side_effect = lambda cat, limit, on_progress: [mock_cps_item] if cat == "phone" else []

    mock_hh = MagicMock()
    mock_hh.scrape_category.side_effect = lambda cat, limit, on_progress: [mock_hh_item] if cat == "laptop" else []

    def fake_get_scraper(source_name: str):
        if source_name == "cellphones":
            return mock_cps
        return mock_hh

    task_id = "test-full-pipeline-" + str(uuid.uuid4())
    req = CrawlTriggerRequest(source=SourceEnum.FULL_PIPELINE, category="all", limit=2)

    with patch.object(ScraperFactory, "get_scraper", side_effect=fake_get_scraper):
        CrawlerService.execute_full_pipeline_job(
            task_id=task_id,
            request=req,
            db_session_factory=lambda: db_session,
        )

    # 4. Kiểm tra tiến độ hoàn tất 100%
    status = CrawlerService.get_task_status(task_id)
    assert status is not None
    assert status["status"] == "COMPLETED"
    assert status["progress_percent"] == 100
    assert status["scraped_count"] == 2
    assert "Hoàn tất" in status["message"]

    # 5. Kiểm tra CrawlResult đã được lưu trong DB
    crawl_results = db_session.query(CrawlResult).all()
    assert len(crawl_results) == 2
    urls = [cr.url for cr in crawl_results]
    assert "https://cellphones.com.vn/test-sample-item" in urls
    assert "https://hoanghamobile.com/test-hh-item" in urls
