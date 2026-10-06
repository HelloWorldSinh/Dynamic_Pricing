import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models import (
    Product,
    InventoryMock,
    CrawlJob,
    CrawlResult,
    SkuMapping,
    PriceRecommendation,
    PricingAuditLog,
)


@pytest.fixture
def client(db_session):
    """TestClient fixture overriding get_db dependency with test db_session."""
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
def sample_product_with_inventory(db_session):
    """Fixture tạo sản phẩm FPT mẫu kèm tồn kho và đối thủ phục vụ test API."""
    product = Product(
        id=uuid.uuid4(),
        sku="SKU-FPT-API-001",
        name="iPhone 15 Pro Max 256GB Titan Tự Nhiên",
        category="PHONE",
        brand="Apple",
        base_retail_price=30_000_000,
        cost_price=25_000_000,
        floor_price=26_000_000,
        min_margin_pct=5.0,
        is_active=True,
    )
    db_session.add(product)

    inv = InventoryMock(
        fpt_product_id=product.id,
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
        fpt_product_id=product.id,
        competitor_crawl_id=crawl.id,
        match_type="EXACT_PN",
        confidence_score=1.0,
        status="APPROVED",
    )
    db_session.add(mapping)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_second_product(db_session):
    """Fixture tạo sản phẩm thứ 2 đang active."""
    product2 = Product(
        id=uuid.uuid4(),
        sku="SKU-FPT-API-002",
        name="Samsung Galaxy S24 Ultra 256GB Xam Titan",
        category="PHONE",
        brand="Samsung",
        base_retail_price=28_000_000,
        cost_price=23_000_000,
        floor_price=24_000_000,
        min_margin_pct=5.0,
        is_active=True,
    )
    db_session.add(product2)

    inv2 = InventoryMock(
        fpt_product_id=product2.id,
        stock_quantity=30,
        doh=15,
        cost_price=23_000_000,
        floor_price=24_000_000,
    )
    db_session.add(inv2)
    db_session.commit()
    db_session.refresh(product2)
    return product2


def test_api_generate_and_approve_recommendation(client, sample_product_with_inventory):
    """Test tạo đề xuất giá cho một sản phẩm và duyệt đề xuất (Approval workflow)."""
    # 1. Trigger generate recommendation cho 1 san pham
    res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(sample_product_with_inventory.id)},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1

    rec_data = data["items"][0]
    rec_id = rec_data["id"]
    assert rec_data["fpt_product_id"] == str(sample_product_with_inventory.id)
    assert rec_data["current_fpt_price"] == 30_000_000
    assert rec_data["status"] == "PENDING"
    assert rec_data["recommended_price"] > 0
    assert "composite_score" in rec_data
    assert "scenario_name" in rec_data
    assert "reasoning_3layers" in rec_data

    # 2. Action Approve
    act_res = client.post(
        f"/api/v1/pricing/recommendations/{rec_id}/action",
        json={"action": "APPROVE", "reviewed_by": "HaiNN58"},
    )
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["id"] == rec_id
    assert act_data["status"] == "APPROVED"
    assert act_data["reviewed_by"] == "HaiNN58"
    assert act_data["reviewed_at"] is not None

    # 3. Kiem tra audit log tuong ung
    audit_res = client.get(f"/api/v1/pricing/audit-logs?entity_id={rec_id}")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total"] >= 1
    log_item = audit_data["items"][0]
    assert log_item["action"] == "APPROVE_PRICE"
    assert log_item["actor"] == "HaiNN58"
    assert log_item["entity_type"] == "price_recommendations"
    assert log_item["old_value"]["status"] == "PENDING"
    assert log_item["new_value"]["status"] == "APPROVED"


def test_api_generate_recommendation_with_custom_weights(client, sample_product_with_inventory):
    """Test tạo đề xuất với trọng số tùy biến custom_weights."""
    res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={
            "fpt_product_id": str(sample_product_with_inventory.id),
            "custom_weights": {"D": 0.5, "I": 0.3, "C": 0.2},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["fpt_product_id"] == str(sample_product_with_inventory.id)


def test_api_generate_recommendations_batch(client, sample_product_with_inventory, sample_second_product):
    """Test tạo đề xuất hàng loạt cho toàn bộ sản phẩm active."""
    res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    product_ids = [item["fpt_product_id"] for item in data["items"]]
    assert str(sample_product_with_inventory.id) in product_ids
    assert str(sample_second_product.id) in product_ids


def test_api_generate_recommendation_not_found(client):
    """Test tạo đề xuất cho sản phẩm không tồn tại trả về 404."""
    random_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": random_id},
    )
    assert res.status_code == 404
    assert f"Product with id '{random_id}' not found" in res.json()["detail"]


def test_api_list_recommendations_with_filters(client, sample_product_with_inventory):
    """Test tra cứu danh sách đề xuất kèm bộ lọc status, scenario_name, is_floor_capped và phân trang."""
    # Sinh de xuat
    gen_res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(sample_product_with_inventory.id)},
    )
    assert gen_res.status_code == 200
    scenario_name = gen_res.json()["items"][0]["scenario_name"]

    # Loc theo status=PENDING
    list_res = client.get("/api/v1/pricing/recommendations?status=PENDING&skip=0&limit=10")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["fpt_product_id"] == str(sample_product_with_inventory.id) for item in list_data["items"])

    # Loc theo scenario_name
    scenario_res = client.get(f"/api/v1/pricing/recommendations?scenario_name={scenario_name}")
    assert scenario_res.status_code == 200
    assert scenario_res.json()["total"] >= 1

    # Loc theo status=APPROVED khi chua co ai duyet
    approved_res = client.get("/api/v1/pricing/recommendations?status=APPROVED")
    assert approved_res.status_code == 200
    assert approved_res.json()["total"] == 0


def test_api_get_recommendation_by_id(client, sample_product_with_inventory):
    """Test xem chi tiết một đề xuất giá theo id."""
    # Sinh de xuat
    gen_res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(sample_product_with_inventory.id)},
    )
    rec_id = gen_res.json()["items"][0]["id"]

    # Lay chi tiet theo id
    detail_res = client.get(f"/api/v1/pricing/recommendations/{rec_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == rec_id
    assert detail_data["fpt_product_id"] == str(sample_product_with_inventory.id)

    # Id khong ton tai tra ve 404
    fake_id = str(uuid.uuid4())
    not_found_res = client.get(f"/api/v1/pricing/recommendations/{fake_id}")
    assert not_found_res.status_code == 404
    assert "Price recommendation not found" in not_found_res.json()["detail"]


def test_api_action_reject_recommendation(client, sample_product_with_inventory):
    """Test từ chối đề xuất giá (Reject) và ghi nhận lý do từ chối."""
    gen_res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(sample_product_with_inventory.id)},
    )
    rec_id = gen_res.json()["items"][0]["id"]

    reject_res = client.post(
        f"/api/v1/pricing/recommendations/{rec_id}/action",
        json={
            "action": "REJECT",
            "reviewed_by": "PricingSpecialist",
            "rejection_reason": "Doi thu sap het hang khuyen mai",
        },
    )
    assert reject_res.status_code == 200
    data = reject_res.json()
    assert data["status"] == "REJECTED"
    assert data["reviewed_by"] == "PricingSpecialist"
    assert data["rejection_reason"] == "Doi thu sap het hang khuyen mai"
    assert data["reviewed_at"] is not None

    # Kiem tra audit log
    audit_res = client.get(f"/api/v1/pricing/audit-logs?entity_id={rec_id}")
    assert audit_res.status_code == 200
    logs = audit_res.json()["items"]
    assert any(log["action"] == "REJECT_PRICE" and log["actor"] == "PricingSpecialist" for log in logs)


def test_api_action_validation_errors(client, sample_product_with_inventory):
    """Test cac ngoai le va loi nghiep vu khi thao tac action."""
    gen_res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(sample_product_with_inventory.id)},
    )
    rec_id = gen_res.json()["items"][0]["id"]

    # 1. Action khong hop le (khac APPROVE / REJECT)
    invalid_act_res = client.post(
        f"/api/v1/pricing/recommendations/{rec_id}/action",
        json={"action": "INVALID_ACTION", "reviewed_by": "User1"},
    )
    assert invalid_act_res.status_code == 400
    assert invalid_act_res.json()["detail"] == "Action must be APPROVE or REJECT."

    # 2. Duyet thanh cong lan 1
    approve_res = client.post(
        f"/api/v1/pricing/recommendations/{rec_id}/action",
        json={"action": "APPROVE", "reviewed_by": "User1"},
    )
    assert approve_res.status_code == 200

    # 3. Thao tac tiep khi ban ghi da duoc xu ly (status khac PENDING)
    second_act_res = client.post(
        f"/api/v1/pricing/recommendations/{rec_id}/action",
        json={"action": "APPROVE", "reviewed_by": "User2"},
    )
    assert second_act_res.status_code == 400
    assert second_act_res.json()["detail"] == "Recommendation has already been processed."

    # 4. Action tren recommendation khong ton tai
    fake_id = str(uuid.uuid4())
    fake_res = client.post(
        f"/api/v1/pricing/recommendations/{fake_id}/action",
        json={"action": "APPROVE", "reviewed_by": "User1"},
    )
    assert fake_res.status_code == 404
    assert "Price recommendation not found" in fake_res.json()["detail"]


def test_api_list_audit_logs_filters_and_pagination(client, sample_product_with_inventory):
    """Test xem danh sach audit log kem bo loc actor, entity_id va phan trang."""
    # Sinh va duyet
    gen_res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(sample_product_with_inventory.id)},
    )
    rec_id = gen_res.json()["items"][0]["id"]

    client.post(
        f"/api/v1/pricing/recommendations/{rec_id}/action",
        json={"action": "APPROVE", "reviewed_by": "AuditTester"},
    )

    # Loc theo actor
    actor_res = client.get("/api/v1/pricing/audit-logs?actor=AuditTester")
    assert actor_res.status_code == 200
    actor_data = actor_res.json()
    assert actor_data["total"] >= 1
    assert all(item["actor"] == "AuditTester" for item in actor_data["items"])

    # Loc theo entity_id
    entity_res = client.get(f"/api/v1/pricing/audit-logs?entity_id={rec_id}")
    assert entity_res.status_code == 200
    entity_data = entity_res.json()
    assert entity_data["total"] >= 1
    assert all(item["entity_id"] == rec_id for item in entity_data["items"])

    # Phân trang
    paged_res = client.get("/api/v1/pricing/audit-logs?skip=0&limit=1")
    assert paged_res.status_code == 200
    assert len(paged_res.json()["items"]) <= 1


def test_api_generate_recommendation_non_positive_price(client, db_session):
    """Test sinh de xuat cho san pham co gia bang 0 tra ve 400 Bad Request."""
    bad_product = Product(
        sku="SKU-ZERO-PRICE-API",
        name="San pham gia 0 VND",
        category="PHONE",
        base_retail_price=0,
        is_active=True,
    )
    db_session.add(bad_product)
    db_session.commit()

    res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(bad_product.id)},
    )
    assert res.status_code == 400
    assert "has non-positive current price" in res.json()["detail"]


def test_api_list_recommendations_floor_capped_filter(client, sample_product_with_inventory):
    """Test loc danh sach de xuat theo cờ is_floor_capped."""
    # Sinh de xuat
    client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(sample_product_with_inventory.id)},
    )

    # Loc is_floor_capped=True
    res_true = client.get("/api/v1/pricing/recommendations?is_floor_capped=true")
    assert res_true.status_code == 200
    assert all(item["is_floor_capped"] is True for item in res_true.json()["items"])

    # Loc is_floor_capped=false
    res_false = client.get("/api/v1/pricing/recommendations?is_floor_capped=false")
    assert res_false.status_code == 200
    assert all(item["is_floor_capped"] is False for item in res_false.json()["items"])


def test_zero_emojis_or_icons_in_pricing_api(client, sample_product_with_inventory):
    """Kiem tra tuyet doi khong co emoji hoac icon trang tri trong response va OpenAPI schema."""
    def contains_emoji(text: str) -> bool:
        for char in text:
            code = ord(char)
            if (
                0x1F600 <= code <= 0x1F64F
                or 0x1F300 <= code <= 0x1F5FF
                or 0x1F680 <= code <= 0x1F6FF
                or 0x1F1E0 <= code <= 0x1F1FF
                or 0x2600 <= code <= 0x26FF
                or 0x2700 <= code <= 0x27BF
            ):
                return True
        return False

    # 1. Kiem tra OpenAPI spec cho router /pricing
    openapi_res = client.get("/openapi.json")
    assert openapi_res.status_code == 200
    openapi_data = openapi_res.json()
    for path, path_item in openapi_data.get("paths", {}).items():
        if "/pricing" in path:
            for method, op_data in path_item.items():
                summary = op_data.get("summary", "")
                description = op_data.get("description", "")
                assert not contains_emoji(summary), f"Found emoji in OpenAPI summary: {summary}"
                assert not contains_emoji(description), f"Found emoji in OpenAPI description: {description}"

    # 2. Kiem tra response payload
    gen_res = client.post(
        "/api/v1/pricing/recommendations/generate",
        json={"fpt_product_id": str(sample_product_with_inventory.id)},
    )
    rec_item = gen_res.json()["items"][0]
    assert not contains_emoji(rec_item["scenario_name"])
    for k, v in rec_item["reasoning_3layers"].items():
        assert not contains_emoji(str(v))


def test_get_pricing_matrix_endpoint(client, sample_product_with_inventory):
    """Kiem tra endpoint GET /api/v1/pricing/matrix tra ve du lieu doi soat 3 ben."""
    res = client.get("/api/v1/pricing/matrix")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert item["sku"] == sample_product_with_inventory.sku
    assert item["name"] == sample_product_with_inventory.name
    assert item["fpt_price"] == sample_product_with_inventory.base_retail_price
    assert item["cellphones"] is not None
    assert item["cellphones"]["source"] == "CELLPHONES"
    assert item["min_competitor_price"] == item["cellphones"]["price"]
    assert "status" in item
    assert item["status"] in ["SAFE", "WARNING", "DANGER", "EQUAL"]


def test_get_pricing_history_endpoint(client, sample_product_with_inventory, db_session):
    """Kiem tra endpoint GET /api/v1/pricing/history tra ve lich su thay doi gia."""
    # Tao ban ghi mau
    from app.models.pricing import PriceHistory
    from datetime import datetime, timezone
    hist = PriceHistory(
        fpt_product_id=sample_product_with_inventory.id,
        source="FPTSHOP",
        price=31_000_000,
        is_in_stock=True,
        recorded_at=datetime.now(timezone.utc),
    )
    db_session.add(hist)
    db_session.commit()

    res = client.get("/api/v1/pricing/history")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert item["sku"] == sample_product_with_inventory.sku
    assert item["new_price"] == 31_000_000


