"""Service đồng bộ giá bán thực tế từ website FPT Shop vào cơ sở dữ liệu.

Thực hiện đối soát SKU 2 tầng:
1. Tầng 1: So khớp mã Part-Number chính xác (đặc biệt cho Laptop).
2. Tầng 2: So khớp Fuzzy Matching trên tên sản phẩm bằng RapidFuzz (ngưỡng >= 75%).

Cập nhật giá bán, giá vốn (85%), giá sàn (105% giá vốn), ghi vết PriceHistory
và tự động kích hoạt PricingEngine tái tính toán đề xuất giá.
Áp dụng Phương án B: Các sản phẩm không còn xuất hiện trên web FPT Shop sẽ
được đánh dấu is_active = False (ngừng kinh doanh).
"""

import logging
from typing import Any, Dict, List, Optional, Union
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.models.inventory import InventoryMock
from app.models.pricing import PriceHistory
from app.models.product import Product
from app.schemas.crawl import ScrapedProductItem
from app.services.pricing.engine import PricingEngine
from app.services.scrapers.fpt import FptShopScraper
from app.utils.datetime_utils import get_vietnam_now

logger = logging.getLogger(__name__)


class FptPriceSyncService:
    """Service đối soát và đồng bộ giá bán trực tiếp từ FPT Shop về hệ thống."""

    def __init__(
        self,
        scraper: Optional[FptShopScraper] = None,
        pricing_engine: Optional[PricingEngine] = None,
    ) -> None:
        """Khởi tạo service với scraper và pricing engine tương ứng."""
        self.scraper = scraper or FptShopScraper()
        self.pricing_engine = pricing_engine or PricingEngine()

    def sync_live_prices(
        self_or_cls,
        db: Session,
        scraped_items: Optional[List[ScrapedProductItem]] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """Thực hiện đồng bộ giá real-time từ FPT Shop vào bảng Product và PriceHistory.

        Args:
            db: SQLAlchemy Session kết nối cơ sở dữ liệu.
            scraped_items: Danh sách sản phẩm đã cào từ trước (nếu None, sẽ tự cào qua FptShopScraper).
            auto_commit: Tự động commit transaction sau khi cập nhật nếu True.

        Returns:
            Dict chứa các chỉ số thống kê kết quả đồng bộ.
        """
        # Hỗ trợ gọi cả dưới dạng method thể hiện (instance) lẫn class/static method
        if isinstance(self_or_cls, FptPriceSyncService):
            self = self_or_cls
        else:
            self = FptPriceSyncService()

        # 1. Thu thập dữ liệu cào nếu chưa được cung cấp
        if scraped_items is None:
            logger.info("Chưa có scraped_items, khởi tạo FptShopScraper và cào toàn bộ danh mục...")
            scraped_items = self.scraper.scrape_category("all") or []

        # 2. Lấy toàn bộ danh mục sản phẩm từ CSDL
        products = db.query(Product).all()
        total_catalog = len(products)
        logger.info(
            f"Bắt đầu đối soát giá cho {total_catalog} sản phẩm với {len(scraped_items)} item cào được từ FPT Shop..."
        )

        matched_count = 0
        price_updated_count = 0
        deactivated_count = 0
        recalculated_count = 0
        unmatched_skus: List[str] = []

        now_vn = get_vietnam_now()

        # 3. Tiến hành đối soát và cập nhật từng sản phẩm
        for prod in products:
            best_match: Optional[ScrapedProductItem] = None
            best_score = 0.0

            # Tầng 1: So khớp mã Part-Number chính xác (nếu part_number có độ dài >= 4)
            if prod.part_number and len(prod.part_number.strip()) >= 4:
                p_lower = prod.part_number.strip().lower()
                for item in scraped_items:
                    item_name_lower = (item.product_name or "").lower()
                    in_name = p_lower in item_name_lower

                    in_specs = False
                    if item.specifications and isinstance(item.specifications, dict):
                        in_specs = any(p_lower in str(v).lower() for v in item.specifications.values())

                    if in_name or in_specs:
                        best_match = item
                        best_score = 100.0
                        break

            # Tầng 2: So khớp Fuzzy Matching trên tên sản phẩm nếu chưa khớp Part-Number
            if not best_match:
                prod_name_lower = (prod.name or "").lower()
                for item in scraped_items:
                    item_name_lower = (item.product_name or "").lower()
                    score = fuzz.token_sort_ratio(prod_name_lower, item_name_lower)
                    if score > best_score and score >= 75.0:
                        best_score = float(score)
                        best_match = item

            # Xử lý trường hợp SẢN PHẨM KHỚP (Matched)
            if best_match and best_match.current_price and best_match.current_price > 0:
                matched_count += 1
                prod.is_active = True
                new_price = int(best_match.current_price)

                # Kiểm tra nếu giá bán có sự thay đổi
                if prod.base_retail_price != new_price:
                    price_updated_count += 1
                    old_price = int(prod.base_retail_price or 0)

                    prod.base_retail_price = new_price
                    prod.cost_price = int(new_price * 0.85)
                    prod.floor_price = int(prod.cost_price * 1.05)
                    prod.updated_at = now_vn

                    # Cập nhật thông tin giá vốn và giá sàn trên bảng InventoryMock nếu có
                    inv = db.query(InventoryMock).filter(InventoryMock.fpt_product_id == prod.id).first()
                    if inv:
                        inv.cost_price = prod.cost_price
                        inv.floor_price = prod.floor_price

                    # Thêm bản ghi theo dõi biến động giá vào PriceHistory
                    p_change = new_price - old_price
                    p_change_percent = (
                        round(((new_price - old_price) / old_price) * 100, 2)
                        if old_price > 0
                        else 0.0
                    )
                    hist = PriceHistory(
                        fpt_product_id=prod.id,
                        source="FPTSHOP",
                        price=new_price,
                        old_price=old_price,
                        new_price=new_price,
                        price_change=p_change,
                        price_change_percent=p_change_percent,
                        cost_price=prod.cost_price,
                        floor_price=prod.floor_price,
                        change_type="REALTIME_CRAWL",
                        scenario="Đồng bộ giá trực tiếp từ website FPT Shop",
                        changed_by="FPT Realtime Crawler",
                        changed_at=now_vn,
                        status="SYNCED_POS",
                    )
                    db.add(hist)

                # Tái tính toán đề xuất giá thông qua PricingEngine
                try:
                    self.pricing_engine.generate_for_product(db, prod.id)
                    recalculated_count += 1
                except Exception as ex:
                    logger.warning(
                        f"Lỗi khi tái tính toán khuyến nghị giá cho SKU {prod.sku} (id={prod.id}): {ex}"
                    )

            else:
                # Xử lý trường hợp SẢN PHẨM KHÔNG KHỚP (Unmatched) - Phương án B
                deactivated_count += 1
                unmatched_skus.append(prod.sku)
                prod.is_active = False
                logger.info(
                    f"Sản phẩm {prod.sku} ({prod.name}) không còn xuất hiện trên FPT Shop -> Đánh dấu is_active = False"
                )

        if auto_commit:
            db.commit()

        logger.info(
            f"Hoàn tất đồng bộ giá FPT Shop: Tổng {total_catalog} SP | "
            f"Khớp: {matched_count} | Cập nhật giá: {price_updated_count} | "
            f"Deactivated: {deactivated_count} | Tính lại giá: {recalculated_count}"
        )

        return {
            "total_catalog": total_catalog,
            "matched_count": matched_count,
            "price_updated_count": price_updated_count,
            "deactivated_count": deactivated_count,
            "recalculated_count": recalculated_count,
            "unmatched_skus": unmatched_skus,
        }

