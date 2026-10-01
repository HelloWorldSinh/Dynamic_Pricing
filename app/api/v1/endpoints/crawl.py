from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.crawl_result import CrawlResult
from app.schemas.crawl import CrawlTriggerRequest, CrawlJobResponse
from app.services.crawler_service import CrawlerService

router = APIRouter()


@router.post(
    "/trigger",
    response_model=CrawlJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Kích hoạt job cào giá tức thời (PBI-004)",
    description="Kích hoạt tác vụ cào dữ liệu từ FPT Shop, CellphoneS hoặc Hoàng Hà Mobile. Có cơ chế Debounce 30 giây bảo vệ hệ thống."
)
def trigger_crawl(
    request: CrawlTriggerRequest,
    background_tasks: BackgroundTasks,
):
    # 1. Kiểm tra debounce 30s
    is_debounced, remaining = CrawlerService.check_debounce(request.source.value)
    if is_debounced:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Hệ thống vừa nhận yêu cầu cho '{request.source.value}'. Vui lòng đợi {remaining}s trước khi kích hoạt lại."
        )

    # 2. Đưa tác vụ vào background
    return CrawlerService.trigger_crawl(
        request=request,
        background_tasks=background_tasks,
        db_session_factory=SessionLocal
    )


@router.get(
    "/results",
    summary="Xem danh sách kết quả cào mới nhất",
    description="Lấy danh sách các sản phẩm đã cào thành công từ các nguồn để hiển thị lên bảng đối soát."
)
def get_crawl_results(
    source: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(CrawlResult)
    if source:
        query = query.filter(CrawlResult.source == source.upper())
    results = query.order_by(CrawlResult.crawled_at.desc()).limit(limit).all()
    return results
