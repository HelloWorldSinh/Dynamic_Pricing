---
title: Phân Tích và Đánh Giá So Sánh Các Kiến Trúc Chatbot AI (AI Pricing Assistant)
tags: [dynamic-pricing, ai-architecture, rag, text-to-sql, function-calling, adr, sprint-2]
date: 2026-10-21
status: approved
author: HaiNN58 & SinhDTD
---

# BÁO CÁO PHÂN TÍCH VÀ ĐÁNH GIÁ CÁC KIẾN TRÚC CHO PHÂN HỆ TRỢ LÝ AI CHATBOT

- **Dự án**: Dynamic Pricing System (LQSMART-OJT)
- **Đơn vị**: FPT Shop / FPT Software
- **Phân hệ**: EPIC 5 — Trợ lý AI Chat (AI Pricing Assistant & Explainable Engine)
- **Hạng mục PBI**: PBI-017 (Chatbot hỏi đáp nghiệp vụ RAG) & PBI-018 (Giải thích minh bạch lý do đề xuất giá)
- **Tài liệu tham chiếu**: [[Dynamic Pricing Index]], [[Product Backlog – Dynamic Pricing]], [[Kế hoạch Chi tiết Triển khai Chatbot AI (PBI-017 & PBI-018)]]

---

## 1. BỐI CẢNH VÀ ĐẶC THÙ NGHIỆP VỤ

### 1.1. Mục tiêu phân hệ
Phân hệ Trợ lý AI Chatbot đóng vai trò là **FPT Shop Market Copilot** hỗ trợ người dùng duy nhất (**Single User / Pricing Analyst**) thực hiện 2 nhiệm vụ cốt lõi:
1. **PBI-017**: Truy vấn, so sánh giá đối thủ (CellphoneS, Hoàng Hà) và phân tích rủi ro tồn kho (DOH > 45 ngày) bằng ngôn ngữ tự nhiên.
2. **PBI-018**: Giải trình minh bạch lý do điều chỉnh giá theo cấu trúc chuẩn 3 lớp (Biến động đối thủ + Tồn kho FPT + Bảo vệ giá sàn).

### 1.2. Đặc thù dữ liệu và các ràng buộc phi chức năng (NFR)
- **Dữ liệu định lượng và có cấu trúc cao**: Toàn bộ dữ liệu nằm trong cơ sở dữ liệu quan hệ (`products`, `crawl_results`, `sku_mappings`, `inventories`, `price_recommendations`).
- **Quy tắc kinh doanh nghiêm ngặt**:
  - Không so sánh giá khi đối thủ có trạng thái hết hàng online (`is_in_stock = False`).
  - Chỉ chấp nhận so khớp giá khi cặp SKU đã được duyệt (`APPROVED`) hoặc có điểm tin cậy $Confidence \ge 80\%$.
  - Tuyệt đối không đề xuất giá dưới giá sàn ($\text{Floor Price} = \text{Cost} + \text{Minimum Margin}$).
- **Môi trường đa CSDL**: Sử dụng **SQLite** cho môi trường phát triển cục bộ và kiểm thử tự động (CI/CD), sử dụng **PostgreSQL** cho môi trường triển khai thực tế.
- **Yêu cầu SLA**: Thời gian phản hồi câu hỏi $\le 3\text{ giây}$ (vượt xa chuẩn Acceptance Criteria $\le 10\text{ giây}$).
- **Khả năng chịu lỗi (Resilience)**: Hệ thống phải hoạt động ổn định, không sập khi mất kết nối Internet hoặc chưa cấu hình API Key bên ngoài.

---

## 2. KHẢO SÁT VÀ PHÂN TÍCH 4 KIẾN TRÚC KHẢ THI

### 2.1. Kiến trúc 1: Text-to-SQL Thuần túy (Natural Language to SQL)

#### Mô hình hoạt động
Mô hình đưa toàn bộ lược đồ CSDL (DDL) vào System Prompt của LLM. Khi người dùng đặt câu hỏi, LLM tự động sinh câu truy vấn SQL thô (`SELECT ... JOIN ... WHERE ...`), Backend thực thi câu SQL này vào CSDL và gửi kết quả dạng bảng phẳng (flat rows) trở lại cho LLM để viết văn bản trả lời.

```
[User Question] ──► [LLM + Schema DDL] ──► [Raw SQL Query] ──► [Database Execution] ──► [LLM Summarization] ──► [User Response]
```

#### Ưu điểm
- **Tính linh hoạt cực cao**: Có khả năng trả lời các câu hỏi truy vấn đa chiều mà lập trình viên chưa dự kiến trước (ví dụ: *"Đếm số lượng sản phẩm cào được theo từng ngày trong tuần qua"*).
- **Không cần định nghĩa trước nhiều API**: Tận dụng trực tiếp khả năng biểu đạt của ngôn ngữ SQL.

#### Nhược điểm và Rủi ro nghiêm trọng
- **Sai lệch quy tắc nghiệp vụ cốt lõi**: LLM khi tự sinh SQL rất dễ bỏ quên các điều kiện lọc bắt buộc như `crawl_results.is_in_stock = true` hoặc quên lọc trạng thái `sku_mappings.status = 'APPROVED'`. Điều này dẫn đến việc đưa ra dữ liệu so sánh giá sai lệch, ảnh hưởng trực tiếp đến quyết định kinh doanh.
- **Xung đột phương ngữ CSDL (SQLite vs PostgreSQL)**:
  - SQLite không hỗ trợ hàm `ILIKE` (chỉ có `LIKE`), khác biệt về hàm thời gian (`strftime` vs `date_trunc`), và cách xử lý kiểu dữ liệu UUID/JSON.
  - LLM thường sinh SQL theo chuẩn Postgres, khiến test tự động trên SQLite bị lỗi cú pháp (`OperationalError: no such function`).
- **Không đáp ứng được Thẻ Giải trình 3 lớp (PBI-018)**:
  - PBI-018 đòi hỏi một cấu trúc JSON lồng nhau gồm 3 đối tượng riêng biệt (`competitor_shift`, `inventory_status`, `floor_protection`).
  - Một câu lệnh SQL đơn thuần chỉ trả về bảng dữ liệu phẳng, không thể tự sinh cấu trúc lồng nhau phức tạp này nếu không có tầng code xử lý chuyên biệt.
- **Rủi ro bảo mật & Hiệu năng**:
  - Nguy cơ SQL Injection thông qua Prompt Injection (người dùng cố tình lừa LLM sinh câu lệnh `DROP TABLE` hoặc `UPDATE`).
  - LLM có thể sinh câu truy vấn thiếu `LIMIT` hoặc phép JOIN không có index làm nghẽn CPU database.
- **Độ trễ cao**: Cần 2 lượt gọi LLM (Lượt 1: sinh SQL -> Lượt 2: giải thích dữ liệu), tổng thời gian thường mất từ 4 đến 8 giây.

---

### 2.2. Kiến trúc 2: Vector Search / Semantic RAG (Embedding-based)

#### Mô hình hoạt động
Tài liệu hoặc bản ghi sản phẩm được phân cắt (chunking) và chuyển thành các vector số học thông qua mô hình Embedding (Text-Embedding-004 của Google hoặc OpenAI). Dữ liệu vector được lưu vào Vector Database (ChromaDB, FAISS hoặc pgvector). Khi có câu hỏi, hệ thống tính toán khoảng cách cosine giữa vector câu hỏi và vector dữ liệu để tìm ra các đoạn văn bản tương đồng nhất.

```
[User Question] ──► [Embedding Model] ──► [Vector DB (Cosine Similarity)] ──► [Top K Chunks] ──► [LLM Answer]
```

#### Ưu điểm
- Rất mạnh trong việc tìm kiếm ngữ nghĩa văn bản phi cấu trúc (ví dụ: cẩm nang hướng dẫn sử dụng, tài liệu chính sách bảo hành, mô tả bài viết).

#### Nhược điểm và Lý do không phù hợp
- **Bất lực trước các bài toán số học và lọc định lượng**:
  - Không thể thực hiện phép so sánh số: `fpt_price > competitor_price` hoặc `doh > 45`.
  - Không thể tính toán số tiền chênh lệch tuyệt đối hay tỷ lệ phần trăm biên an toàn.
  - Vector search dựa trên sự tương đồng từ ngữ, không thể thực hiện các phép toán tập hợp (Sort, Filter, Group By, Limit).
- **Chi phí vận hành và tài nguyên thừa thãi**: Phải dựng thêm hạ tầng Vector DB và tốn chi phí embedding định kỳ mỗi khi giá sản phẩm thay đổi sau các lượt cào giá.

---

### 2.3. Kiến trúc 3: Rule-based & Deterministic Engine (Hệ chuyên gia nội bộ)

#### Mô hình hoạt động
Sử dụng biểu thức chính quy (Regex) và bộ phân tích từ khóa nội bộ (Parser) để bóc tách ý định người dùng (Intent: tra giá, tra kho, hay giải trình). Sau đó gọi trực tiếp các câu truy vấn SQLAlchemy ORM đã viết sẵn và định dạng câu trả lời theo các mẫu khuôn định sẵn (Templates). Hoàn toàn không gọi bất kỳ LLM nào bên ngoài.

```
[User Question] ──► [Keyword/Regex Parser] ──► [SQLAlchemy ORM Functions] ──► [Template Formatter] ──► [User Response]
```

#### Ưu điểm
- **Độ trễ siêu tốc**: Thời gian xử lý dưới $50\text{ms}$.
- **Độc lập 100%**: Hoạt động hoàn toàn offline, không cần internet, không tốn chi phí API.
- **Độ chính xác nghiệp vụ tuyệt đối (100%)**: Không bao giờ xảy ra hiện tượng ảo giác (hallucination).
- **An toàn bảo mật tối đa**: Không có rủi ro rò rỉ dữ liệu hay SQL Injection.

#### Nhược điểm
- **Thiếu tính linh hoạt về ngôn ngữ**: Chỉ nhận diện được các mẫu câu hỏi đã được định nghĩa trước; nếu người dùng diễn đạt theo cách khác lạ, hệ thống sẽ không hiểu được hoặc báo lỗi.
- **Thiếu trải nghiệm hội thoại tự nhiên**: Câu trả lời mang tính máy móc, rập khuôn theo mẫu template.

---

### 2.4. Kiến trúc 4: Tool-Augmented RAG với Function Calling (Kiến trúc Đề xuất)

#### Mô hình hoạt động
Mô hình kết hợp ưu thế vượt trội của LLM trong việc hiểu ngôn ngữ tự nhiên với tính chính xác, an toàn của mã nguồn Python và SQLAlchemy ORM:
1. LLM (**Google Gemini 1.5/2.0 Flash**) đóng vai trò là **Bộ điều phối (Orchestrator)**.
2. Lập trình viên định nghĩa sẵn các **Công cụ nghiệp vụ (Semantic Tools)** viết bằng SQLAlchemy ORM:
   - `get_price_discrepancies(...)`: Truy vấn chênh lệch giá, tự động đóng gói quy tắc lọc `is_in_stock = True`, `confidence >= 80%`.
   - `get_inventory_risks(...)`: Truy vấn sản phẩm $DOH \ge 45\text{ ngày}$.
   - `get_sku_explain_factors(...)`: Trích xuất đủ 3 lớp yếu tố (đối thủ, tồn kho, giá sàn).
3. Gemini đọc hiểu câu hỏi của người dùng, tự động quyết định gọi Tool nào với tham số gì (ví dụ: bóc tách `{category: 'LAPTOP', brand: 'ASUS', limit: 5}`).
4. Backend thực thi Tool nội bộ bằng ORM (tự động tương thích cả SQLite lẫn PostgreSQL).
5. Kết quả dữ liệu sạch (JSON) được nạp ngược lại cho Gemini để sinh ra câu trả lời tự nhiên, đồng thời trả kèm cấu trúc `tableData` và `explainFactors` trực tiếp cho giao diện Frontend.
6. **Cơ chế Chạy kép (Dual-Mode & Graceful Fallback)**: Tích hợp sẵn một bộ Deterministic Engine dự phòng. Khi mất kết nối Internet hoặc không có `GEMINI_API_KEY`, hệ thống tự động chuyển sang chạy offline mà không làm gián đoạn trải nghiệm người dùng hay gãy CI/CD test.

```
[Chuyên viên hỏi]
       │
       ▼
[FastAPI Endpoint: POST /api/v1/ai/chat]
       │
       ▼
[Gemini 1.5 Flash (Orchestrator)] 
(Phân tích ngôn ngữ tự nhiên & trích xuất tham số)
       │
       ├─► Yêu cầu gọi Tool: `get_price_discrepancies(category='LAPTOP', brand='ASUS')`
       │
       ▼
[Backend Python ORM Tools]
(Thực thi truy vấn an toàn bằng SQLAlchemy, áp dụng 100% logic nghiệp vụ)
       │
       ▼
[Dữ liệu JSON chuẩn xác từ Database]
       │
       ▼
[Gemini tổng hợp phản hồi]
       │
       ├─► Nội dung trả lời tự nhiên bằng tiếng Việt
       ├─► Bảng dữ liệu chi tiết đa cột (`tableData`)
       └─► Thẻ giải trình minh bạch 3 lớp (`explainFactors`)
       │
       ▼
[Frontend UI: Hiển thị trực quan trên Popup / Drawer]
```

---

## 3. BẢNG SO SÁNH TRỰC DIỆN (MULTI-CRITERIA EVALUATION MATRIX)

| Tiêu chí Đánh giá | 1. Text-to-SQL Thuần túy | 2. Vector Search RAG | 3. Rule-based Deterministic | 4. Tool-Augmented RAG (Đề xuất) |
| :--- | :---: | :---: | :---: | :---: |
| **Độ chính xác quy tắc nghiệp vụ** | Thấp (dễ quên lọc hàng tồn/hết hàng) | Không áp dụng (không lọc được số) | Tuyệt đối (100%) | **Tuyệt đối (100% qua ORM)** |
| **Khả năng xử lý số liệu & tính toán** | Tốt (nếu SQL sinh đúng) | Không thể xử lý | Tốt (trong phạm vi hàm viết sẵn) | **Rất tốt (kết hợp ORM + LLM)** |
| **Tính linh hoạt ngôn ngữ tự nhiên** | Rất cao | Cao | Thấp (theo mẫu định sẵn) | **Rất cao (Gemini hiểu mọi câu hỏi)** |
| **Hỗ trợ thẻ giải trình 3 lớp (PBI-018)**| Kém (chỉ trả về bảng phẳng) | Kém | Tốt (theo mẫu template) | **Hoàn hảo (trả về đúng schema JSON)** |
| **Tương thích SQLite & PostgreSQL** | Rất kém (dễ lỗi phương ngữ SQL) | Không phụ thuộc CSDL | An toàn 100% (SQLAlchemy) | **An toàn 100% (SQLAlchemy ORM)** |
| **Bảo mật (Chống SQL Injection)** | Rủi ro cao (cần AST parser) | An toàn | An toàn tuyệt đối | **An toàn tuyệt đối (tham số hóa)** |
| **Độ trễ trung bình (Latency)** | Cao ($4.0 - 8.0\text{s}$) | Trung bình ($1.5 - 3.0\text{s}$) | Cực thấp ($< 0.05\text{s}$) | **Thấp ($1.0 - 2.5\text{s}$)** |
| **Khả năng chạy Offline / Test CI-CD**| Không thể chạy offline | Không thể chạy offline | Chạy offline 100% | **Hoàn hảo (hỗ trợ Dual-Mode Fallback)** |

---

## 4. QUYẾT ĐỊNH KIẾN TRÚC (ARCHITECTURAL DECISION - ADR)

### 4.1. Lựa chọn chính thức
Hệ thống chính thức thông qua kiến trúc **Tool-Augmented RAG kết hợp Dual-Mode Fallback**:
- Sử dụng mô hình **Google Gemini 1.5 Flash** cho tầng suy luận và phân loại ý định (Reasoning Layer).
- Sử dụng **SQLAlchemy ORM** để xây dựng bộ 3 công cụ truy vấn nghiệp vụ (Data Retrieval Layer).
- Tích hợp bộ **Deterministic Fallback Engine** nội bộ để đảm bảo hệ thống luôn sẵn sàng 100% trong môi trường kiểm thử tự động, build CI/CD hoặc khi gặp sự cố mạng bên ngoài.

### 4.2. Lý do lựa chọn
1. **Bảo vệ toàn vẹn logic định giá**: Toàn bộ các quy tắc sống còn của hệ thống (bảo vệ giá sàn, loại trừ đối thủ hết hàng, chỉ so sánh khi confidence $\ge 80\%$) được kiểm soát chặt chẽ bằng code Python, loại bỏ hoàn toàn nguy cơ ảo giác hay tính toán sai của LLM.
2. **Đáp ứng hoàn hảo cả 2 PBI**:
   - PBI-017: Trả về câu trả lời tự nhiên kèm bảng số liệu chi tiết (`tableData`).
   - PBI-018: Trả về đối tượng `explainFactors` chuẩn 3 lớp, tương thích trực tiếp với component [ExplainableCard.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/ai/ExplainableCard.tsx).
3. **Chi phí 0đ và Độ trễ tối ưu**: Gemini 1.5 Flash cung cấp hạn mức miễn phí 15 requests/phút, tốc độ phản hồi trung bình chỉ 1.2s – 1.8s, đáp ứng nghiêm ngặt SLA của hệ thống.
4. **Không phát sinh nợ kỹ thuật (Technical Debt)**: Không cần cài đặt các framework cồng kềnh (LangChain/LlamaIndex) hay hạ tầng Vector DB riêng biệt, giữ codebase tinh gọn, sạch sẽ theo đúng tinh thần Clean Architecture và nguyên tắc YAGNI.

---

## 5. HƯỚNG MỞ RỘNG TRONG TƯƠNG LAI

Nếu sau giai đoạn MVP hệ thống có nhu cầu mở rộng, kiến trúc hiện tại cho phép tích hợp thêm hai thành phần phụ:
1. **Bổ sung Text-to-SQL làm Tool dự phòng (Fallback Analytic Tool)**: Nếu chuyên viên định giá hỏi một câu hỏi thống kê tùy biến ngoài 3 tool định sẵn (ví dụ: *"Có bao nhiêu lần giá bị đổi trong tháng trước?"*), Backend có thể chuyển tiếp câu hỏi sang một tool phụ là `execute_safe_readonly_query()`. Tool này sẽ kiểm duyệt cú pháp qua `sqlglot` để chỉ cho phép lệnh `SELECT` thuần túy trước khi thực thi.
2. **Bổ sung Vector Search khi có dữ liệu chính sách phi cấu trúc**: Khi hệ thống cần tra cứu các văn bản chính sách bảo hành, thỏa thuận phân phối từ nhà cung cấp (dạng PDF/Word), một Vector Store nhẹ (như ChromaDB hoặc pgvector) có thể được bổ sung vào dưới dạng một Tool tra cứu văn bản chuyên biệt.
