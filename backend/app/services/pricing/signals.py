from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.product import Product
from app.models.inventory import InventoryMock, InventorySnapshot
from app.models.demand import DemandHourlyAggregate, DemandEvent
from app.models.sku_mapping import SkuMapping
from app.models.crawl_result import CrawlResult
from app.services.pricing.schemas import SignalScores


class SignalsExtractor:
    """Trích xuất và chuẩn hóa 3 nhóm tín hiệu thị trường D, I, C từ cơ sở dữ liệu."""

    def calculate_demand_score(self, db: Session, product_id: UUID) -> float:
        """Tính điểm Demand Score D (-2.0 đến +2.0)."""
        # Ưu tiên lấy từ bảng DemandHourlyAggregate gần nhất
        latest_agg = (
            db.query(DemandHourlyAggregate)
            .filter(DemandHourlyAggregate.fpt_product_id == product_id)
            .order_by(desc(DemandHourlyAggregate.aggregate_hour))
            .first()
        )
        if latest_agg is not None and latest_agg.demand_score is not None:
            return round(float(latest_agg.demand_score), 2)

        # Fallback phân tích các sự kiện clickstream DemandEvent gần nhất
        events = (
            db.query(DemandEvent)
            .filter(DemandEvent.fpt_product_id == product_id)
            .order_by(desc(DemandEvent.event_ts))
            .limit(100)
            .all()
        )
        if not events:
            return 0.0

        total_views = sum(1 for e in events if e.event_type == "view")
        purchases = sum(1 for e in events if e.event_type == "purchase")
        cart_adds = sum(1 for e in events if e.event_type == "cart_add")
        bounces = sum(1 for e in events if e.is_bounce)

        if total_views > 0:
            cvr = (purchases / total_views) * 100.0
            bounce_rate = (bounces / total_views) * 100.0

            if cvr > 5.0 or cart_adds > 10:
                return 2.0
            if cvr > 3.0 or cart_adds > 5:
                return 1.0
            if bounce_rate > 75.0 or cvr < 0.5:
                return -2.0
            if bounce_rate > 50.0:
                return -1.0

        return 0.0

    def calculate_inventory_score(self, db: Session, product_id: UUID) -> float:
        """Tính điểm Inventory Score I (-2.0 đến +2.0)."""
        # Kiểm tra bảng chi tiết InventorySnapshot trước
        latest_snap = (
            db.query(InventorySnapshot)
            .filter(InventorySnapshot.fpt_product_id == product_id)
            .order_by(desc(InventorySnapshot.snapshot_ts))
            .first()
        )

        if latest_snap is not None:
            if latest_snap.is_obsolescence_risk:
                return -2.0
            if latest_snap.stock_cover_days > 45:
                return -2.0
            if latest_snap.stock_cover_days < 7 or latest_snap.competitor_oos_count > 0:
                return 2.0

            if latest_snap.target_stock > 0:
                ratio = latest_snap.qty_available / latest_snap.target_stock
                if ratio > 1.5:
                    return -2.0
                if ratio > 1.1:
                    return -1.0
                if ratio < 0.3:
                    return 2.0
                if ratio < 0.6:
                    return 1.0
            return 0.0

        # Fallback kiểm tra bảng InventoryMock
        inv_mock = (
            db.query(InventoryMock)
            .filter(InventoryMock.fpt_product_id == product_id)
            .first()
        )
        if inv_mock is not None:
            if inv_mock.doh > 45:
                return -2.0
            if inv_mock.doh < 7:
                return 2.0
            if inv_mock.doh <= 15:
                return 1.0
            if inv_mock.doh >= 35:
                return -1.0
            return 0.0

        return 0.0

    def calculate_competitor_score(self, db: Session, product_id: UUID) -> float:
        """Tính điểm Competitor Score C (-2.0 đến +2.0)."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product or not product.base_retail_price:
            return 0.0

        mappings = (
            db.query(SkuMapping)
            .filter(
                SkuMapping.fpt_product_id == product_id,
                SkuMapping.status.in_(["APPROVED", "AUTO_MATCHED"]),
            )
            .all()
        )
        if not mappings:
            return 0.0

        scraped_ids = [m.competitor_crawl_id for m in mappings]
        competitor_results = (
            db.query(CrawlResult)
            .filter(CrawlResult.id.in_(scraped_ids))
            .all()
        )
        if not competitor_results:
            return 0.0

        # Nếu tất cả đối thủ đều hết hàng -> Tín hiệu khan hiếm C = +2.0
        all_oos = all(not r.is_in_stock for r in competitor_results)
        if all_oos:
            return 2.0

        # Lọc danh sách đối thủ còn hàng có giá hợp lệ
        in_stock_prices = [
            r.current_price for r in competitor_results
            if r.is_in_stock and r.current_price is not None and r.current_price > 0
        ]
        if not in_stock_prices:
            return 2.0

        min_competitor_price = min(in_stock_prices)
        diff_pct = (min_competitor_price - product.base_retail_price) / product.base_retail_price

        if diff_pct > 0.15:
            return 2.0
        if diff_pct >= 0.05:
            return 1.0
        if -0.05 <= diff_pct < 0.05:
            return 0.0
        if -0.15 <= diff_pct < -0.05:
            return -1.0
        return -2.0

    def extract_signals(self, db: Session, product_id: UUID) -> SignalScores:
        """Trích xuất toàn bộ 3 điểm số tín hiệu thị trường."""
        d_score = self.calculate_demand_score(db, product_id)
        i_score = self.calculate_inventory_score(db, product_id)
        c_score = self.calculate_competitor_score(db, product_id)
        return SignalScores(
            demand_score=d_score,
            inventory_score=i_score,
            competitor_score=c_score,
        )

    def extract_reasoning_details(self, db: Session, product_id: UUID) -> Dict[str, Any]:
        """Tạo dữ liệu giải trình 3 lớp định lượng cho RAG và chuyên viên giá."""
        # 1. Competitor factor
        c_score = self.calculate_competitor_score(db, product_id)
        product = db.query(Product).filter(Product.id == product_id).first()
        fpt_price = product.base_retail_price if product else 0

        mappings = (
            db.query(SkuMapping)
            .filter(SkuMapping.fpt_product_id == product_id)
            .all()
        )
        scraped_ids = [m.competitor_crawl_id for m in mappings]
        c_items = (
            db.query(CrawlResult)
            .filter(CrawlResult.id.in_(scraped_ids))
            .all()
        ) if scraped_ids else []

        if not c_items:
            comp_factor = "Chua co du lieu gia doi thu doi soat."
        else:
            in_stock = [item for item in c_items if item.is_in_stock and item.current_price]
            if not in_stock:
                comp_factor = "Tat ca doi thu chinh (CellphoneS, Hoang Ha) deu dang het hang (Out-of-Stock)."
            else:
                cheapest = min(in_stock, key=lambda x: x.current_price)
                diff_amount = cheapest.current_price - fpt_price
                diff_pct = (diff_amount / fpt_price) * 100 if fpt_price else 0
                if diff_pct < 0:
                    comp_factor = f"Doi thu {cheapest.source} dang ban re hon {abs(diff_pct):.1f}% ({abs(diff_amount):,} VND)."
                else:
                    comp_factor = f"Doi thu {cheapest.source} dang ban cao hon {diff_pct:.1f}% ({diff_amount:,} VND)."


        # 2. Inventory factor
        inv = db.query(InventoryMock).filter(InventoryMock.fpt_product_id == product_id).first()
        snap = db.query(InventorySnapshot).filter(InventorySnapshot.fpt_product_id == product_id).order_by(desc(InventorySnapshot.snapshot_ts)).first()
        doh = snap.stock_cover_days if snap else (inv.doh if inv else 0)
        qty = snap.qty_available if snap else (inv.stock_quantity if inv else 0)

        if snap and snap.is_obsolescence_risk:
            inv_factor = f"Canh bao hang ton kho loi thoi (DOH={doh} ngay, so luong={qty})."
        elif doh > 45:
            inv_factor = f"Hang ton kho u dong cao (DOH={doh} ngay > 45 ngay, luong ton={qty})."
        elif doh < 7 and doh > 0:
            inv_factor = f"Hang khan hiem sap het (DOH={doh} ngay < 7 ngay, luong ton={qty})."
        else:
            inv_factor = f"Ton kho on dinh (DOH={doh} ngay, luong ton kha dung={qty})."

        # 3. Market demand factor
        agg = db.query(DemandHourlyAggregate).filter(DemandHourlyAggregate.fpt_product_id == product_id).order_by(desc(DemandHourlyAggregate.aggregate_hour)).first()
        if agg:
            demand_factor = f"Luu luong quan tam: {agg.total_views} views, {agg.cart_adds} gio hang, CVR={agg.cvr_pct:.1f}%."
        else:
            demand_factor = "Nhu cau thi truong o muc tieu chuan (Neutral)."

        return {
            "competitor_factor": comp_factor,
            "inventory_factor": inv_factor,
            "market_demand_factor": demand_factor,
        }
