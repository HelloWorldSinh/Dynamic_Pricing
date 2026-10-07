import uuid
from datetime import datetime, timezone
import pytest
from app.models import (
    Product,
    InventoryMock,
    Warehouse,
    InventorySnapshot,
    DemandHourlyAggregate,
    SkuMapping,
    CrawlJob,
    CrawlResult,
)
from app.services.pricing.signals import SignalsExtractor
from app.services.pricing.schemas import SignalScores


@pytest.fixture
def sample_product(db_session):
    p = Product(
        id=uuid.uuid4(),
        sku="SKU-FPT-001",
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
    db_session.commit()
    return p



def test_inventory_score_scarce_and_excess(db_session, sample_product):
    extractor = SignalsExtractor()

    # Fallback when no inventory exists
    assert extractor.calculate_inventory_score(db_session, sample_product.id) == 0.0

    # 1. Scarce stock: DOH = 5 days -> I = +2.0
    inv = InventoryMock(
        fpt_product_id=sample_product.id,
        stock_quantity=10,
        doh=5,
        cost_price=25_000_000,
        floor_price=26_000_000,
    )
    db_session.add(inv)
    db_session.commit()
    assert extractor.calculate_inventory_score(db_session, sample_product.id) == 2.0

    # 2. Excess stock: DOH = 50 days (> 45 days) -> I = -2.0
    inv.doh = 50
    db_session.commit()
    assert extractor.calculate_inventory_score(db_session, sample_product.id) == -2.0

    # 3. Normal stock: DOH = 25 days -> I = 0.0
    inv.doh = 25
    db_session.commit()
    assert extractor.calculate_inventory_score(db_session, sample_product.id) == 0.0


def test_inventory_score_with_snapshot_and_obsolescence(db_session, sample_product):
    extractor = SignalsExtractor()
    wh = Warehouse(warehouse_id="WH-HN-01", warehouse_name="Kho Hà Nội", region="NORTH")
    db_session.add(wh)
    db_session.commit()

    # Obsolescence risk -> I = -2.0
    snap = InventorySnapshot(
        fpt_product_id=sample_product.id,
        warehouse_id="WH-HN-01",
        qty_on_hand=100,
        qty_available=100,
        target_stock=100,
        stock_cover_days=30,
        is_obsolescence_risk=True,
    )
    db_session.add(snap)
    db_session.commit()

    assert extractor.calculate_inventory_score(db_session, sample_product.id) == -2.0


def test_demand_score_evaluation(db_session, sample_product):
    extractor = SignalsExtractor()

    # Fallback with no demand data
    assert extractor.calculate_demand_score(db_session, sample_product.id) == 0.0

    # Surge demand: high CVR and views
    agg = DemandHourlyAggregate(
        fpt_product_id=sample_product.id,
        aggregate_hour=datetime.now(timezone.utc),
        total_views=200,
        search_clicks=60,
        cart_adds=30,
        purchases=15,
        cvr_pct=7.5,
        demand_score=2.0,
    )
    db_session.add(agg)
    db_session.commit()

    assert extractor.calculate_demand_score(db_session, sample_product.id) == 2.0


def test_competitor_score_evaluation(db_session, sample_product):
    extractor = SignalsExtractor()

    # Fallback when no competitor mapped
    assert extractor.calculate_competitor_score(db_session, sample_product.id) == 0.0

    job = CrawlJob(source="CELLPHONES", status="COMPLETED")
    db_session.add(job)
    db_session.commit()

    # Case 1: Competitor is much cheaper (>15% cheaper)
    # FPT = 30,000,000 -> Competitor = 25,000,000 (diff = -16.67%) -> C = -2.0
    c_res1 = CrawlResult(
        job_id=job.id,
        source="CELLPHONES",
        url="https://cellphones.com.vn/iphone-15-pro-max.html",
        raw_name="iPhone 15 Pro Max 256GB VN/A",
        current_price=25_000_000,
        is_in_stock=True,
    )
    db_session.add(c_res1)
    db_session.commit()

    mapping = SkuMapping(
        fpt_product_id=sample_product.id,
        competitor_crawl_id=c_res1.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=0.95,
        status="APPROVED",
    )

    db_session.add(mapping)
    db_session.commit()

    assert extractor.calculate_competitor_score(db_session, sample_product.id) == -2.0

    # Case 2: Competitor is Out of Stock -> C = +2.0
    c_res1.is_in_stock = False
    db_session.commit()
    assert extractor.calculate_competitor_score(db_session, sample_product.id) == 2.0

    # Case 3: Competitor is more expensive (>15% higher)
    # Competitor = 35,000,000 -> C = +2.0
    c_res1.is_in_stock = True
    c_res1.current_price = 35_000_000
    db_session.commit()
    assert extractor.calculate_competitor_score(db_session, sample_product.id) == 2.0



def test_extract_signals_and_reasoning(db_session, sample_product):
    extractor = SignalsExtractor()
    scores = extractor.extract_signals(db_session, sample_product.id)
    assert isinstance(scores, SignalScores)

    reasoning = extractor.extract_reasoning_details(db_session, sample_product.id)
    assert "competitor_factor" in reasoning
    assert "inventory_factor" in reasoning
    assert "market_demand_factor" in reasoning
