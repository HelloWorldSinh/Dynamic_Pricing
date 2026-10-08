from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.crawl_result import CrawlResult
from app.schemas.crawl import CrawlTriggerRequest, CrawlJobResponse, CrawlProgressResponse
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
    "/status/{task_id}",
    response_model=CrawlProgressResponse,
    summary="Tra cứu tiến độ tác vụ cào dữ liệu theo task_id",
    description="Lấy trạng thái thực thi, phần trăm hoàn thành, số sản phẩm đã cào của job cào dữ liệu."
)
def get_crawl_task_status(task_id: str):
    task = CrawlerService.get_task_status(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tác vụ cào với task_id '{task_id}'."
        )
    return task


@router.get(
    "/results",
    summary="Xem danh sách kết quả cào mới nhất",
    description="Lấy danh sách các sản phẩm đã cào thành công từ các nguồn để hiển thị lên bảng đối soát. Hỗ trợ lazy loading và pagination."
)
def get_crawl_results(
    source: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    stock_status: Optional[str] = None,
    sort_order: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    from sqlalchemy import or_
    query = db.query(CrawlResult)
    
    if source and source.upper() != 'ALL':
        query = query.filter(CrawlResult.source == source.upper())
        
    if stock_status and stock_status != 'ALL':
        is_in_stock = (stock_status == 'IN_STOCK')
        query = query.filter(CrawlResult.is_in_stock == is_in_stock)
        
    if search:
        search_term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                CrawlResult.raw_name.ilike(search_term),
                CrawlResult.url.ilike(search_term)
            )
        )
        
    if sort_order == 'PRICE_ASC':
        query = query.order_by(CrawlResult.current_price.asc().nulls_last())
    elif sort_order == 'PRICE_DESC':
        query = query.order_by(CrawlResult.current_price.desc().nulls_last())
    elif sort_order == 'NAME_ASC':
        query = query.order_by(CrawlResult.raw_name.asc())
    else:
        query = query.order_by(CrawlResult.crawled_at.desc())
        
    total = query.count()
    results = query.offset(skip).limit(limit).all()
    
    return {
        "items": results,
        "total": total
    }


@router.get(
    "/stats",
    summary="Thống kê dữ liệu cào",
    description="Lấy các chỉ số tổng quan: số lượng theo nguồn, tỷ lệ còn hàng, v.v."
)
def get_crawl_stats(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    from sqlalchemy import func, or_
    
    query = db.query(CrawlResult)
    # Nếu DB schema có cột category, ta có thể filter. 
    # Nhưng hiện CrawlResult không có cột category rõ ràng (dựa vào spec hoặc url/raw_name).
    # Tạm thời để đơn giản, ta tính tổng cục bộ nếu không map được category chuẩn.
    
    total = query.count()
    
    cellphones_count = query.filter(CrawlResult.source == 'CELLPHONES').count()
    hoangha_count = query.filter(CrawlResult.source == 'HOANGHA').count()
    
    phone_count = query.filter(
        or_(
            CrawlResult.raw_name.ilike('%phone%'),
            CrawlResult.raw_name.ilike('%xiaomi%'),
            CrawlResult.raw_name.ilike('%samsung%')
        )
    ).count()
    
    laptop_count = query.filter(
        or_(
            CrawlResult.raw_name.ilike('%laptop%'),
            CrawlResult.raw_name.ilike('%macbook%'),
            CrawlResult.raw_name.ilike('%asus%')
        )
    ).count()
    
    in_stock_count = query.filter(CrawlResult.is_in_stock == True).count()
    
    latest_crawled_at = db.query(func.max(CrawlResult.crawled_at)).scalar()
    
    return {
        "total": total,
        "cellphones_count": cellphones_count,
        "hoangha_count": hoangha_count,
        "phone_count": phone_count,
        "laptop_count": laptop_count,
        "in_stock_count": in_stock_count,
        "latest_crawled_at": latest_crawled_at.isoformat() if latest_crawled_at else None
    }


@router.post(
    "/cleanup",
    summary="Dọn dẹp sản phẩm cào đã cũ chưa từng map SKU",
    description="Xóa các bản ghi CrawlResult có ngày cào cũ hơn số ngày quy định (mặc định 60 ngày) và chưa từng được map vào SKU FPT."
)
def cleanup_crawl_results(
    days: int = 60,
    db: Session = Depends(get_db)
):
    deleted_count = CrawlerService.cleanup_stale_crawl_results(days=days, db=db)
    return {
        "message": f"Đã dọn dẹp thành công {deleted_count} bản ghi cào cũ (> {days} ngày) chưa được map.",
        "deleted_count": deleted_count,
        "retention_days": days,
    }
