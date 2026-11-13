# TÀI LIỆU HƯỚNG DẪN VẬN HÀNH & BÀN GIAO KỸ THUẬT PHÂN HỆ AI CHATBOT
## DỰ ÁN DYNAMIC PRICING SYSTEM (PBI-017 & PBI-018)

---

### 1. TỔNG QUAN PHÂN HỆ

Phân hệ **Trợ lý AI Chatbot (FPT Shop Market Copilot)** được phát triển nhằm hỗ trợ chuyên viên phân tích giá (Pricing Analyst) thực hiện hai nhiệm vụ cốt lõi:
- **PBI-017**: Truy vấn, phân tích và so sánh giá thị trường thời gian thực, phát hiện chênh lệch giá giữa FPT Shop và các đối thủ cạnh tranh (CellphoneS, Hoàng Hà Mobile), đồng thời cảnh báo rủi ro tồn kho lâu ngày (DOH >= 45 ngày) qua giao diện hội thoại ngôn ngữ tự nhiên.
- **PBI-018**: Cung cấp thẻ giải trình minh bạch 3 lớp (3-Layer Explainable Factors) cho từng mã SKU trước khi phê duyệt đề xuất giá:
  1. Lớp 1: Biến động giá và động thái đối thủ cạnh tranh.
  2. Lớp 2: Tình trạng tồn kho nội bộ FPT (Số lượng tồn khả dụng, Tốc độ bán Sales Velocity, Số ngày tồn kho DOH).
  3. Lớp 3: Biên an toàn giá sàn (Cost-Plus Floor Protection) và giới hạn chặn giá sàn.

Hệ thống được thiết kế theo kiến trúc **Tool-Augmented RAG** kết hợp cơ chế hoạt động kép (**Dual-Mode Architecture**):
- **Chế độ trực tuyến (Live LLM)**: Sử dụng Google Gemini API (`gemini-2.5-flash` / `gemini-1.5-flash`) kết hợp Function Calling để truy xuất dữ liệu từ các Semantic Tools chuẩn hóa.
- **Chế độ nội bộ dự phòng (Intelligent Deterministic Engine)**: Tự động kích hoạt khi hệ thống không có API Key hoặc gặp sự cố mạng, bảo đảm 100% thời gian hoạt động với độ trễ xử lý <= 0.5 giây.

---

### 2. CẤU HÌNH HỆ THỐNG VÀ BIẾN MÔI TRƯỜNG

#### 2.1. Cấu hình Backend (`backend/.env`)

Để kích hoạt kết nối với Google Gemini API, cấu hình các biến môi trường trong file `backend/.env`:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=your_google_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Cơ sở dữ liệu
DATABASE_URL=sqlite:///./test.db
```

> **Ghi chú quan trọng**: Nếu `GEMINI_API_KEY` để trống hoặc không hợp lệ, hệ thống sẽ tự động chuyển sang cơ chế **Deterministic Engine** mà không gây gián đoạn dịch vụ hoặc phát sinh lỗi 500.

#### 2.2. Khởi chạy Dịch vụ Backend

```powershell
# Di chuyển vào thư mục backend và khởi chạy server
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
Tài liệu tương tác Swagger UI: `http://localhost:8000/docs`

#### 2.3. Khởi chạy Giao diện Frontend

```powershell
# Di chuyển vào thư mục frontend và khởi chạy Vite dev server
cd frontend
npm install
npm run dev -- --port 5173
```
Truy cập giao diện: `http://localhost:5173`

---

### 3. KIẾN TRÚC VÀ LUỒNG DỮ LIỆU (DATA FLOW)

```
[ Người dùng / Giao diện Frontend ]
   |
   +---> Gửi câu hỏi / Thao tác "Giải thích đề xuất giá"
   |
[ AiChatContext & aiApi.ts ]
   |
   +---> REST API: POST /api/v1/ai/chat hoặc GET /api/v1/ai/explain/{sku}
   |
[ FastAPI Router: backend/app/api/v1/endpoints/ai.py ]
   |
   +---> ChatService (Quản lý phiên, nạp 4 tin nhắn gần nhất)
   |
   +---> GeminiClient (Bộ điều phối Dual-Mode)
          |
          |-- (Có API Key) ----> Google Gemini API + Function Calling
          |                         |
          |-- (Fallback / Offline) -> Intelligent Deterministic Engine
                                     |
                                     v
                        [ Semantic Tools Layer: tools.py ]
                           |
                           +---> get_price_discrepancies()
                           +---> get_inventory_risks()
                           +---> get_sku_explain_factors()
                           |
                        [ SQLAlchemy ORM Queries ]
                           |
                           v
                        [ Cơ sở dữ liệu: SQLite / PostgreSQL ]
                                     |
[ Dữ liệu trả về có cấu trúc: tableData + explainFactors ]
   |
   +---> REST Response JSON (HTTP 200)
   |
[ Frontend Render: ExpandedAiDrawer / CompactChatPopup / PricingDetailModal ]
```

---

### 4. DANH MỤC API ENDPOINTS

Phân hệ AI Chatbot cung cấp 5 endpoints chuẩn RESTful tại prefix `/api/v1/ai`:

| Phương thức | Đường dẫn Endpoint | Mô tả chức năng | Request Body / Params | Định dạng phản hồi |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/ai/chat` | Xử lý hội thoại AI, tra cứu đối thủ, cảnh báo tồn kho, giải trình giá | `AiChatRequest` (`message`, `session_id`, `sku_context`) | `AiChatResponse` (`response`, `session_id`, `tableData`, `explainFactors`) |
| `GET` | `/api/v1/ai/explain/{sku}` | Truy xuất thẻ giải trình 3 lớp của mã SKU | Path param: `sku` (string) | `ExplainableFactors` |
| `GET` | `/api/v1/ai/sessions` | Lấy danh sách các phiên hội thoại | Không | `List[ChatSessionSummaryResponse]` |
| `GET` | `/api/v1/ai/sessions/{session_id}` | Lấy chi tiết lịch sử tin nhắn của phiên | Path param: `session_id` | `List[ChatMessageResponse]` |
| `DELETE` | `/api/v1/ai/sessions/{session_id}` | Xóa bỏ một phiên hội thoại | Path param: `session_id` | `{"message": "Session deleted successfully"}` |

---

### 5. CÁC CÔNG CỤ NGHIỆP VỤ (SEMANTIC TOOLS)

Nằm tại `backend/app/services/ai/tools.py`, các Semantic Tools đóng gói toàn bộ logic truy vấn dữ liệu từ cơ sở dữ liệu:

1. **`get_price_discrepancies(db, category, brand, competitor_name, min_price_diff, limit)`**:
   - Truy vấn chênh lệch giá giữa FPT và các đối thủ.
   - Điều kiện lọc nghiêm ngặt: Chỉ lấy bản ghi đối thủ còn hàng trực tuyến (`is_in_stock = True`), trạng thái liên kết SKU đã duyệt (`APPROVED`) hoặc có điểm tin cậy cao (`confidence >= 0.85`), chỉ lấy các mặt hàng mà giá FPT đang cao hơn đối thủ.
2. **`get_inventory_risks(db, min_doh, category, limit)`**:
   - Truy vấn các mã hàng có mức độ lưu kho nguy hiểm với số ngày tồn kho $DOH >= 45\text{ ngày}$.
   - Phân loại mức độ rủi ro vốn: `HIGH` (DOH >= 60 ngày), `MEDIUM` (DOH 45 - 59 ngày), `LOW` (DOH < 45 ngày).
3. **`get_sku_explain_factors(db, sku)`**:
   - Tổng hợp dữ liệu từ 4 bảng (`products`, `inventories`, `crawl_results`, `price_recommendations`) để tạo thẻ giải trình 3 lớp minh bạch.
   - Trả về đối tượng `ExplainableFactors` gồm: `competitor_shift`, `inventory_status`, `floor_protection`, kèm theo tóm tắt khuyến nghị hành động.

---

### 6. QUY TRÌNH KIỂM CHỨNG TỰ ĐỘNG (QUALITY GATE)

Toàn bộ hệ thống được bảo đảm chất lượng thông qua bộ kiểm thử tự động toàn diện:

```powershell
# 1. Kiểm thử Unit Test các Semantic Tools (6 tests)
pytest backend/tests/test_ai_tools.py -v

# 2. Kiểm thử Unit Test bộ điều phối AI Engine & Fallback (6 tests)
pytest backend/tests/test_ai_engine.py -v

# 3. Kiểm thử Integration Test các API Endpoints (6 tests)
pytest backend/tests/test_ai_endpoints.py -v

# 4. Kiểm thử tích hợp toàn bộ luồng kết nối FE - BE (16 endpoints)
python backend/scripts/verify_fe_be_integration.py

# 5. Kiểm thử hồi quy toàn bộ hệ thống Backend (174 tests)
pytest backend/tests/ -q
```

Tiêu chuẩn nghiệm thu đã đạt:
- **Tỷ lệ vượt qua kiểm thử**: 174/174 tests PASSED (100%).
- **Thời gian phản hồi API AI**: <= 0.5s (vượt xa tiêu chuẩn yêu cầu <= 10s).
- **Cấu trúc dữ liệu**: Đạt chuẩn Pydantic v2, tương thích hoàn toàn giữa Backend Python và Frontend TypeScript.
