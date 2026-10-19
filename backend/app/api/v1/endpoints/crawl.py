from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.crawl_job import CrawlJob
from app.models.crawl_result import CrawlResult
from app.schemas.crawl import CrawlTriggerRequest, CrawlJobResponse, CrawlProgressResponse, CrawlJobRecordResponse
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
def get_crawl_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    task = CrawlerService.get_task_status(task_id, db=db)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tác vụ cào với task_id '{task_id}'."
        )
    return task


@router.get(
    "/jobs",
    response_model=List[CrawlJobRecordResponse],
    summary="Lấy danh sách lịch sử các đợt cào dữ liệu",
    description="Truy vấn danh sách lịch sử các đợt cào dữ liệu từ bảng crawl_jobs, sắp xếp mới nhất lên đầu."
)
def list_crawl_jobs(
    limit: int = 20,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    jobs = db.query(CrawlJob).order_by(CrawlJob.started_at.desc()).offset(skip).limit(limit).all()
    return [
        CrawlJobRecordResponse(
            id=str(j.id),
            trigger_type=j.trigger_type,
            source=j.source,
            category=j.category,
            status=j.status,
            total_items=j.total_items,
            success_items=j.success_items,
            error_items=j.error_items,
            error_log=j.error_log,
            started_at=j.started_at,
            finished_at=j.finished_at,
        )
        for j in jobs
    ]


@router.get(
    "/jobs/latest",
    response_model=Optional[CrawlJobRecordResponse],
    summary="Lấy đợt cào dữ liệu gần nhất",
    description="Truy vấn đợt cào dữ liệu mới nhất (ưu tiên trạng thái COMPLETED) từ bảng crawl_jobs."
)
def get_latest_crawl_job(
    status: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CrawlJob)
    if status and status.upper() != "ALL":
        query = query.filter(CrawlJob.status == status.upper())
    if source and source.upper() != "ALL":
        query = query.filter(CrawlJob.source == source.upper())

    job = query.order_by(CrawlJob.started_at.desc()).first()
    if not job:
        return None

    return CrawlJobRecordResponse(
        id=str(job.id),
        trigger_type=job.trigger_type,
        source=job.source,
        category=job.category,
        status=job.status,
        total_items=job.total_items,
        success_items=job.success_items,
        error_items=job.error_items,
        error_log=job.error_log,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )




def _build_category_filter(category: str):
    from sqlalchemy import or_, and_
    from app.models.product import Product
    from app.models.sku_mapping import SkuMapping

    cat = category.strip().upper()
    if cat in ("LAPTOP", "NOTEBOOK", "PC"):
        laptop_keywords = [
            "%laptop%", "%macbook%", "%vivobook%", "%zenbook%", "%thinkpad%",
            "%ideapad%", "%legion%", "%tuf%", "%nitro%", "%loq%", "%victus%",
            "%predator%", "%inspiron%", "%vostro%", "%latitude%", "%yoga%",
            "%swift%", "%pavilion%", "%envy%", "%spectre%", "%omen%", "%surface%"
        ]
        return or_(
            *[CrawlResult.raw_name.ilike(k) for k in laptop_keywords],
            *[CrawlResult.url.ilike(k) for k in ["%/laptop%", "%laptop%"]],
            CrawlResult.mappings.any(SkuMapping.product.has(Product.category == "LAPTOP"))
        )
    elif cat in ("PHONE", "SMARTPHONE", "DIEN-THOAI"):
        phone_keywords = [
            "%iphone%", "%galaxy%", "%redmi%", "%oppo%", "%realme%",
            "%dien-thoai%", "%poco%", "%infinix%", "%tecno%"
        ]
        return or_(
            *[CrawlResult.raw_name.ilike(k) for k in phone_keywords],
            *[CrawlResult.url.ilike(k) for k in ["%/dtdd%", "%/dien-thoai%"]],
            and_(
                CrawlResult.raw_name.ilike("%xiaomi%"),
                ~CrawlResult.raw_name.ilike("%laptop%"),
                ~CrawlResult.raw_name.ilike("%pad%")
            ),
            and_(
                CrawlResult.raw_name.ilike("%samsung%"),
                ~CrawlResult.raw_name.ilike("%laptop%"),
                ~CrawlResult.raw_name.ilike("%tab%")
            ),
            CrawlResult.mappings.any(SkuMapping.product.has(Product.category == "PHONE"))
        )
    elif cat in ("TABLET", "MAY-TINH-BANG"):
        tablet_keywords = ["%ipad%", "%tablet%", "%may-tinh-bang%", "%galaxy tab%"]
        return or_(
            *[CrawlResult.raw_name.ilike(k) for k in tablet_keywords],
            CrawlResult.mappings.any(SkuMapping.product.has(Product.category == "TABLET"))
        )
    return None


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

    if category and category.upper() != 'ALL':
        cat_filter = _build_category_filter(category)
        if cat_filter is not None:
            query = query.filter(cat_filter)
        
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
    if category and category.upper() != 'ALL':
        cat_filter = _build_category_filter(category)
        if cat_filter is not None:
            query = query.filter(cat_filter)
    
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
    
    # Ưu tiên lấy mốc thời gian từ đợt cào COMPLETED trong bảng crawl_jobs
    latest_job = (
        db.query(CrawlJob)
        .filter(CrawlJob.status == "COMPLETED")
        .order_by(CrawlJob.started_at.desc())
        .first()
    )
    if latest_job and (latest_job.finished_at or latest_job.started_at):
        latest_crawled_at = latest_job.finished_at or latest_job.started_at
    else:
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
    description="Xóa các bản ghi CrawlResult có ngày cào cũ hơn số ngày quy định (mặc định 7 ngày) và chưa từng được map vào SKU FPT."
)
def cleanup_crawl_results(
    days: int = 7,
    db: Session = Depends(get_db)
):
    deleted_count = CrawlerService.cleanup_stale_crawl_results(days=days, db=db)
    return {
        "message": f"Đã dọn dẹp thành công {deleted_count} bản ghi cào cũ (> {days} ngày) chưa được map.",
        "deleted_count": deleted_count,
        "retention_days": days,
    }
