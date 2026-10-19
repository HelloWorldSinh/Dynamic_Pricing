import time
import uuid
import logging
from datetime import timedelta
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.crawl_job import CrawlJob
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.models.pricing import PriceHistory
from app.models.product import Product
from app.schemas.crawl import CrawlTriggerRequest, CrawlJobResponse, ScrapedProductItem
from app.services.scrapers.factory import ScraperFactory
from app.utils.datetime_utils import get_vietnam_now, to_vietnam_iso

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
    def get_task_status(cls, task_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Lấy thông tin tiến độ của một task theo task_id (ưu tiên RAM, fallback CSDL)."""
        task = cls._tasks.get(task_id)
        if task:
            return task

        if db is not None:
            try:
                job_uuid = uuid.UUID(task_id) if isinstance(task_id, str) else task_id
                job = db.query(CrawlJob).filter(CrawlJob.id == job_uuid).first()
                if job:
                    pct = 100 if job.status == "COMPLETED" else (0 if job.status in ["PENDING", "FAILED"] else 50)
                    msg = (
                        f"Đã hoàn tất cào {job.total_items} sản phẩm."
                        if job.status == "COMPLETED"
                        else (f"Gặp lỗi: {job.error_log}" if job.status == "FAILED" else f"Đang thực thi ({job.status})")
                    )
                    return {
                        "task_id": str(job.id),
                        "source": job.source,
                        "category": job.category,
                        "status": job.status,
                        "current_page": 0,
                        "total_pages": 1,
                        "scraped_count": job.total_items,
                        "progress_percent": pct,
                        "message": msg,
                        "started_at": to_vietnam_iso(job.started_at) if job.started_at else None,
                        "completed_at": to_vietnam_iso(job.finished_at) if job.finished_at else None,
                        "error": job.error_log,
                    }
            except Exception as err:
                logger.warning(f"Lỗi khi tra cứu CrawlJob fallback từ DB cho task {task_id}: {err}")

        return None

    @classmethod
    def _update_crawl_job_record(
        cls,
        db: Session,
        task_id: str,
        status: str,
        total_items: Optional[int] = None,
        success_items: Optional[int] = None,
        error_items: Optional[int] = None,
        error_log: Optional[str] = None,
    ):
        """Cập nhật trạng thái và số liệu của CrawlJob trong CSDL."""
        try:
            job_uuid = uuid.UUID(task_id) if isinstance(task_id, str) else task_id
            job = db.query(CrawlJob).filter(CrawlJob.id == job_uuid).first()
            if job:
                job.status = status
                if total_items is not None:
                    job.total_items = total_items
                if success_items is not None:
                    job.success_items = success_items
                if error_items is not None:
                    job.error_items = error_items
                if error_log is not None:
                    job.error_log = error_log
                if status in ["COMPLETED", "FAILED"]:
                    job.finished_at = get_vietnam_now()
                db.commit()
        except Exception as err:
            logger.warning(f"Lỗi khi cập nhật CrawlJob record {task_id}: {err}")
            db.rollback()

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
                "started_at": to_vietnam_iso(),
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
            task["completed_at"] = to_vietnam_iso()

    @classmethod
    def execute_crawl_job(cls, task_id: str, request: CrawlTriggerRequest, db_session_factory):
        """Hàm chạy ngầm (Background Task) để cào dữ liệu và ghi vào CSDL."""
        logger.info(f"Bắt đầu chạy task {task_id} cho source {request.source} - category {request.category}")
        try:
            job_uuid = uuid.UUID(task_id) if isinstance(task_id, str) else task_id
        except (ValueError, TypeError, AttributeError):
            job_uuid = None

        # Đánh dấu trạng thái RUNNING trong CSDL
        db_init: Session = db_session_factory()
        try:
            cls._update_crawl_job_record(db=db_init, task_id=str(task_id), status="RUNNING")
        finally:
            db_init.close()

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

                # Nếu chọn category 'all', cào cả phone và laptop cho nguồn này
                if request.category.value.lower() == "all":
                    cls.update_task_progress(task_id, message=f"Đang cào Điện thoại ({request.source.value.upper()})...")
                    phones = scraper.scrape_category("phone", limit=request.limit, on_progress=on_progress)
                    cls.update_task_progress(task_id, message=f"Đang cào Laptop ({request.source.value.upper()})...")
                    laptops = scraper.scrape_category("laptop", limit=request.limit, on_progress=on_progress)
                    items_to_save = phones + laptops
                else:
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

            # Lưu dữ liệu vào CSDL bằng cơ chế UPSERT theo URL (tránh duplicate & log price history)
            db: Session = db_session_factory()
            try:
                stats = cls.save_scraped_items_upsert(items_to_save, db=db, job_id=job_uuid)
                logger.info(
                    f"Hoàn tất task {task_id}: Đã xử lý {len(items_to_save)} sản phẩm "
                    f"(Thêm mới: {stats['inserted']}, Cập nhật: {stats['updated']})."
                )

                # Dọn dẹp định kỳ các bản ghi cào cũ (> 60 ngày) chưa từng được map SKU
                try:
                    cleaned_count = cls.cleanup_stale_crawl_results(days=60, db=db)
                    if cleaned_count > 0:
                        logger.info(f"Đã dọn dẹp {cleaned_count} bản ghi cào cũ hơn 60 ngày chưa map.")
                except Exception as clean_err:
                    logger.warning(f"Lỗi khi dọn dẹp bản ghi cũ trong task {task_id}: {clean_err}")

                cls.update_task_progress(
                    task_id,
                    status="COMPLETED",
                    progress_percent=100,
                    scraped_count=len(items_to_save),
                    message=(
                        f"Hoàn thành xuất sắc! Đã cào {len(items_to_save)} sản phẩm "
                        f"(Mới: {stats['inserted']}, Cập nhật: {stats['updated']})."
                    ),
                )
                cls._update_crawl_job_record(
                    db=db,
                    task_id=str(job_uuid),
                    status="COMPLETED",
                    total_items=len(items_to_save),
                    success_items=stats["inserted"] + stats["updated"],
                    error_items=max(0, len(items_to_save) - (stats["inserted"] + stats["updated"])),
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
                cls._update_crawl_job_record(
                    db=db,
                    task_id=str(job_uuid),
                    status="FAILED",
                    error_log=str(e),
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
            db_err_session: Session = db_session_factory()
            try:
                cls._update_crawl_job_record(
                    db=db_err_session,
                    task_id=str(job_uuid),
                    status="FAILED",
                    error_log=str(e),
                )
            finally:
                db_err_session.close()

    @classmethod
    def execute_full_pipeline_job(cls, task_id: str, request: CrawlTriggerRequest, db_session_factory):
        """Hàm chạy ngầm FULL PIPELINE:
        1. Cào toàn bộ CellphoneS (Điện thoại & Laptop)
        2. Cào toàn bộ Hoàng Hà Mobile (Điện thoại & Laptop)
        3. Lưu CSDL crawl_results theo cơ chế UPSERT & PriceHistory
        4. Đối soát 329 SKU FPT bằng SkuMatcher & Xuất Excel 3 sheets
        5. Đồng bộ kết quả vào sku_mappings trong CSDL
        6. Cập nhật tiến độ hoàn thành và tổng kết.
        """
        logger.info(f"Bắt đầu chạy FULL PIPELINE cho task {task_id}")
        try:
            job_uuid = uuid.UUID(task_id) if isinstance(task_id, str) else task_id
        except (ValueError, TypeError, AttributeError):
            job_uuid = None

        # Đánh dấu trạng thái RUNNING trong CSDL
        db_init: Session = db_session_factory()
        try:
            cls._update_crawl_job_record(db=db_init, task_id=str(task_id), status="RUNNING")
        finally:
            db_init.close()

        cls.update_task_progress(
            task_id,
            status="RUNNING",
            progress_percent=5,
            message="Đang khởi tạo Full Pipeline: Kết nối CellphoneS & Hoàng Hà Mobile...",
        )

        try:
            scraper_cps = ScraperFactory.get_scraper("cellphones")
            scraper_hh = ScraperFactory.get_scraper("hoangha")

            limit = request.limit if (request.limit and request.limit > 0) else None

            # --- GIAI ĐOẠN 1: CÀO CELLPHONES (5% -> 45%) ---
            cls.update_task_progress(
                task_id,
                status="RUNNING",
                progress_percent=10,
                message="[1/4] Đang cào toàn bộ danh mục CellphoneS (Điện thoại)...",
            )

            def on_cps_phone_progress(p, tp, cnt, msg=None):
                pct = min(25, 10 + int((cnt / 1200) * 15)) if cnt else 10
                cls.update_task_progress(
                    task_id,
                    status="RUNNING",
                    progress_percent=pct,
                    scraped_count=cnt,
                    message=f"CellphoneS (Điện thoại): {cnt} sản phẩm...",
                )

            cps_phones = scraper_cps.scrape_category("phone", limit=limit, on_progress=on_cps_phone_progress)

            cls.update_task_progress(
                task_id,
                status="RUNNING",
                progress_percent=25,
                scraped_count=len(cps_phones),
                message=f"[1/4] CellphoneS Phone xong ({len(cps_phones)} SP). Đang cào CellphoneS Laptop...",
            )

            def on_cps_laptop_progress(p, tp, cnt, msg=None):
                total_cnt = len(cps_phones) + cnt
                pct = min(45, 25 + int((cnt / 3000) * 20)) if cnt else 25
                cls.update_task_progress(
                    task_id,
                    status="RUNNING",
                    progress_percent=pct,
                    scraped_count=total_cnt,
                    message=f"CellphoneS (Laptop): {cnt} SP (Tổng CPS: {total_cnt})...",
                )

            cps_laptops = scraper_cps.scrape_category("laptop", limit=limit, on_progress=on_cps_laptop_progress)
            cps_items = cps_phones + cps_laptops
            total_cps = len(cps_items)

            # --- GIAI ĐOẠN 2: CÀO HOÀNG HÀ MOBILE (45% -> 75%) ---
            cls.update_task_progress(
                task_id,
                status="RUNNING",
                progress_percent=48,
                scraped_count=total_cps,
                message=f"[2/4] CellphoneS hoàn tất ({total_cps} SP). Đang cào Hoàng Hà Mobile (Điện thoại)...",
            )

            def on_hh_phone_progress(p, tp, cnt, msg=None):
                total_cnt = total_cps + cnt
                pct = min(62, 48 + int((cnt / 300) * 14)) if cnt else 48
                cls.update_task_progress(
                    task_id,
                    status="RUNNING",
                    progress_percent=pct,
                    scraped_count=total_cnt,
                    message=f"Hoàng Hà (Điện thoại): {cnt} SP...",
                )

            hh_phones = scraper_hh.scrape_category("phone", limit=limit, on_progress=on_hh_phone_progress)

            cls.update_task_progress(
                task_id,
                status="RUNNING",
                progress_percent=63,
                scraped_count=total_cps + len(hh_phones),
                message=f"[2/4] Hoàng Hà Phone xong ({len(hh_phones)} SP). Đang cào Hoàng Hà Laptop...",
            )

            def on_hh_laptop_progress(p, tp, cnt, msg=None):
                total_cnt = total_cps + len(hh_phones) + cnt
                pct = min(75, 63 + int((cnt / 200) * 12)) if cnt else 63
                cls.update_task_progress(
                    task_id,
                    status="RUNNING",
                    progress_percent=pct,
                    scraped_count=total_cnt,
                    message=f"Hoàng Hà (Laptop): {cnt} SP...",
                )

            hh_laptops = scraper_hh.scrape_category("laptop", limit=limit, on_progress=on_hh_laptop_progress)

            # Khử trùng lặp URL cho Hoàng Hà
            unique_hh = []
            seen_hh_urls = set()
            for it in (hh_phones + hh_laptops):
                if it.url not in seen_hh_urls:
                    seen_hh_urls.add(it.url)
                    unique_hh.append(it)
            hh_items = unique_hh
            total_hh = len(hh_items)

            all_items = cps_items + hh_items
            total_all = len(all_items)

            # --- GIAI ĐOẠN 3: LƯU CSDL (75% -> 85%) ---
            cls.update_task_progress(
                task_id,
                status="RUNNING",
                progress_percent=78,
                scraped_count=total_all,
                message=f"[3/4] Đã cào xong {total_all:,} sản phẩm (CPS: {total_cps:,}, HH: {total_hh:,}). Đang lưu CSDL...",
            )

            db: Session = db_session_factory()
            try:
                stats = cls.save_scraped_items_upsert(all_items, db=db, job_id=job_uuid)
                logger.info(f"[Full Pipeline] Đã lưu DB: {stats['inserted']} mới, {stats['updated']} cập nhật.")

                # Dọn dẹp bản ghi cũ > 60 ngày chưa map
                try:
                    cls.cleanup_stale_crawl_results(days=60, db=db)
                except Exception as clean_err:
                    logger.warning(f"Lỗi dọn dẹp stale crawl: {clean_err}")

                # --- GIAI ĐOẠN 4: ĐỐI SOÁT SKU & XUẤT EXCEL & ĐỒNG BỘ SKU_MAPPINGS (85% -> 100%) ---
                cls.update_task_progress(
                    task_id,
                    status="RUNNING",
                    progress_percent=85,
                    scraped_count=total_all,
                    message="[4/4] Đang đối soát với 329 SKU FPT Shop và xuất báo cáo Excel...",
                )

                # Chuyển đổi dữ liệu sang định dạng dictionary cho SkuMatcher
                def to_dict_list(items, source_label):
                    res = []
                    now_str = get_vietnam_now().strftime("%Y-%m-%d %H:%M:%S")
                    for it in items:
                        specs = it.specifications or {}
                        res.append({
                            "Nguồn": it.source or source_label,
                            "Tên sản phẩm cào được": it.product_name,
                            "Giá bán đối thủ (VND)": it.current_price,
                            "Giá niêm yết (VND)": it.original_price or it.current_price,
                            "Còn hàng": "Còn hàng" if it.is_in_stock else "Hết hàng",
                            "Thông số kỹ thuật tóm tắt": specs.get("summary", "N/A"),
                            "URL sản phẩm": it.url,
                            "Thời gian cào": now_str,
                        })
                    return res

                dict_cps = to_dict_list(cps_items, "CellphoneS")
                dict_hh = to_dict_list(hh_items, "HOANGHA")

                backend_dir = Path(__file__).resolve().parent.parent.parent
                data_dir = backend_dir / "data"
                data_dir.mkdir(parents=True, exist_ok=True)
                dim_prod_path = str(data_dir / "dim_product.xlsx")
                demand_path = str(data_dir / "demand_events_20260723.xlsx")
                output_excel_path = str(data_dir / "crawl_and_sku_mapping_output.xlsx")

                # Lưu cache JSON
                try:
                    import json
                    with open(data_dir / "scraped_products_cellphones.json", "w", encoding="utf-8") as f:
                        json.dump(dict_cps, f, ensure_ascii=False, indent=2)
                    with open(data_dir / "scraped_products_hoangha.json", "w", encoding="utf-8") as f:
                        json.dump(dict_hh, f, ensure_ascii=False, indent=2)
                except Exception as cache_err:
                    logger.warning(f"Lỗi lưu cache JSON: {cache_err}")

                # Chạy SkuMatcher xuất Excel 3 sheets
                from app.services.sku_matcher import SkuMatcher
                matcher = SkuMatcher(
                    dim_product_path=dim_prod_path,
                    demand_events_path=demand_path
                )
                matcher.match_multi_sources(
                    cellphones_items=dict_cps,
                    hoangha_items=dict_hh,
                    output_excel_path=output_excel_path
                )

                cls.update_task_progress(
                    task_id,
                    status="RUNNING",
                    progress_percent=90,
                    scraped_count=total_all,
                    message="[4/4] Đã xuất báo cáo Excel. Đang chuẩn bị đồng bộ vào Cơ sở dữ liệu...",
                )

                # Kiểm tra và tự động nạp danh mục chuẩn nếu bảng products rỗng
                if db.query(Product).count() == 0:
                    logger.info("[Full Pipeline] Bảng products rỗng, tiến hành nạp danh mục từ dim_product.xlsx...")
                    try:
                        from app.services.seeder import seed_catalog_and_inventory
                        seed_catalog_and_inventory(db)
                        db.commit()
                    except Exception as seed_err:
                        logger.warning(f"[Full Pipeline] Không thể tự động seed danh mục: {seed_err}")

                cls.update_task_progress(
                    task_id,
                    status="RUNNING",
                    progress_percent=95,
                    scraped_count=total_all,
                    message="[4/4] Đang đối soát và ghi kết quả vào CSDL (sku_mappings)...",
                )

                # Đồng bộ kết quả đối soát vào bảng sku_mappings trong CSDL
                from app.services.matching_persistence import run_sku_matching_and_persist
                run_sku_matching_and_persist(db=db, overwrite_existing=True)

                # Thống kê kết quả ghép cặp SKU
                total_fpt = db.query(Product).count() or 329
                mapped_fpt = db.query(SkuMapping.fpt_product_id).distinct().count()
                match_pct = round((mapped_fpt / total_fpt) * 100, 1) if total_fpt else 0

                cls.update_task_progress(
                    task_id,
                    status="COMPLETED",
                    progress_percent=100,
                    scraped_count=total_all,
                    message=(
                        f"Hoàn tất! Đã thu thập {total_all:,} sản phẩm đối thủ (CPS: {total_cps:,}, HH: {total_hh:,}). "
                        f"Ghép cặp thành công {mapped_fpt}/{total_fpt} SKU FPT Shop ({match_pct}%)."
                    ),
                )
                cls._update_crawl_job_record(
                    db=db,
                    task_id=str(task_id),
                    status="COMPLETED",
                    total_items=total_all,
                    success_items=stats["inserted"] + stats["updated"],
                    error_items=max(0, total_all - (stats["inserted"] + stats["updated"])),
                )
            except Exception as e:
                db.rollback()
                logger.error(f"[Full Pipeline] Lỗi lưu DB / so khớp: {e}", exc_info=True)
                cls.update_task_progress(
                    task_id,
                    status="FAILED",
                    error=str(e),
                    message=f"Lỗi khi lưu dữ liệu hoặc đối soát: {e}",
                )
                cls._update_crawl_job_record(
                    db=db,
                    task_id=str(task_id),
                    status="FAILED",
                    error_log=str(e),
                )
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[Full Pipeline] Lỗi khi cào dữ liệu: {e}", exc_info=True)
            cls.update_task_progress(
                task_id,
                status="FAILED",
                error=str(e),
                message=f"Lỗi trong quá trình cào Full Pipeline: {e}",
            )
            db_err_session: Session = db_session_factory()
            try:
                cls._update_crawl_job_record(
                    db=db_err_session,
                    task_id=str(task_id),
                    status="FAILED",
                    error_log=str(e),
                )
            finally:
                db_err_session.close()

    @classmethod
    def trigger_crawl(cls, request: CrawlTriggerRequest, background_tasks, db_session_factory) -> CrawlJobResponse:
        """Interface gọi cào dữ liệu từ API controller."""
        task_id = str(uuid.uuid4())
        job_uuid = uuid.UUID(task_id)

        is_full = request.source.value in ["full_pipeline", "all"]
        source_label = "FULL_PIPELINE" if is_full else request.source.value.upper()
        category_label = "ALL" if is_full else request.category.value

        # Khởi tạo bản ghi CrawlJob trong CSDL để lưu vết lịch sử bền vững
        db: Session = db_session_factory()
        try:
            job_rec = CrawlJob(
                id=job_uuid,
                trigger_type="ON_DEMAND",
                source=source_label,
                category=category_label.upper(),
                status="PENDING",
                started_at=get_vietnam_now(),
            )
            db.add(job_rec)
            db.commit()
        except Exception as db_err:
            logger.warning(f"Không thể khởi tạo bản ghi CrawlJob trong DB: {db_err}")
            db.rollback()
        finally:
            db.close()

        # Khởi tạo trạng thái ban đầu của task trên RAM
        cls._tasks[task_id] = {
            "task_id": task_id,
            "source": source_label,
            "category": category_label,
            "status": "PENDING",
            "current_page": 0,
            "total_pages": 1,
            "scraped_count": 0,
            "progress_percent": 0,
            "message": f"Đã tiếp nhận yêu cầu {source_label} ({category_label}). Đang chuẩn bị...",
            "started_at": to_vietnam_iso(),
            "completed_at": None,
            "error": None,
        }

        target_fn = cls.execute_full_pipeline_job if is_full else cls.execute_crawl_job

        # Đưa vào FastAPI BackgroundTasks chạy bất đồng bộ ngầm
        background_tasks.add_task(
            target_fn,
            task_id,
            request,
            db_session_factory,
        )

        return CrawlJobResponse(
            task_id=task_id,
            status="PROCESSING",
            message=f"Đã tiếp nhận yêu cầu cào giá {source_label}. Đang xử lý ngầm.",
        )

    @classmethod
    def save_scraped_items_upsert(
        cls,
        items: List[ScrapedProductItem],
        db: Session,
        job_id: Optional[uuid.UUID] = None
    ) -> Dict[str, int]:
        """Lưu danh sách sản phẩm cào được vào CSDL theo cơ chế UPSERT:
        1. Tìm kiếm theo URL xem đã tồn tại trong CSDL chưa.
        2. Nếu đã có: Cập nhật tại chỗ (giữ nguyên ID để bảo toàn SkuMapping liên kết).
           - Nếu giá thay đổi (old_price != new_price) và sản phẩm đã map SKU, tự động ghi 1 dòng log vào PriceHistory.
           - Cập nhật job_id để liên kết đợt cào mới nhất.
        3. Nếu chưa có: Thêm mới bản ghi CrawlResult gắn kèm job_id.
        4. Trả về dict thống kê {"inserted": X, "updated": Y}.
        """
        if not items:
            return {"inserted": 0, "updated": 0}

        # Khử trùng lặp URL trong chính lô items hiện tại (lấy bản ghi cuối cùng của mỗi URL)
        deduped_items = {}
        for it in items:
            u = it.url if hasattr(it, "url") else it.get("url")
            if u:
                deduped_items[u] = it

        urls = list(deduped_items.keys())
        existing_records = db.query(CrawlResult).filter(CrawlResult.url.in_(urls)).all()
        existing_map = {r.url: r for r in existing_records}

        inserted_count = 0
        updated_count = 0
        now_dt = get_vietnam_now()

        for url, item in deduped_items.items():
            source = getattr(item, "source", None) or (item.get("source") if isinstance(item, dict) else "")
            product_name = getattr(item, "product_name", None) or (item.get("product_name") if isinstance(item, dict) else "")
            current_price = getattr(item, "current_price", None) or (item.get("current_price") if isinstance(item, dict) else None)
            original_price = getattr(item, "original_price", None) or (item.get("original_price") if isinstance(item, dict) else None)
            is_in_stock = getattr(item, "is_in_stock", True) if hasattr(item, "is_in_stock") else item.get("is_in_stock", True)
            stock_status_text = getattr(item, "stock_status_text", None) or (item.get("stock_status_text") if isinstance(item, dict) else None)
            specs = getattr(item, "specifications", None) or (item.get("specifications") if isinstance(item, dict) else {})

            norm_source = (source or "").upper()

            if url in existing_map:
                record = existing_map[url]
                old_price = record.current_price
                new_price = current_price

                # Kiểm tra biến động giá để ghi PriceHistory nếu đã map SKU
                price_changed = (old_price is not None and new_price is not None and old_price != new_price)
                if price_changed and record.mappings:
                    for m in record.mappings:
                        hist_log = PriceHistory(
                            id=uuid.uuid4(),
                            fpt_product_id=m.fpt_product_id,
                            source=record.source or norm_source,
                            price=new_price,
                            is_in_stock=bool(is_in_stock),
                            recorded_at=now_dt,
                        )
                        db.add(hist_log)

                # Cập nhật tại chỗ
                if job_id is not None:
                    record.job_id = job_id
                record.raw_name = product_name or record.raw_name
                record.current_price = current_price
                record.original_price = original_price
                record.is_in_stock = is_in_stock
                if stock_status_text:
                    record.stock_status_text = stock_status_text
                record.raw_specs = specs or record.raw_specs
                record.crawled_at = now_dt

                updated_count += 1
            else:
                new_rec = CrawlResult(
                    id=uuid.uuid4(),
                    job_id=job_id,
                    source=norm_source,
                    url=url,
                    raw_name=product_name or "Chưa cập nhật tên",
                    current_price=current_price,
                    original_price=original_price,
                    is_in_stock=is_in_stock,
                    stock_status_text=stock_status_text,
                    raw_specs=specs,
                    crawled_at=now_dt,
                )
                db.add(new_rec)
                existing_map[url] = new_rec
                inserted_count += 1

        db.commit()
        return {"inserted": inserted_count, "updated": updated_count}

    @classmethod
    def cleanup_stale_crawl_results(cls, days: int = 60, db: Session = None) -> int:
        """Dọn dẹp các bản ghi CrawlResult cũ (> days ngày) mà CHƯA TỪNG ĐƯỢC MAP vào SKU FPT nào.
        Bảo toàn 100% các bản ghi đã map để phục vụ so khớp và phân tích lịch sử.
        """
        if db is None:
            return 0

        cutoff = get_vietnam_now() - timedelta(days=days)
        mapped_crawl_ids = [row[0] for row in db.query(SkuMapping.competitor_crawl_id).all() if row[0]]

        query = db.query(CrawlResult).filter(CrawlResult.crawled_at < cutoff)
        if mapped_crawl_ids:
            query = query.filter(~CrawlResult.id.in_(mapped_crawl_ids))

        stale_records = query.all()
        deleted_count = len(stale_records)

        for rec in stale_records:
            db.delete(rec)

        db.commit()
        return deleted_count
