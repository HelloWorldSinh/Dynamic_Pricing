# KẾ HOẠCH CHI TIẾT TRIỂN KHAI PHÂN HỆ TRỢ LÝ AI CHATBOT

- **Dự án**: Dynamic Pricing System (LQSMART-OJT)
- **Đơn vị**: FPT Shop / FPT Software
- **Phân hệ**: EPIC 5 — Trợ lý AI Chat (AI Pricing Assistant & Explainable Engine)
- **Hạng mục PBI**: PBI-017 (Chatbot hỏi đáp nghiệp vụ RAG) & PBI-018 (Giải thích minh bạch lý do đề xuất giá)

---

## 1. TỔNG QUAN VÀ MỤC TIÊU PHÂN HỆ

Xây dựng hoàn chỉnh trợ lý ảo thông minh **FPT Shop Market Copilot** phục vụ duy nhất một Persona là **Pricing Analyst** (chuyên viên phân tích giá). Hệ thống cho phép:
1. Truy vấn so sánh giá 3 bên (FPT Shop vs CellphoneS vs Hoàng Hà) và phát hiện chênh lệch giá bằng ngôn ngữ tự nhiên.
2. Cảnh báo nguy cơ tồn kho lâu ngày (DOH > 45 ngày) và áp lực xả hàng.
3. Giải trình minh bạch 3 lớp (Biến động đối thủ + Tồn kho FPT + Bảo vệ giá sàn) trước khi phê duyệt đề xuất giá.
4. Cơ chế vận hành kép (**Dual-Mode**): Ưu tiên gọi Google Gemini API (`gemini-1.5-flash` / `gemini-2.0-flash`) và tự động chuyển sang Deterministic Engine nội bộ khi offline hoặc chưa nạp API key.

---

## 2. BẢNG PHÂN RÃ CÔNG VIỆC CHI TIẾT (WORK BREAKDOWN STRUCTURE - WBS)

### GIAI ĐOẠN 1: NGHIÊN CỨU & KHẢO SÁT KIẾN TRÚC (RESEARCH & ARCHITECTURE)
- [x] **Task 1.1: Khảo sát yêu cầu nghiệp vụ và Acceptance Criteria**
  - Rà soát đặc tả PBI-017 và PBI-018 trong Product Backlog.
  - Xác định Persona: Single User — Pricing Analyst vận hành toàn trình trên Dashboard.
  - Thu thập danh mục các mẫu câu hỏi nghiệp vụ thực tế (so sánh giá 3 bên, cảnh báo rủi ro DOH > 45 ngày, giải trình đề xuất giá).
- [x] **Task 1.2: Nghiên cứu và so sánh các phương án kỹ thuật AI Core**
  - Phân tích Text-to-SQL thuần túy: Xác định rủi ro sai lệch quy tắc nghiệp vụ (`is_in_stock`, ngưỡng mapping confidence), xung đột cú pháp giữa SQLite (local) và PostgreSQL (production), và nguy cơ bảo mật SQL Injection.
  - Phân tích Tool-Augmented RAG (Function Calling): Đánh giá tính an toàn khi đóng gói logic bằng SQLAlchemy ORM.
  - Phân tích Rule-based Deterministic: Thiết lập làm tầng bảo hiểm khi mất kết nối mạng.
- [x] **Task 1.3: Chốt kiến trúc giải pháp và mô hình LLM**
  - Chốt mô hình: Google Gemini API (`gemini-1.5-flash`) qua cơ chế Function Calling với thời gian phản hồi < 1.5s.
  - Chốt phương pháp: Tool-Augmented RAG kết hợp Dual-Mode (Graceful Fallback nội bộ).
- [x] **Task 1.4: Lập tài liệu thiết kế kỹ thuật (Technical Plan)**
  - Viết tài liệu Kế hoạch triển khai chi tiết lưu trữ tại `docs/superpowers/plans/2026-10-20-ai-chatbot-implementation-plan.md`.
  - Thiết kế sơ đồ luồng dữ liệu (Data Flow) từ Frontend UI -> FastAPI -> ORM Tools -> Gemini -> Response.

---

### GIAI ĐOẠN 2: THIẾT KẾ DỮ LIỆU & TẦNG TRUY VẤN NGHIỆP VỤ (DATA CONTRACTS & RETRIEVAL LAYER)
- [x] **Task 2.1: Xây dựng Data Contracts (Pydantic Schemas)**
  - Tạo file `backend/app/schemas/ai.py`.
  - Khai báo schema `CompetitorShift`: đối thủ, giá cũ, giá mới, mức hạ, trạng thái còn hàng online.
  - Khai báo schema `InventoryStatus`: mã SKU, số lượng tồn khả dụng, DOH, mức độ rủi ro vốn (LOW, MEDIUM, HIGH).
  - Khai báo schema `FloorProtection`: giá sàn tối thiểu, giá đề xuất, biên an toàn %, cờ cảnh báo chạm giá sàn (`is_capped`).
  - Khai báo schema `ExplainableFactors`: cấu trúc tổng hợp 3 lớp chuẩn phục vụ PBI-018.
  - Khai báo request/response models: `AiChatRequest`, `AiChatResponse`, `ChatSessionSummaryResponse`, `ChatMessageResponse`.
- [x] **Task 2.2: Xây dựng Semantic Tool 1 — Tra cứu chênh lệch giá đối thủ**
  - Tạo hàm `get_price_discrepancies()` trong `backend/app/services/ai/tools.py`.
  - Dùng SQLAlchemy ORM JOIN các bảng: `products`, `sku_mappings`, `crawl_results`, `inventories`.
  - Ràng buộc nghiệp vụ: Chỉ lấy sản phẩm đối thủ còn hàng (`is_in_stock = True`), trạng thái mapping đã duyệt hoặc confidence $\ge 80\%$, lọc FPT đắt hơn đối thủ.
- [x] **Task 2.3: Xây dựng Semantic Tool 2 — Tra cứu rủi ro tồn kho**
  - Tạo hàm `get_inventory_risks()` trong `tools.py`.
  - Lọc các sản phẩm tồn kho có $DOH \ge 45\text{ ngày}$ (hoặc ngưỡng tùy biến).
  - Phân loại cấp độ rủi ro vốn (HIGH khi DOH > 45, MEDIUM khi 30–45, LOW khi < 30).
- [x] **Task 2.4: Xây dựng Semantic Tool 3 — Trích xuất giải trình 3 lớp theo SKU**
  - Tạo hàm `get_sku_explain_factors()` trong `tools.py`.
  - Truy xuất dữ liệu từ `price_recommendations`, `inventories`, `crawl_results` cho 1 mã SKU chỉ định.
  - Định dạng kết quả trả về đúng chuẩn đối tượng `ExplainableFactors`.

---

### GIAI ĐOẠN 3: PHÁT TRIỂN LÕI AI ENGINE & ĐIỀU PHỐI (REASONING & SYNTHESIS LAYER)
- [ ] **Task 3.1: Cấu hình biến môi trường và Settings**
  - Bổ sung cấu hình `GEMINI_API_KEY` và `GEMINI_MODEL` vào `backend/app/core/config.py`.
  - Cập nhật file mẫu `.env.example`.
- [ ] **Task 3.2: Xây dựng Client kết nối Gemini (gemini_client.py)**
  - Tạo file `backend/app/services/ai/gemini_client.py`.
  - Thiết lập HTTP request gọi Gemini API với System Prompt nghiệp vụ định giá.
  - Khai báo Function Calling declarations tương ứng với 3 Semantic Tools.
- [ ] **Task 3.3: Xây dựng bộ sinh dự phòng nội bộ (Deterministic Engine)**
  - Tích hợp logic phân tích từ khóa câu hỏi (laptop, asus, iphone, doh, đối thủ...).
  - Đảm bảo khi mất kết nối mạng hoặc không có API key, hệ thống vẫn trả về câu trả lời và bảng dữ liệu chính xác 100%.
- [ ] **Task 3.4: Xây dựng dịch vụ điều phối hội thoại (chat_service.py)**
  - Tạo file `backend/app/services/ai/chat_service.py`.
  - Quản lý phiên chat: Tạo mới hoặc tái sử dụng `ChatSession`.
  - Xử lý lịch sử: Nạp 4 tin nhắn gần nhất từ `chat_messages` để duy trì ngữ cảnh trao đổi.
  - Điều phối vòng lặp Tool Execution: Nhận yêu cầu gọi Tool từ LLM -> Thực thi hàm ORM với DB Session -> Gửi kết quả ngược lại cho LLM để tổng hợp văn bản cuối cùng.
  - Lưu trữ tin nhắn người dùng và phản hồi của trợ lý vào bảng `chat_messages` kèm dữ liệu ngữ cảnh `retrieved_context`.

---

### GIAI ĐOẠN 4: XÂY DỰNG API ENDPOINTS & ROUTING (FASTAPI BACKEND)
- [ ] **Task 4.1: Xây dựng endpoint trò chuyện chính**
  - Tạo file `backend/app/api/v1/endpoints/ai.py`.
  - Triển khai `POST /api/v1/ai/chat`: Nhận câu hỏi, gọi qua `chat_service`, trả về tin nhắn + tableData + explainFactors.
- [ ] **Task 4.2: Xây dựng endpoint giải trình độc lập**
  - Triển khai `GET /api/v1/ai/explain/{sku}`: Tra cứu và trả về trực tiếp thẻ giải trình 3 lớp của mã SKU được chọn.
- [ ] **Task 4.3: Xây dựng các endpoint quản lý lịch sử phiên chat**
  - Triển khai `GET /api/v1/ai/sessions`: Lấy danh sách các phiên trò chuyện của chuyên viên.
  - Triển khai `GET /api/v1/ai/sessions/{session_id}`: Xem lại toàn bộ lịch sử tin nhắn của một phiên.
  - Triển khai `DELETE /api/v1/ai/sessions/{session_id}`: Xóa phiên hội thoại.
- [ ] **Task 4.4: Đăng ký Router**
  - Đăng ký `ai.router` vào `backend/app/api/v1/router.py` với tag `"AI Pricing Assistant (PBI-017 & PBI-018)"`.
  - Kiểm tra Swagger UI (`/docs`) để xác nhận các route đã hiển thị đầy đủ.

---

### GIAI ĐOẠN 5: TÍCH HỢP GIAO DIỆN NGƯỜI DÙNG (FRONTEND LIVE INTEGRATION)
- [ ] **Task 5.1: Cập nhật API Client kết nối thật**
  - Chỉnh sửa `frontend/src/api/aiApi.ts`: Xóa bỏ mock data giả lập ở luồng chính, kết nối trực tiếp vào `POST /api/v1/ai/chat` và `GET /api/v1/ai/explain/{sku}`.
- [ ] **Task 5.2: Quản lý trạng thái phiên chat phía Frontend**
  - Cập nhật `frontend/src/context/AiChatContext.tsx`.
  - Bổ sung `sessionId` vào context state, tự động lưu vào `sessionStorage` để không mất ngữ cảnh khi tải lại trang.
- [ ] **Task 5.3: Đồng bộ luồng "Giải thích đề xuất giá"**
  - Kiểm tra liên kết từ nút "Giải thích" tại bảng Ma trận giá / Bảng phê duyệt.
  - Đảm bảo khi bấm vào một SKU, hệ thống tự động mở Expanded Drawer (750px) và hiển thị thẻ `ExplainableCard.tsx` tương ứng.
- [ ] **Task 5.4: Kiểm thử hiển thị trên 3 trạng thái giao diện**
  - Kiểm tra Floating Action Button (FAB).
  - Kiểm tra Compact Chat Popup (380px) kèm các Prompt Chips gợi ý nhanh.
  - Kiểm tra Expanded Studio Drawer (750px) với các bảng dữ liệu nhiều cột.

---

### GIAI ĐOẠN 6: KIỂM THỬ TỰ ĐỘNG & ĐẢM BẢO CHẤT LƯỢNG (TESTING & QUALITY GATE)
- [ ] **Task 6.1: Viết Unit Tests cho các Semantic Tools**
  - Tạo file `backend/tests/test_ai_tools.py`.
  - Viết test kiểm tra loại trừ đối thủ hết hàng (`test_get_price_discrepancies_filters_out_of_stock`).
  - Viết test kiểm tra lọc ngưỡng DOH tồn kho (`test_get_inventory_risks_threshold`).
  - Viết test kiểm tra cấu trúc thẻ giải trình 3 lớp (`test_get_sku_explain_factors_structure`).
- [ ] **Task 6.2: Viết Integration Tests cho các API Endpoints**
  - Tạo file `backend/tests/test_ai_endpoints.py`.
  - Dùng FastAPI `TestClient` kiểm tra luồng hỏi giá đối thủ qua `POST /api/v1/ai/chat`.
  - Kiểm tra luồng hỏi rủi ro tồn kho DOH.
  - Kiểm tra endpoint `GET /api/v1/ai/explain/{sku}`.
  - Kiểm tra vòng đời tạo, đọc và xóa phiên chat.
- [ ] **Task 6.3: Kiểm tra hồi quy và đo lường SLA**
  - Chạy toàn bộ test suite backend bằng `pytest backend/tests/ -v`.
  - Đo thời gian phản hồi của endpoint AI: Đảm bảo thời gian xử lý $\le 3\text{ giây}$ (vượt chuẩn AC $\le 10\text{ giây}$ của PBI-017).

---

### GIAI ĐOẠN 7: TỔNG KẾT, TÀI LIỆU HÓA & NGHIỆM THU (HANDOVER & ACCEPTANCE)
- [ ] **Task 7.1: Hoàn thiện tài liệu kỹ thuật**
  - Cập nhật Walkthrough và hướng dẫn cấu hình vào tài liệu dự án.
- [ ] **Task 7.2: Chuẩn bị kịch bản Demo nghiệm thu**
  - Kịch bản 1: Hỏi so sánh giá laptop Asus (kiểm tra bảng dữ liệu đa cột).
  - Kịch bản 2: Hỏi rủi ro tồn kho iPhone (kiểm tra phân tích DOH).
  - Kịch bản 3: Bấm giải thích đề xuất giá từ bảng gợi ý (kiểm tra thẻ 3 lớp).
- [ ] **Task 7.3: Bàn giao và nghiệm thu PBI**
  - Đối soát Acceptance Criteria của PBI-017 và PBI-018 theo định dạng Given-When-Then.
  - Tạo Pull Request theo chuẩn Conventional Commits (`feat: implement ai pricing assistant and explainable engine`).

---

## 3. BẢNG TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA MAPPING)

| Mã PBI | Tiêu chí Nghiệm thu (Given - When - Then) | Task tương ứng | Trạng thái |
| :--- | :--- | :--- | :--- |
| **PBI-017** | **Given** chuyên viên nhập câu hỏi về giá laptop/điện thoại, **When** AI xử lý, **Then** phản hồi chính xác kèm bảng so sánh đa cột thời gian thực trong $\le 10\text{s}$. | Task 2.2, Task 3.4, Task 4.1 | Sẵn sàng triển khai |
| **PBI-017** | **Given** chuyên viên hỏi về tồn kho rủi ro, **When** AI xử lý, **Then** lọc ra các mã có $DOH > 45\text{ ngày}$ kèm cảnh báo xả hàng. | Task 2.3, Task 3.4, Task 4.1 | Sẵn sàng triển khai |
| **PBI-018** | **Given** chuyên viên hỏi *"Tại sao đề xuất giảm giá mã X?"*, **When** AI phân tích, **Then** trả về thẻ 3 lớp minh bạch: biến động đối thủ, tồn kho FPT, và an toàn giá sàn. | Task 2.4, Task 4.2, Task 5.3 | Sẵn sàng triển khai |
| **Hạ tầng** | **Given** hệ thống mất mạng hoặc không có API key, **When** gửi câu hỏi, **Then** tự động chuyển sang Deterministic Engine nội bộ, không báo lỗi sập hệ thống. | Task 3.3, Task 6.2 | Sẵn sàng triển khai |
