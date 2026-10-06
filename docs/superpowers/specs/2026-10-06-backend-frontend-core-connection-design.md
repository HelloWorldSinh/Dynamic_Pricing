# Thiết kế Kỹ thuật: Kết nối Toàn diện Backend và Frontend cho các Tính năng Cốt lõi (Core Features)

- **Ngày ban hành:** 2026-10-06
- **Tác giả:** AI Pair Programmer & Lead Engineer
- **Trạng thái:** DRAFT / Đề xuất phê duyệt
- **Mục tiêu:** Kết nối thực tế và đồng bộ hóa hợp đồng dữ liệu giữa FastAPI Backend và React Frontend cho 5 module cốt lõi, xóa bỏ sự phụ thuộc vào mock data và đảm bảo dữ liệu hiển thị từ cơ sở dữ liệu SQLite thật.

---

## 1. Bối cảnh & Mục tiêu Nghiệp vụ

Hệ thống Dynamic Pricing System hiện đã phát triển hoàn thiện các thuật toán và logic nghiệp vụ ở cả Backend (87/87 tests passed) và giao diện người dùng Frontend (TypeScript build thành công). Tuy nhiên, giữa hai tầng còn tồn tại một số điểm lệch hợp đồng dữ liệu (schema mismatch) và thiếu các API endpoints trung gian:
1. **Ma trận so sánh giá & Mô phỏng:** Backend đã có endpoint nhưng CSDL chưa nạp dữ liệu thật (0 sản phẩm).
2. **Đề xuất giá (Pricing Recommendations):** Schema trả về từ Backend là dữ liệu thô từ bảng DB, thiếu các trường sản phẩm đã làm giàu (`sku`, `product_name`, `floor_price`, `cost_price`, `doh`) mà giao diện duyệt giá cần. Thiếu endpoint `reject` và `apply-custom`.
3. **Hàng đợi đối soát SKU (SKU Matching Queue):** Chưa có router `/matching` để Frontend duyệt các cặp 60% - 79%.
4. **AI Trợ lý & Giải trình 3 lớp (AI Assistant):** Chưa có router `/ai` kết nối trợ lý chat và API bóc tách 3 tầng quyết định giá (`/ai/explain/{sku}`).

Mục tiêu là hoàn thiện các routers Backend còn thiếu, chuẩn hóa hợp đồng dữ liệu, nạp dữ liệu thật từ catalog FPT (329 SKU) và dữ liệu cào đối thủ, sau đó kết nối thông suốt với Frontend.

---

## 2. Thiết kế Kiến trúc & Hợp đồng Dữ liệu (Data Contracts)

### 2.1. Module Đề xuất & Phê duyệt Giá (`/pricing`)

#### Endpoints Bổ sung & Nâng cấp:
1. **`GET /api/v1/pricing/recommendations`**
   - **Mục đích:** Trả về danh sách đề xuất giá kèm thông tin sản phẩm và tồn kho chi tiết để Frontend hiển thị trên `PricingApprovalsPage`.
   - **Response Format:**
     ```json
     {
       "total": 329,
       "items": [
         {
           "id": "uuid",
           "sku": "FPT-IPHONE-15PM-256",
           "product_name": "iPhone 15 Pro Max 256GB",
           "category": "PHONE",
           "brand": "Apple",
           "current_price": 29990000,
           "suggested_price": 28990000,
           "floor_price": 27500000,
           "cost_price": 26000000,
           "is_floor_protected": false,
           "doh": 48,
           "inventory_quantity": 85,
           "min_competitor_price": 28900000,
           "competitor_name": "CellphoneS",
           "competitor_in_stock": true,
           "cellphones_price": 28900000,
           "cellphones_in_stock": true,
           "hoangha_price": 29100000,
           "hoangha_in_stock": true,
           "scenario": "Kịch bản 4: Cầu cao nhưng Hàng ứ",
           "margin_impact_percent": -3.33,
           "status": "PENDING",
           "reviewed_at": null,
           "reviewed_by": null
         }
       ]
     }
     ```
2. **`POST /api/v1/pricing/recommendations/{id}/reject`**
   - **Mục đích:** Chuyên viên từ chối đề xuất giá (chuyển trạng thái sang `REJECTED`, ghi nhật ký `pricing_audit_logs`).
3. **`POST /api/v1/pricing/recommendations/{id}/apply-custom`**
   - **Mục đích:** Chuyên viên áp dụng mức giá điều chỉnh thủ công (`custom_price`).
   - **Request:**
     ```json
     {
       "custom_price": 28500000,
       "change_type": "MANUAL_CONFIG",
       "reviewed_by": "Pricing Analyst"
     }
     ```
   - **Hành vi:** Cập nhật đề xuất sang `APPROVED`, đặt `recommended_price = custom_price`, ghi nhật ký kiểm toán và lưu biến động vào `price_history`.

---

### 2.2. Module Hàng đợi Đối soát SKU (`/matching`)

Tạo mới file router `backend/app/api/v1/endpoints/matching.py` và đăng ký vào `api_router`.

#### Endpoints:
1. **`GET /api/v1/matching/queue`**
   - **Query Params:** `skip: int = 0, limit: int = 50, status: str = "PENDING"`
   - **Mục đích:** Truy vấn các cặp so khớp có độ tin cậy từ 60% đến 79% cần con người duyệt.
   - **Response Format:**
     ```json
     [
       {
         "id": "uuid",
         "fpt_sku": "FPT-ASUS-VIVO15",
         "fpt_name": "Laptop Asus Vivobook 15 X1504ZA i3 1215U/8GB/512GB",
         "fpt_part_number": "X1504ZA-NJ517W",
         "fpt_price": 10990000,
         "competitor_source": "CELLPHONES",
         "competitor_name": "Laptop ASUS Vivobook 15 X1504ZA-NJ517W 8GB 512GB",
         "competitor_url": "https://cellphones.com.vn/...",
         "competitor_price": 10490000,
         "confidence_score": 75.5,
         "matched_attributes": ["brand: ASUS", "ram: 8GB", "storage: 512GB"],
         "differing_attributes": ["cpu_naming: i3 1215U vs Gen 12"],
         "status": "PENDING"
       }
     ]
     ```
2. **`POST /api/v1/matching/queue/{id}/approve`**
   - Chuyển `SkuMapping.status` thành `APPROVED`.
3. **`POST /api/v1/matching/queue/{id}/reject`**
   - Chuyển `SkuMapping.status` thành `REJECTED`.

---

### 2.3. Module AI Trợ lý & Giải trình 3 lớp (`/ai`)

Tạo mới file router `backend/app/api/v1/endpoints/ai.py` và đăng ký vào `api_router`.

#### Endpoints:
1. **`POST /api/v1/ai/chat`**
   - **Request:**
     ```json
     {
       "message": "Phân tích rủi ro tồn kho iPhone 15",
       "session_id": "optional-uuid"
     }
     ```
   - **Xử lý:**
     - Trích xuất thực thể (SKU, nhãn hàng, dòng máy) từ câu hỏi.
     - Truy vấn CSDL thật: `Product`, `InventoryMock`, `CrawlResult`, `PriceRecommendation`.
     - Sinh câu trả lời định hướng dữ liệu thực tế (Data-Grounded Answer), kèm bảng so sánh nếu câu hỏi liên quan đến giá hoặc tồn kho.
     - Lưu hội thoại vào `chat_sessions` và `chat_messages`.
   - **Response:**
     ```json
     {
       "message": "Phân tích rủi ro tồn kho iPhone: ...",
       "tableData": [
         {
           "SKU": "...",
           "Tên sản phẩm": "...",
           "Giá FPT": "...",
           "CellphoneS": "...",
           "DOH": "..."
         }
       ]
     }
     ```
2. **`GET /api/v1/ai/explain/{sku}`**
   - **Mục đích:** Cung cấp dữ liệu bóc tách 3 tầng quyết định giá cho cửa sổ chi tiết sản phẩm và AI Drawer.
   - **Response Format:**
     ```json
     {
       "competitor_shift": {
         "competitor": "CellphoneS",
         "old_price": 18490000,
         "new_price": 17890000,
         "price_cut": 600000,
         "is_in_stock": true
       },
       "inventory_status": {
         "sku": "FPT-ASUS-VIVO15",
         "doh": 54,
         "quantity": 42,
         "doh_risk_level": "HIGH"
       },
       "floor_protection": {
         "floor_price": 17325000,
         "suggested_price": 17890000,
         "safety_margin_percent": 3.26,
         "is_capped": false
       }
     }
     ```

---

### 2.4. Module Thu thập Dữ liệu (`/crawl`)

- Các endpoints đã có sẵn trong `backend/app/api/v1/endpoints/crawl.py` (`POST /trigger`, `GET /status/{task_id}`, `GET /results`).
- Đảm bảo Frontend `crawlerApi.ts` gọi trực tiếp và hiển thị chính xác đếm ngược thời gian khi nhận mã lỗi HTTP `429 Too Many Requests` (Debounce 30s).

---

## 3. Kế hoạch Nạp Dữ liệu Thật (Seeding & Pipeline)

Hiện tại file SQLite `dynamic_pricing.db` chưa có bản ghi sản phẩm. Kế hoạch nạp dữ liệu:
1. Chạy `backend/scripts/run_e2e_pipeline.py`:
   - Nạp 329 SKU FPT chuẩn, 3 kho hàng, tồn kho và chỉ số clickstream.
   - Chạy thuật toán đối soát 2 tầng với 5,616 sản phẩm cào được từ CellphoneS & Hoàng Hà Mobile.
   - Chạy Dynamic Pricing Engine sinh đề xuất giá cho toàn bộ 329 sản phẩm.
   - Khởi tạo lịch sử biến động giá (`price_history`) và nhật ký kiểm toán (`pricing_audit_logs`).

---

## 4. Kế hoạch Kiểm thử & Tiêu chuẩn Chất lượng (Quality Assurance)

1. **Tuân thủ Hiến chương (Constitution & TDD):**
   - Viết các test case mới trong `backend/tests/` trước hoặc song song:
     - `test_matching_api.py`: Kiểm thử `GET /matching/queue`, `POST /approve`, `POST /reject`.
     - `test_ai_api.py`: Kiểm thử `POST /ai/chat`, `GET /ai/explain/{sku}`.
     - `test_pricing_api_extensions.py`: Kiểm thử `/reject`, `/apply-custom`, và làm giàu schema của `/recommendations`.
   - Đảm bảo toàn bộ 87+ bài test của backend tiếp tục PASS 100%.
2. **Quy tắc UI Design:**
   - Tuyệt đối không chèn emoji hoặc icon trang trí trong bất kỳ API response string hay giao diện người dùng.
3. **Kiểm thử Frontend:**
   - Chạy `npm run build` xác nhận không có lỗi TypeScript compilation.
   - Xác nhận Frontend hiển thị dữ liệu thật từ Backend (không rớt về mock data).
