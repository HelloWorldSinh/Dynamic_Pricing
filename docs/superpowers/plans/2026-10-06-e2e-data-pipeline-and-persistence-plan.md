# Kế Hoạch Triển Khai: Kịch Bản Toàn Trình (E2E Pipeline) & Lưu Trữ Dữ Liệu Thật Vào CSDL

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nạp toàn bộ dữ liệu thực nghiệm vào cơ sở dữ liệu SQLite (`backend/dynamic_pricing.db`), xây dựng kịch bản kiểm thử toàn trình từ Cào dữ liệu $\rightarrow$ So khớp SKU $\rightarrow$ Động cơ định giá $\rightarrow$ Phê duyệt kiểm toán, và kết nối API để Frontend hiển thị dữ liệu thật 100%.

**Architecture:** Sử dụng kiến trúc phân tầng Clean Architecture, SQLAlchemy ORM, Service Layer (`SkuMatcher`, `PricingEngine`, `SignalsExtractor`, `SafetyGuardrails`), và RESTful API endpoints trong FastAPI.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.x, SQLite, pandas, openpyxl, pytest, React 18, TypeScript, TailwindCSS.

**Spec:** `docs/superpowers/specs/2026-10-06-e2e-data-pipeline-and-persistence-design.md`

---

## Danh Mục Tệp Tin (File Structure)

- **Tạo mới:**
  - `backend/scripts/seed_database.py`: Module nạp dữ liệu danh mục FPT, kho hàng, tồn kho và sự kiện clickstream vào SQLite.
  - `backend/scripts/run_e2e_pipeline.py`: Script chạy kịch bản toàn trình E2E (Seed $\rightarrow$ Matching $\rightarrow$ Pricing $\rightarrow$ Approval $\rightarrow$ Report).
  - `backend/tests/test_database_seeding.py`: Test kiểm thử tính chính xác khi nạp dữ liệu từ các file Excel vào DB.
  - `backend/tests/test_e2e_pricing_pipeline.py`: Test tự động kiểm thử toàn trình 5 giai đoạn luồng dữ liệu.
- **Chỉnh sửa:**
  - `backend/app/api/v1/endpoints/pricing.py`: Bổ sung endpoint `GET /pricing/matrix` và `GET /pricing/history` truy vấn trực tiếp từ CSDL.
  - `backend/app/schemas/pricing.py`: Bổ sung schemas nếu cần cho matrix query.

---

## Chi Tiết Các Tác Vụ (Tasks)

### Task 1: Module Nạp Dữ Liệu Chuẩn Vào CSDL (Database Seeder)

**Files:**
- Create: `backend/tests/test_database_seeding.py`
- Create: `backend/scripts/seed_database.py`

**Mô tả:**
- Đọc 329 SKU từ `dim_product.xlsx` và giá tham chiếu từ `crawl_and_sku_mapping_output.xlsx`.
- Dùng `FeatureExtractor` bóc tách `brand`, `category`, `part_number`, `specs`.
- Tính `cost_price` ($85\%$ giá bán), `floor_price` ($\text{cost\_price} \times 1.05$) và lưu vào bảng `products`.
- Tạo 3 bản ghi `warehouses` (`WH-HN-01`, `WH-HCM-01`, `WH-DN-01`).
- Đọc `inventory_snapshot_20260723.xlsx` (1,000 dòng) và nạp vào `inventory_snapshots` cùng tổng hợp vào `inventory_mock`.
- Đọc `demand_events_20260723.xlsx` (1,500 dòng) và nạp vào `demand_events`.

- [ ] **Step 1: Viết test failing `test_database_seeding.py`**
- [ ] **Step 2: Chạy test để xác nhận RED**
- [ ] **Step 3: Triển khai hàm `seed_catalog_and_inventory(db)` trong `backend/scripts/seed_database.py`**
- [ ] **Step 4: Chạy lại test để xác nhận GREEN**

---

### Task 2: So Khớp SKU Đối Thủ & Lưu Trữ Bảng `sku_mappings`

**Files:**
- Test: `backend/tests/test_sku_matching_persistence.py`
- Create/Extend: hàm `run_sku_matching_and_persist(db)` trong `backend/scripts/run_e2e_pipeline.py`

**Mô tả:**
- Đọc 5,616 sản phẩm cào đối thủ đã có trong bảng `crawl_results` (CellphoneS & Hoàng Hà).
- Gọi `SkuMatcher` để thực hiện so khớp 2 tầng với 329 sản phẩm FPT vừa nạp trong bảng `products`.
- Lưu các cặp ghép hợp lệ vào bảng `sku_mappings` (tỷ lệ tin cậy $\ge 80\%$ gắn `APPROVED`, $60-79\%$ gắn `PENDING`).

- [ ] **Step 1: Viết test failing `test_sku_matching_persistence.py`**
- [ ] **Step 2: Chạy test để xác nhận RED**
- [ ] **Step 3: Triển khai hàm `run_sku_matching_and_persist(db)`**
- [ ] **Step 4: Chạy lại test để xác nhận GREEN**

---

### Task 3: Kích Hoạt Động Cơ Định Giá & Lưu Trữ Đề Xuất Giá Thật

**Files:**
- Test: `backend/tests/test_e2e_pricing_pipeline.py`
- Extend: hàm `run_pricing_recommendations_batch(db)` trong `backend/scripts/run_e2e_pipeline.py`

**Mô tả:**
- Gọi `PricingEngine.generate_batch(db)`.
- Xác nhận các điểm tín hiệu $D, I, C$, Composite Score, nhận diện kịch bản và rào cản an toàn (Rate Cap, Floor Cap) được tính toán chính xác và lưu vào bảng `price_recommendations`.
- Thực hiện phê duyệt thử nghiệm một số đề xuất, lưu vết kiểm toán vào `pricing_audit_logs` và lịch sử vào `price_history`.

- [ ] **Step 1: Viết test failing kiểm thử toàn trình E2E**
- [ ] **Step 2: Chạy test để xác nhận RED**
- [ ] **Step 3: Triển khai hàm thực thi toàn trình trong `run_e2e_pipeline.py`**
- [ ] **Step 4: Chạy lại test để xác nhận GREEN**

---

### Task 4: Bổ Sung API Endpoint `GET /pricing/matrix` & `GET /pricing/history`

**Files:**
- Test: `backend/tests/test_pricing_api.py` (bổ sung test case)
- Edit: `backend/app/api/v1/endpoints/pricing.py`

**Mô tả:**
- Thêm route `GET /pricing/matrix`: Truy vấn danh mục sản phẩm FPT từ `products` kết hợp `sku_mappings`, `crawl_results`, và `inventory_mock` để trả về danh sách đối soát giá 3 bên thực tế `PriceComparisonItem[]`.
- Thêm route `GET /pricing/history`: Trả về lịch sử thay đổi giá từ `price_history` / `pricing_audit_logs`.

- [ ] **Step 1: Viết test cho endpoint `GET /pricing/matrix`**
- [ ] **Step 2: Chạy test để xác nhận RED**
- [ ] **Step 3: Triển khai endpoint `GET /pricing/matrix` và `GET /pricing/history`**
- [ ] **Step 4: Chạy lại test để xác nhận GREEN**

---

### Task 5: Thực Thi Kịch Bản Toàn Trình Trên SQLite Thật & Nghiệm Thu UI

**Files:**
- Execute: `python backend/scripts/run_e2e_pipeline.py`
- Verify DB: `backend/dynamic_pricing.db`
- Verify Frontend: `npm run build`

**Mô tả:**
- Chạy script nạp và sinh giá trực tiếp trên database `backend/dynamic_pricing.db`.
- Xác nhận số lượng bản ghi thực tế của từng bảng:
  - `products`: 329 dòng
  - `inventory_mock`: 329 dòng
  - `sku_mappings`: 200+ dòng
  - `price_recommendations`: 329 dòng
  - `pricing_audit_logs`: > 0 dòng
- Chạy `npm run build` kiểm tra frontend không lỗi.
- Kiểm tra kết nối API hiển thị đầy đủ dữ liệu thật.

- [ ] **Step 1: Chạy `python backend/scripts/run_e2e_pipeline.py` trên SQLite**
- [ ] **Step 2: Kiểm tra số lượng bản ghi từng bảng**
- [ ] **Step 3: Chạy toàn bộ test suite `pytest backend/tests/`**
- [ ] **Step 4: Chạy `npm run build` xác nhận Frontend hoàn toàn sẵn sàng**
