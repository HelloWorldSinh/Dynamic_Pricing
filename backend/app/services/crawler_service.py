import time
import uuid
import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.crawl_result import CrawlResult
from app.schemas.crawl import CrawlTriggerRequest, CrawlJobResponse
from app.services.scrapers.factory import ScraperFactory

logger = logging.getLogger(__name__)


class CrawlerService:
    """Deep Module: Điều phối toàn bộ hoạt động cào dữ liệu, debounce, tiến độ và lưu DB."""

    # Lưu timestamp lần kích hoạt gần nhất theo source để thực hiện debounce 30s
    _last_triggered: Dict[str, float] = {}

    # Lưu trạng thái tiến độ thời gian thực của các tác vụ cào
    _tasks: Dict[str, Dict[str, Any]] = {}

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
    def get_task_status(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin tiến độ của một task theo task_id."""
        return cls._tasks.get(task_id)

    @classmethod
    def update_task_progress(
        cls,
        task_id: str,
        status: Optional[str] = None,
        current_page: Optional[int] = None,
        total_pages: Optional[int] = None,
        scraped_count: Optional[int] = None,
        progress_percent: Optional[int] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Cập nhật tiến độ của task_id trong RAM store."""
        if task_id not in cls._tasks:
            cls._tasks[task_id] = {
                "task_id": task_id,
                "source": "unknown",
                "category": "unknown",
                "status": "PENDING",
                "current_page": 0,
                "total_pages": 1,
                "scraped_count": 0,
                "progress_percent": 0,
                "message": "Đang khởi tạo...",
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error": None,
            }

        task = cls._tasks[task_id]
        if status is not None:
            task["status"] = status
        if current_page is not None:
            task["current_page"] = current_page
        if total_pages is not None:
            task["total_pages"] = total_pages
        if scraped_count is not None:
            task["scraped_count"] = scraped_count
        if progress_percent is not None:
            task["progress_percent"] = progress_percent
        if message is not None:
            task["message"] = message
        if error is not None:
            task["error"] = error
        if status in ["COMPLETED", "FAILED"]:
            task["completed_at"] = datetime.utcnow().isoformat()

    @classmethod
    def execute_crawl_job(cls, task_id: str, request: CrawlTriggerRequest, db_session_factory):
        """Hàm chạy ngầm (Background Task) để cào dữ liệu và ghi vào CSDL."""
        logger.info(f"Bắt đầu chạy task {task_id} cho source {request.source} - category {request.category}")

        cls.update_task_progress(
            task_id,
            status="RUNNING",
            progress_percent=10,
            message=f"Đang kết nối tới đối thủ {request.source.value.upper()}...",
        )

        scraper = ScraperFactory.get_scraper(request.source.value)
        items_to_save = []

        try:
            if request.target_url:
                cls.update_task_progress(
                    task_id,
                    status="RUNNING",
                    current_page=1,
                    total_pages=1,
                    progress_percent=50,
                    message=f"Đang cào dữ liệu từ URL: {request.target_url}",
                )
                item = scraper.scrape_product(request.target_url)
                if item:
                    items_to_save.append(item)
            else:
                def on_progress(page: int, total_pages: Optional[int], count: int, msg: Optional[str] = None):
                    pct = 85 if not total_pages else min(85, int((page / total_pages) * 85))
                    cls.update_task_progress(
                        task_id,
                        status="RUNNING",
                        current_page=page,
                        total_pages=total_pages or 1,
                        scraped_count=count,
                        progress_percent=pct,
                        message=msg or f"Đang cào trang {page}... Đã thu thập {count} sản phẩm.",
                    )

                # Gọi cào có hỗ trợ progress callback
                import inspect
                sig = inspect.signature(scraper.scrape_category)
                if "on_progress" in sig.parameters:
                    items_to_save = scraper.scrape_category(
                        request.category.value,
                        limit=request.limit,
                        on_progress=on_progress,
                    )
                else:
                    items_to_save = scraper.scrape_category(
                        request.category.value,
                        limit=request.limit,
                    )

            cls.update_task_progress(
                task_id,
                status="RUNNING",
                progress_percent=90,
                scraped_count=len(items_to_save),
                message=f"Đã thu thập {len(items_to_save)} sản phẩm. Đang lưu vào cơ sở dữ liệu...",
            )

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
                        raw_specs=item.specifications,
                    )
                    db.add(crawl_record)
                db.commit()
                logger.info(f"Hoàn tất task {task_id}: Đã lưu {len(items_to_save)} sản phẩm vào DB.")
                cls.update_task_progress(
                    task_id,
                    status="COMPLETED",
                    progress_percent=100,
                    scraped_count=len(items_to_save),
                    message=f"Hoàn thành xuất sắc! Đã cào và lưu {len(items_to_save)} sản phẩm.",
                )
            except Exception as e:
                db.rollback()
                logger.error(f"Lỗi khi lưu kết quả cào vào DB: {e}")
                cls.update_task_progress(
                    task_id,
                    status="FAILED",
                    error=str(e),
                    message=f"Lỗi khi lưu kết quả vào CSDL: {e}",
                )
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Lỗi trong quá trình cào dữ liệu task {task_id}: {e}")
            cls.update_task_progress(
                task_id,
                status="FAILED",
                error=str(e),
                message=f"Lỗi trong quá trình cào: {e}",
            )

    @classmethod
    def trigger_crawl(cls, request: CrawlTriggerRequest, background_tasks, db_session_factory) -> CrawlJobResponse:
        """Interface gọi cào dữ liệu từ API controller."""
        task_id = str(uuid.uuid4())

        # Khởi tạo trạng thái ban đầu của task
        cls._tasks[task_id] = {
            "task_id": task_id,
            "source": request.source.value,
            "category": request.category.value,
            "status": "PENDING",
            "current_page": 0,
            "total_pages": 1,
            "scraped_count": 0,
            "progress_percent": 0,
            "message": f"Đã tiếp nhận yêu cầu cào giá {request.source.value.upper()} ({request.category.value}). Đang chuẩn bị...",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
        }

        # Đưa vào FastAPI BackgroundTasks chạy bất đồng bộ ngầm
        background_tasks.add_task(
            cls.execute_crawl_job,
            task_id,
            request,
            db_session_factory,
        )

        return CrawlJobResponse(
            task_id=task_id,
            status="PROCESSING",
            message=f"Đã tiếp nhận yêu cầu cào giá {request.source.value.upper()} ({request.category.value}). Đang xử lý ngầm.",
        )
