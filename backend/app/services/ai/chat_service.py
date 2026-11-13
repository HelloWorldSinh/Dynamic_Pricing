from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession
from app.schemas.ai import (
    AiChatResponse,
    ChatMessageResponse,
    ChatSessionSummaryResponse,
    ExplainableFactors,
)
from app.services.ai.gemini_client import (
    GeminiClient,
    format_out_of_scope_reply,
    OUT_OF_SCOPE_SUGGESTIONS,
    STANDARD_OUT_OF_SCOPE_MESSAGE,
)
from app.services.ai.tools import get_sku_explain_factors

class ChatService:
    """Dịch vụ điều phối hội thoại Gemini cho Trợ lý AI định giá (PBI-017 & PBI-018)."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None) -> None:
        self.gemini_client = gemini_client or GeminiClient()

    def handle_chat(
        self,
        db: Session,
        message: str,
        session_id: Optional[UUID] = None,
    ) -> AiChatResponse:
        """
        Tiếp nhận và xử lý câu hỏi của chuyên viên phân tích giá:
        1. Tạo mới hoặc nạp phiên hội thoại `ChatSession`.
        2. Nạp ngữ cảnh hội thoại gần nhất từ `chat_messages`.
        3. Lưu tin nhắn của người dùng.
        4. Gọi Gemini Client để xử lý logic và gọi Semantic Tools.
        5. Lưu phản hồi của trợ lý vào database kèm ngữ cảnh `retrieved_context`.
        6. Trả về `AiChatResponse`.
        """
        # 1. Tìm hoặc khởi tạo phiên chat
        session = None
        if session_id:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

        if not session:
            # Tạo tiêu đề tóm tắt ngắn từ câu hỏi đầu tiên
            clean_title = message.strip()
            summary_title = (clean_title[:45] + "...") if len(clean_title) > 45 else clean_title
            session = ChatSession(title=summary_title)
            db.add(session)
            db.flush()

        # 2. Nạp ngữ cảnh 4 lượt tin nhắn gần nhất
        recent_messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(4)
            .all()
        )
        recent_messages.reverse()

        history_payload = [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]

        # 3. Lưu tin nhắn của người dùng
        user_message_record = ChatMessage(
            session_id=session.id,
            role="user",
            content=message.strip(),
        )
        db.add(user_message_record)
        db.flush()

        # 4. Điều phối xử lý câu hỏi qua GeminiClient
        try:
            reply_text, table_data, explain_factors, intent = self.gemini_client.generate_chat_response(
                db=db,
                message=message,
                history=history_payload,
            )
        except Exception:
            db.rollback()
            raise

        # 5. Lưu phản hồi của trợ lý AI vào DB kèm ngữ cảnh truy xuất
        retrieved_context: Dict[str, Any] = {}
        suggestions: Optional[List[str]] = None

        if intent == "OUT_OF_SCOPE":
            # Ghi đè 100% bằng câu thông báo chuẩn cố định kèm câu hỏi gợi ý
            reply_text = format_out_of_scope_reply()
            suggestions = OUT_OF_SCOPE_SUGGESTIONS
            retrieved_context["suggestions"] = suggestions
        else:
            if table_data:
                retrieved_context["tableData"] = table_data
            if explain_factors:
                retrieved_context["explainFactors"] = explain_factors.model_dump()

        assistant_message_record = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=reply_text,
            intent=intent,
            retrieved_context=retrieved_context if retrieved_context else None,
        )
        db.add(assistant_message_record)
        db.commit()

        # 6. Trả về phản hồi cấu trúc cho Client
        return AiChatResponse(
            message=reply_text,
            session_id=session.id,
            tableData=table_data,
            explainFactors=explain_factors,
            suggestions=suggestions,
        )

    def get_sessions(self, db: Session, limit: int = 20) -> List[ChatSessionSummaryResponse]:
        """Lấy danh sách các phiên trò chuyện gần nhất kèm số lượng tin nhắn."""
        sessions = (
            db.query(ChatSession)
            .order_by(ChatSession.created_at.desc())
            .limit(limit)
            .all()
        )

        results: List[ChatSessionSummaryResponse] = []
        for s in sessions:
            count = db.query(func.count(ChatMessage.id)).filter(ChatMessage.session_id == s.id).scalar() or 0
            results.append(
                ChatSessionSummaryResponse(
                    id=s.id,
                    title=s.title,
                    created_at=s.created_at,
                    message_count=count,
                )
            )
        return results

    def get_session_messages(self, db: Session, session_id: UUID) -> List[ChatMessageResponse]:
        """Lấy toàn bộ lịch sử tin nhắn của một phiên hội thoại cụ thể."""
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        return [ChatMessageResponse.model_validate(m) for m in messages]

    def delete_session(self, db: Session, session_id: UUID) -> bool:
        """Xóa hoàn toàn một phiên hội thoại và toàn bộ tin nhắn liên quan."""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return False

        db.delete(session)
        db.commit()
        return True

    def get_sku_explanation(self, db: Session, sku: str) -> Optional[ExplainableFactors]:
        """Tra cứu thẻ giải trình 3 lớp độc lập cho một mã SKU cụ thể (PBI-018)."""
        return get_sku_explain_factors(db=db, sku=sku)
