import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class ChatSession(Base, TimestampMixin):
    """Bảng phiên hội thoại giữa chuyên viên định giá và AI Assistant (PBI-017 & PBI-018)."""
    __tablename__ = "chat_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="Cuộc hội thoại mới")

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Bảng chi tiết các lượt tin nhắn trong phiên hội thoại AI."""
    __tablename__ = "chat_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID(), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)                           # user | assistant | system
    content = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)                          # PRICE_EXPLANATION | COMPETITOR_LOOKUP | INVENTORY_RISK
    retrieved_context = Column(JSON, nullable=True)                     # Context JSON trích xuất từ database phục vụ giải trình RAG
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
