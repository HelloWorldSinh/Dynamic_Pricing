import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.crawl_result import CrawlResult
from app.models.inventory import InventoryMock
from app.models.pricing import PriceRecommendation
from app.models.product import Product
from app.models.sku_mapping import SkuMapping
from app.services.pricing.guardrails import SafetyGuardrails
from app.services.pricing.matrix import ScenarioMatrix
from app.services.pricing.schemas import SignalScores
from app.services.pricing.signals import SignalsExtractor

logger = logging.getLogger(__name__)


def _get_product_price(product: Product) -> int:
    """Lay gia hien tai cua san pham tu price hoac base_retail_price."""
    price_val = getattr(product, "price", None)
    if price_val is not None and not callable(price_val):
        return int(price_val)
    return int(getattr(product, "base_retail_price", 0) or 0)


class PricingEngine:
    """Facade dieu phoi toan bo quy trinh de xuat gia dong (PBI-010, PBI-011, PBI-012).

    Tich hop:
    1. SignalsExtractor: Trich xuat cac diem tin hieu thi truong D, I, C va chi tiet giai trinh.
    2. ScenarioMatrix: Tinh Composite Score va khop 9 kich ban dac thu hoac 7 dai composite.
    3. SafetyGuardrails: Kiem soat bien do thay doi (Rate Cap) va bao ve gia san (Margin Floor).
    4. Database Persistence: Cap nhat in-place de xuat PENDING hoac tao moi de xuat gia.
    """

    def __init__(
        self,
        signals_extractor: Optional[SignalsExtractor] = None,
        scenario_matrix: Optional[ScenarioMatrix] = None,
        guardrails: Optional[SafetyGuardrails] = None,
    ) -> None:
        """Khoi tao PricingEngine voi cac thanh phan nghiep vu tuong ung."""
        self.signals_extractor = signals_extractor or SignalsExtractor()
        self.scenario_matrix = scenario_matrix or ScenarioMatrix()
        self.guardrails = guardrails or SafetyGuardrails()

    def generate_for_product(
        self,
        db: Session,
        product_id: UUID,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> PriceRecommendation:
        """Sinh de xuat gia cho mot san pham cu the va luu vao co so du lieu.

        Args:
            db: Database session.
            product_id: UUID cua san pham can dinh gia.
            custom_weights: Trong so tuy bien D, I, C (tuy chon).

        Returns:
            PriceRecommendation: Ban ghi de xuat gia da duoc commit trong DB.

        Raises:
            ValueError: Neu product_id khong ton tai hoac gia san pham khong hop le.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product with id '{product_id}' not found")

        current_price = _get_product_price(product)
        if current_price <= 0:
            raise ValueError(
                f"Product '{product.sku}' (id={product_id}) has non-positive current price: {current_price}"
            )

        # 1. Xac dinh cost_price va floor_price tu InventoryMock hoac fallback tu current_price
        inv = (
            db.query(InventoryMock)
            .filter(InventoryMock.fpt_product_id == product_id)
            .first()
        )
        if inv and inv.cost_price and inv.cost_price > 0:
            cost_price = int(inv.cost_price)
            floor_price = (
                int(inv.floor_price)
                if inv.floor_price and inv.floor_price > 0
                else int(cost_price * 1.05)
            )
        else:
            prod_cost = int(getattr(product, "cost_price", 0) or 0)
            prod_floor = int(getattr(product, "floor_price", 0) or 0)
            cost_price = prod_cost if prod_cost > 0 else int(current_price * 0.85)
            floor_price = prod_floor if prod_floor > 0 else int(current_price * 0.90)

        if floor_price <= 0:
            floor_price = cost_price

        # 2. Tim gia doi thu thap nhat con hang (in-stock)
        mappings = (
            db.query(SkuMapping)
            .filter(SkuMapping.fpt_product_id == product_id)
            .all()
        )
        scraped_ids = [m.competitor_crawl_id for m in mappings if m.competitor_crawl_id]
        c_items = (
            db.query(CrawlResult)
            .filter(CrawlResult.id.in_(scraped_ids))
            .all()
        ) if scraped_ids else []

        in_stock_prices = [
            int(item.current_price)
            for item in c_items
            if item.is_in_stock and item.current_price and item.current_price > 0
        ]
        competitor_min_price = min(in_stock_prices) if in_stock_prices else None

        # 3. Trich xuat diem tin hieu va thong tin giai trinh
        scores: SignalScores = self.signals_extractor.extract_signals(db, product_id)
        reasoning_details = self.signals_extractor.extract_reasoning_details(db, product_id)

        # 4. Danh gia ma tran kich ban va tinh Composite Score
        scenario = self.scenario_matrix.evaluate(scores, weights=custom_weights)
        composite_score = self.scenario_matrix.calculate_composite(scores, weights=custom_weights)

        # 5. Ap dung cac rao can an toan (Margin Floor, Rate Cap, Predatory)
        max_rate_cap = 0.15 if "Strong" in scenario.action_type else 0.10
        guardrail_res = self.guardrails.apply(
            current_price=current_price,
            target_delta_pct=scenario.target_delta_pct,
            floor_price=floor_price,
            cost_price=cost_price,
            competitor_price=competitor_min_price,
            max_rate_cap=max_rate_cap,
        )

        # 6. Dong goi 3 lop giai trinh reasoning_3layers JSON (khong dung emoji/icon)
        floor_protection_factor = (
            "Muc gia de xuat da duoc dieu chinh ve muc gia san de bao toan bien loi nhuan an toan."
            if guardrail_res.is_floor_capped
            else "Muc gia de xuat nam trong nguong an toan tren muc gia san."
        )

        reasoning_3layers: Dict[str, Any] = {
            "competitor_factor": reasoning_details.get("competitor_factor", ""),
            "inventory_factor": reasoning_details.get("inventory_factor", ""),
            "market_demand_factor": reasoning_details.get("market_demand_factor", ""),
            "floor_protection_factor": floor_protection_factor,
            "guardrail_notes": guardrail_res.guardrail_notes,
        }

        # 7. Luu tru hoac cap nhat ban ghi PriceRecommendation
        existing = (
            db.query(PriceRecommendation)
            .filter(
                PriceRecommendation.fpt_product_id == product_id,
                PriceRecommendation.status == "PENDING",
            )
            .first()
        )

        now_utc = datetime.now(timezone.utc)
        if existing is not None:
            existing.current_fpt_price = current_price
            existing.competitor_min_price = competitor_min_price
            existing.recommended_price = guardrail_res.final_price
            existing.price_delta_amount = guardrail_res.price_delta_amount
            existing.price_delta_pct = guardrail_res.price_delta_pct
            existing.demand_score = scores.demand_score
            existing.inventory_score = scores.inventory_score
            existing.competitor_score = scores.competitor_score
            existing.composite_score = composite_score
            existing.scenario_name = scenario.scenario_name
            existing.reasoning_3layers = reasoning_3layers
            existing.is_floor_capped = guardrail_res.is_floor_capped
            existing.created_at = now_utc
            rec = existing
        else:
            rec = PriceRecommendation(
                fpt_product_id=product_id,
                current_fpt_price=current_price,
                competitor_min_price=competitor_min_price,
                recommended_price=guardrail_res.final_price,
                price_delta_amount=guardrail_res.price_delta_amount,
                price_delta_pct=guardrail_res.price_delta_pct,
                demand_score=scores.demand_score,
                inventory_score=scores.inventory_score,
                competitor_score=scores.competitor_score,
                composite_score=composite_score,
                scenario_name=scenario.scenario_name,
                reasoning_3layers=reasoning_3layers,
                is_floor_capped=guardrail_res.is_floor_capped,
                status="PENDING",
                created_at=now_utc,
            )
            db.add(rec)

        db.commit()
        db.refresh(rec)
        return rec

    def generate_batch(
        self,
        db: Session,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> List[PriceRecommendation]:
        """Tu dong sinh de xuat gia cho toan bo san pham dang hoat dong (is_active=True).

        Args:
            db: Database session.
            custom_weights: Trong so tuy bien D, I, C (tuy chon).

        Returns:
            List[PriceRecommendation]: Danh sach ban ghi de xuat gia da tao/cap nhat.
        """
        active_products = (
            db.query(Product)
            .filter(Product.is_active == True)
            .all()
        )
        recommendations: List[PriceRecommendation] = []
        for product in active_products:
            try:
                rec = self.generate_for_product(
                    db=db,
                    product_id=product.id,
                    custom_weights=custom_weights,
                )
                recommendations.append(rec)
            except Exception as exc:
                logger.warning(
                    "Failed to generate price recommendation for product %s: %s",
                    product.id,
                    exc,
                )
        return recommendations
