import logging
from typing import Any, Dict, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import ChatSession
from app.schemas.ai import (
    AiChatRequest,
    AiChatResponse,
    ChatMessageResponse,
    ChatSessionSummaryResponse,
    ExplainableFactors,
)
from app.services.ai.chat_service import ChatService
from app.services.ai.gemini_client import GeminiUnavailableError

router = APIRouter()
chat_service = ChatService()
logger = logging.getLogger(__name__)


@router.post(
    "/chat",
    response_model=AiChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Hội thoại nghiệp vụ định giá với Trợ lý AI",
    description="Gửi câu hỏi bằng ngôn ngữ tự nhiên đến FPT Shop Market Copilot. "
                "Hệ thống tự động kích hoạt Semantic Tools, trích xuất dữ liệu đa nguồn (Crawl, Inventory, Pricing) "
                "và trả về phản hồi kèm bảng số liệu hoặc thẻ giải trình 3 lớp.",
)
def chat_with_assistant(
    request: AiChatRequest,
    db: Session = Depends(get_db),
) -> AiChatResponse:
    """Xử lý lượt trò chuyện của chuyên viên định giá."""
    try:
        return chat_service.handle_chat(
            db=db,
            message=request.message,
            session_id=request.session_id,
        )
    except GeminiUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hạn mức gọi AI tạm thời vượt quá (HTTP 429 Quota Exceeded). Vui lòng thử lại sau 1-2 phút." if "429" in str(exc) else "Dịch vụ AI hiện không khả dụng. Vui lòng thử lại sau.",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error("Unexpected AI chat failure: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi nội bộ khi xử lý hội thoại AI.",
        ) from exc


@router.get(
    "/explain/{sku}",
    response_model=ExplainableFactors,
    status_code=status.HTTP_200_OK,
    summary="Thẻ căn cứ giải trình 3 lớp theo mã SKU",
    description="Truy vấn tức thời căn cứ giải trình 3 lớp (Biến động đối thủ + Tồn kho FPT + An toàn giá sàn) "
                "cho một mã SKU cụ thể phục vụ thẻ ExplainableCard (PBI-018).",
)
def get_sku_explain_factors(
    sku: str,
    db: Session = Depends(get_db),
) -> ExplainableFactors:
    """Trích xuất 3 lớp yếu tố định giá của một mã sản phẩm FPT."""
    clean_sku = sku.strip().upper()
    factors = chat_service.get_sku_explanation(db=db, sku=clean_sku)
    if not factors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy dữ liệu giải trình cho mã SKU: {sku}",
        )
    return factors


@router.get(
    "/sessions",
    response_model=List[ChatSessionSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Danh sách các phiên hội thoại",
    description="Lấy danh sách các phiên trò chuyện của chuyên viên định giá sắp xếp theo thời gian mới nhất.",
)
def list_chat_sessions(
    limit: int = Query(20, ge=1, le=100, description="Số lượng phiên tối đa cần lấy"),
    db: Session = Depends(get_db),
) -> List[ChatSessionSummaryResponse]:
    """Danh sách phiên chat kèm số lượng tin nhắn."""
    return chat_service.get_sessions(db=db, limit=limit)


@router.get(
    "/sessions/{session_id}",
    response_model=List[ChatMessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Lịch sử tin nhắn của một phiên chat",
    description="Xem lại toàn bộ các lượt tin nhắn trong một phiên hội thoại cụ thể theo thứ tự thời gian.",
)
def get_session_history(
    session_id: UUID,
    db: Session = Depends(get_db),
) -> List[ChatMessageResponse]:
    """Lấy danh sách tin nhắn theo session_id."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phiên hội thoại {session_id} không tồn tại trên hệ thống",
        )
    return chat_service.get_session_messages(db=db, session_id=session_id)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa phiên hội thoại",
    description="Xóa hoàn toàn một phiên hội thoại và tất cả các tin nhắn liên quan khỏi cơ sở dữ liệu.",
)
def delete_chat_session(
    session_id: UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Xóa phiên hội thoại."""
    deleted = chat_service.delete_session(db=db, session_id=session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phiên hội thoại {session_id} không tồn tại",
        )
    return {
        "success": True,
        "message": f"Đã xóa thành công phiên hội thoại {session_id}",
    }
