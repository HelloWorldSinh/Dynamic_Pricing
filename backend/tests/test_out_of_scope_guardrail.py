import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.ai.gemini_client import (
    GeminiClient,
    TOOL_DECLARATIONS,
    STANDARD_OUT_OF_SCOPE_MESSAGE,
    OUT_OF_SCOPE_SUGGESTIONS,
)
from app.services.ai.chat_service import ChatService


def test_reject_tool_declaration_exists():
    """Kiểm tra tool reject_out_of_scope_query đã được khai báo chính xác trong TOOL_DECLARATIONS."""
    tool_names = [t.get("name") for t in TOOL_DECLARATIONS]
    assert "reject_out_of_scope_query" in tool_names

    reject_tool = next(t for t in TOOL_DECLARATIONS if t.get("name") == "reject_out_of_scope_query")
    assert "parameters" in reject_tool
    props = reject_tool["parameters"]["properties"]
    assert "reason" in props
    assert props["reason"]["type"] == "STRING"


def test_execute_tool_reject_out_of_scope(db_session: Session):
    """Kiểm tra hàm _execute_tool xử lý đúng khi Gemini gọi reject_out_of_scope_query."""
    client = GeminiClient()
    args = {"reason": "Người dùng hỏi làm thơ tình yêu ngoài phạm vi định giá"}
    
    tool_result, table_data, explain_factors, intent = client._execute_tool(
        db=db_session,
        func_name="reject_out_of_scope_query",
        args=args
    )
    
    assert intent == "OUT_OF_SCOPE"
    assert table_data is None
    assert explain_factors is None
    assert isinstance(tool_result, dict)
    assert tool_result.get("status") == "REJECTED"
    assert tool_result.get("reason") == args["reason"]


def test_chat_service_handles_out_of_scope(db_session: Session):
    """Kiểm tra ChatService ghi đè tin nhắn chuẩn cố định khi intent là OUT_OF_SCOPE."""
    mock_gemini = MagicMock(spec=GeminiClient)
    # Giả lập GeminiClient trả về tuple với intent OUT_OF_SCOPE
    mock_gemini.generate_chat_response.return_value = (
        "Tôi không thể làm thơ",  # Text gốc từ Gemini
        None,
        None,
        "OUT_OF_SCOPE"
    )
    
    service = ChatService(gemini_client=mock_gemini)
    response = service.handle_chat(
        db=db_session,
        message="Hãy làm một bài thơ về mùa thu"
    )
    
    assert response.session_id is not None
    assert STANDARD_OUT_OF_SCOPE_MESSAGE in response.message
    # Đảm bảo có danh sách câu hỏi mẫu gợi ý trong tin nhắn
    for suggestion in OUT_OF_SCOPE_SUGGESTIONS:
        assert suggestion in response.message


def test_api_chat_endpoint_out_of_scope(db_session: Session):
    """Kiểm tra API endpoint /api/v1/ai/chat trả về phản hồi hợp lệ khi bị chặn ngoài phạm vi."""
    client = TestClient(app)
    
    with patch("app.api.v1.endpoints.ai.chat_service.gemini_client") as mock_gemini:
        mock_gemini.generate_chat_response.return_value = (
            STANDARD_OUT_OF_SCOPE_MESSAGE,
            None,
            None,
            "OUT_OF_SCOPE"
        )
        
        payload = {"message": "Viết code C++ giải phương trình bậc hai"}
        response = client.post("/api/v1/ai/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert STANDARD_OUT_OF_SCOPE_MESSAGE in data["message"]
        assert data["tableData"] is None
        assert data["explainFactors"] is None

