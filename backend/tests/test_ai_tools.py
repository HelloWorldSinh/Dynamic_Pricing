"""
Unit tests for AI Schemas and Semantic Tools (Phase 1 of AI Pricing Assistant).
Follows TDD Red-Green-Refactor methodology.
"""
import uuid
import pytest
from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.models.inventory import InventoryMock
from app.models.pricing import PriceRecommendation

from app.schemas.ai import (
    CompetitorShift,
    InventoryStatus,
    FloorProtection,
    ExplainableFactors,
    AiChatRequest,
    AiChatResponse,
)
from app.services.ai.tools import (
    get_price_discrepancies,
    get_inventory_risks,
    get_sku_explain_factors,
)


def test_ai_schemas_serialization():
    """Kiểm tra tính hợp lệ và serialize của các Pydantic AI Schemas."""
    factors = ExplainableFactors(
        competitor_shift=CompetitorShift(
            competitor="CELLPHONES",
            old_price=18490000,
            new_price=17890000,
            price_cut=600000,
            is_in_stock=True,
        ),
        inventory_status=InventoryStatus(
            sku="FPT-ASUS-VIVO15",
            doh=54,
            quantity=42,
            doh_risk_level="HIGH",
        ),
        floor_protection=FloorProtection(
            floor_price=17325000,
            suggested_price=17890000,
            safety_margin_percent=3.26,
            is_capped=False,
        ),
    )
    assert factors.competitor_shift.competitor == "CELLPHONES"
    assert factors.inventory_status.doh_risk_level == "HIGH"
    assert factors.floor_protection.safety_margin_percent == 3.26

    # Test request & response models
    session_id = uuid.uuid4()
    req = AiChatRequest(message="Top laptop Asus đắt hơn CellphoneS", session_id=session_id)
    assert req.message == "Top laptop Asus đắt hơn CellphoneS"
    assert req.session_id == session_id

    res = AiChatResponse(
        message="Dưới đây là danh sách sản phẩm:",
        session_id=session_id,
        tableData=[{"SKU": "FPT-ASUS-VIVO15", "Giá FPT": "18.990.000đ"}],
        explainFactors=factors,
    )
    assert len(res.tableData) == 1
    assert res.explainFactors is not None


def test_get_price_discrepancies_filters_out_of_stock(db_session):
    """
    Ràng buộc nghiệp vụ quan trọng:
    Nếu đối thủ bán rẻ hơn nhưng HẾT HÀNG (is_in_stock = False),
    sản phẩm không được đưa vào danh sách chênh lệch giá!
    """
    # 1. Tạo sản phẩm FPT
    p1 = Product(
        id=uuid.uuid4(),
        sku="FPT-TEST-01",
        name="Laptop Test In Stock",
        category="LAPTOP",
        brand="ASUS",
        base_retail_price=20000000,
        cost_price=17000000,
        floor_price=18000000,
    )
    p2 = Product(
        id=uuid.uuid4(),
        sku="FPT-TEST-02",
        name="Laptop Test OOS",
        category="LAPTOP",
        brand="ASUS",
        base_retail_price=20000000,
        cost_price=17000000,
        floor_price=18000000,
    )
    db_session.add_all([p1, p2])
    db_session.flush()

    # 2. Tạo kho
    inv1 = InventoryMock(fpt_product_id=p1.id, stock_quantity=15, doh=30, cost_price=17000000, floor_price=18000000)
    inv2 = InventoryMock(fpt_product_id=p2.id, stock_quantity=20, doh=40, cost_price=17000000, floor_price=18000000)
    db_session.add_all([inv1, inv2])

    # 3. Tạo kết quả cào đối thủ: c1 còn hàng (giá 18tr), c2 hết hàng (giá 17tr)
    c1 = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="http://test.com/1",
        raw_name="Laptop Test In Stock",
        current_price=18000000,
        is_in_stock=True,
    )
    c2 = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="http://test.com/2",
        raw_name="Laptop Test OOS",
        current_price=17000000,
        is_in_stock=False,  # Out of stock
    )
    db_session.add_all([c1, c2])
    db_session.flush()

    # 4. Tạo SkuMapping approved
    m1 = SkuMapping(
        fpt_product_id=p1.id,
        competitor_crawl_id=c1.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=1.0,
        status="APPROVED",
    )
    m2 = SkuMapping(
        fpt_product_id=p2.id,
        competitor_crawl_id=c2.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=1.0,
        status="APPROVED",
    )
    db_session.add_all([m1, m2])
    db_session.commit()

    # Chạy tool
    results = get_price_discrepancies(db=db_session, category="LAPTOP", brand="ASUS", competitor="CELLPHONES")
    
    assert len(results) == 1
    assert results[0]["SKU"] == "FPT-TEST-01"
    assert "FPT-TEST-02" not in [r["SKU"] for r in results]


def test_get_price_discrepancies_requires_approved_or_high_confidence(db_session):
    """Chỉ lấy mapping đã APPROVED hoặc có confidence >= 0.8."""
    p1 = Product(
        id=uuid.uuid4(),
        sku="FPT-UNAPPROVED",
        name="Laptop Unapproved Mapping",
        category="LAPTOP",
        brand="DELL",
        base_retail_price=25000000,
        cost_price=20000000,
        floor_price=21000000,
    )
    db_session.add(p1)
    db_session.flush()

    inv = InventoryMock(fpt_product_id=p1.id, stock_quantity=10, doh=25, cost_price=20000000, floor_price=21000000)
    c = CrawlResult(
        id=uuid.uuid4(),
        source="HOANGHA",
        url="http://test.com/dell",
        raw_name="Laptop Dell In Stock",
        current_price=22000000,
        is_in_stock=True,
    )
    db_session.add_all([inv, c])
    db_session.flush()

    # Mapping REJECTED
    m = SkuMapping(
        fpt_product_id=p1.id,
        competitor_crawl_id=c.id,
        match_type="NORMALIZED_ATTRIBUTE",
        confidence_score=0.7,
        status="REJECTED",
    )
    db_session.add(m)
    db_session.commit()

    results = get_price_discrepancies(db=db_session, category="LAPTOP", brand="DELL")
    assert len(results) == 0


def test_get_inventory_risks_threshold(db_session):
    """Kiểm tra lọc sản phẩm tồn kho theo ngưỡng DOH và phân loại rủi ro."""
    p_high = Product(
        id=uuid.uuid4(),
        sku="FPT-DOH-HIGH",
        name="iPhone 15 Plus 128GB",
        category="PHONE",
        brand="Apple",
        base_retail_price=22000000,
    )
    p_safe = Product(
        id=uuid.uuid4(),
        sku="FPT-DOH-SAFE",
        name="iPhone 16 Pro Max 256GB",
        category="PHONE",
        brand="Apple",
        base_retail_price=34000000,
    )
    db_session.add_all([p_high, p_safe])
    db_session.flush()

    inv_high = InventoryMock(fpt_product_id=p_high.id, stock_quantity=48, doh=52, cost_price=19000000, floor_price=20000000)
    inv_safe = InventoryMock(fpt_product_id=p_safe.id, stock_quantity=115, doh=18, cost_price=30000000, floor_price=31500000)
    db_session.add_all([inv_high, inv_safe])
    db_session.commit()

    # Lọc với ngưỡng DOH >= 45
    risks = get_inventory_risks(db=db_session, doh_threshold=45)
    assert len(risks) == 1
    assert risks[0]["SKU"] == "FPT-DOH-HIGH"
    assert "DOH = 52 ngày" in risks[0]["DOH"]
    assert "CAO" in risks[0]["Rủi ro"]


def test_get_sku_explain_factors_complete_structure(db_session):
    """Kiểm tra trích xuất cấu trúc thẻ giải trình 3 lớp của một mã SKU cụ thể."""
    product_id = uuid.uuid4()
    p = Product(
        id=product_id,
        sku="FPT-ASUS-VIVO15",
        name="ASUS Vivobook 15 OLED A1505VA",
        category="LAPTOP",
        brand="ASUS",
        base_retail_price=18990000,
        cost_price=16500000,
        floor_price=17325000,
    )
    db_session.add(p)
    db_session.flush()

    inv = InventoryMock(
        fpt_product_id=product_id,
        stock_quantity=42,
        doh=54,
        cost_price=16500000,
        floor_price=17325000,
    )
    c = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="http://cellphones.com/vivobook",
        raw_name="ASUS Vivobook 15",
        current_price=17890000,
        original_price=18490000,
        is_in_stock=True,
    )
    db_session.add_all([inv, c])
    db_session.flush()

    rec = PriceRecommendation(
        id=uuid.uuid4(),
        fpt_product_id=product_id,
        current_fpt_price=18990000,
        competitor_min_price=17890000,
        recommended_price=17890000,
        price_delta_amount=-1100000,
        price_delta_pct=-0.0579,
        demand_score=0.0,
        inventory_score=-2.0,
        competitor_score=-2.0,
        composite_score=-1.2,
        scenario_name="Kịch bản 4: DOH > 45 ngày & Đối thủ còn hàng",
        reasoning_3layers={"competitor_cut": 600000, "safety_margin_pct": 3.26},
        is_floor_capped=False,
    )
    db_session.add(rec)
    db_session.commit()

    factors = get_sku_explain_factors(db=db_session, sku="FPT-ASUS-VIVO15")
    assert factors is not None
    assert isinstance(factors, ExplainableFactors)
    assert factors.competitor_shift.competitor == "CellphoneS"
    assert factors.competitor_shift.new_price == 17890000
    assert factors.inventory_status.sku == "FPT-ASUS-VIVO15"
    assert factors.inventory_status.doh == 54
    assert factors.inventory_status.doh_risk_level == "HIGH"
    assert factors.floor_protection.floor_price == 17325000
    assert factors.floor_protection.suggested_price == 17890000
    assert factors.floor_protection.is_capped is False


def test_get_sku_explain_factors_nonexistent_sku(db_session):
    """Khi tra cứu một SKU không tồn tại trong hệ thống, trả về None."""
    factors = get_sku_explain_factors(db=db_session, sku="NON-EXISTENT-SKU")
    assert factors is None
