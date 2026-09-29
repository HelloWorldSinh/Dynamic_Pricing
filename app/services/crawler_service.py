import time
import uuid
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.crawl_result import CrawlResult
from app.schemas.crawl import CrawlTriggerRequest, CrawlJobResponse, SourceEnum
from app.services.scrapers.factory import ScraperFactory

logger = logging.getLogger(__name__)


class CrawlerService:
    """Deep Module: Điều phối toàn bộ hoạt động cào dữ liệu, debounce và lưu DB."""
    
    # Lưu timestamp lần kích hoạt gần nhất theo source để thực hiện debounce 30s
    _last_triggered: dict = {}

    @classmethod
    def check_debounce(cls, source: str) -> Tuple[bool, int]:
        """Kiểm tra xem tác vụ có đang trong thời gian debounce hay không.
        Trả về: (is_debounced, remaining_seconds)
        """
        now = time.time()
        last_time = cls._last_triggered.get(source, 0)
        elapsed = now - last_time
        debounce_limit = settings.DEBOUNCE_SECONDS

        if elapsed < debounce_limit:
            remaining = int(debounce_limit - elapsed)
            return True, remaining

        cls._last_triggered[source] = now
        return False, 0

    @classmethod
    def execute_crawl_job(cls, task_id: str, request: CrawlTriggerRequest, db_session_factory):
        """Hàm chạy ngầm (Background Task) để cào dữ liệu và ghi vào CSDL."""
        logger.info(f" bắt đầu chạy task {task_id} cho source {request.source} - category {request.category}")
        
        scraper = ScraperFactory.get_scraper(request.source.value)
        items_to_save = []

        if request.target_url:
            item = scraper.scrape_product(request.target_url)
            if item:
                items_to_save.append(item)
        else:
            items_to_save = scraper.scrape_category(request.category.value, limit=5)

        # Lưu dữ liệu vào CSDL
        db: Session = db_session_factory()
        try:
            for item in items_to_save:
                crawl_record = CrawlResult(
                    source=item.source,
                    url=item.url,
                    raw_name=item.product_name,
                    current_price=item.current_price,
                    original_price=item.original_price,
                    is_in_stock=item.is_in_stock,
                    raw_specs=item.specifications
                )
                db.add(crawl_record)
            db.commit()
            logger.info(f" Hoàn tất task {task_id}: Đã lưu {len(items_to_save)} sản phẩm vào DB.")
        except Exception as e:
            db.rollback()
            logger.error(f"Lỗi khi lưu kết quả cào vào DB: {e}")
        finally:
            db.close()

    @classmethod
    def trigger_crawl(cls, request: CrawlTriggerRequest, background_tasks, db_session_factory) -> CrawlJobResponse:
        """Interface gọi cào dữ liệu từ API controller."""
        task_id = str(uuid.uuid4())
        
        # Đưa vào FastAPI BackgroundTasks chạy bất đồng bộ ngầm
        background_tasks.add_task(
            cls.execute_crawl_job,
            task_id,
            request,
            db_session_factory
        )

        return CrawlJobResponse(
            task_id=task_id,
            status="PROCESSING",
            message=f"Đã tiếp nhận yêu cầu cào giá {request.source.value.upper()} ({request.category.value}). Đang xử lý ngầm."
        )
