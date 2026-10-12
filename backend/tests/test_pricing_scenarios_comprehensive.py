"""Comprehensive Test Suite for Backend Price Recommendations.

Covers:
1. 10 Business Scenarios (ScenarioMatrix EXACT_SCENARIOS: 9 classic + 1 Clearance)
2. 7 Composite Fallback Action Bands & Precise Boundary Thresholds
3. 4 Industry Weight Profiles (Standard ICT, FMCG, Flagship, Commodity)
4. Safety Guardrails Matrix (Margin Floor, Rate-of-Change Cap, Predatory Pricing)
5. API Simulation Endpoint (/api/v1/pricing/matrix/simulate) across all 10 scenarios
6. PricingEngine DB Integration across scenarios & lifecycle (PENDING update, APPROVED create)
7. Strict Zero-Emoji & Zero-Icon Quality Enforcement
"""

import re
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.models import (
    Product,
    InventoryMock,
    PriceRecommendation,
    SkuMapping,
    CrawlJob,
    CrawlResult,
)
from app.services.pricing import (
    PricingEngine,
    ScenarioMatrix,
    SafetyGuardrails,
    SignalsExtractor,
)
from app.services.pricing.schemas import SignalScores, ScenarioMatch, GuardrailResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(db_session):
    """TestClient fixture overriding database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_product(db_session):
    """Fixture tạo sản phẩm cơ sở dùng cho kiểm thử."""
    p = Product(
        id=uuid.uuid4(),
        sku="SKU-COMP-001",
        name="Laptop ThinkPad T14 Gen 4 Core i7 16GB 512GB",
        category="LAPTOP",
        brand="Lenovo",
        base_retail_price=25_000_000,
        cost_price=20_000_000,
        floor_price=21_000_000,
        min_margin_pct=5.0,
        is_active=True,
    )
    db_session.add(p)

    inv = InventoryMock(
        fpt_product_id=p.id,
        stock_quantity=40,
        doh=22,
        cost_price=20_000_000,
        floor_price=21_000_000,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(p)
    return p


def assert_no_emojis(text: str):
    """Kiểm tra nghiêm ngặt không chứa emoji hoặc icon trang trí."""
    assert not re.search(r"[\U00010000-\U0010ffff]", text), f"Found emoji in text: {text}"
    disallowed_symbols = ["↑", "↓", "⚠️", "⚡", "🎯", "✨", "🔥", "🛑", "🚨", "🚀", "💡"]
    for sym in disallowed_symbols:
        assert sym not in text, f"Found disallowed symbol '{sym}' in text: {text}"


# ---------------------------------------------------------------------------
# 1. Test 10 Exact Business Scenarios in ScenarioMatrix
# ---------------------------------------------------------------------------

SCENARIO_TEST_DATA = [
    (
        (2.0, 2.0, 2.0),
        "Kịch bản 1: Festival / Sự kiện lớn",
        0.12,
        "Strong raise",
        "Nhu cầu bùng nổ",
    ),
    (
        (2.0, 0.0, 0.0),
        "Kịch bản 2: Sản phẩm Viral",
        0.06,
        "Moderate raise",
        "Lượt tìm kiếm và quan tâm tăng vọt",
    ),
    (
        (0.0, 0.0, 0.0),
        "Kịch bản 3: Bình thường (Baseline)",
        0.0,
        "Hold",
        "Thị trường ổn định",
    ),
    (
        (2.0, -2.0, 0.0),
        "Kịch bản 4: Cầu cao nhưng Hàng ứ",
        0.0,
        "Hold + Review",
        "lượng tồn kho thực tế quá cao",
    ),
    (
        (-1.0, 2.0, 2.0),
        "Kịch bản 5: Hàng khan, Đối thủ hết nhưng Cầu yếu",
        0.02,
        "Mild raise",
        "Kho sắp hết hàng",
    ),
    (
        (-2.0, -2.0, -2.0),
        "Kịch bản 6: Khủng hoảng Nhu cầu",
        -0.15,
        "Strong lower",
        "Cả 3 yếu tố đều chạm đáy",
    ),
    (
        (-2.0, 0.0, -2.0),
        "Kịch bản 7: Khách quay lưng, Đối thủ rẻ",
        -0.10,
        "Moderate lower",
        "đối thủ đang bán rẻ hơn",
    ),
    (
        (2.0, 2.0, -2.0),
        "Kịch bản 8: Cầu cao, Hàng khan nhưng Đối thủ rẻ",
        0.06,
        "Moderate raise",
        "khan hàng tạo động lực tăng giá",
    ),
    (
        (1.0, -1.0, 1.0),
        "Kịch bản 9: Tín hiệu Hỗn độn",
        0.0,
        "Hold + A/B Test",
        "Các tín hiệu giằng co",
    ),
    (
        (-2.0, -2.0, 0.0),
        "Kịch bản 10: Cuối vòng đời (Clearance)",
        -0.15,
        "Strong lower",
        "cuối vòng đời",
    ),
]


@pytest.mark.parametrize("scores_tuple,expected_name,expected_delta,expected_action,keyword_rationale", SCENARIO_TEST_DATA)
def test_matrix_all_10_scenarios_evaluated_accurately(
    scores_tuple, expected_name, expected_delta, expected_action, keyword_rationale
):
    matrix = ScenarioMatrix()
    scores = SignalScores(*scores_tuple)
    match = matrix.evaluate(scores)

    assert match.scenario_name == expected_name
    assert match.target_delta_pct == expected_delta
    assert match.action_type == expected_action
    assert keyword_rationale.lower() in match.rationale.lower()
    assert_no_emojis(match.scenario_name)
    assert_no_emojis(match.rationale)


# ---------------------------------------------------------------------------
# 2. Test 7 Composite Fallback Bands & Thresholds
# ---------------------------------------------------------------------------

FALLBACK_BAND_TEST_DATA = [
    # Band 1: Composite >= 1.50 -> Strong raise (+12%)
    (SignalScores(1.9, 1.8, 1.7), "Strong raise", 0.12, 1.50),
    # Band 2: 0.75 <= Composite < 1.50 -> Moderate raise (+6%)
    (SignalScores(1.0, 0.8, 0.9), "Moderate raise", 0.06, 0.75),
    # Band 3: 0.25 <= Composite < 0.75 -> Mild raise (+2%)
    (SignalScores(0.5, 0.4, 0.3), "Mild raise", 0.02, 0.25),
    # Band 4: -0.24 <= Composite < 0.25 -> Hold (0%)
    (SignalScores(0.1, -0.1, 0.0), "Hold", 0.0, -0.24),
    # Band 5: -0.74 <= Composite < -0.24 -> Mild lower (-2%)
    (SignalScores(-0.5, -0.4, -0.3), "Mild lower", -0.02, -0.74),
    # Band 6: -1.49 <= Composite < -0.74 -> Moderate lower (-6%)
    (SignalScores(-1.0, -0.9, -0.8), "Moderate lower", -0.06, -1.49),
    # Band 7: Composite < -1.49 -> Strong lower (-12%)
    (SignalScores(-1.9, -1.8, -1.7), "Strong lower", -0.12, -2.0),
]


@pytest.mark.parametrize("scores,expected_action,expected_delta,min_bound", FALLBACK_BAND_TEST_DATA)
def test_matrix_fallback_bands(scores, expected_action, expected_delta, min_bound):
    matrix = ScenarioMatrix()
    match = matrix.evaluate(scores)
    assert match.action_type == expected_action
    assert match.target_delta_pct == expected_delta
    assert "Dải Composite" in match.scenario_name
    assert_no_emojis(match.scenario_name)
    assert_no_emojis(match.rationale)


def test_matrix_boundary_exact_thresholds():
    """Kiểm tra chính xác các điểm ngưỡng chuyển đổi giữa 7 dải composite."""
    matrix = ScenarioMatrix()

    # Boundary 1.50 (Strong raise) vs 1.49 (Moderate raise)
    # Using uniform scores D=I=C=x so composite = x
    m_150 = matrix.evaluate(SignalScores(1.50, 1.50, 1.50))
    assert m_150.action_type == "Strong raise"

    m_149 = matrix.evaluate(SignalScores(1.49, 1.49, 1.49))
    assert m_149.action_type == "Moderate raise"

    # Boundary 0.75 (Moderate raise) vs 0.74 (Mild raise)
    m_075 = matrix.evaluate(SignalScores(0.75, 0.75, 0.75))
    assert m_075.action_type == "Moderate raise"

    m_074 = matrix.evaluate(SignalScores(0.74, 0.74, 0.74))
    assert m_074.action_type == "Mild raise"

    # Boundary 0.25 (Mild raise) vs 0.24 (Hold)
    m_025 = matrix.evaluate(SignalScores(0.25, 0.25, 0.25))
    assert m_025.action_type == "Mild raise"

    m_024 = matrix.evaluate(SignalScores(0.24, 0.24, 0.24))
    assert m_024.action_type == "Hold"

    # Boundary -0.24 (Hold) vs -0.25 (Mild lower)
    m_neg024 = matrix.evaluate(SignalScores(-0.24, -0.24, -0.24))
    assert m_neg024.action_type == "Hold"

    m_neg025 = matrix.evaluate(SignalScores(-0.25, -0.25, -0.25))
    assert m_neg025.action_type == "Mild lower"

    # Boundary -0.74 (Mild lower) vs -0.75 (Moderate lower)
    m_neg074 = matrix.evaluate(SignalScores(-0.74, -0.74, -0.74))
    assert m_neg074.action_type == "Mild lower"

    m_neg075 = matrix.evaluate(SignalScores(-0.75, -0.75, -0.75))
    assert m_neg075.action_type == "Moderate lower"

    # Boundary -1.49 (Moderate lower) vs -1.50 (Strong lower)
    m_neg149 = matrix.evaluate(SignalScores(-1.49, -1.49, -1.49))
    assert m_neg149.action_type == "Moderate lower"

    m_neg150 = matrix.evaluate(SignalScores(-1.50, -1.50, -1.50))
    assert m_neg150.action_type == "Strong lower"


# ---------------------------------------------------------------------------
# 3. Test 4 Industry Weight Profiles
# ---------------------------------------------------------------------------

def test_industry_weight_profiles_impact():
    """Kiểm tra 4 nhóm ngành hàng quy định trong tài liệu nghiệp vụ:
    1. Standard ICT: D: 40%, I: 35%, C: 25%
    2. FMCG / Phụ kiện: D: 45%, I: 30%, C: 25%
    3. Hàng khan hiếm / Flagship: D: 35%, I: 45%, C: 20%
    4. Hàng phổ thông / Laptop: D: 30%, I: 40%, C: 30%
    """
    matrix = ScenarioMatrix()
    # Scenario: Demand cao (1.8), Kho ổn định (0.0), Đối thủ rẻ (-1.0)
    scores = SignalScores(demand_score=1.8, inventory_score=0.0, competitor_score=-1.0)

    # 1. Standard ICT: 1.8*0.40 + 0*0.35 + (-1.0)*0.25 = 0.72 - 0.25 = 0.47
    w_standard = {"D": 0.40, "I": 0.35, "C": 0.25}
    comp_standard = matrix.calculate_composite(scores, weights=w_standard)
    assert comp_standard == 0.47

    # 2. FMCG (nhạy cảm Demand hơn): 1.8*0.45 + 0*0.30 + (-1.0)*0.25 = 0.81 - 0.25 = 0.56
    w_fmcg = {"D": 0.45, "I": 0.30, "C": 0.25}
    comp_fmcg = matrix.calculate_composite(scores, weights=w_fmcg)
    assert comp_fmcg == 0.56
    assert comp_fmcg > comp_standard  # Cầu nhạy hơn giúp điểm cao hơn

    # 3. Flagship (tồn kho trọng số cao): 1.8*0.35 + 0*0.45 + (-1.0)*0.20 = 0.63 - 0.20 = 0.43
    w_flagship = {"D": 0.35, "I": 0.45, "C": 0.20}
    comp_flagship = matrix.calculate_composite(scores, weights=w_flagship)
    assert comp_flagship == 0.43

    # 4. Commodity (cạnh tranh giá gay gắt): 1.8*0.30 + 0*0.40 + (-1.0)*0.30 = 0.54 - 0.30 = 0.24
    w_commodity = {"D": 0.30, "I": 0.40, "C": 0.30}
    comp_commodity = matrix.calculate_composite(scores, weights=w_commodity)
    assert comp_commodity == 0.24


# ---------------------------------------------------------------------------
# 4. Test Safety Guardrails Combinations
# ---------------------------------------------------------------------------

def test_guardrails_margin_floor_strict_capping():
    """Kiểm tra khi giá đề xuất bị giảm sâu dưới giá sàn, phải bị ép về floor_price."""
    guard = SafetyGuardrails()
    current = 20_000_000
    cost = 17_000_000
    floor = 18_500_000  # Margin floor: 18.5M

    # Kịch bản giảm 15% -> 17,000,000 < 18,500,000
    res = guard.apply(
        current_price=current,
        target_delta_pct=-0.15,
        floor_price=floor,
        cost_price=cost,
        max_rate_cap=0.15,
    )
    assert res.final_price == 18_500_000
    assert res.is_floor_capped is True
    assert res.price_delta_amount == -1_500_000
    assert res.price_delta_pct == -0.075
    assert any("Margin floor protection activated" in note for note in res.guardrail_notes)


def test_guardrails_rate_cap_overridden_by_margin_floor():
    """Khi rate cap clamp ở mức -10% nhưng mức giá đó vẫn thấp hơn giá sàn,
    thì giá sàn floor_price phải có mức ưu tiên cao hơn (precedence)."""
    guard = SafetyGuardrails()
    current = 20_000_000
    cost = 18_000_000
    floor = 19_000_000  # Floor = 19M (-5%)

    # Target delta = -20% -> Rate cap clamp về -10% (18M) -> Vẫn thấp hơn 19M -> Floor cap về 19M
    res = guard.apply(
        current_price=current,
        target_delta_pct=-0.20,
        floor_price=floor,
        cost_price=cost,
        max_rate_cap=0.10,
    )
    assert res.final_price == 19_000_000
    assert res.is_floor_capped is True
    assert res.price_delta_amount == -1_000_000
    assert res.price_delta_pct == -0.05
    # Cả rate-cap và floor-cap đều xuất hiện trong notes
    assert any("Rate-of-change cap activated" in note for note in res.guardrail_notes)
    assert any("Margin floor protection activated" in note for note in res.guardrail_notes)


def test_guardrails_predatory_pricing_conditions():
    """Kiểm tra điều kiện phát hiện đối thủ bán phá giá (< 80% giá vốn)."""
    guard = SafetyGuardrails()
    cost = 10_000_000
    threshold = int(cost * 0.8)  # 8,000,000

    # 1. Bán dưới ngưỡng: 7,999,999 -> Cảnh báo
    res_below = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.0,
        floor_price=9_000_000,
        cost_price=cost,
        competitor_price=threshold - 1,
    )
    assert any("Predatory pricing warning" in note for note in res_below.guardrail_notes)

    # 2. Bán đúng bằng ngưỡng: 8,000,000 -> Không cảnh báo
    res_equal = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.0,
        floor_price=9_000_000,
        cost_price=cost,
        competitor_price=threshold,
    )
    assert not any("Predatory pricing warning" in note for note in res_equal.guardrail_notes)

    # 3. Không có đối thủ (None): Không cảnh báo
    res_none = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.0,
        floor_price=9_000_000,
        cost_price=cost,
        competitor_price=None,
    )
    assert not any("Predatory pricing warning" in note for note in res_none.guardrail_notes)


# ---------------------------------------------------------------------------
# 5. Test API Simulation Endpoint (/api/v1/pricing/matrix/simulate) across All 10 Scenarios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scores_tuple,expected_name,expected_delta,expected_action,_", SCENARIO_TEST_DATA)
def test_api_simulate_all_10_scenarios(client, scores_tuple, expected_name, expected_delta, expected_action, _):
    """Kiểm tra toàn bộ 10 kịch bản khi gửi request qua endpoint /matrix/simulate."""
    d, i, c = scores_tuple
    current_price = 20_000_000
    cost_price = 15_000_000
    floor_price = 16_000_000

    payload = {
        "demand_score": d,
        "inventory_score": i,
        "competitor_score": c,
        "current_price": current_price,
        "cost_price": cost_price,
        "floor_price": floor_price,
        "competitor_price": 21_000_000,
        "max_rate_cap": 0.15,  # Cho phép biên độ rộng để kiểm tra delta tự nhiên
    }
    response = client.post("/api/v1/pricing/matrix/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["scenario_name"] == expected_name
    assert data["action_type"] == expected_action
    assert data["target_delta_pct"] == expected_delta

    # Expected target price
    expected_recommended = int(round(current_price * (1.0 + expected_delta)))
    assert data["recommended_price"] == expected_recommended
    assert data["price_delta_amount"] == expected_recommended - current_price

    # Verify zero emojis
    assert_no_emojis(data["scenario_name"])
    assert_no_emojis(data["rationale"])
    for note in data["guardrail_notes"]:
        assert_no_emojis(note)


# ---------------------------------------------------------------------------
# 6. Test PricingEngine DB Integration across Scenarios & State Lifecycle
# ---------------------------------------------------------------------------

def test_pricing_engine_generates_all_10_scenarios_in_db(db_session):
    """Kiểm tra PricingEngine tạo đề xuất trong database khớp với kịch bản được mock."""
    for idx, (scores_tuple, expected_name, expected_delta, expected_action, _) in enumerate(SCENARIO_TEST_DATA):
        # Tạo product riêng cho từng test case
        prod = Product(
            id=uuid.uuid4(),
            sku=f"SKU-SCENARIO-{idx:02d}",
            name=f"Sản phẩm kịch bản {idx}",
            category="PHONE",
            brand="Apple",
            base_retail_price=20_000_000,
            cost_price=15_000_000,
            floor_price=16_000_000,
            min_margin_pct=5.0,
            is_active=True,
        )
        db_session.add(prod)

        inv = InventoryMock(
            fpt_product_id=prod.id,
            stock_quantity=50,
            doh=20,
            cost_price=15_000_000,
            floor_price=16_000_000,
        )
        db_session.add(inv)
        db_session.commit()

        # Mock SignalScores thông qua custom extractor
        class MockExtractor(SignalsExtractor):
            def __init__(self, scores):
                self.scores = scores
            def extract_signals(self, db, product_id):
                return self.scores
            def extract_reasoning_details(self, db, product_id):
                return {
                    "competitor_factor": "Gia doi thu on dinh",
                    "inventory_factor": "Ton kho binh thuong",
                    "market_demand_factor": "Nhu cau tieu chuan",
                }

        custom_engine = PricingEngine(signals_extractor=MockExtractor(SignalScores(*scores_tuple)))
        rec = custom_engine.generate_for_product(db_session, prod.id)

        assert rec.scenario_name == expected_name
        assert rec.status == "PENDING"
        assert rec.current_fpt_price == 20_000_000

        # Kiểm tra 3 lớp giải trình reasoning_3layers
        assert "competitor_factor" in rec.reasoning_3layers
        assert "inventory_factor" in rec.reasoning_3layers
        assert "market_demand_factor" in rec.reasoning_3layers
        assert "floor_protection_factor" in rec.reasoning_3layers
        assert "guardrail_notes" in rec.reasoning_3layers
        assert isinstance(rec.reasoning_3layers["guardrail_notes"], list)

        # Kiểm tra zero emojis
        assert_no_emojis(rec.scenario_name)
        assert_no_emojis(rec.reasoning_3layers["floor_protection_factor"])


def test_pricing_engine_lifecycle_pending_update_vs_approved_create(db_session, test_product):
    """Kiểm tra vòng đời đề xuất:
    - Khi đang PENDING: Chạy lại cập nhật in-place, không tạo thêm bản ghi.
    - Khi đã APPROVED: Chạy lại tạo đề xuất PENDING mới, giữ nguyên lịch sử cũ.
    """
    engine = PricingEngine()

    # Lần 1: Tạo mới PENDING
    rec1 = engine.generate_for_product(db_session, test_product.id)
    assert rec1.status == "PENDING"
    rec1_id = rec1.id

    # Lần 2: Rerun khi vẫn PENDING -> cập nhật in-place
    rec2 = engine.generate_for_product(db_session, test_product.id)
    assert rec2.id == rec1_id
    count_pending = (
        db_session.query(PriceRecommendation)
        .filter(PriceRecommendation.fpt_product_id == test_product.id)
        .count()
    )
    assert count_pending == 1

    # Phê duyệt đề xuất rec2
    rec2.status = "APPROVED"
    rec2.reviewed_by = "Pricing Manager"
    rec2.reviewed_at = datetime.now(timezone.utc)
    db_session.commit()

    # Lần 3: Rerun sau khi đã APPROVED -> tạo bản ghi PENDING mới
    rec3 = engine.generate_for_product(db_session, test_product.id)
    assert rec3.id != rec1_id
    assert rec3.status == "PENDING"

    total_recs = (
        db_session.query(PriceRecommendation)
        .filter(PriceRecommendation.fpt_product_id == test_product.id)
        .count()
    )
    assert total_recs == 2


def test_pricing_engine_out_of_stock_competitor_handling(db_session, test_product):
    """Kiểm tra đối thủ hết hàng (is_in_stock = False) bị loại khỏi giá rẻ nhất (competitor_min_price)."""
    job = CrawlJob(source="CELLPHONES", status="COMPLETED")
    db_session.add(job)
    db_session.commit()

    # Đối thủ 1: Rất rẻ nhưng hết hàng (OOS)
    c_oos = CrawlResult(
        job_id=job.id,
        source="CELLPHONES",
        url="https://cellphones.com.vn/oos-product.html",
        raw_name="ThinkPad T14",
        current_price=18_000_000,
        is_in_stock=False,
    )
    # Đối thủ 2: Giá cao hơn nhưng còn hàng (In Stock)
    c_instock = CrawlResult(
        job_id=job.id,
        source="HOANGHA",
        url="https://hoanghamobile.com/instock-product.html",
        raw_name="ThinkPad T14",
        current_price=24_000_000,
        is_in_stock=True,
    )
    db_session.add_all([c_oos, c_instock])
    db_session.commit()

    map1 = SkuMapping(
        fpt_product_id=test_product.id,
        competitor_crawl_id=c_oos.id,
        match_type="EXACT_PN",
        status="APPROVED",
    )
    map2 = SkuMapping(
        fpt_product_id=test_product.id,
        competitor_crawl_id=c_instock.id,
        match_type="EXACT_PN",
        status="APPROVED",
    )
    db_session.add_all([map1, map2])
    db_session.commit()

    engine = PricingEngine()
    rec = engine.generate_for_product(db_session, test_product.id)

    # competitor_min_price phải là 24,000,000 (bỏ qua giá 18M hết hàng)
    assert rec.competitor_min_price == 24_000_000


def test_pricing_engine_batch_processes_only_active_products(db_session):
    """Kiểm tra generate_batch chỉ xử lý các sản phẩm active (is_active=True)."""
    p_active = Product(
        sku="SKU-ACT-101",
        name="San pham active",
        category="PHONE",
        brand="Apple",
        base_retail_price=10_000_000,
        is_active=True,
    )
    p_inactive = Product(
        sku="SKU-INACT-102",
        name="San pham inactive",
        category="PHONE",
        brand="Apple",
        base_retail_price=10_000_000,
        is_active=False,
    )
    db_session.add_all([p_active, p_inactive])
    db_session.commit()

    engine = PricingEngine()
    results = engine.generate_batch(db_session)

    res_product_ids = {r.fpt_product_id for r in results}
    assert p_active.id in res_product_ids
    assert p_inactive.id not in res_product_ids
