"""Script khởi tạo dữ liệu danh mục sản phẩm (Product Catalog) và kho bãi FPT Shop."""

import sys
import logging
from pathlib import Path

# Đảm bảo import được app package
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal, Base, engine
from app.models.product import Product
from app.services.seeder import seed_catalog_and_inventory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_products")


def main():
    logger.info("Đang kiểm tra và khởi tạo các bảng CSDL nếu chưa có...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        logger.info("Đang nạp danh mục sản phẩm FPT từ backend/data/dim_product.xlsx...")
        counts = seed_catalog_and_inventory(db)
        logger.info(f"Kết quả nạp: {counts}")

        total_products = db.query(Product).count()
        print("\n" + "=" * 55)
        print(f" KHỞI TẠO THÀNH CÔNG: {total_products} SẢN PHẨM TRONG BẢNG PRODUCT")
        print(f" Chi tiết nạp: {counts}")
        print("=" * 55 + "\n")
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi khi nạp dữ liệu: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
