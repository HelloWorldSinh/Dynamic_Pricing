import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models import Product, CrawlResult, SkuMapping, PricingAuditLog


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
def setup_pending_mapping(db_session):
    prod = Product(
        id=uuid.uuid4(),
        sku="SKU-FPT-ASUS-VIVO15",
        name="Laptop Asus Vivobook 15 X1504ZA",
        category="LAPTOP",
        brand="ASUS",
        part_number="X1504ZA-NJ517W",
        base_retail_price=11_990_000,
        cost_price=10_000_000,
        floor_price=10_500_000,
        is_active=True,
    )
    db_session.add(prod)
    db_session.flush()

    crawl = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="https://cellphones.com.vn/laptop-asus-vivobook-15.html",
        raw_name="Laptop ASUS Vivobook 15 X1504ZA 8GB 512GB",
        current_price=11_490_000,
        is_in_stock=True,
        raw_specs={"ram": "8GB", "storage": "512GB"},
        crawled_at=datetime.now(timezone.utc),
    )
    db_session.add(crawl)
    db_session.flush()

    mapping = SkuMapping(
        id=uuid.uuid4(),
        fpt_product_id=prod.id,
        competitor_crawl_id=crawl.id,
        match_type="NORMALIZED_ATTRIBUTE",
        confidence_score=0.745,
        status="PENDING",
        matched_at=datetime.now(timezone.utc),
    )
    db_session.add(mapping)
    db_session.commit()
    db_session.refresh(mapping)
    return prod, crawl, mapping


def test_get_matching_queue_pending_items(client, db_session, setup_pending_mapping):
    prod, crawl, mapping = setup_pending_mapping
    response = client.get("/api/v1/matching/queue")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    item = next(it for it in data if it["id"] == str(mapping.id))
    assert item["fpt_sku"] == prod.sku
    assert item["fpt_name"] == prod.name
    assert item["competitor_source"] == "CELLPHONES"
    assert item["competitor_price"] == 11_490_000
    assert item["status"] == "PENDING"
    assert item["confidence_score"] == 74.5
    assert isinstance(item["matched_attributes"], list)
    assert isinstance(item["differing_attributes"], list)


def test_approve_matching_queue_item(client, db_session, setup_pending_mapping):
    _, _, mapping = setup_pending_mapping
    response = client.post(f"/api/v1/matching/queue/{mapping.id}/approve")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"

    # Verify db status
    db_session.refresh(mapping)
    assert mapping.status == "APPROVED"


def test_reject_matching_queue_item(client, db_session, setup_pending_mapping):
    _, _, mapping = setup_pending_mapping
    response = client.post(f"/api/v1/matching/queue/{mapping.id}/reject")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"

    # Verify db status
    db_session.refresh(mapping)
    assert mapping.status == "REJECTED"
