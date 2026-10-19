Dưới đây là **Bảng Checklist Toàn diện (Master Verification Checklist)** bao phủ cả 3 trụ cột cốt lõi của hệ thống: **Cào dữ liệu (Crawling)**, **So khớp SKU (Matching)** và **Gợi ý giá (Dynamic Pricing)**. 

Mỗi mục kiểm tra được thiết kế theo cấu trúc chuẩn 4 phần (**Tính năng → Kiến trúc & File phụ trách → Cấu trúc CSDL → Luồng hoạt động & Tiêu chí nghiệm thu**) giúp người kiểm tra nắm bắt ngay bức tranh kỹ thuật mà không cần đọc lại toàn bộ code.

---

```
                       SƠ ĐỒ TỔNG THỂ HỆ THỐNG DYNAMIC PRICING
 ┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐
 │   1. DATA CRAWLING   │  ───►  │   2. SKU MATCHING    │  ───►  │  3. DYNAMIC PRICING  │
 │  CellphoneS, Hoàng Hà│        │  Two-Tiered Engine   │        │   3-Layer Reasoning  │
 │   & FPT Catalog      │        │  FPT Master Loop     │        │   Composite D/I/C    │
 └──────────┬───────────┘        └──────────┬───────────┘        └──────────┬───────────┘
            │                               │                               │
            ▼                               ▼                               ▼
     [crawl_results]                 [sku_mappings]             [price_recommendations]
```

---

# PHẦN 1: THU THẬP DỮ LIỆU ĐỐI THỦ (DATA CRAWLING)

### [ ] 1.1. Cơ chế cào đa nguồn theo Strategy Pattern (CellphoneS & Hoàng Hà Mobile)
* **🎯 Tính năng:** Trích xuất tự động danh mục Phone và Laptop từ 2 đối thủ cạnh tranh chính; trích xuất tên sản phẩm, giá bán hiện tại, giá niêm yết, tình trạng tồn kho (`is_in_stock`) và cấu hình thô.
* **🏛️ Kiến trúc & File phụ trách:**
  * Pattern: **Strategy Pattern** với `ScraperFactory`.
  * Gốc: [backend/app/services/scrapers/base.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/scrapers/base.py) (`BaseScraper`).
  * Thực thi CellphoneS: [cellphones.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/scrapers/cellphones.py) (Gọi GraphQL API, phân trang, trích xuất biến thể màu sắc).
  * Thực thi Hoàng Hà Mobile: [hoangha.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/scrapers/hoangha.py) (Gọi REST/HTML, xử lý quy chuẩn giá).
  * Bộ điều phối: [crawler_service.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/crawler_service.py) (`CrawlerService`).
* **🗄️ Cấu trúc CSDL:**
  * Bảng `crawl_jobs`: Lưu phiên cào (`id`, `trigger_type` = `SCHEDULED`|`ON_DEMAND`, `source`, `category`, `status` = `PENDING`|`RUNNING`|`COMPLETED`|`FAILED`, `total_items`, `success_items`).
  * Bảng `crawl_results`: Lưu dữ liệu cào thô (`id`, `job_id`, `source` = `CELLPHONES`|`HOANGHA`, `url`, `raw_name`, `current_price`, `original_price`, `is_in_stock`, `stock_status_text`, `raw_specs`).
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  1. API endpoint `/api/v1/crawler/trigger` hoặc `/trigger-full-pipeline` tạo 1 record `crawl_jobs` trạng thái `RUNNING`.
  2. Scraper thực hiện HTTP request (httpx), parse dữ liệu, lọc bỏ sản phẩm rác hoặc giá 0đ.
  3. Dữ liệu được bulk-insert vào `crawl_results`. Job chuyển sang `COMPLETED`.
  4. **Tiêu chí pass:** Sau khi chạy, bảng `crawl_results` có dữ liệu mới; các sản phẩm hết hàng phải có `is_in_stock = False`.

---

### [ ] 1.2. Cơ chế Debounce Trigger & Quản lý tác vụ chạy ngầm
* **🎯 Tính năng:** Tránh tình trạng spam nút cào dữ liệu từ người dùng web; quản lý tiến trình không chặn (non-blocking) qua FastAPI BackgroundTasks.
* **🏛️ Kiến trúc & File phụ trách:**
  * Backend API: [backend/app/api/v1/crawler.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/api/v1/crawler.py) (Background execution).
  * Frontend: [DebounceTriggerBar.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/matrix/DebounceTriggerBar.tsx) (Countdown 30s debounce protection, hiển thị trạng thái `isCrawling`).
* **🗄️ Cấu trúc CSDL:** `crawl_jobs.status`, `crawl_jobs.started_at`, `crawl_jobs.finished_at`.
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  1. Người dùng bấm **Cào & Đối soát SKU** trên UI. Nút chuyển sang trạng thái loading xoay tròn và countdown 30 giây khóa nút.
  2. Server phản hồi HTTP `202 Accepted` ngay lập tức, job tiếp tục chạy dưới nền.
  3. **Tiêu chí pass:** Không bị lỗi 504 Gateway Timeout khi cào khối lượng lớn; spam click không tạo ra nhiều job trùng lặp.

---

# PHẦN 2: ĐỐI SOÁT & SO KHỚP SKU (SKU MATCHING ENGINE)

```
                            QUY TRÌNH MATCHING 2 TẦNG (TWO-TIERED)
  Crawled Product Name
          │
          ├──► [Tier 1: Regex Exact Part-Number] ──(Trùng mã hãng)──► Score = 1.0 (APPROVED)
          │
          └──► [Tier 2: Attribute Hard Filters]
                     ├── Khác Brand?          ──► Bỏ qua (UNMATCHED)
                     ├── Khác Model ID?       ──► Bỏ qua (UNMATCHED)
                     ├── Lệch RAM / ROM?      ──► Bỏ qua (UNMATCHED)
                     └── Lệch màu sắc?        ──► Bỏ qua (UNMATCHED)
                     └── Thỏa mãn tất cả      ──► SequenceMatcher + Bonus
                                                      ├── Score >= 0.85 ──► APPROVED
                                                      ├── 0.75 <= S < 0.85 ──► PENDING (Duyệt tay)
                                                      └── S < 0.75 ──────► UNMATCHED
```

### [ ] 2.1. Trích xuất đặc trưng có cấu trúc (Feature Extraction)
* **🎯 Tính năng:** Chuẩn hóa chuỗi tên sản phẩm phức tạp thành các thuộc tính kỹ thuật hạt nhân: Part-Number hãng (Model Code), Brand, Model Identifier, RAM, ROM/SSD, Màu sắc.
* **🏛️ Kiến trúc & File phụ trách:**
  * Module: [feature_extractor.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/matching/feature_extractor.py) (`FeatureExtractor`).
  * Models DTO: [models.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/matching/models.py) (`SkuFeatures`).
* **🗄️ Cấu trúc CSDL:** Bảng `products` (Catalog FPT) chứa các cột: `sku`, `name`, `part_number`, `specs` (JSON: ram, storage, color, model_id).
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  1. Nhận tên thô từ FPT Catalog và Crawl Result.
  2. Chạy Regex bóc tách Part-Number (VD: `83JC00LVVN`, `MYGW3ZA/A`).
  3. Bóc tách Model Identifier chuẩn hóa (VD: `iphone_16_pro_max`, `galaxy_s24_ultra`, `ideapad_slim_5`).
  4. Trích xuất RAM (`8gb`, `16gb`), ROM (`128gb`, `512gb`, `1tb`) và Màu sắc (`titan sa mạc`, `đen`, `xám`).
  5. **Tiêu chí pass:** Tên iPhone 15 Pro Max 256GB Titan Tự Nhiên phải trích xuất đúng: Brand=`apple`, Model ID=`iphone_15_pro_max`, ROM=`256gb`, Color=`titan tự nhiên`.

---

### [ ] 2.2. Thuật toán So khớp Phân tầng (Two-Tiered Matching Engine)
* **🎯 Tính năng:** Đảm bảo độ chính xác (Precision > 95%), tuyệt đối không ghép sai cấu hình phần cứng (không ghép bản 128GB với 256GB).
* **🏛️ Kiến trúc & File phụ trách:**
  * Engine: [matching_engine.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/matching/matching_engine.py) (`MatchingEngine`).
  * Index: [sku_index.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/matching/sku_index.py) (Brand Bucketing để tìm kiếm O(1)).
* **🗄️ Cấu trúc CSDL:**
  * Bảng `sku_mappings`: Lưu liên kết giữa sản phẩm FPT và đối thủ (`id`, `fpt_product_id` -> FK `products.id`, `competitor_crawl_id` -> FK `crawl_results.id`, `match_type`, `confidence_score`, `status`, `matched_at`).
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  * **Tầng 1 (Exact Regex):** Nếu Part-Number trùng khớp 100% → gán `match_type = EXACT_PART_NUMBER`, `confidence_score = 1.0`, `status = APPROVED`.
  * **Tầng 2 (Normalized Attributes + Fuzzy):**
    * Áp dụng **Rào cản cứng (Hard Filters):** Khác Brand, khác Model ID, lệch RAM, lệch ROM hoặc lệch Màu sắc sẽ bị loại bỏ ngay lập tức (Score = 0.0, UNMATCHED).
    * Áp dụng độ tương đồng chuỗi `SequenceMatcher` + điểm thưởng khớp RAM/ROM/Model.
    * Ngưỡng phân loại:
      * $\ge 0.85$ → `status = APPROVED` (Tự động duyệt).
      * $0.75 \le \text{Score} < 0.85$ → `status = PENDING` (Chuyển sang hàng đợi cho nhân viên kiểm tra).
      * $< 0.75$ → `UNMATCHED`.
  * **Tiêu chí pass:** Chạy bộ test [test_matching_modules.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/tests/test_matching_modules.py) đạt 100% pass (không có false positives giữa các biến thể dung lượng).

---

### [ ] 2.3. Quy trình FPT Master Loop & Lưu trữ đối soát (Persistence)
* **🎯 Tính năng:** Lấy 329 sản phẩm FPT Shop chuẩn làm trung tâm (Master List), gom nhóm crawl results đối thủ và chọn ra đúng **1 Best Match** cho mỗi nguồn đối thủ (`CELLPHONES`, `HOANGHA`).
* **🏛️ Kiến trúc & File phụ trách:**
  * [matching_persistence.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/matching_persistence.py) (`run_sku_matching_and_persist`).
* **🗄️ Cấu trúc CSDL:** `sku_mappings` liên kết 1-n giữa `products` và `crawl_results`.
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  1. Duyệt qua từng sản phẩm FPT chuẩn.
  2. Lọc các record cào cùng Brand từ Hoàng Hà và CellphoneS.
  3. Chọn bản ghi có `status = APPROVED` với `confidence_score` cao nhất cho mỗi đối thủ.
  4. Lưu vào bảng `sku_mappings`.
  5. **Tiêu chí pass:** Mỗi sản phẩm FPT chỉ có tối đa 1 mapping CellphoneS và 1 mapping Hoàng Hà Mobile ở trạng thái hợp lệ.

---

# PHẦN 3: ĐỘNG CƠ ĐỊNH GIÁ ĐỘNG (DYNAMIC PRICING & RECOMMENDATION)

```
                            LUỒNG 3 TẦNG ĐỊNH GIÁ (3-LAYER REASONING)
  Tín hiệu D / I / C
  ├── Demand Score (D)      [ -2.0 đến +2.0 ]
  ├── Inventory Score (I)   [ -2.0 đến +2.0 ]
  └── Competitor Score (C)  [ -2.0 đến +2.0 ]
          │
          ▼
  Composite Score = 0.4*D + 0.35*I + 0.25*C
          │
          ▼
  [Layer 2: Scenario Matrix] ──► Khớp 1 trong 9 Kịch bản (Clearance, Strong Raise, Under-cut...)
          │
          ▼
  [Layer 3: Safety Guardrails]
          ├── BẢO VỆ GIÁ SÀN: Price >= cost_price * (1 + min_margin_pct)  [Nếu phạm -> Capped]
          └── BẢO VỆ BIẾN ĐỘNG: -15% <= delta_pct <= +15%
          │
          ▼
  Lưu kết quả: [price_recommendations] (status: PENDING)
```

### [ ] 3.1. Xử lý & Chuẩn hóa 3 Trụ cột Tín hiệu (D - I - C Signals)
* **🎯 Tính năng:** Thu thập và chuẩn hóa dữ liệu kinh doanh đa chiều thành thang điểm chuẩn từ `-2.0` (rất yếu / bất lợi) đến `+2.0` (rất mạnh / thuận lợi).
* **🏛️ Kiến trúc & File phụ trách:**
  * Module: [backend/app/services/pricing/signals.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/pricing/signals.py).
* **🗄️ Cấu trúc CSDL:**
  * **Nhu cầu (Demand):** Bảng `demand_events`, `demand_hourly_aggregates` (views, thêm vào giỏ, lượt mua).
  * **Tồn kho (Inventory):** Bảng `inventory_mock`, `inventory_snapshots` (số lượng tồn kho, Days of Inventory - DOI).
  * **Đối thủ (Competitor):** Bảng `sku_mappings` kết nối sang `crawl_results` (lọc các sản phẩm `is_in_stock = True`).
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  1. **Demand Signal (D):** Doanh số cao / lượt xem tăng vọt $\rightarrow D > 0$; nhu cầu thấp / ế ẩm $\rightarrow D < 0$.
  2. **Inventory Signal (I):** Tồn kho báo động đỏ (DOI > 90 ngày) $\rightarrow I < 0$ (áp lực phải xả hàng); cháy hàng $\rightarrow I > 0$.
  3. **Competitor Signal (C):** Lấy giá thấp nhất còn hàng của đối thủ (`competitor_min_price`). FPT đắt hơn đối thủ $\rightarrow C < 0$; FPT rẻ hơn $\rightarrow C > 0$.
  4. **Tính Composite Score:**
     $$\text{Composite Score} = 0.4 \times D + 0.35 \times I + 0.25 \times C$$
  5. **Tiêu chí pass:** Nếu đối thủ hết hàng (`is_in_stock = False`), thuật toán bỏ qua và không dùng giá đó để làm căn cứ cạnh tranh.

---

### [ ] 3.2. Ma trận 9 Kịch bản Nghiệp vụ & Khuyến nghị Giá (Scenario Matrix)
* **🎯 Tính năng:** Tự động xếp loại sản phẩm vào 1 trong 9 kịch bản kinh doanh và tính toán mức giá đề xuất tối ưu.
* **🏛️ Kiến trúc & File phụ trách:**
  * Module: [backend/app/services/pricing/matrix.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/pricing/matrix.py) & [engine.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/pricing/engine.py).
* **🗄️ Cấu trúc CSDL:**
  * Bảng `price_recommendations`:
    * `current_fpt_price`, `competitor_min_price`, `recommended_price`.
    * `price_delta_amount` (VND), `price_delta_pct` (%).
    * `demand_score`, `inventory_score`, `competitor_score`, `composite_score`.
    * `scenario_name` (Clearance, Strong Raise, Match Competitor, Under-cut, Hold Price...).
    * `reasoning_3layers` (JSON: giải trình lý do tính giá dựa trên đối thủ, tồn kho và giá sàn).
    * `status` = `PENDING` | `APPROVED` | `REJECTED`.
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  1. Engine nhận thông tin từ bảng `products` và các mapping hợp lệ.
  2. Tra cứu Composite Score và ma trận D/I/C để kích hoạt kịch bản tương ứng:
     * *Ví dụ (Kịch bản Xả hàng - Clearance):* Tồn kho cao ($I < -1.0$) + Cầu thấp ($D < 0$) + Đối thủ rẻ hơn ($C < 0$) $\rightarrow$ Giảm giá mạnh xả hàng tồn kho.
     * *Ví dụ (Kịch bản Tăng biên lợi nhuận - Strong Raise):* Cầu cao ($D > 1.0$) + Tồn kho ít ($I > 1.0$) $\rightarrow$ Tăng giá để tối đa hóa lợi nhuận.
  3. **Tiêu chí pass:** Mọi đề xuất sinh ra đều có `reasoning_3layers` đầy đủ, giải thích minh bạch vì sao tăng/giảm giá.

---

### [ ] 3.3. Rào chắn An toàn (Safety Guardrails) & Chặn lỗ
* **🎯 Tính năng:** Đảm bảo hệ thống AI không bao giờ đưa ra mức giá gây lỗ vốn hoặc gây sốc giá trên thị trường.
* **🏛️ Kiến trúc & File phụ trách:**
  * Module: [backend/app/services/pricing/guardrails.py](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/backend/app/services/pricing/guardrails.py).
* **🗄️ Cấu trúc CSDL:**
  * Bảng `products`: `cost_price` (giá vốn), `min_margin_pct` (biên lợi nhuận tối thiểu, mặc định 5%), `floor_price` (giá sàn).
  * Bảng `price_recommendations`: Cột cờ cảnh báo `is_floor_capped` (Boolean).
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  1. **Kiểm tra Giá sàn (Floor Protection):**
     $$\text{Floor Price} = \text{cost\_price} \times (1 + \text{min\_margin\_pct})$$
     Nếu giá đề xuất của kịch bản $< \text{Floor Price}$, hệ thống **tự động cắt về đúng Giá sàn** và đánh dấu `is_floor_capped = True`.
  2. **Kiểm tra Biên độ Biến động (Volatility Cap):**
     Giới hạn tỷ lệ thay đổi giá tối đa trong một chu kỳ (ví dụ: không tăng quá $+15\%$ và không giảm quá $-15\%$).
  3. **Tiêu chí pass:** Thử nghiệm sản phẩm có giá đối thủ bán phá giá dưới giá vốn FPT $\rightarrow$ Giá đề xuất phải dừng lại ở giá sàn (`is_floor_capped = True`), không gây âm biên lợi nhuận.

---

# PHẦN 4: VÒNG ĐỜI PHÊ DUYỆT & NHẬT KÝ KIỂM TOÁN (AUDIT & APPROVAL)

### [ ] 4.1. Quy trình Chuyên viên Phê duyệt Giá (Human-in-the-loop)
* **🎯 Tính năng:** Cho phép chuyên viên định giá FPT xem bảng ma trận, phân tích lý do 3 tầng và bấm **Approve** (Áp dụng giá mới) hoặc **Reject** (Từ chối kèm lý do).
* **🏛️ Kiến trúc & File phụ trách:**
  * API: `/api/v1/pricing/recommendations/{id}/approve` & `/reject`.
  * Frontend: Bảng Matrix Pricing View, Modal chi tiết 3-Layer Reasoning.
* **🗄️ Cấu trúc CSDL:**
  * Bảng `price_recommendations`: Cập nhật `status = APPROVED` / `REJECTED`, `reviewed_by`, `reviewed_at`, `rejection_reason`.
  * Bảng `products`: Khi Approve, cập nhật giá bán mới vào `products.base_retail_price`.
  * Bảng `price_history`: Lưu lại điểm mốc giá mới vào lịch sử để vẽ biểu đồ (`price`, `source = FPTSHOP`, `recorded_at`).
  * Bảng `pricing_audit_logs`: Lưu vết thao tác (`actor`, `action = APPROVE_PRICE`, `old_value`, `new_value`, `created_at`).
* **🔄 Luồng hoạt động & Tiêu chí nghiệm thu:**
  1. Chuyên viên duyệt giá duyệt đề xuất trên màn hình.
  2. Trạng thái recommendation chuyển từ `PENDING` sang `APPROVED`.
  3. Giá trong bảng `products` được cập nhật; bảng `pricing_audit_logs` có 1 bản ghi mới.
  4. **Tiêu chí pass:** Không cho phép duyệt 2 lần trên cùng 1 recommendation; lịch sử thao tác được ghi vết 100%.

---

# BẢNG TỔNG HỢP LIÊN KẾT CƠ SỞ DỮ LIỆU TOÀN HỆ THỐNG

| Bảng CSDL | Trọng tâm dữ liệu | Liên kết Khóa ngoại (FK) | Trạng thái / Cờ quan trọng |
| :--- | :--- | :--- | :--- |
| `crawl_jobs` | Quản lý đợt cào | Không | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` |
| `crawl_results` | Dữ liệu đối thủ thô | `job_id` $\rightarrow$ `crawl_jobs.id` | `is_in_stock` (True/False) |
| `products` | Master Catalog FPT | Không | `sku` (Unique), `floor_price`, `cost_price` |
| `sku_mappings` | Đối soát SKU 2 tầng | `fpt_product_id` $\rightarrow$ `products.id`<br>`competitor_crawl_id` $\rightarrow$ `crawl_results.id` | `EXACT_PART_NUMBER`, `NORMALIZED_ATTRIBUTE`<br>`APPROVED`, `PENDING`, `REJECTED` |
| `price_recommendations` | Đề xuất giá từ AI Engine | `fpt_product_id` $\rightarrow$ `products.id` | `is_floor_capped` (True/False)<br>`PENDING`, `APPROVED`, `REJECTED` |
| `price_history` | Lịch sử biến động giá | `fpt_product_id` $\rightarrow$ `products.id` | Nguồn: `FPTSHOP`, `CELLPHONES`, `HOANGHA` |
| `pricing_audit_logs` | Nhật ký chuyên viên | `entity_id` $\rightarrow$ `price_recommendations.id` | `APPROVE_PRICE`, `REJECT_PRICE` |