from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CompetitorShift(BaseModel):
    """Lớp 1: Biến động giá thị trường đối thủ."""
    model_config = ConfigDict(from_attributes=True)

    competitor: str = Field(..., description="Tên đối thủ: CELLPHONES | HOANGHA")
    old_price: Optional[float] = Field(None, description="Mức giá trước điều chỉnh (VND)")
    new_price: float = Field(..., description="Mức giá bán hiện tại (VND)")
    price_cut: float = Field(..., description="Mức giảm giá tuyệt đối (VND)")
    is_in_stock: bool = Field(..., description="Trạng thái còn hàng thực tế trên web")


class InventoryStatus(BaseModel):
    """Lớp 2: Hiện trạng tồn kho FPT Shop."""
    model_config = ConfigDict(from_attributes=True)

    sku: str = Field(..., description="Mã SKU FPT Shop")
    doh: int = Field(..., description="Số ngày lưu kho (Days On Hand)")
    quantity: int = Field(..., description="Lượng tồn kho khả dụng")
    doh_risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ..., description="Mức độ rủi ro tồn kho: HIGH khi DOH > 45 ngày"
    )


class FloorProtection(BaseModel):
    """Lớp 3: Kiểm tra an toàn giá sàn."""
    model_config = ConfigDict(from_attributes=True)

    floor_price: float = Field(..., description="Giá sàn tối thiểu: Giá vốn + Biên lợi nhuận tối thiểu")
    suggested_price: float = Field(..., description="Mức giá đề xuất mới")
    safety_margin_percent: float = Field(..., description="Biên an toàn còn lại so với giá sàn (%)")
    is_capped: bool = Field(..., description="Cờ cảnh báo nếu giá bị ghim chặn tại giá sàn")


class ExplainableFactors(BaseModel):
    """Tổng hợp căn cứ giải trình 3 lớp của thuật toán định giá (PBI-018)."""
    model_config = ConfigDict(from_attributes=True)

    competitor_shift: CompetitorShift
    inventory_status: InventoryStatus
    floor_protection: FloorProtection


class AiChatRequest(BaseModel):
    """Yêu cầu trò chuyện của Pricing Analyst."""
    message: str = Field(..., min_length=1, max_length=2000, description="Nội dung câu hỏi của chuyên viên")
    session_id: Optional[UUID] = Field(None, description="ID phiên chat hiện tại; nếu null hệ thống tự tạo mới")


class AiChatResponse(BaseModel):
    """Phản hồi thông minh từ Trợ lý AI Định giá (PBI-017)."""
    message: str = Field(..., description="Câu trả lời giải thích tự nhiên bằng tiếng Việt")
    session_id: UUID = Field(..., description="Định danh phiên hội thoại")
    tableData: Optional[List[Dict[str, Any]]] = Field(None, description="Bảng dữ liệu đa cột chi tiết (nếu có)")
    explainFactors: Optional[ExplainableFactors] = Field(
        None, description="Thẻ giải trình minh bạch 3 lớp (nếu là yêu cầu giải thích)"
    )
    suggestions: Optional[List[str]] = Field(
        None, description="Danh sách các câu hỏi mẫu gợi ý (khi ngoài phạm vi hoặc cần định hướng)"
    )


class ChatMessageResponse(BaseModel):
    """Lịch sử chi tiết một tin nhắn trong phiên chat."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: str
    content: str
    intent: Optional[str] = None
    created_at: datetime
    retrieved_context: Optional[Dict[str, Any]] = None


class ChatSessionSummaryResponse(BaseModel):
    """Tóm tắt thông tin một phiên trò chuyện."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    message_count: int = 0
