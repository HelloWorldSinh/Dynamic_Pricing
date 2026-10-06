# Thiết Kế Hệ Thống: Kịch Bản Toàn Trình (E2E Pipeline) & Lưu Trữ Dữ Liệu Thật Vào CSDL

- **Ngày tạo:** 2026-10-06
- **Trạng thái:** DRAFT (Chờ phê duyệt)
- **Tác giả:** AI Pairing Agent & Human Partner
- **Mục tiêu:** Xây dựng luồng thực thi toàn trình (End-to-End) từ thu thập dữ liệu cào đối thủ, đối soát so khớp SKU, trích xuất tín hiệu thị trường, kích hoạt ma trận gợi ý giá, lưu trữ thực tế vào cơ sở dữ liệu SQLite và hiển thị trực tiếp lên giao diện Frontend.

---

## 1. Bối Cảnh & Vấn Đề (Context & Problem Statement)

### 1.1. Hiện trạng
- Hệ thống đã có đầy đủ cấu trúc bảng (SQLAlchemy models) cho 14 thực thể trong `backend/app/models/`.
- Bảng `crawl_results` trong SQLite (`backend/dynamic_pricing.db`) đã chứa 5,616 bản ghi cào giá từ CellphoneS và Hoàng Hà Mobile.
- Tuy nhiên, các bảng cốt lõi phục vụ vận hành như `products`, `inventory_mock`, `sku_mappings`, `price_recommendations`, `pricing_audit_logs` hiện đang có **0 bản ghi**.
- Toàn bộ dữ liệu thực nghiệm chuẩn vẫn đang nằm rải rác ở các tệp Excel tĩnh trong thư mục `backend/data/` (`dim_product.xlsx`, `inventory_snapshot_20260723.xlsx`, `demand_events_20260723.xlsx`, `crawl_and_sku_mapping_output.xlsx`).
- Frontend hiện đang phải dựa vào cơ chế fallback sang dữ liệu mẫu (`mockData.ts`).

### 1.2. Yêu cầu nghiệp vụ
1. **Lưu trữ dữ liệu thật (Real Persistence):** Nạp toàn bộ danh mục 329 sản phẩm FPT, 1,000 dòng tồn kho ERP, 1,500 sự kiện clickstream vào các bảng SQLite thật.
2. **Kịch bản kiểm thử toàn trình (E2E Test Scenario):** Thiết lập một chu trình khép kín tự động thực thi và kiểm thử từng mắt xích:
   - **Mắt xích 1:** Dữ liệu cào đối thủ (`crawl_results`).
   - **Mắt xích 2:** Ghép cặp và đối soát SKU (`sku_mappings`) bằng thuật toán 2 tầng (Part-Number Regex + Normalized Fuzzy).
   - **Mắt xích 3:** Trích xuất tín hiệu $D, I, C$ và tính Composite Score theo trọng số ngành hàng.
   - **Mắt xích 4:** Sinh gợi ý giá từ Ma trận 9 kịch bản, kiểm soát rào cản Margin Floor và Rate-of-Change Cap ($\pm 10\%$).
   - **Mắt xích 5:** Ghi nhận đề xuất vào bảng `price_recommendations` (`PENDING`).
   - **Mắt xích 6:** Mô phỏng chuyên viên giá phê duyệt đề xuất, lưu vết kiểm toán vào `pricing_audit_logs` và ghi lịch sử vào `price_history`.
3. **Cung cấp dữ liệu thật cho Giao diện:** Bổ sung các API endpoints kết nối DB để Frontend hiển thị dữ liệu trực tiếp từ CSDL.

---

## 2. Kiến Trúc Luồng Dữ Liệu Toàn Trình (Architecture & Data Flow)

```mermaid
flowchart TD
    subgraph S1 [Giai đoạn 1: Khởi tạo Danh mục & Tồn kho FPT]
        X1[dim_product.xlsx<br/>329 SKU] --> P_SEED[Trích xuất FeatureExtractor & Nạp DB]
        X2[inventory_snapshot.xlsx<br/>1000 bản ghi] --> I_SEED[Nạp Warehouses & Inventory]
        X3[demand_events.xlsx<br/>1500 sự kiện] --> D_SEED[Nạp DemandEvents]
        
        P_SEED --> DB_PROD[(Bảng: products)]
        I_SEED --> DB_WH[(Bảng: warehouses)]
        I_SEED --> DB_INV[(Bảng: inventory_mock<br/>& inventory_snapshots)]
        D_SEED --> DB_DEM[(Bảng: demand_events)]
    end

    subgraph S2 [Giai đoạn 2: Ghép Cặp SKU Hai Tầng]
        DB_CRAWL[(Bảng: crawl_results<br/>5,616 sản phẩm đối thủ)] --> MATCHER[SkuMatcher Engine]
        DB_PROD --> MATCHER
        MATCHER -->|Tier 1: Regex Part-Number| T1[Exact Match: Confidence 100%]
        MATCHER -->|Tier 2: Normalized Specs| T2[Fuzzy Match: Confidence 80-95%]
        T1 --> DB_MAP[(Bảng: sku_mappings<br/>status: APPROVED)]
        T2 --> DB_MAP
    end

    subgraph S3 [Giai đoạn 3: Động Cơ Gợi Ý Định Giá]
        DB_DEM --> SIG[SignalsExtractor]
        DB_INV --> SIG
        DB_MAP --> SIG
        DB_CRAWL --> SIG
        
        SIG -->|D, I, C| MATRIX[ScenarioMatrix & Composite Calculation]
        MATRIX --> GUARDS[SafetyGuardrails<br/>Floor Price & Rate Cap]
        GUARDS --> DB_REC[(Bảng: price_recommendations<br/>status: PENDING)]
    end

    subgraph S4 [Giai đoạn 4: Phê Duyệt & Kiểm Toán]
        DB_REC --> ACTION[API: /recommendations/{id}/action]
        ACTION -->|Phê duyệt| DB_AUDIT[(Bảng: pricing_audit_logs)]
        ACTION -->|Cập nhật| DB_HIST[(Bảng: price_history)]
    end

    subgraph S5 [Giai đoạn 5: Hiển Thị Giao Diện Người Dùng]
        DB_PROD & DB_MAP & DB_CRAWL --> API_MAT[GET /api/v1/pricing/matrix]
        DB_REC --> API_REC[GET /api/v1/pricing/recommendations]
        DB_HIST --> API_HIST[GET /api/v1/pricing/history]
        
        API_MAT --> UI_MAT[Trang: Price Comparison Matrix]
        API_REC --> UI_APP[Trang: Pricing Approvals]
        API_HIST --> UI_HIST[Modal: Lịch sử giá & Biểu đồ]
    end
```

---

## 3. Đặc Tả Chi Tiết Từng Module (Component Specifications)

### 3.1. Module Nạp Dữ Liệu & Đối Soát SKU (`backend/scripts/run_e2e_pipeline.py`)

#### Bước 1: Nạp Danh mục Sản phẩm FPT (`products`)
- Đọc 329 SKU từ `backend/data/dim_product.xlsx` và giá tham chiếu từ `backend/data/crawl_and_sku_mapping_output.xlsx`.
- Dùng `FeatureExtractor` bóc tách tự động:
  - `brand`: Apple, Asus, Acer, Dell, HP, Lenovo, Samsung, Xiaomi...
  - `category`: PHONE hoặc LAPTOP.
  - `part_number`: Mã Part hãng (vd: A715-59G-57TU, 83JC00LVVN...).
  - `specs`: RAM, ROM, CPU tóm tắt.
- Tính toán giá tài chính chuẩn:
  - `base_retail_price`: Giá niêm yết bán lẻ gốc (lấy từ cột giá tham chiếu FPT).
  - `cost_price`: $85\%$ của `base_retail_price`.
  - `min_margin_pct`: $5.0\%$.
  - `floor_price`: $\text{cost\_price} \times 1.05$.
- Lưu toàn bộ 329 bản ghi vào bảng `products`.

#### Bước 2: Nạp Kho Hàng & Tồn Kho (`warehouses`, `inventory_mock`, `inventory_snapshots`)
- Khởi tạo 3 kho trung tâm: `WH-HN-01` (Miền Bắc), `WH-HCM-01` (Miền Nam), `WH-DN-01` (Miền Trung).
- Đọc 1,000 dòng từ `inventory_snapshot_20260723.xlsx`:
  - Khớp `sku_id` với `fpt_product_id`.
  - Lưu chi tiết vào bảng `inventory_snapshots`.
  - Tính tổng hợp cho bảng `inventory_mock`: `stock_quantity`, `doh` (Days On Hand trung bình), `cost_price`, `floor_price`.

#### Bước 3: Nạp Sự Kiện Clickstream (`demand_events`)
- Đọc 1,500 sự kiện từ `demand_events_20260723.xlsx`:
  - Map `sku_id` sang `fpt_product_id`.
  - Lưu vào bảng `demand_events` phục vụ tính toán CVR, tỷ lệ thoát (bounce rate), số lượt thêm giỏ hàng.

#### Bước 4: So Khớp SKU Đối Thủ (`sku_mappings`)
- Duyệt qua 5,616 sản phẩm cào đối thủ đã có trong bảng `crawl_results`.
- Dùng `SkuMatcher` so khớp với 329 sản phẩm FPT:
  - Nếu khớp chính xác Part-Number (Tier 1): Gắn `match_type = 'EXACT_PART_NUMBER'`, `confidence_score = 1.0`, `status = 'APPROVED'`.
  - Nếu khớp cấu hình chuẩn hóa (Tier 2): Gắn `match_type = 'NORMALIZED_ATTRIBUTE'`, `confidence_score = 0.85 - 0.95`, `status = 'APPROVED'`.
  - Nếu điểm tin cậy $60-79\%$: Gắn `match_type = 'NORMALIZED_ATTRIBUTE'`, `status = 'PENDING'` (đưa vào hàng đợi duyệt thủ công PBI-008).
- Lưu kết quả vào bảng `sku_mappings`.

#### Bước 5: Kích Hoạt Pricing Engine & Sinh Đề Xuất Giá Thật
- Gọi `PricingEngine.generate_batch(db)`:
  - `SignalsExtractor` tính Demand Score ($D$), Inventory Score ($I$), Competitor Score ($C$).
  - `ScenarioMatrix` tính Composite Score $D \times 0.40 + I \times 0.35 + C \times 0.25$.
  - Nhận diện 9 kịch bản hoặc 7 dải Composite.
  - `SafetyGuardrails` áp dụng trần hãm sốc $\pm 10\%$ và bảo vệ giá sàn Margin Floor.
  - Lưu toàn bộ các bản ghi đề xuất vào bảng `price_recommendations` với trạng thái `PENDING`.

#### Bước 6: Mô Phỏng Phê Duyệt Giá & Ghi Vết Kiểm Toán
- Lấy một số đề xuất đại diện (ví dụ 5 sản phẩm đầu tiên) và gọi hàm xử lý hành động:
  - Cập nhật trạng thái thành `APPROVED` hoặc `REJECTED`.
  - Lưu bản ghi vết kiểm toán vào bảng `pricing_audit_logs`.
  - Ghi bản ghi biến động giá vào bảng `price_history`.

---

### 3.2. Cập Nhật API Endpoints Phục Vụ Frontend (`backend/app/api/v1/endpoints/pricing.py`)

1. **`GET /api/v1/pricing/matrix`:**
   - Truy vấn danh sách sản phẩm chuẩn FPT (`products`), kèm giá đối thủ thấp nhất từ `sku_mappings` $\rightarrow$ `crawl_results` (CellphoneS & Hoàng Hà), và tồn kho từ `inventory_mock`.
   - Trả về cấu trúc `PriceComparisonItem[]` để trang **Price Matrix** trên Frontend tải trực tiếp từ DB.
2. **`GET /api/v1/pricing/history`:**
   - Truy vấn bảng `price_history` kết hợp `pricing_audit_logs`.
   - Trả về cấu trúc `PriceChangeHistoryItem[]` cho tab Lịch sử duyệt giá.
3. **`GET /api/v1/matching/queue` (trong `backend/app/api/v1/endpoints/matching.py` hoặc router pricing):**
   - Trả về danh sách SKU Mapping ở trạng thái `PENDING` (độ tin cậy $60-79\%$) cho trang **SKU Mapping Queue**.

---

## 4. Kế Hoạch Kiểm Thử Tự Động (Automated Testing Strategy)

Tạo file kiểm thử mới: [`backend/tests/test_e2e_pricing_pipeline.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/tests/test_e2e_pricing_pipeline.py):
1. **`test_e2e_product_seeding`:** Kiểm tra 329 sản phẩm FPT được nạp đầy đủ thuộc tính và giá sàn/giá vốn hợp lệ.
2. **`test_e2e_inventory_and_demand_seeding`:** Kiểm tra tồn kho, DOH và sự kiện clickstream được liên kết đúng `fpt_product_id`.
3. **`test_e2e_sku_matching`:** Kiểm tra các cặp SKU đối thủ được ánh xạ đúng về mã FPT và lưu vào `sku_mappings`.
4. **`test_e2e_pricing_recommendation_generation`:** Kiểm tra `generate_batch()` sinh đề xuất giá thực tế lưu vào bảng `price_recommendations`, tính đúng Composite Score và rào cản an toàn.
5. **`test_e2e_approval_and_audit_log`:** Kiểm tra thao tác phê duyệt cập nhật đúng `status = 'APPROVED'` và tạo bản ghi tương ứng trong `pricing_audit_logs` và `price_history`.
6. **`test_e2e_api_matrix_response`:** Kiểm tra endpoint `GET /api/v1/pricing/matrix` trả về dữ liệu 3 bên hợp lệ từ cơ sở dữ liệu.

---

## 5. Tiêu Chuẩn Nghiệm Thu (Acceptance Criteria)

- [ ] Toàn bộ 329 sản phẩm FPT được lưu trữ thành công trong bảng `products`.
- [ ] Bảng `inventory_mock` và `inventory_snapshots` có đầy đủ dữ liệu tồn kho và DOH.
- [ ] Bảng `sku_mappings` có ít nhất 200+ liên kết giữa sản phẩm FPT và dữ liệu cào đối thủ.
- [ ] Bảng `price_recommendations` có dữ liệu đề xuất giá thật cho các sản phẩm active.
- [ ] Bảng `pricing_audit_logs` ghi vết đầy đủ các thao tác kiểm toán giá.
- [ ] Tất cả các test tự động trong `backend/tests/test_e2e_pricing_pipeline.py` vượt qua $100\%$.
- [ ] Frontend tải dữ liệu thật từ SQLite khi mở trang Price Matrix và Pricing Approvals mà không bị fallback về mock.
