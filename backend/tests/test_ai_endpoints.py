"""
Integration tests for AI Endpoints & Routing (Phase 3 of AI Pricing Assistant).
Follows TDD methodology & tests /api/v1/ai/chat, /explain/{sku}, and session management routes.
"""
import uuid
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.api.v1.endpoints import ai as ai_endpoint
from app.models.chat import ChatSession
from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.models.inventory import InventoryMock
from app.models.pricing import PriceRecommendation
from app.schemas.ai import ExplainableFactors
from app.services.ai.tools import (
    get_inventory_risks,
    get_price_discrepancies,
    get_sku_explain_factors,
)


@pytest.fixture
def client(db_session):
    """Fixture override get_db dependency to use the isolated test SQLite session."""
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
def mock_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dùng câu trả lời Gemini giả lập cho các test API thành công."""

    def generate_response(
        db: Session,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, Optional[List[Dict[str, Any]]], Optional[ExplainableFactors], Optional[str]]:
        normalized = message.lower()
        if "doh" in normalized or "tồn kho" in normalized:
            table_data = get_inventory_risks(db=db, doh_threshold=45)
            return "Kết quả tra cứu tồn kho.", table_data or None, None, "INVENTORY_RISK"

        if any(term in normalized for term in ("giải thích", "giải trình", "lý do")):
            sku = next(
                (
                    token.strip("\"'.,?!").upper()
                    for token in message.split()
                    if token.strip("\"'.,?!").upper().startswith(("FPT-", "SKU"))
                ),
                "",
            )
            factors = get_sku_explain_factors(db=db, sku=sku)
            return "Căn cứ giải trình giá.", None, factors, "PRICE_EXPLANATION"

        table_data = get_price_discrepancies(db=db, limit=5)
        return "Kết quả tra cứu giá đối thủ.", table_data or None, None, "COMPETITOR_LOOKUP"

    monkeypatch.setattr(
        ai_endpoint.chat_service.gemini_client,
        "generate_chat_response",
        generate_response,
    )


@pytest.fixture
def setup_ai_test_data(db_session):
    """Dữ liệu mẫu phục vụ kiểm thử API AI."""
    prod_id = uuid.uuid4()
    prod = Product(
        id=prod_id,
        sku="FPT-ASUS-VIVO15",
        name="Laptop ASUS Vivobook 15 OLED",
        category="LAPTOP",
        brand="ASUS",
        base_retail_price=18990000,
        cost_price=16000000,
        floor_price=17000000,
    )
    db_session.add(prod)
    db_session.flush()

    inv = InventoryMock(
        fpt_product_id=prod_id,
        stock_quantity=45,
        doh=52,
        cost_price=16000000,
        floor_price=17000000,
    )
    crawl = CrawlResult(
        id=uuid.uuid4(),
        source="CELLPHONES",
        url="http://cellphones.com/asus-vivo-15",
        raw_name="ASUS Vivobook 15 OLED",
        current_price=17990000,
        original_price=18990000,
        is_in_stock=True,
    )
    db_session.add_all([inv, crawl])
    db_session.flush()

    mapping = SkuMapping(
        fpt_product_id=prod_id,
        competitor_crawl_id=crawl.id,
        match_type="EXACT_PART_NUMBER",
        confidence_score=1.0,
        status="APPROVED",
    )
    rec = PriceRecommendation(
        id=uuid.uuid4(),
        fpt_product_id=prod_id,
        current_fpt_price=18990000,
        competitor_min_price=17990000,
        recommended_price=17890000,
        price_delta_amount=-1100000,
        price_delta_pct=-0.0579,
        demand_score=0.0,
        inventory_score=-2.0,
        competitor_score=-2.0,
        composite_score=-1.2,
        scenario_name="Kịch bản 4: DOH > 45 ngày",
        reasoning_3layers={"competitor_cut": 1000000},
        is_floor_capped=False,
    )
    db_session.add_all([mapping, rec])
    db_session.commit()
    return prod


def test_post_chat_competitor_lookup(client: TestClient, setup_ai_test_data, mock_gemini):
    """Kiểm thử gửi câu hỏi tra cứu đối thủ đến POST /api/v1/ai/chat."""
    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "Top laptop Asus đang bán đắt hơn CellphoneS"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "message" in data
    assert data["tableData"] is not None
    assert len(data["tableData"]) >= 1
    assert data["tableData"][0]["SKU"] == "FPT-ASUS-VIVO15"


def test_post_chat_inventory_risk(client: TestClient, setup_ai_test_data, mock_gemini):
    """Kiểm thử gửi câu hỏi cảnh báo rủi ro tồn kho đến POST /api/v1/ai/chat."""
    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "Cảnh báo tồn kho DOH >= 45 ngày"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["tableData"] is not None
    assert "FPT-ASUS-VIVO15" in [item["SKU"] for item in data["tableData"]]


def test_post_chat_sku_explain(client: TestClient, setup_ai_test_data, mock_gemini):
    """Kiểm thử gửi câu hỏi giải trình mã SKU đến POST /api/v1/ai/chat."""
    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "Giải thích lý do giảm giá FPT-ASUS-VIVO15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["explainFactors"] is not None
    factors = data["explainFactors"]
    assert factors["competitor_shift"]["competitor"] == "CellphoneS"
    assert factors["inventory_status"]["doh"] == 52
    assert factors["floor_protection"]["floor_price"] == 17000000.0


def test_post_chat_returns_503_when_gemini_is_not_configured(
    client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(ai_endpoint.chat_service.gemini_client, "api_key", None)

    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "Top laptop Asus đang bán đắt hơn CellphoneS"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Dịch vụ AI hiện không khả dụng. Vui lòng thử lại sau."
    assert db_session.query(ChatSession).count() == 0


def test_post_chat_returns_503_when_gemini_request_fails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        ai_endpoint.chat_service.gemini_client,
        "api_key",
        "configured-test-key",
    )

    def fail_request(**kwargs):
        raise httpx.ConnectError("provider is offline")

    monkeypatch.setattr(
        ai_endpoint.chat_service.gemini_client,
        "_call_gemini_api",
        fail_request,
    )

    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "Top laptop Asus đang bán đắt hơn CellphoneS"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Dịch vụ AI hiện không khả dụng. Vui lòng thử lại sau."


def test_post_chat_unexpected_errors_are_sanitized(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    def fail_chat(**kwargs):
        raise RuntimeError("private provider diagnostic")

    monkeypatch.setattr(ai_endpoint.chat_service, "handle_chat", fail_chat)

    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "Xin chào"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Lỗi nội bộ khi xử lý hội thoại AI."
    assert "private provider diagnostic" not in response.json()["detail"]


def test_get_sku_explain_factors_endpoint(client: TestClient, setup_ai_test_data):
    """Kiểm thử GET /api/v1/ai/explain/{sku} trả về 3 lớp giải trình."""
    response = client.get("/api/v1/ai/explain/FPT-ASUS-VIVO15")
    assert response.status_code == 200
    data = response.json()
    assert "competitor_shift" in data
    assert "inventory_status" in data
    assert "floor_protection" in data
    assert data["inventory_status"]["sku"] == "FPT-ASUS-VIVO15"


def test_get_sku_explain_factors_not_found(client: TestClient):
    """Kiểm thử GET /api/v1/ai/explain/{sku} trả về 404 với SKU không tồn tại."""
    response = client.get("/api/v1/ai/explain/NON-EXISTENT-SKU")
    assert response.status_code == 404
    assert "Không tìm thấy dữ liệu giải trình" in response.json()["detail"]


def test_sessions_lifecycle_endpoints(client: TestClient, setup_ai_test_data, mock_gemini):
    """Kiểm thử toàn bộ vòng đời phiên chat: Tạo, Lấy danh sách, Xem tin nhắn, Xóa."""
    # 1. Tạo tin nhắn đầu tiên -> tự động tạo session
    chat_resp = client.post(
        "/api/v1/ai/chat",
        json={"message": "Top laptop Asus đắt hơn CellphoneS"},
    )
    assert chat_resp.status_code == 200
    session_id = chat_resp.json()["session_id"]

    # 2. Lấy danh sách session -> có session_id
    sessions_resp = client.get("/api/v1/ai/sessions")
    assert sessions_resp.status_code == 200
    sessions = sessions_resp.json()
    assert len(sessions) >= 1
    target_session = next((s for s in sessions if s["id"] == session_id), None)
    assert target_session is not None
    assert target_session["message_count"] == 2

    # 3. Lấy lịch sử tin nhắn của session
    history_resp = client.get(f"/api/v1/ai/sessions/{session_id}")
    assert history_resp.status_code == 200
    messages = history_resp.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    # 4. Xóa session
    delete_resp = client.delete(f"/api/v1/ai/sessions/{session_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is True

    # 5. Kiểm tra session sau khi xóa -> trả về 404
    get_deleted = client.get(f"/api/v1/ai/sessions/{session_id}")
    assert get_deleted.status_code == 404

    # 6. Xóa lại session đã xóa -> trả về 404
    delete_again = client.delete(f"/api/v1/ai/sessions/{session_id}")
    assert delete_again.status_code == 404
