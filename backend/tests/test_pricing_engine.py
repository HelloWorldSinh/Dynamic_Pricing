import uuid
from datetime import datetime, timezone
import pytest
from app.models import (
    Product,
    InventoryMock,
    CrawlJob,
    CrawlResult,
    SkuMapping,
    PriceRecommendation,
)
from app.services.pricing import PricingEngine


@pytest.fixture
def sample_product_with_inventory(db_session):
    """Tạo sản phẩm mẫu kèm tồn kho và đối thủ cạnh tranh."""
    p = Product(
        id=uuid.uuid4(),
        sku="SKU-FPT-E2E-001",
        name="iPhone 15 Pro Max 256GB Titan Tự Nhiên",
        category="PHONE",
        brand="Apple",
        base_retail_price=30_000_000,
        cost_price=25_000_000,
        floor_price=26_000_000,
        min_margin_pct=5.0,
        is_active=True,
    )
    db_session.add(p)

    inv = InventoryMock(
        fpt_product_id=p.id,
        stock_quantity=50,
        doh=20,
        cost_price=25_000_000,
        floor_price=26_000_000,
    )
    db_session.add(inv)

    job = CrawlJob(
        trigger_type="ON_DEMAND",
        source="CELLPHONES",
        category="PHONE",
        status="COMPLETED",
        total_items=1,
        success_items=1,
    )
    db_session.add(job)
    db_session.commit()

    crawl = CrawlResult(
        job_id=job.id,
        source="CELLPHONES",
        url="https://cellphones.com.vn/iphone-15-pro-max.html",
        raw_name="iPhone 15 Pro Max 256GB",
        current_price=29_500_000,
        original_price=34_000_000,
        is_in_stock=True,
    )
    db_session.add(crawl)
    db_session.commit()

    mapping = SkuMapping(
        fpt_product_id=p.id,
        competitor_crawl_id=crawl.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=1.0,
        status="APPROVED",
    )
    db_session.add(mapping)
    db_session.commit()
    db_session.refresh(p)
    return p


def test_pricing_engine_end_to_end_persists_recommendation(db_session, sample_product_with_inventory):
    """PBI-010: Engine trích xuất dữ liệu, khớp ma trận, áp guardrail và lưu PriceRecommendation."""
    engine = PricingEngine()
    rec = engine.generate_for_product(db_session, sample_product_with_inventory.id)

    assert rec.id is not None
    assert rec.fpt_product_id == sample_product_with_inventory.id
    assert rec.status == "PENDING"
    assert rec.current_fpt_price == 30_000_000
    assert rec.competitor_min_price == 29_500_000
    assert rec.recommended_price >= sample_product_with_inventory.inventory.floor_price

    # Kiểm tra 3 lớp giải trình reasoning_3layers
    layers = rec.reasoning_3layers
    assert "competitor_factor" in layers
    assert "inventory_factor" in layers
    assert "market_demand_factor" in layers
    assert "floor_protection_factor" in layers
    assert "guardrail_notes" in layers
    assert isinstance(layers["guardrail_notes"], list)

    # Kiểm tra tồn tại trong DB
    persisted = db_session.query(PriceRecommendation).filter(PriceRecommendation.id == rec.id).first()
    assert persisted is not None
    assert persisted.scenario_name == rec.scenario_name


def test_rerun_pending_recommendation_updates_in_place_no_duplicate(db_session, sample_product_with_inventory):
    """Khi chạy lại cho sản phẩm đã có đề xuất PENDING, cập nhật in-place thay vì tạo trùng lặp."""
    engine = PricingEngine()

    # Lần chạy 1
    rec1 = engine.generate_for_product(db_session, sample_product_with_inventory.id)
    rec1_id = rec1.id

    count_after_first = (
        db_session.query(PriceRecommendation)
        .filter(PriceRecommendation.fpt_product_id == sample_product_with_inventory.id)
        .count()
    )
    assert count_after_first == 1

    # Lần chạy 2 (giả lập thay đổi trọng số để cập nhật giá trị)
    rec2 = engine.generate_for_product(
        db_session,
        sample_product_with_inventory.id,
        custom_weights={"D": 0.1, "I": 0.8, "C": 0.1},
    )

    count_after_second = (
        db_session.query(PriceRecommendation)
        .filter(PriceRecommendation.fpt_product_id == sample_product_with_inventory.id)
        .count()
    )
    assert count_after_second == 1
    assert rec2.id == rec1_id
    assert rec2.status == "PENDING"


def test_rerun_after_approved_creates_new_pending_recommendation(db_session, sample_product_with_inventory):
    """Nếu đề xuất cũ đã APPROVED, lần chạy tiếp theo phải tạo một đề xuất PENDING mới."""
    engine = PricingEngine()
    rec1 = engine.generate_for_product(db_session, sample_product_with_inventory.id)
    rec1.status = "APPROVED"
    db_session.commit()

    rec2 = engine.generate_for_product(db_session, sample_product_with_inventory.id)
    assert rec2.id != rec1.id
    assert rec2.status == "PENDING"

    total_count = (
        db_session.query(PriceRecommendation)
        .filter(PriceRecommendation.fpt_product_id == sample_product_with_inventory.id)
        .count()
    )
    assert total_count == 2


def test_graceful_fallback_no_inventory_and_no_competitor_data(db_session):
    """Không có tồn kho, không có crawl data đối thủ: fallback an toàn không gây chia cho 0 hay crash."""
    p = Product(
        id=uuid.uuid4(),
        sku="SKU-NO-DATA-001",
        name="Tai nghe Bluetooth Generic",
        category="ACCESSORY",
        brand="Generic",
        base_retail_price=500_000,
        cost_price=0,
        floor_price=0,
        min_margin_pct=5.0,
        is_active=True,
    )
    db_session.add(p)
    db_session.commit()

    engine = PricingEngine()
    rec = engine.generate_for_product(db_session, p.id)

    assert rec is not None
    assert rec.current_fpt_price == 500_000
    assert rec.competitor_min_price is None
    assert rec.recommended_price >= int(500_000 * 0.85)  # floor price fallback
    assert rec.status == "PENDING"
    assert "competitor_factor" in rec.reasoning_3layers


def test_margin_floor_capping_reflected_in_db(db_session):
    """Khi đề xuất giảm giá chạm hoặc vượt giá sàn, engine phải chặn tại floor_price và bật cờ is_floor_capped."""
    p = Product(
        id=uuid.uuid4(),
        sku="SKU-FLOOR-CAP-001",
        name="Laptop Gaming Cũ Tồn Kho",
        category="LAPTOP",
        brand="Asus",
        base_retail_price=20_000_000,
        cost_price=18_000_000,
        floor_price=19_000_000,
        is_active=True,
    )
    db_session.add(p)

    # Tồn kho ứ đọng nặng -> DOH = 60 ngày -> I = -2.0
    inv = InventoryMock(
        fpt_product_id=p.id,
        stock_quantity=200,
        doh=60,
        cost_price=18_000_000,
        floor_price=19_000_000,
    )
    db_session.add(inv)

    # Đối thủ bán cực rẻ -> C = -2.0
    crawl = CrawlResult(
        source="CELLPHONES",
        url="https://cellphones.com.vn/laptop-gaming.html",
        raw_name="Laptop Gaming",
        current_price=15_000_000,
        is_in_stock=True,
    )
    db_session.add(crawl)
    db_session.commit()

    mapping = SkuMapping(
        fpt_product_id=p.id,
        competitor_crawl_id=crawl.id,
        match_type="EXACT_PART_NUMBER",
        status="APPROVED",
    )
    db_session.add(mapping)
    db_session.commit()

    engine = PricingEngine()
    rec = engine.generate_for_product(db_session, p.id)

    assert rec.is_floor_capped is True
    assert rec.recommended_price == 19_000_000
    assert "gia san" in rec.reasoning_3layers["floor_protection_factor"].lower()


def test_product_not_found_raises_value_error(db_session):
    """Khi product_id không tồn tại trong CSDL, raise ValueError rõ ràng."""
    engine = PricingEngine()
    random_id = uuid.uuid4()
    with pytest.raises(ValueError, match=f"Product with id '{random_id}' not found"):
        engine.generate_for_product(db_session, random_id)


def test_batch_generation_across_active_products(db_session):
    """generate_batch chỉ xử lý các sản phẩm active (is_active=True)."""
    p1 = Product(
        sku="SKU-BATCH-001",
        name="Chuột Logitech M1",
        category="ACCESSORY",
        base_retail_price=300_000,
        is_active=True,
    )
    p2 = Product(
        sku="SKU-BATCH-002",
        name="Chuột Logitech M2",
        category="ACCESSORY",
        base_retail_price=400_000,
        is_active=True,
    )
    p3_inactive = Product(
        sku="SKU-BATCH-003",
        name="Chuột ngừng kinh doanh",
        category="ACCESSORY",
        base_retail_price=500_000,
        is_active=False,
    )
    db_session.add_all([p1, p2, p3_inactive])
    db_session.commit()

    engine = PricingEngine()
    recs = engine.generate_batch(db_session)

    assert len(recs) == 2
    rec_product_ids = {r.fpt_product_id for r in recs}
    assert p1.id in rec_product_ids
    assert p2.id in rec_product_ids
    assert p3_inactive.id not in rec_product_ids


def test_zero_emojis_or_icons_in_output(db_session, sample_product_with_inventory):
    """Tuân thủ nghiêm ngặt quy tắc toàn cục: Tuyệt đối không có emoji hoặc icon trang trí trong toàn bộ dữ liệu đề xuất."""
    engine = PricingEngine()
    rec = engine.generate_for_product(db_session, sample_product_with_inventory.id)

    def contains_emoji(text: str) -> bool:
        # Kiểm tra dải ký tự emoji tiêu biểu
        for ch in text:
            code = ord(ch)
            if (
                0x1F600 <= code <= 0x1F64F  # Emoticons
                or 0x1F300 <= code <= 0x1F5FF  # Misc Symbols and Pictographs
                or 0x1F680 <= code <= 0x1F6FF  # Transport and Map
                or 0x1F700 <= code <= 0x1F77F  # Alchemical Symbols
                or 0x1F780 <= code <= 0x1F7FF  # Geometric Shapes Extended
                or 0x1F800 <= code <= 0x1F8FF  # Supplemental Arrows-C
                or 0x1F900 <= code <= 0x1F9FF  # Supplemental Symbols and Pictographs
                or 0x1FA00 <= code <= 0x1FA6F  # Chess Symbols
                or 0x1FA70 <= code <= 0x1FAFF  # Symbols and Pictographs Extended-A
                or 0x2600 <= code <= 0x26FF  # Misc Symbols
                or 0x2700 <= code <= 0x27BF  # Dingbats
            ):
                return True
        return False

    assert not contains_emoji(rec.scenario_name), f"Found emoji in scenario_name: {rec.scenario_name}"
    for key, val in rec.reasoning_3layers.items():
        if isinstance(val, str):
            assert not contains_emoji(val), f"Found emoji in reasoning_3layers[{key}]: {val}"
        elif isinstance(val, list):
            for item in val:
                assert not contains_emoji(str(item)), f"Found emoji in note: {item}"


def test_product_with_non_positive_price_raises_value_error(db_session):
    """Sản phẩm có giá niêm yết bằng 0 hoặc âm phải kích hoạt ValueError."""
    p = Product(
        sku="SKU-ZERO-PRICE",
        name="San pham gia 0",
        category="ACCESSORY",
        base_retail_price=0,
        is_active=True,
    )
    db_session.add(p)
    db_session.commit()

    engine = PricingEngine()
    with pytest.raises(ValueError, match="has non-positive current price"):
        engine.generate_for_product(db_session, p.id)


def test_dependency_injection_of_custom_collaborators(db_session, sample_product_with_inventory):
    """Kiểm tra DI: có thể inject custom SignalsExtractor, ScenarioMatrix, SafetyGuardrails."""
    from app.services.pricing import SignalsExtractor, ScenarioMatrix, SafetyGuardrails

    custom_extractor = SignalsExtractor()
    custom_matrix = ScenarioMatrix()
    custom_guardrails = SafetyGuardrails()

    engine = PricingEngine(
        signals_extractor=custom_extractor,
        scenario_matrix=custom_matrix,
        guardrails=custom_guardrails,
    )
    assert engine.signals_extractor is custom_extractor
    assert engine.scenario_matrix is custom_matrix
    assert engine.guardrails is custom_guardrails

    rec = engine.generate_for_product(db_session, sample_product_with_inventory.id)
    assert rec.id is not None


def test_batch_generation_empty_when_no_active_products(db_session):
    """Khi không có sản phẩm nào active, generate_batch trả về danh sách rỗng an toàn."""
    p = Product(
        sku="SKU-INACTIVE-ONLY",
        name="San pham khong hoat dong",
        category="ACCESSORY",
        base_retail_price=100_000,
        is_active=False,
    )
    db_session.add(p)
    db_session.commit()

    engine = PricingEngine()
    recs = engine.generate_batch(db_session)
    assert recs == []


def test_competitor_out_of_stock_ignored_for_cheapest_price(db_session):
    """Đối thủ hết hàng (is_in_stock=False) phải bị bỏ qua khi tính competitor_min_price."""
    p = Product(
        sku="SKU-OOS-COMPETITOR",
        name="Dien thoai flagship",
        category="PHONE",
        base_retail_price=25_000_000,
        cost_price=21_000_000,
        floor_price=22_000_000,
        is_active=True,
    )
    db_session.add(p)
    db_session.commit()

    # Đối thủ 1: giá cực rẻ 20M nhưng hết hàng
    c1 = CrawlResult(
        source="CELLPHONES",
        url="https://cellphones.com.vn/oos.html",
        raw_name="Flagship OOS",
        current_price=20_000_000,
        is_in_stock=False,
    )
    # Đối thủ 2: giá 24M còn hàng
    c2 = CrawlResult(
        source="HOANGHA",
        url="https://hoanghamobile.com/instock.html",
        raw_name="Flagship In Stock",
        current_price=24_000_000,
        is_in_stock=True,
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    m1 = SkuMapping(fpt_product_id=p.id, competitor_crawl_id=c1.id, match_type="EXACT_PART_NUMBER")
    m2 = SkuMapping(fpt_product_id=p.id, competitor_crawl_id=c2.id, match_type="EXACT_PART_NUMBER")
    db_session.add_all([m1, m2])
    db_session.commit()

    engine = PricingEngine()
    rec = engine.generate_for_product(db_session, p.id)

    # Phải lấy giá của c2 (24_000_000) vì c1 đã hết hàng
    assert rec.competitor_min_price == 24_000_000


def test_batch_generation_isolates_product_errors(db_session, caplog):
    """Khi một sản phẩm trong batch bị lỗi (vd giá <= 0), batch ghi log warning và tiếp tục xử lý các sản phẩm còn lại."""
    import logging

    p1_valid = Product(
        sku="SKU-BATCH-ISO-001",
        name="San pham hop le 1",
        category="ACCESSORY",
        base_retail_price=200_000,
        is_active=True,
    )
    p2_invalid = Product(
        sku="SKU-BATCH-ISO-002",
        name="San pham loi gia 0",
        category="ACCESSORY",
        base_retail_price=0,
        is_active=True,
    )
    p3_valid = Product(
        sku="SKU-BATCH-ISO-003",
        name="San pham hop le 2",
        category="ACCESSORY",
        base_retail_price=400_000,
        is_active=True,
    )
    db_session.add_all([p1_valid, p2_invalid, p3_valid])
    db_session.commit()

    engine = PricingEngine()
    with caplog.at_level(logging.WARNING):
        recs = engine.generate_batch(db_session)

    # p2_invalid bị lỗi nhưng p1 và p3 vẫn phải được tạo thành công
    assert len(recs) == 2
    rec_product_ids = {r.fpt_product_id for r in recs}
    assert p1_valid.id in rec_product_ids
    assert p3_valid.id in rec_product_ids
    assert p2_invalid.id not in rec_product_ids

    # Kiểm tra logger đã ghi nhận warning
    assert any("Failed to generate price recommendation for product" in record.message for record in caplog.records)


