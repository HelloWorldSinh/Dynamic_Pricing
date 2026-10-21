# Kế hoạch Triển khai Hệ thống Trợ lý AI Định giá (AI Pricing Assistant - PBI-017 & PBI-018)

> **Mục tiêu**: Xây dựng hoàn chỉnh phân hệ Chatbot AI định giá (FPT Shop Market Copilot) với kiến trúc Tool-Augmented RAG kết hợp Google Gemini API và cơ sở dữ liệu nội bộ, đáp ứng hai yêu cầu cốt lõi: hỏi đáp nghiệp vụ thời gian thực (PBI-017) và giải trình minh bạch đề xuất giá 3 lớp (PBI-018).

---

## 1. Goal Description (Mục tiêu Kỹ thuật)

Xây dựng tầng dịch vụ AI Backend (`backend/app/services/ai/`) và hệ thống API Endpoint (`/api/v1/ai/`) để kết nối giao diện AI Studio sẵn có ([frontend/src/components/ai/](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/ai/)) với cơ sở dữ liệu quan hệ (Crawl Results, SKU Mappings, Inventories, Price Recommendations).

Hệ thống hoạt động theo mô hình **Tool-Augmented RAG**:
- Ngôn ngữ tự nhiên từ người dùng được phân tích bởi Gemini để nhận diện ý định (Intent) và trích xuất tham số.
- Các hàm truy vấn nghiệp vụ (Semantic Tools) viết bằng **SQLAlchemy ORM** được gọi để truy xuất dữ liệu chính xác từ database, đảm bảo tôn trọng 100% các quy tắc kinh doanh (loại trừ hàng hết, lọc độ tin cậy mapping, bảo vệ giá sàn).
- Kết quả được tổng hợp thành cấu trúc phản hồi trực quan gồm: văn bản giải thích tự nhiên, bảng dữ liệu đa cột (`tableData`), và thẻ giải trình minh bạch 3 lớp (`ExplainableCard`).
- Hệ thống hỗ trợ cơ chế chạy kép (**Dual-Mode**): Ưu tiên gọi Google Gemini API khi có `GEMINI_API_KEY`, và tự động chuyển sang chế độ dự phòng nội bộ (**Intelligent Deterministic Engine**) khi offline hoặc chưa cấu hình key, đảm bảo CI/CD và test luôn pass 100%.

---

## 2. User Review Required (Các điểm cần xác nhận)

> [!IMPORTANT]
> **1. Biến môi trường `GEMINI_API_KEY`**:
> Hệ thống sẽ đọc key từ biến môi trường `GEMINI_API_KEY` trong file `backend/.env`. Nếu chưa có key, hệ thống sẽ tự động fallback sang Rule-based Deterministic Generator để các lệnh test và demo không bao giờ bị gián đoạn.
> 
> **2. Mô hình AI mặc định**:
> Sử dụng `gemini-1.5-flash` hoặc `gemini-2.0-flash` qua Google AI Studio API (độ trễ cực thấp < 1.5s, miễn phí 15 RPM).
> 
> **3. Lưu trữ phiên hội thoại**:
> Tận dụng trực tiếp 2 bảng CSDL đã được migrate sẵn trong Alembic: `chat_sessions` và `chat_messages` ([backend/app/models/chat.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/models/chat.py)).

---

## 3. Phân chia các Giai đoạn Triển khai (Implementation Phases)

```
┌────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Schemas & Semantic Tools Layer (Data Retrieval)               │
│ - Pydantic Contracts (ai.py)                                           │
│ - 3 Semantic Tools với SQLAlchemy ORM (tools.py)                       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Phase 2: AI Engine & Gemini Orchestration (Reasoning & Synthesis)       │
│ - Gemini Client với Dual-Mode & Fallback (gemini_client.py)             │
│ - Chat Service & Session Coordinator (chat_service.py)                 │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Phase 3: API Endpoints & Routing (FastAPI)                             │
│ - POST /api/v1/ai/chat & GET /api/v1/ai/explain/{sku}                  │
│ - Quản lý Sessions & History                                           │
│ - Đăng ký router vào router.py & cập nhật Settings config.py           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Phase 4: Frontend Live Integration (UI Layer)                          │
│ - Cập nhật aiApi.ts kết nối endpoint thật                             │
│ - Đồng bộ luồng 'Giải thích đề xuất giá' từ bảng so sánh               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ Phase 5: Automated Testing & Verification (Quality Gate)               │
│ - Unit Tests cho Semantic Tools (test_ai_tools.py)                     │
│ - API Integration Tests qua TestClient (test_ai_endpoints.py)          │
│ - Chạy verify_fe_be_integration script                                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Chi tiết từng Phase & Task

### PHASE 1: Data Contracts & Semantic Tools (Data Retrieval Layer)

#### [NEW] `backend/app/schemas/ai.py`
Xây dựng Pydantic v2 schemas khớp 100% với giao diện Frontend `frontend/src/types/ai.ts`.
- `CompetitorShift`: thông tin biến động giá đối thủ.
- `InventoryStatus`: hiện trạng kho hàng (SKU, DOH, số lượng tồn, mức độ rủi ro).
- `FloorProtection`: kiểm tra giá sàn, giá đề xuất, biên an toàn %, cờ cảnh báo chạm giá sàn.
- `ExplainableFactors`: tổng hợp 3 lớp trên phục vụ PBI-018.
- `AiChatRequest`: `{ message: str, session_id: Optional[UUID] = None }`.
- `AiChatResponse`: `{ message: str, session_id: UUID, tableData: Optional[List[Dict[str, Any]]], explainFactors: Optional[ExplainableFactors] }`.
- `ChatSessionSummaryResponse`, `ChatMessageResponse`: danh sách phiên và tin nhắn.

#### [NEW] `backend/app/services/ai/tools.py`
Xây dựng 3 hàm Semantic Tools truy vấn dữ liệu bằng SQLAlchemy ORM:
1. `get_price_discrepancies(db: Session, category: Optional[str], brand: Optional[str], competitor: Optional[str], limit: int = 5) -> List[Dict[str, Any]]`:
   - Truy vấn kết hợp `Product`, `SkuMapping`, `CrawlResult`, `InventoryMock`.
   - Áp dụng các bộ lọc nghiệp vụ: chỉ lấy đối thủ còn hàng (`is_in_stock = True`), mapping đã duyệt hoặc confidence >= 80%, FPT đắt hơn đối thủ.
2. `get_inventory_risks(db: Session, category: Optional[str], brand: Optional[str], doh_threshold: int = 45, limit: int = 5) -> List[Dict[str, Any]]`:
   - Truy vấn các mã tồn kho FPT có số ngày lưu kho $DOH \ge doh\_threshold$.
   - Tính toán cấp độ rủi ro: HIGH ($DOH > 45$), MEDIUM ($30 \le DOH \le 45$), LOW ($DOH < 30$).
3. `get_sku_explain_factors(db: Session, sku: str) -> Optional[ExplainableFactors]`:
   - Trích xuất toàn bộ dữ liệu cần thiết của 1 mã SKU từ `PriceRecommendation`, `InventoryMock`, `CrawlResult`.
   - Trả về đối tượng `ExplainableFactors` chuẩn 3 lớp:
     - Lớp 1: Biến động đối thủ (tên đối thủ, mức giảm giá, trạng thái online).
     - Lớp 2: Tồn kho FPT (số lượng khả dụng, DOH, cảnh báo nguy cơ).
     - Lớp 3: An toàn giá sàn (giá sàn, giá đề xuất, biên an toàn %, trạng thái bị hãm trần/sàn).

---

### PHASE 2: AI Engine & Gemini Orchestration (Reasoning & Synthesis Layer)

#### [NEW] `backend/app/services/ai/gemini_client.py`
- Quản lý giao tiếp HTTP với Google Gemini API (endpoint `generateContent` của `gemini-1.5-flash` / `gemini-2.0-flash`).
- Hỗ trợ khai báo Function Calling / Tools declarations để Gemini tự động trích xuất intent và parameters.
- Thiết lập cơ chế **Graceful Fallback**: Nếu không có API Key hoặc gặp lỗi kết nối mạng, tự động kích hoạt bộ sinh nội bộ thông minh (Deterministic Generator) để phân tích từ khóa và tạo phản hồi mà không gây gián đoạn hệ thống.

#### [NEW] `backend/app/services/ai/chat_service.py`
Bộ điều phối toàn diện cho Chatbot:
- Quản lý phiên hội thoại (`ChatSession`) và lưu trữ lịch sử (`ChatMessage`).
- Quy trình xử lý câu hỏi:
  1. Tra cứu hoặc khởi tạo phiên chat mới trong `chat_sessions`.
  2. Nạp ngữ cảnh hội thoại gần nhất (lịch sử 4 lượt tin nhắn).
  3. Gửi câu hỏi đến Gemini kèm danh sách Semantic Tools.
  4. Nếu Gemini yêu cầu gọi Tool: Thực thi hàm trong `tools.py` với `db: Session`, gửi kết quả trở lại Gemini để tổng hợp câu trả lời tự nhiên.
  5. Nếu người dùng hỏi giải trình một mã SKU: Tự động trích xuất mã SKU và bổ sung thẻ `explainFactors`.
  6. Lưu tin nhắn của người dùng và tin nhắn phản hồi của trợ lý vào bảng `chat_messages` kèm trường `retrieved_context`.

---

### PHASE 3: API Endpoints & Routing (FastAPI)

#### [MODIFY] `backend/app/core/config.py`
Bổ sung các tham số cấu hình:
- `GEMINI_API_KEY: Optional[str] = None`
- `GEMINI_MODEL: str = "gemini-1.5-flash"`

#### [NEW] `backend/app/api/v1/endpoints/ai.py`
Định nghĩa các REST endpoints:
- `POST /api/v1/ai/chat`: Nhận `AiChatRequest`, trả về `AiChatResponse`.
- `GET /api/v1/ai/explain/{sku}`: Trả về trực tiếp `ExplainableFactors` phục vụ thẻ giải trình nhanh.
- `GET /api/v1/ai/sessions`: Danh sách các phiên hội thoại gần nhất.
- `GET /api/v1/ai/sessions/{session_id}`: Lịch sử tin nhắn của một phiên cụ thể.
- `DELETE /api/v1/ai/sessions/{session_id}`: Xóa phiên hội thoại.

#### [MODIFY] `backend/app/api/v1/router.py`
Đăng ký router AI vào hệ thống:
```python
from app.api.v1.endpoints import crawl, products, pricing, matching, ai

api_router.include_router(ai.router, prefix="/ai", tags=["AI Pricing Assistant (PBI-017 & PBI-018)"])
```

---

### PHASE 4: Frontend Live Integration (UI Layer)

#### [MODIFY] `frontend/src/api/aiApi.ts`
- Bỏ cơ chế sinh mock tự tạo khi API trả về kết quả thành công.
- Giữ try-catch để chỉ fallback khi mạng bị gián đoạn hoàn toàn.
- Đảm bảo các trường dữ liệu `tableData` và `explainFactors` truyền tải trực tiếp từ Backend lên `ExpandedAiDrawer` và `CompactChatPopup`.

#### [MODIFY] `frontend/src/context/AiChatContext.tsx`
- Bổ sung quản lý `session_id` để duy trì ngữ cảnh xuyên suốt cuộc trò chuyện.
- Lưu `session_id` vào `sessionStorage` để không mất ngữ cảnh khi người dùng F5 tải lại trang.

---

### PHASE 5: Automated Testing & Verification (Quality Gate)

Tuân thủ nghiêm ngặt quy tắc **API Testing First & Only** (không test qua UI browser):

#### [NEW] `backend/tests/test_ai_tools.py`
Kiểm thử Unit Test các Semantic Tools:
- `test_get_price_discrepancies_filters_out_of_stock()`: Chứng minh đối thủ hết hàng bị loại bỏ khỏi danh sách.
- `test_get_inventory_risks_threshold()`: Kiểm tra lọc chính xác ngưỡng DOH > 45 ngày.
- `test_get_sku_explain_factors_structure()`: Kiểm tra tính đầy đủ 3 lớp của thẻ giải trình.

#### [NEW] `backend/tests/test_ai_endpoints.py`
Kiểm thử Integration Test với FastAPI `TestClient`:
- `test_ai_chat_endpoint_competitor_lookup()`: Gửi câu hỏi "Top laptop ASUS đắt hơn CellphoneS", kiểm tra HTTP 200 và cấu trúc `tableData`.
- `test_ai_chat_endpoint_inventory_risk()`: Gửi câu hỏi "iPhone tồn kho cao", kiểm tra HTTP 200 và nội dung phản hồi.
- `test_ai_explain_endpoint()`: Gọi `GET /api/v1/ai/explain/FPT-ASUS-VIVO15`, kiểm tra HTTP 200 và 3 lớp yếu tố.
- `test_ai_sessions_lifecycle()`: Tạo phiên chat, gửi tin nhắn, đọc lịch sử và xóa phiên.

---

## 5. Verification Plan (Kế hoạch Kiểm chứng)

### Kiểm thử Tự động qua API (Bắt buộc)

Thực thi bộ test bằng `pytest` trong môi trường backend:
```powershell
# 1. Chạy unit tests cho các semantic tools
pytest backend/tests/test_ai_tools.py -v

# 2. Chạy integration tests cho các API endpoints
pytest backend/tests/test_ai_endpoints.py -v

# 3. Chạy toàn bộ regression test suite của backend để đảm bảo không gãy tính năng cũ
pytest backend/tests/ -v
```

Tiêu chí nghiệm thu:
- Tất cả các test cases mới đều đạt trạng thái `PASSED`.
- Độ trễ phản hồi của endpoint `/api/v1/ai/chat` đối với các câu hỏi chuẩn $\le 3\text{ giây}$ (đáp ứng tiêu chuẩn AC $\le 10\text{ giây}$ của PBI-017).
- Thẻ giải trình trả về đầy đủ 3 yếu tố đối thủ, tồn kho, giá sàn (đáp ứng PBI-018).
