import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models import (
    Product,
    InventoryMock,
    PriceRecommendation,
    PricingAuditLog,
    PriceHistory,
)


@pytest.fixture
def client(db_session):
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
def setup_recommendation(db_session):
    product = Product(
        id=uuid.uuid4(),
        sku="SKU-TEST-REC-001",
        name="iPhone 15 Pro 128GB",
        category="PHONE",
        brand="Apple",
        base_retail_price=28_000_000,
        cost_price=24_000_000,
        floor_price=25_000_000,
        min_margin_pct=5.0,
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()

    inv = InventoryMock(
        fpt_product_id=product.id,
        doh=35,
        stock_quantity=50,
        cost_price=24_000_000,
        floor_price=25_000_000,
    )
    db_session.add(inv)

    rec = PriceRecommendation(
        id=uuid.uuid4(),
        fpt_product_id=product.id,
        current_fpt_price=28_000_000,
        competitor_min_price=27_000_000,
        recommended_price=27_500_000,
        price_delta_amount=-500_000,
        price_delta_pct=-0.0179,
        demand_score=0.5,
        inventory_score=-0.2,
        competitor_score=0.8,
        composite_score=0.33,
        scenario_name="Kịch bản 4: Cầu cao nhưng Hàng ứ",
        reasoning_3layers={
            "competitor_factor": "Competitor cheaper",
            "inventory_factor": "DOH normal",
            "floor_protection_factor": "Safe",
        },
        is_floor_capped=False,
        status="PENDING",
    )
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)
    return product, rec


def test_reject_recommendation_endpoint(client, db_session, setup_recommendation):
    _, rec = setup_recommendation
    response = client.post(f"/api/v1/pricing/recommendations/{rec.id}/reject")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
    assert data["reviewed_by"] is not None

    # Check audit log
    audit = db_session.query(PricingAuditLog).filter(PricingAuditLog.entity_id == rec.id).first()
    assert audit is not None
    assert audit.action == "REJECT_PRICE"


def test_apply_custom_price_endpoint(client, db_session, setup_recommendation):
    prod, rec = setup_recommendation
    payload = {
        "custom_price": 27_200_000,
        "change_type": "MANUAL_CONFIG",
        "reviewed_by": "Senior Analyst",
    }
    response = client.post(f"/api/v1/pricing/recommendations/{rec.id}/apply-custom", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["recommended_price"] == 27_200_000
    assert data["reviewed_by"] == "Senior Analyst"

    # Check price history created
    hist = db_session.query(PriceHistory).filter(PriceHistory.fpt_product_id == prod.id).first()
    assert hist is not None
    assert hist.price == 27_200_000


def test_list_recommendations_enriched_fields(client, db_session, setup_recommendation):
    prod, rec = setup_recommendation
    response = client.get("/api/v1/pricing/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    item = next(it for it in data["items"] if it["id"] == str(rec.id))
    # Enriched fields
    assert item["sku"] == "SKU-TEST-REC-001"
    assert item["product_name"] == "iPhone 15 Pro 128GB"
    assert item["category"] == "PHONE"
    assert item["brand"] == "Apple"
    assert item["cost_price"] == 24_000_000
    assert item["floor_price"] == 25_000_000
    assert item["doh"] == 35
    assert item["inventory_quantity"] == 50
    assert item["current_price"] == 28_000_000
    assert item["suggested_price"] == 27_500_000
    assert item["scenario"] == "Kịch bản 4: Cầu cao nhưng Hàng ứ"
