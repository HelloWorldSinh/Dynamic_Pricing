import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    Product,
    CrawlJob,
    CrawlResult,
    SkuMapping,
    InventoryMock,
    Warehouse,
    InventorySnapshot,
    DemandEvent,
    DemandHourlyAggregate,
    PriceRecommendation,
    PriceHistory,
    PricingAuditLog,
    ChatSession,
    ChatMessage,
)


@pytest.fixture(scope="function")
def db_session():
    """Tạo in-memory SQLite database để test toàn bộ schema CSDL."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_all_tables_registered_in_metadata():
    """Kiểm tra toàn bộ 13 bảng nghiệp vụ đã được định nghĩa trong SQLAlchemy metadata."""
    expected_tables = {
        "products",
        "crawl_jobs",
        "crawl_results",
        "sku_mappings",
        "inventory_mock",
        "warehouses",
        "inventory_snapshots",
        "demand_events",
        "demand_hourly_aggregates",
        "price_recommendations",
        "price_history",
        "pricing_audit_logs",
        "chat_sessions",
        "chat_messages",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_complete_data_flow_persistence(db_session):
    """Kiểm thử tính toàn vẹn dữ liệu xuyên suốt 6 phân hệ CSDL."""
    now = datetime.now(timezone.utc)

    # 1. Product Catalog
    product = Product(
        sku="SKU-TEST-001",
        name="iPhone 15 Pro Max 256GB Titan Tự Nhiên",
        category="PHONE",
        brand="Apple",
        part_number="MU773VN/A",
        specs={"cpu": "A17 Pro", "ram": "8GB", "storage": "256GB", "color": "Natural Titanium"},
        cost_price=26000000,
        min_margin_pct=5.0,
        floor_price=27300000,
        base_retail_price=29990000,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    assert product.id is not None

    # 2. Crawler & Job
    crawl_job = CrawlJob(
        trigger_type="ON_DEMAND",
        source="CELLPHONES",
        category="PHONE",
        status="COMPLETED",
        total_items=1,
        success_items=1,
    )
    db_session.add(crawl_job)
    db_session.commit()
    db_session.refresh(crawl_job)

    crawl_result = CrawlResult(
        job_id=crawl_job.id,
        source="CELLPHONES",
        url="https://cellphones.com.vn/iphone-15-pro-max-256gb.html",
        raw_name="iPhone 15 Pro Max 256GB Chính Hãng VN/A",
        current_price=29490000,
        original_price=34990000,
        is_in_stock=True,
        stock_status_text="Còn hàng",
    )
    db_session.add(crawl_result)
    db_session.commit()
    db_session.refresh(crawl_result)

    # 3. SKU Mapping
    mapping = SkuMapping(
        fpt_product_id=product.id,
        competitor_crawl_id=crawl_result.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=1.0,
        status="APPROVED",
    )
    db_session.add(mapping)

    # 4. Multi-Warehouse Inventory
    warehouse = Warehouse(
        warehouse_id="WH-HN-01",
        warehouse_name="Tổng kho FPT Shop Hà Nội",
        region="NORTH",
    )
    db_session.add(warehouse)
    db_session.commit()

    inv_snapshot = InventorySnapshot(
        fpt_product_id=product.id,
        warehouse_id=warehouse.warehouse_id,
        qty_on_hand=50,
        qty_reserved=5,
        qty_available=45,
        stock_cover_days=22,
        is_obsolescence_risk=False,
    )
    db_session.add(inv_snapshot)

    # 5. Demand Telemetry
    demand_event = DemandEvent(
        event_id="EVT-0001",
        fpt_product_id=product.id,
        session_id="SESS-12345",
        event_type="view",
        time_on_page_sec=120,
        scroll_depth_pct=85,
    )
    db_session.add(demand_event)

    hourly_aggregate = DemandHourlyAggregate(
        fpt_product_id=product.id,
        aggregate_hour=now,
        total_views=150,
        purchases=12,
        cvr_pct=8.0,
        demand_score=1.25,
    )
    db_session.add(hourly_aggregate)

    # 6. Pricing Engine Recommendation & Price History
    recommendation = PriceRecommendation(
        fpt_product_id=product.id,
        current_fpt_price=29990000,
        competitor_min_price=29490000,
        recommended_price=29390000,
        price_delta_amount=-600000,
        price_delta_pct=-2.0,
        demand_score=1.2,
        inventory_score=0.8,
        competitor_score=-0.5,
        composite_score=0.635,
        scenario_name="Slight Raise / Match Competitor",
        reasoning_3layers={
            "competitor_factor": "CellphoneS bán 29.49M, còn hàng",
            "inventory_factor": "DOH 22 ngày nằm trong ngưỡng an toàn",
            "floor_protection": "Giá đề xuất 29.39M cao hơn giá sàn 27.30M",
        },
        is_floor_capped=False,
        status="PENDING",
    )
    db_session.add(recommendation)
    db_session.commit()
    db_session.refresh(recommendation)

    price_history = PriceHistory(
        fpt_product_id=product.id,
        source="FPTSHOP",
        price=29990000,
        is_in_stock=True,
    )
    db_session.add(price_history)

    audit_log = PricingAuditLog(
        actor="System",
        action="CREATE_RECOMMENDATION",
        entity_type="price_recommendations",
        entity_id=recommendation.id,
        new_value={"recommended_price": 29390000},
    )
    db_session.add(audit_log)

    # 7. AI Chat Assistant
    chat_session = ChatSession(
        user_id="analyst_01",
        title="Phân tích giá iPhone 15 Pro Max",
    )
    db_session.add(chat_session)
    db_session.commit()
    db_session.refresh(chat_session)

    chat_message = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content="Giá đề xuất 29.39M được đưa ra do CellphoneS đang bán 29.49M và tồn kho FPT Shop ở mức 22 ngày DOH.",
        intent="PRICE_EXPLANATION",
        retrieved_context={"sku": "SKU-TEST-001", "recommended_price": 29390000},
    )
    db_session.add(chat_message)
    db_session.commit()

    # Assertions
    assert len(product.mappings) == 1
    assert len(product.inventory_snapshots) == 1
    assert len(product.demand_events) == 1
    assert len(product.price_recommendations) == 1
    assert len(product.price_history) == 1
    assert len(recommendation.audit_logs) == 1
    assert len(chat_session.messages) == 1
    assert chat_session.messages[0].intent == "PRICE_EXPLANATION"
