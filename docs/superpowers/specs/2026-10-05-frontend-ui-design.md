# TÀI LIỆU ĐẶC TẢ THIẾT KẾ GIAO DIỆN (DESIGN SPEC)
# DYNAMIC PRICING SYSTEM — FRONTEND DASHBOARD

**Ngày khởi tạo:** 2026-10-05  
**Tác giả:** Antigravity AI & Pricing Analyst  
**Phiên bản:** 1.0 (Architectural Specification)  
**Phạm vi:** Giao diện người dùng Web SPA cho Chuyên viên phân tích giá (Single User / Pricing Analyst Scope)  

---

## 1. TỔNG QUAN HỆ THỐNG & MỤC TIÊU SẢN PHẨM

Hệ thống **Dynamic Pricing System** tự động hóa chu trình theo dõi giá đối thủ (CellphoneS, Hoàng Hà Mobile), so khớp sản phẩm với FPT Shop (SKU Matching Engine), tính toán đề xuất điều chỉnh giá theo tồn kho & bảo vệ giá sàn, đồng thời cung cấp trợ lý ảo AI để hỏi đáp và giải thích lý do đề xuất giá.

Giao diện Web SPA đóng vai trò trung tâm điều hành thống nhất (Cockpit Dashboard) cho **Pricing Analyst**, thay thế hoàn toàn các bảng tính Excel thủ công, nâng cao tốc độ phản ứng giá thị trường và đảm bảo an toàn biên lợi nhuận kinh doanh.

---

## 2. NGUYÊN TẮC THIẾT KẾ & HỆ THỐNG NHẬN DIỆN (DESIGN SYSTEM)

### 2.1. Phong cách thị giác (Aesthetics & Mood)
* **Modern Financial & Data-Dense Analytics:** Phong cách công cụ phân tích tài chính/SaaS cao cấp, hiển thị dữ liệu mật độ cao nhưng rành mạch, hạn chế khoảng trắng thừa, hỗ trợ thao tác nhanh qua phím tắt và chuột.
* **Chế độ hiển thị linh hoạt (Dark/Light Mode):**
  * *Dark Mode (Mặc định):* Nền Slate/Navy sâu (`#0B0F17` / `#0F172A`), thẻ phủ Glassmorphism bóng mờ, viền mảnh bán trong suốt (`rgba(255,255,255,0.08)`), làm nổi bật các chỉ số tài chính và bảng đối soát giá.
  * *Light Mode:* Nền trắng sứ và xám lạnh (`#F8FAFC` / `#FFFFFF`), độ tương phản cao, chuẩn mực báo cáo doanh nghiệp.
* **Typography:** Phông chữ `Plus Jakarta Sans` hoặc `Inter`, tối ưu định dạng số tiền tệ (VND) và thông số kỹ thuật (CPU, RAM, Part Number).

### 2.2. Bảng mã màu nghiệp vụ (Semantic Tokens & Brand Identity)

| Tên Token | Mã Hex (Dark / Light) | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- |
| `brand-fpt` | `#F26F21` / `#EA580C` | Màu cam nhận diện FPT Shop: Nút CTA, điểm nhấn chính, logo |
| `bg-primary` | `#0B0F17` / `#F8FAFC` | Nền canvas toàn ứng dụng |
| `bg-surface` | `#111827` / `#FFFFFF` | Nền card, bảng biểu, modal, popup |
| `border-subtle` | `#1F2937` / `#E2E8F0` | Đường phân cách và đường viền bảng |
| `status-danger` | `#EF4444` / `#DC2626` | **FPT đắt hơn đối thủ > 5%** (Nguy cơ mất thị phần) |
| `status-warning`| `#F59E0B` / `#D97706` | **FPT đắt hơn 1% – 5%** hoặc Sản phẩm cần duyệt khớp SKU |
| `status-success`| `#10B981` / `#059669` | **FPT cạnh tranh tốt** (rẻ hơn) hoặc Match chính xác 100% |
| `status-info`   | `#3B82F6` / `#2563EB` | **FPT bằng giá đối thủ** hoặc Match thuộc tính 80% – 95% |
| `status-floor`  | `#EC4899` / `#DB2777` | Cảnh báo chạm giá sàn (Floor Price Floor Protection) |

---

## 3. CẤU TRÚC ĐIỀU HƯỚNG & PHÂN HỆ MÀN HÌNH

Hệ thống gồm **Sidebar cố định bên trái (có thể thu nhỏ gọn gàng)** và **5 phân hệ màn hình chính**, cùng **1 Khung Trợ lý AI đa trạng thái** xuất hiện toàn hệ thống.

```
Layout Tổng thể:
+-----------------------------------------------------------------------------------+
| [Logo FPT Dynamic Pricing]   | [Breadcrumb] [Category Filter] [Theme Toggle] [User] |
+------------------------------+----------------------------------------------------+
| SIDEBAR:                     | NỘI DUNG MÀN HÌNH CHÍNH (DYNAMIC ROUTE VIEW)      |
|  [1] 📊 Price Matrix         |                                                    |
|  [2] ⚡ Recommendations      |                                                    |
|  [3] 🔍 SKU Mapping Queue    |                                                    |
|  [4] 🕷️ Crawl Operations     |                                                    |
|  [5] 🤖 AI Studio            |                                                    |
|                              |                                                    |
|                              |                 [✨ AI Assistant Floating Widget]  |
+------------------------------+----------------------------------------------------+
```

---

## 4. CHI TIẾT CÁC MÀN HÌNH NGHIỆP VỤ

### 4.1. Màn hình 1: Ma trận So sánh Giá 3 Bên (Price Matrix Dashboard)
* **Mục tiêu:** Cho phép Pricing Analyst rà soát tức thì vị thế giá FPT Shop so với CellphoneS và Hoàng Hà Mobile.
* **Thành phần giao diện:**
  1. **Top Metric Cards (KPI tổng quan):**
     * *Tổng mã theo dõi:* Tổng số SKU đã kích hoạt đối soát.
     * *FPT Đang Đắt Hơn:* Số SKU cần xử lý gấp (gắn badge Đỏ).
     * *Tỉ lệ cạnh tranh giá (Win Rate %):* % số SKU mà FPT rẻ hơn hoặc bằng giá.
     * *Đề xuất giá chờ duyệt:* Số lượng gợi ý giá mới đang chờ xử lý.
  2. **Thanh tác vụ On-Demand Crawl (PBI-004):**
     * Nút **"Trigger Crawl"**: Kích hoạt cào tức thời cho danh mục đang chọn.
     * Countdown Debounce 30s trực quan (vô hiệu hóa nút và đếm ngược kèm animation quay).
     * Toast/Progress bar hiển thị trạng thái job cào ngầm.
  3. **Bộ lọc nghiệp vụ nâng cao (PBI-014):**
     * Dropdown chọn Ngành hàng: *Tất cả / Điện thoại / Laptop*.
     * Thanh trượt/Lọc ngưỡng chênh lệch: *FPT đắt hơn ≥ 5% (Mặc định), ≥ 2%, Tất cả*.
     * Checkbox lọc tồn kho: *DOH > 30 ngày* (hàng tồn kho lâu ngày).
     * Checkbox lọc trạng thái đối thủ: *Chỉ xem đối thủ thực sự còn hàng (In-Stock Only)*.
  4. **Bảng dữ liệu Ma trận Giá (PBI-013):**
     * **Cột:**
       * Mã SKU FPT & Tên sản phẩm (kèm chip Part-Number nếu có).
       * Giá FPT (VNĐ).
       * Giá CellphoneS (VNĐ + tag Còn hàng / Hết hàng).
       * Giá Hoàng Hà Mobile (VNĐ + tag Còn hàng / Hết hàng).
       * Chênh lệch (VNĐ tuyệt đối + Tỷ lệ % kèm màu Đỏ / Cam / Xanh lá / Xanh dương).
       * Độ tin cậy khớp (Confidence Score Badge: 100% / 85% / 70%).
       * Tồn kho FPT & Số ngày lưu kho (DOH).
       * Thao tác nhanh: Nút "Xem chi tiết" (Mở modal) & Nút "AI Explain" (Hỏi lý do đề xuất).

---

### 4.2. Màn hình 2: Trung tâm Đề xuất & Phê duyệt Giá (Pricing Approvals)
* **Mục tiêu:** Thực thi quy tắc bảo vệ giá sàn và thuật toán điều chỉnh giá theo tồn kho DOH (PBI-010, PBI-011, PBI-012).
* **Thành phần giao diện:**
  1. **Hệ thống Tab phân loại:** `Chờ duyệt (Pending)` | `Đã duyệt (Approved)` | `Đã từ chối (Rejected)`.
  2. **Thanh công cụ Phê duyệt Hàng loạt (Batch Actions):** Checkbox chọn tất cả, nút "Duyệt toàn bộ đã chọn" (Batch Approve), nút "Bác bỏ toàn bộ" (Batch Reject).
  3. **Bảng Đề xuất Giá:**
     * Sản phẩm & SKU.
     * Giá bán hiện tại.
     * **Giá Đề Xuất Mới** (Tính từ Ma trận 9 kịch bản).
     * **Giá Sàn Bảo Vệ (Floor Price):** Giá vốn + Biên lợi nhuận tối thiểu. Nếu đề xuất < sàn, hệ thống tự động chốt bằng giá sàn và hiển thị biểu tượng khiên bảo vệ `Floor Protected`.
     * Biến động biên lợi nhuận ước tính (Margin Impact: e.g. `+1.8%` hoặc `-2.4%`).
     * Lý do gợi ý tóm tắt (e.g. *DOH = 52 ngày (>45d) & CellphoneS đang rẻ hơn 400.000đ*).
     * 2 nút hành động: **Approve (Xanh lá)** & **Reject (Đỏ xám)**.

---

### 4.3. Màn hình 3: Hàng đợi Đối soát Khớp SKU Thủ công (Manual Mapping Queue)
* **Mục tiêu:** Xử lý các sản phẩm ghép cặp có độ tin cậy vừa phải (60% – 79%) nhằm đảm bảo 100% dữ liệu so sánh chuẩn xác (PBI-008).
* **Thành phần giao diện:**
  1. **Bảng so sánh 2 cột song song (Side-by-side Diff Card):**
     * **Cột FPT Shop (Chuẩn):** Tên đầy đủ, Mã SKU, Hãng, Part Number, CPU, RAM, ROM, Màu sắc.
     * **Cột Đối thủ (Cần đối soát):** Tên cào được, Nguồn (CellphoneS hoặc Hoàng Hà), Thông số bóc tách, URL gốc.
     * Highlight trực quan: Các trường trùng khớp có viền xanh lá mờ; các trường khác biệt (như màu sắc, mã CPU) hiển thị viền vàng cam.
  2. **Thanh điều khiển:**
     * Confidence Gauge: Đồng hồ hiển thị điểm tương đồng (e.g., `72% Confidence`).
     * Nút **"Xác nhận Ghép cặp" (Approve Match):** Lưu kết quả vào DB để lần cào sau tự động nhận diện với 100% confidence.
     * Nút **"Từ chối Ghép cặp" (Reject & Unlink):** Hủy cặp so khớp để đưa sản phẩm về danh sách độc lập.

---

### 4.4. Màn hình 4: Trung tâm Vận hành Cào Dữ liệu (Crawl Operations & Raw Inspector)
* **Mục tiêu:** Giám sát sức khỏe crawler, kiểm tra dữ liệu thô và cấu hình lịch quét giá tự động (PBI-001, PBI-002, PBI-003, PBI-005, PBI-015).
* **Thành phần giao diện:**
  1. **Thẻ tình trạng 3 nguồn cào:**
     * FPT Shop, CellphoneS, Hoàng Hà: Thời điểm cào gần nhất, Tỉ lệ thành công (%), Tổng số sản phẩm thu thập.
  2. **Quản lý Lịch cào tự động (Cron Schedule):**
     * Lịch định kỳ mặc định 2 lần/ngày: `08:00` và `18:00`.
     * Nút Bật/Tắt lịch cào tự động và lịch sử chạy (Run History).
  3. **Bảng Dữ liệu Thô (Raw Scraped Data Inspector):**
     * Tìm kiếm nhanh theo từ khóa URL hoặc tên sản phẩm.
     * Xem dữ liệu JSON gốc, giá bóc tách, trạng thái stock, timestamp cào.
     * Nút mở trực tiếp URL đối thủ trong tab mới để kiểm tra thực tế (Cross-check verification).

---

### 4.5. Phân hệ 5: Trợ lý AI Định giá Đa Trạng Thái (AI Pricing Assistant & Explainable AI)
* **Yêu cầu đặc biệt (Theo phản hồi người dùng):** Khung chat AI mặc định ở dạng popup nhỏ gọn gàng, có nút phóng to để mở rộng không gian làm việc chi tiết.
* **3 Trạng thái hiển thị (Multi-state UI Architecture):**

#### 🔹 Trạng thái 1: Nút kích hoạt nổi (Floating Action Button - FAB)
* Biểu tượng AI lấp lánh (Sparkles/Bot icon) cố định ở góc dưới cùng bên phải màn hình (`fixed bottom-6 right-6 z-40`).
* Badge thông báo số phân tích mới hoặc câu trả lời sẵn sàng.

#### 🔹 Trạng thái 2: Popup Chat Box Nhỏ (Compact Floating Chat - Mặc định khi mở)
* **Kích thước:** Chiều rộng ~380px, chiều cao ~520px, neo tại góc dưới phải màn hình.
* **Tiện ích:** Người dùng vừa xem bảng giá vừa hỏi đáp nhanh mà không bị che khuất tầm nhìn dữ liệu chính.
* **Thanh Header tích hợp:**
  * Avatar & Tên Trợ lý: "AI Pricing Assistant".
  * Nút **Phóng to / Mở rộng (`Maximize2` icon)**: Chuyển đổi tức thời sang Trạng thái 3.
  * Nút Thu nhỏ / Đóng (`X` hoặc `Minimize` icon): Quay về nút FAB.
* **Nội dung:**
  * Gợi ý câu hỏi nhanh (Prompt Chips): *"Top 5 laptop FPT đắt hơn?", "Mã nào DOH > 45d?", "So sánh giá iPhone 16"*.
  * Hộp thoại tin nhắn gọn gàng, ô nhập câu hỏi và nút gửi tin.

#### 🔹 Trạng thái 3: Không gian Phân tích Mở rộng (Expanded Studio / Wide Drawer)
* **Kích thước:** Ngăn kéo bên phải (Slide-over Drawer) chiều rộng 720px – 800px (hoặc Modal trung tâm rộng rãi).
* **Thanh Header tích hợp:**
  * Nút **Thu nhỏ về Khung nhỏ (`Minimize2` icon)**: Trở lại Popup chat 380px mà vẫn giữ nguyên ngữ cảnh cuộc trò chuyện.
  * Nút Đóng ngăn kéo.
* **Khả năng hiển thị chuyên sâu:**
  * **Hiển thị Bảng so sánh Markdown:** Kết quả so sánh đa nguồn dưới dạng table đẹp mắt, có thể copy hoặc xuất nhanh.
  * **Thẻ Giải thích Minh bạch 3 Lớp (Explainable AI Card - PBI-018):**
    1. *Lớp 1 — Biến động thị trường đối thủ:* Tên đối thủ vừa giảm, số tiền giảm, tình trạng kho.
    2. *Lớp 2 — Hiện trạng kho FPT:* Tồn kho khả dụng, số ngày lưu kho DOH.
    3. *Lớp 3 — Biên an toàn giá sàn:* Xác nhận giá đề xuất cao hơn giá sàn bao nhiêu %, bảo đảm không bán dưới giá vốn.

---

### 4.6. Component Dùng Chung: Modal Chi tiết Sản phẩm (Product Detail Modal)
* **Kích hoạt:** Bấm vào bất kỳ dòng sản phẩm nào trên Bảng so sánh (PBI-016).
* **Nội dung hiển thị:**
  * Thông số kỹ thuật bóc tách đầy đủ (CPU, RAM, ROM/SSD, Màn hình, Pin, Màu sắc).
  * Mã Part-Number chuẩn của nhà sản xuất.
  * Lịch sử biến động giá 7 ngày/30 ngày (nếu có).
  * Danh sách link nguồn kèm nút mở tab mới truy cập fptshop.com.vn, cellphones.com.vn, hoanghamobile.com.

---

## 5. CẤU TRÚC THƯ MỤC DỰ ÁN FRONTEND (`frontend/`)

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── assets/                      # Logo FPT, biểu tượng đối thủ
│   ├── components/
│   │   ├── common/                  # Button, Badge, Modal, Tabs, Dropdown, Toggle
│   │   ├── layout/                  # Navbar, Sidebar, PageContainer
│   │   ├── matrix/                  # ComparisonTable, PriceDiffBadge, MetricCards, FilterToolbar
│   │   ├── recommendations/         # ApprovalTable, MarginImpactBadge, BatchActionBar
│   │   ├── mapping/                 # SkuDiffCard, ConfidenceGauge, MappingQueue
│   │   ├── crawler/                 # CrawlTriggerButton, SourceStatusCard, RawJsonViewer
│   │   └── ai/                      # AiFloatingLauncher, CompactChatPopup, ExpandedAiDrawer, ExplainCard
│   ├── context/                     # ThemeContext (Dark/Light), AiChatContext (State min/compact/expanded)
│   ├── hooks/                       # useDebounce, useCrawlTrigger, useMatrixFilter
│   ├── services/
│   │   ├── apiClient.ts             # Cấu hình Axios baseURL: http://localhost:8000/api/v1
│   │   ├── crawlApi.ts              # API /crawl/trigger, /crawl/results
│   │   ├── productApi.ts            # API /products
│   │   ├── pricingApi.ts            # API /pricing/recommendations, /pricing/approve
│   │   └── aiApi.ts                 # API /ai/chat, /ai/explain
│   ├── types/                       # TypeScript interfaces
│   ├── utils/                       # currencyFormatter (VND), dateUtils, scoreBadges
│   ├── App.tsx                      # Routing & Layout Root
│   ├── index.css                    # Tailwind CSS Directives & Custom Scrollbars
│   └── main.tsx
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

---

## 6. KẾ HOẠCH BẢO ĐẢM CHẤT LƯỢNG & KIỂM THỬ (QA & VERIFICATION)

1. **Kiểm thử Responsive & Đa độ phân giải:**
   * Màn hình tối ưu: Desktop chuẩn từ 1280px đến 1920px (đặc thù màn hình làm việc của chuyên viên dữ liệu).
   * Thanh cuộn ngang tinh tế (custom scrollbar) cho bảng dữ liệu nhiều cột.
2. **Kiểm thử Luồng Debounce 30s:**
   * Ngăn chặn người dùng spam nút "Trigger Crawl", hiển thị đúng countdown và trạng thái HTTP 429 từ Backend.
3. **Kiểm thử Chuyển đổi Trạng thái Chat AI:**
   * Click FAB $\rightarrow$ Mở Popup nhỏ 380px.
   * Click nút Maximize $\rightarrow$ Phóng rộng thành Drawer 750px mượt mà không mất dữ liệu chat.
   * Click nút Minimize $\rightarrow$ Trở về Popup nhỏ.
4. **Kiểm thử Màu sắc Trực quan:**
   * Đảm bảo mọi trạng thái Đỏ/Cam/Xanh thể hiện đúng quy chuẩn định giá và tương phản hoàn hảo trên cả 2 theme Dark & Light.
