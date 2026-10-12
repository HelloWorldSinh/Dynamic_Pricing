"""Script thực thi toàn trình End-to-End Pipeline trên Cơ sở dữ liệu SQLite thật.

Luồng thực thi:
1. Seed danh mục 329 SKU chuẩn FPT, kho bãi, tồn kho và nhu cầu khách hàng từ backend/data/.
2. Đối soát & so khớp 2 tầng giữa 5,616 sản phẩm cào đối thủ và 329 SKU FPT -> lưu vào sku_mappings.
3. Kích hoạt Pricing Engine tính toán tín hiệu D, I, C, Composite Score và sinh đề xuất giá -> lưu vào price_recommendations.
4. Mô phỏng phê duyệt một số đề xuất, lưu vết kiểm toán vào pricing_audit_logs và lưu biến động vào price_history.
5. Xuất bảng thống kê số lượng bản ghi thực tế của từng bảng.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

# Đảm bảo import được app package
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal, engine, Base
from app.models.product import Product
from app.models.inventory import Warehouse, InventoryMock, InventorySnapshot
from app.models.demand import DemandEvent, DemandHourlyAggregate
import json
import uuid
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.models.pricing import PriceRecommendation, PricingAuditLog, PriceHistory
from app.services.seeder import seed_catalog_and_inventory
from app.services.matching_persistence import run_sku_matching_and_persist
from app.services.pricing import PricingEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("e2e_pipeline")


def ingest_scraped_json(db, data_dir: Path):
    """Nạp danh sách sản phẩm cào được từ file cache JSON vào bảng crawl_results."""
    cps_file = data_dir / "scraped_products_cellphones.json"
    hh_file = data_dir / "scraped_products_hoangha.json"
    existing_urls = {r[0] for r in db.query(CrawlResult.url).all()}

    items_to_add = []
    for fpath, src in [(cps_file, "CELLPHONES"), (hh_file, "HOANGHA")]:
        if not fpath.exists():
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            url = item.get("URL sản phẩm") or item.get("url")
            if not url or url in existing_urls:
                continue
            existing_urls.add(url)
            price = item.get("Giá bán đối thủ (VND)") or item.get("current_price")
            orig_price = item.get("Giá niêm yết (VND)") or item.get("original_price")
            stock_text = item.get("Còn hàng") or item.get("stock_status_text") or ("Còn hàng" if item.get("is_in_stock", True) else "Hết hàng")
            if "is_in_stock" in item:
                is_stock = bool(item["is_in_stock"])
            elif "Còn hàng" in item:
                val = item["Còn hàng"]
                if isinstance(val, bool):
                    is_stock = val
                elif isinstance(val, str):
                    is_stock = val.strip().lower() in ("còn hàng", "true", "1", "available", "in_stock")
                else:
                    is_stock = bool(val)
            else:
                is_stock = True
            name = item.get("Tên sản phẩm cào được") or item.get("product_name") or "Unknown"

            c_res = CrawlResult(
                id=uuid.uuid4(),
                source=src,
                url=url,
                raw_name=name,
                current_price=int(price) if price else None,
                original_price=int(orig_price) if orig_price else None,
                is_in_stock=is_stock,
                stock_status_text=str(stock_text),
                raw_specs={"summary": item.get("Thông số kỹ thuật tóm tắt", "")},
                crawled_at=datetime.now(timezone.utc),
            )
            items_to_add.append(c_res)
            if len(items_to_add) >= 500:
                db.bulk_save_objects(items_to_add)
                db.commit()
                items_to_add = []

    if items_to_add:
        db.bulk_save_objects(items_to_add)
        db.commit()


def run_pipeline():
    logger.info("=== BẮT ĐẦU CHẠY E2E DATA PIPELINE TRÊN SQLITE THẬT ===")
    db = SessionLocal()

    try:
        # 1. Đảm bảo toàn bộ bảng đã được khởi tạo
        Base.metadata.create_all(bind=engine)

        # 2. Bước 1: Seed danh mục và tồn kho
        logger.info("[1/4] Đang nạp danh mục sản phẩm FPT, tồn kho ERP và clickstream...")
        seed_res = seed_catalog_and_inventory(db)
        logger.info(f"-> Hoàn thành Seed: {seed_res}")

        # Bước 1b: Nạp toàn bộ crawl_results từ cache JSON
        data_dir = BACKEND_DIR / "data"
        ingest_scraped_json(db, data_dir)
        total_crawls = db.query(CrawlResult).count()
        logger.info(f"-> Tổng số bản ghi crawl_results sau khi nạp: {total_crawls}")

        # 3. Bước 2: So khớp SKU đối thủ vào bảng sku_mappings
        logger.info("[2/4] Đang thực hiện so khớp 2 tầng với dữ liệu cào đối thủ...")
        matched_new = run_sku_matching_and_persist(db)
        total_mappings = db.query(SkuMapping).count()
        logger.info(f"-> Đã so khớp mới {matched_new} cặp, tổng số bản ghi sku_mappings: {total_mappings}")

        # 4. Bước 3: Kích hoạt Pricing Engine sinh đề xuất giá
        logger.info("[3/4] Đang kích hoạt Pricing Engine sinh đề xuất giá cho toàn bộ SKU active...")
        pricing_engine = PricingEngine()
        recs = pricing_engine.generate_batch(db)
        total_recs = db.query(PriceRecommendation).count()
        logger.info(f"-> Đã sinh {len(recs)} đề xuất giá. Tổng số đề xuất trong price_recommendations: {total_recs}")

        # 5. Bước 4: Mô phỏng phê duyệt một số đề xuất mẫu
        logger.info("[4/4] Mô phỏng phê duyệt mẫu 5 đề xuất giá...")
        sample_pending = (
            db.query(PriceRecommendation)
            .filter(PriceRecommendation.status == "PENDING")
            .limit(5)
            .all()
        )
        approved_count = 0
        for rec in sample_pending:
            rec.status = "APPROVED"
            rec.reviewed_by = "Head of Pricing"
            rec.reviewed_at = datetime.now(timezone.utc)

            audit_log = PricingAuditLog(
                actor="Head of Pricing",
                action="APPROVE_PRICE",
                entity_type="price_recommendations",
                entity_id=rec.id,
                old_value={"status": "PENDING"},
                new_value={
                    "status": "APPROVED",
                    "recommended_price": rec.recommended_price,
                    "price_delta_pct": rec.price_delta_pct,
                },
            )
            db.add(audit_log)

            # Ghi vào price_history
            p_hist = PriceHistory(
                fpt_product_id=rec.fpt_product_id,
                source="FPTSHOP",
                price=rec.recommended_price,
                is_in_stock=True,
                recorded_at=datetime.now(timezone.utc),
            )
            db.add(p_hist)
            approved_count += 1

        db.commit()
        logger.info(f"-> Đã phê duyệt {approved_count} đề xuất mẫu và ghi vết kiểm toán thành công.")

        # 6. Báo cáo tổng kết dữ liệu thực tế
        print("\n" + "=" * 65)
        print("          BAO CAO TONG KET CO SO DU LIEU SQLITE")
        print("=" * 65)
        table_stats = [
            ("products", db.query(Product).count()),
            ("warehouses", db.query(Warehouse).count()),
            ("inventory_mock", db.query(InventoryMock).count()),
            ("inventory_snapshots", db.query(InventorySnapshot).count()),
            ("demand_events", db.query(DemandEvent).count()),
            ("crawl_results", db.query(CrawlResult).count()),
            ("sku_mappings", db.query(SkuMapping).count()),
            ("price_recommendations", db.query(PriceRecommendation).count()),
            ("pricing_audit_logs", db.query(PricingAuditLog).count()),
            ("price_history", db.query(PriceHistory).count()),
        ]
        print(f"{'Ten Bang CSDL':<28} | {'So luong ban ghi':<20}")
        print("-" * 65)
        for tbl, count in table_stats:
            print(f"{tbl:<28} | {count:<20,}")
        print("=" * 65)
        print("Trang thai: HOAN TAT VA SAN SANG KET NOI API & GIAO DIEN.\n")

    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi khi thực thi pipeline: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_pipeline()
