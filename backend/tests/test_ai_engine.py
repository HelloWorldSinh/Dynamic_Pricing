"""
Unit tests for Gemini orchestration, ChatService, and session tracking.
"""
import uuid
from typing import Any, Dict, List
from unittest.mock import Mock

import httpx
import pytest
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.models.inventory import InventoryMock
from app.models.pricing import PriceRecommendation
from app.models.chat import ChatSession, ChatMessage

from app.services.ai.gemini_client import GeminiClient, GeminiUnavailableError
from app.services.ai.chat_service import ChatService
from app.services.ai.tools import get_sku_explain_factors


class FakeResponse:
    def __init__(self, status_code: int, payload: Dict[str, Any]) -> None:
        self.status_code = status_code
        self.payload = payload

    def json(self) -> Dict[str, Any]:
        return self.payload


class FakeGeminiHttpClient:
    def __init__(self, responses: List[FakeResponse]) -> None:
        self.responses = iter(responses)
        self.client_headers: Dict[str, str] = {}
        self.requests: List[Dict[str, Any]] = []

    def __enter__(self) -> "FakeGeminiHttpClient":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> bool:
        return False

    def post(self, *args: Any, **kwargs: Any) -> FakeResponse:
        url = args[0] if args else kwargs.get("url", "")
        self.requests.append({"url": url, "headers": dict(self.client_headers)})
        return next(self.responses)


@pytest.fixture
def sample_ai_data(db_session: Session):
    """Tạo bộ dữ liệu mẫu phục vụ kiểm thử AI Engine."""
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


def test_gemini_client_without_api_key_raises(db_session: Session):
    """Gemini chưa cấu hình phải báo lỗi thay vì trả lời offline."""
    client = GeminiClient()
    client.api_key = None
    assert client.is_configured is False

    with pytest.raises(GeminiUnavailableError, match="Gemini"):
        client.generate_chat_response(db=db_session, message="Xin chào")


def test_gemini_client_provider_error_is_not_replaced_with_offline_response(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    client = GeminiClient()
    client.api_key = "configured-test-key"

    def fail_request(**kwargs: Any) -> Any:
        raise httpx.ConnectError("provider is offline")

    monkeypatch.setattr(client, "_call_gemini_api", fail_request)

    with pytest.raises(GeminiUnavailableError, match="Gemini"):
        client.generate_chat_response(db=db_session, message="Xin chào")


def test_gemini_client_empty_candidates_raise(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    client = GeminiClient()
    client.api_key = "configured-test-key"
    fake_http = FakeGeminiHttpClient([FakeResponse(200, {"candidates": []})])
    monkeypatch.setattr(
        "app.services.ai.gemini_client.httpx.Client",
        lambda **kwargs: fake_http,
    )

    with pytest.raises(GeminiUnavailableError, match="Gemini"):
        client.generate_chat_response(db=db_session, message="Xin chào")


def test_gemini_client_empty_text_raises(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    client = GeminiClient()
    client.api_key = "configured-test-key"
    fake_http = FakeGeminiHttpClient(
        [FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "  "}]}}]})]
    )
    monkeypatch.setattr(
        "app.services.ai.gemini_client.httpx.Client",
        lambda **kwargs: fake_http,
    )

    with pytest.raises(GeminiUnavailableError, match="Gemini"):
        client.generate_chat_response(db=db_session, message="Xin chào")


@pytest.mark.parametrize(
    "payload",
    [
        {"candidates": ["malformed candidate"]},
        {
            "candidates": [
                {"content": {"parts": [{"functionCall": "malformed function call"}]}}
            ]
        },
    ],
)
def test_gemini_client_malformed_candidate_raises(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    payload: Dict[str, Any],
):
    client = GeminiClient()
    client.api_key = "configured-test-key"
    fake_http = FakeGeminiHttpClient([FakeResponse(200, payload)])
    monkeypatch.setattr(
        "app.services.ai.gemini_client.httpx.Client",
        lambda **kwargs: fake_http,
    )

    with pytest.raises(GeminiUnavailableError, match="Gemini"):
        client.generate_chat_response(db=db_session, message="Xin chào")


def test_gemini_client_failed_tool_follow_up_raises(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    client = GeminiClient()
    client.api_key = "configured-test-key"
    fake_http = FakeGeminiHttpClient(
        [
            FakeResponse(
                200,
                {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "functionCall": {
                                            "name": "get_inventory_risks",
                                            "args": {},
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                },
            ),
            FakeResponse(503, {}),
        ]
    )
    monkeypatch.setattr(
        "app.services.ai.gemini_client.httpx.Client",
        lambda **kwargs: fake_http,
    )
    monkeypatch.setattr(
        client,
        "_execute_tool",
        lambda **kwargs: ([{"SKU": "SKU001"}], [{"SKU": "SKU001"}], None, "INVENTORY_RISK"),
    )

    with pytest.raises(GeminiUnavailableError, match="Gemini"):
        client.generate_chat_response(db=db_session, message="Tồn kho DOH cao")


def test_gemini_client_malformed_tool_follow_up_raises(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    client = GeminiClient()
    client.api_key = "configured-test-key"
    fake_http = FakeGeminiHttpClient(
        [
            FakeResponse(
                200,
                {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "functionCall": {
                                            "name": "get_inventory_risks",
                                            "args": {},
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                },
            ),
            FakeResponse(200, {"candidates": ["malformed candidate"]}),
        ]
    )
    monkeypatch.setattr(
        "app.services.ai.gemini_client.httpx.Client",
        lambda **kwargs: fake_http,
    )
    monkeypatch.setattr(
        client,
        "_execute_tool",
        lambda **kwargs: ([{"SKU": "SKU001"}], [{"SKU": "SKU001"}], None, "INVENTORY_RISK"),
    )

    with pytest.raises(GeminiUnavailableError, match="Gemini"):
        client.generate_chat_response(db=db_session, message="Tồn kho DOH cao")


@pytest.mark.parametrize(
    ("func_name", "args"),
    [
        ("get_sku_explain_factors", {"sku": None}),
        ("get_price_discrepancies", {"limit": "bad"}),
        ("get_price_discrepancies", {"category": ["LAPTOP"]}),
        ("get_inventory_risks", {"doh_threshold": True}),
    ],
)
def test_gemini_client_rejects_invalid_tool_arguments(
    db_session: Session,
    func_name: str,
    args: Dict[str, Any],
):
    client = GeminiClient()

    with pytest.raises(GeminiUnavailableError, match="Gemini"):
        client._execute_tool(db=db_session, func_name=func_name, args=args)


def test_gemini_client_successful_tool_call_returns_tool_data(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    client = GeminiClient()
    client.api_key = "configured-test-key"
    tool_data = [{"SKU": "SKU001"}]
    fake_http = FakeGeminiHttpClient(
        [
            FakeResponse(
                200,
                {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "functionCall": {
                                            "name": "get_inventory_risks",
                                            "args": {"doh_threshold": 45},
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                },
            ),
            FakeResponse(
                200,
                {"candidates": [{"content": {"parts": [{"text": "Có một sản phẩm rủi ro."}]}}]},
            ),
        ]
    )
    monkeypatch.setattr(
        "app.services.ai.gemini_client.httpx.Client",
        lambda **kwargs: fake_http,
    )
    monkeypatch.setattr(
        client,
        "_execute_tool",
        lambda **kwargs: (tool_data, tool_data, None, "INVENTORY_RISK"),
    )

    message, table_data, factors, intent = client.generate_chat_response(
        db=db_session,
        message="Cảnh báo tồn kho DOH >= 45 ngày",
    )

    assert message == "Có một sản phẩm rủi ro."
    assert table_data == tool_data
    assert factors is None
    assert intent == "INVENTORY_RISK"


def test_gemini_client_sends_api_key_in_header_for_initial_and_follow_up_requests(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    api_key = "configured-test-key"
    client = GeminiClient()
    client.api_key = api_key
    fake_http = FakeGeminiHttpClient(
        [
            FakeResponse(
                200,
                {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "functionCall": {
                                            "name": "get_inventory_risks",
                                            "args": {},
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                },
            ),
            FakeResponse(
                200,
                {"candidates": [{"content": {"parts": [{"text": "Có một sản phẩm rủi ro."}]}}]},
            ),
        ]
    )

    def create_fake_http_client(**kwargs: Any) -> FakeGeminiHttpClient:
        fake_http.client_headers = kwargs.get("headers", {})
        return fake_http

    monkeypatch.setattr(
        "app.services.ai.gemini_client.httpx.Client",
        create_fake_http_client,
    )
    monkeypatch.setattr(
        client,
        "_execute_tool",
        lambda **kwargs: ([{"SKU": "SKU001"}], [{"SKU": "SKU001"}], None, "INVENTORY_RISK"),
    )

    client.generate_chat_response(db=db_session, message="Cảnh báo tồn kho DOH cao")

    assert len(fake_http.requests) == 2
    for request in fake_http.requests:
        assert "key=" not in request["url"]
        assert api_key not in request["url"]
        assert request["headers"].get("x-goog-api-key") == api_key


def test_chat_service_session_lifecycle(db_session: Session, sample_ai_data):
    """Kiểm tra session lifecycle với phản hồi Gemini được mock."""
    factors = get_sku_explain_factors(db=db_session, sku="FPT-ASUS-VIVO15")
    gemini_client = Mock(spec=GeminiClient)
    gemini_client.generate_chat_response.side_effect = [
        (
            "Danh sách sản phẩm cần xem xét.",
            [{"SKU": "FPT-ASUS-VIVO15"}],
            None,
            "COMPETITOR_LOOKUP",
        ),
        (
            "Căn cứ giải trình giá.",
            None,
            factors,
            "PRICE_EXPLANATION",
        ),
    ]
    service = ChatService(gemini_client=gemini_client)

    # 1. Gửi tin nhắn đầu tiên -> tự động tạo session
    resp1 = service.handle_chat(
        db=db_session,
        message="Top laptop Asus đắt hơn CellphoneS",
        session_id=None,
    )
    assert resp1.session_id is not None
    session_id = resp1.session_id
    assert resp1.tableData is not None

    # Kiểm tra bản ghi ChatSession trong DB
    session_db = db_session.query(ChatSession).filter(ChatSession.id == session_id).first()
    assert session_db is not None
    assert "laptop" in session_db.title.lower()

    # Kiểm tra số lượng tin nhắn (1 user + 1 assistant)
    messages_after_turn_1 = (
        db_session.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .all()
    )
    assert len(messages_after_turn_1) == 2
    assert messages_after_turn_1[0].role == "user"
    assert messages_after_turn_1[1].role == "assistant"
    assert messages_after_turn_1[1].retrieved_context is not None

    # 2. Gửi tin nhắn thứ 2 với session_id sẵn có -> tái sử dụng session
    resp2 = service.handle_chat(
        db=db_session,
        message="Giải thích lý do giảm giá FPT-ASUS-VIVO15",
        session_id=session_id,
    )
    assert resp2.session_id == session_id
    assert resp2.explainFactors is not None

    # Kiểm tra tổng cộng 4 tin nhắn
    session_messages = service.get_session_messages(db=db_session, session_id=session_id)
    assert len(session_messages) == 4

    # 3. Lấy danh sách session
    sessions_list = service.get_sessions(db=db_session)
    assert len(sessions_list) >= 1
    found = [s for s in sessions_list if s.id == session_id]
    assert len(found) == 1
    assert found[0].message_count == 4

    # 4. Tra cứu giải trình trực tiếp
    factors = service.get_sku_explanation(db=db_session, sku="FPT-ASUS-VIVO15")
    assert factors is not None
    assert factors.inventory_status.sku == "FPT-ASUS-VIVO15"

    # 5. Xóa session
    delete_result = service.delete_session(db=db_session, session_id=session_id)
    assert delete_result is True

    # Xác nhận session và messages đã bị xóa khỏi DB
    assert db_session.query(ChatSession).filter(ChatSession.id == session_id).first() is None
    assert db_session.query(ChatMessage).filter(ChatMessage.session_id == session_id).count() == 0
