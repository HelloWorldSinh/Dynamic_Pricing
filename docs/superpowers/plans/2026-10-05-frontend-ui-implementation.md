# Frontend UI Implementation Plan — Dynamic Pricing System

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng toàn bộ giao diện Web SPA chuẩn mực cho hệ thống Dynamic Pricing System (FPT Shop vs CellphoneS & Hoàng Hà Mobile) phục vụ chuyên viên phân tích giá (Pricing Analyst), bao gồm 5 màn hình nghiệp vụ và Trợ lý AI định giá đa trạng thái (Popup nhỏ $\rightarrow$ Phóng rộng).

**Architecture:** Kiến trúc Clean Domain Frontend trong thư mục `frontend/`, giao tiếp với backend FastAPI qua HTTP Contract Seam (`http://localhost:8000/api/v1`). Ứng dụng xây dựng trên React 18 + Vite + TypeScript + Tailwind CSS, tuân thủ nghiêm ngặt nguyên tắc No-Emoji, sử dụng Design Tokens phân cấp màu sắc tài chính (Dark/Light Mode), và bọc toàn bộ HTTP calls qua API Client Adapter.

**Tech Stack:** React 18, Vite, TypeScript, Tailwind CSS, Lucide React (chỉ dùng icon kỹ thuật tối giản, không dùng emoji), Axios, TanStack Table v8.

**Spec:** [docs/superpowers/specs/2026-10-05-frontend-ui-design.md](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/docs/superpowers/specs/2026-10-05-frontend-ui-design.md)

## Global Constraints

- **No-Emoji Rule:** Tuyệt đối không dùng emoji (như 📊, ⚡, 🔍, 🤖) trên các nhãn, nút bấm, bảng hoặc thông báo; chỉ dùng typography và màu sắc ngữ nghĩa.
- **Node/npm Environment:** Mọi lệnh npm trên môi trường Windows PowerShell phải thực thi qua `cmd /c npm ...` hoặc `npm.cmd`.
- **API Base URL:** Mặc định `VITE_API_BASE_URL=http://localhost:8000/api/v1`, cho phép fallback sang Mock Adapter khi backend chưa chạy hoặc thiếu endpoint.
- **Theme Support:** Hỗ trợ Dark Mode (mặc định) và Light Mode thông qua CSS variables và lớp `dark` trên `<html>`.
- **Debounce:** Nút Trigger Crawl phải có cơ chế debounce 30s với bộ đếm ngược trực quan.
- **AI Chat States:** Khung chat AI phải có 3 trạng thái: FAB $\rightarrow$ Popup nhỏ 380px $\rightarrow$ Drawer mở rộng 750px (có nút chuyển đổi Maximize2 / Minimize2).

## Review Focus

1. **Debounce Spamming:** Khi người dùng click liên tục nút "Trigger Crawl", hệ thống phải khóa nút ngay lập tức và đếm ngược từ 30s.
2. **Floor Price Cap Breach:** Sản phẩm có giá đề xuất thấp hơn giá sàn (Floor Price) phải được tự động chốt bằng giá sàn và hiển thị huy hiệu `Floor Protected`.
3. **Empty / Network Failure Handling:** Khi backend chưa bật hoặc API trả về lỗi 500, giao diện phải hiển thị trạng thái Empty State / Error Banner thanh lịch, không được crash trắng trang.
4. **AI Chat Window Resize Preservation:** Chuyển đổi giữa Popup nhỏ (380px) và Drawer mở rộng (750px) phải bảo toàn 100% lịch sử tin nhắn và câu trả lời đang hiển thị.
5. **High Density Data Display:** Bảng ma trận giá 3 bên phải hiển thị rõ ràng trên độ phân giải tối thiểu 1280px, hỗ trợ cuộn ngang mượt mà cho các cột thông số chi tiết.

---

### Task 1: Scaffolding Khung Dự Án Frontend & Design System Tokens

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/index.css`
- Create: `frontend/src/types/theme.ts`
- Create: `frontend/src/context/ThemeContext.tsx`
- Create: `frontend/src/components/layout/AppLayout.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/Navbar.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`

**Interfaces:**
- Consumes: None (khởi tạo nền tảng).
- Produces: `ThemeContext` (`theme: 'dark' | 'light'`, `toggleTheme: () => void`), `AppLayout` bọc các phân hệ màn hình.

- [ ] **Step 1: Khởi tạo cấu hình package.json và cài đặt thư viện**
  Khởi tạo `frontend/package.json` với React 18, Vite 5, Tailwind CSS, Lucide React, Axios, TanStack Table. Chạy `cmd /c npm install`.
- [ ] **Step 2: Thiết lập Tailwind & Design Tokens (Dark/Light)**
  Tạo `tailwind.config.js` và `src/index.css` định nghĩa các biến màu: `brand-fpt` (`#F26F21`), `bg-primary`, `bg-surface`, `status-danger` (`#EF4444`), `status-warning` (`#F59E0B`), `status-success` (`#10B981`), `status-info` (`#3B82F6`), `status-floor` (`#EC4899`).
- [ ] **Step 3: Xây dựng ThemeContext và Shell Layout (Sidebar & Navbar)**
  Xây dựng `Sidebar` chuẩn mực không emoji (dùng icon kỹ thuật SVG từ `lucide-react`), có thanh điều hướng 5 phân hệ: `Price Matrix`, `Pricing Approvals`, `SKU Mapping`, `Crawl Manager`.
- [ ] **Step 4: Kiểm thử render Shell Layout**
  Chạy lệnh build kiểm tra TypeScript: `cmd /c npm run build`. Đảm bảo không có lỗi type.
- [ ] **Step 5: Commit**
  `git add frontend/`  
  `git commit -m "feat(frontend): scaffold react vite project with design system and layout"`

---

### Task 2: Xây Dựng Data Models & API Client Adapter (Clean HTTP Seam)

**Files:**
- Create: `frontend/src/types/product.ts`
- Create: `frontend/src/types/crawl.ts`
- Create: `frontend/src/types/pricing.ts`
- Create: `frontend/src/types/matching.ts`
- Create: `frontend/src/types/ai.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/crawlerApi.ts`
- Create: `frontend/src/api/productApi.ts`
- Create: `frontend/src/api/pricingApi.ts`
- Create: `frontend/src/api/aiApi.ts`
- Create: `frontend/src/api/mockData.ts`

**Interfaces:**
- Consumes: Base URL từ `VITE_API_BASE_URL` hoặc fallback.
- Produces: 
  - `triggerCrawlApi(source: string, category: string): Promise<CrawlJobResponse>`
  - `getCrawlResultsApi(source?: string): Promise<CrawlResult[]>`
  - `getProductsApi(category?: string): Promise<Product[]>`
  - `getPriceMatrixApi(): Promise<PriceComparisonItem[]>`
  - `getRecommendationsApi(): Promise<PricingRecommendation[]>`
  - `approveRecommendationApi(id: string): Promise<void>`
  - `rejectRecommendationApi(id: string): Promise<void>`
  - `getSkuMappingQueueApi(): Promise<SkuMappingPair[]>`
  - `approveSkuMappingApi(id: string): Promise<void>`
  - `sendAiMessageApi(message: string): Promise<AiMessageResponse>`

- [ ] **Step 1: Khai báo đầy đủ TypeScript Types**
  Định nghĩa chính xác schema cho sản phẩm, dữ liệu cào, đề xuất giá, cặp SKU đối soát và tin nhắn AI.
- [ ] **Step 2: Xây dựng Axios Base Client và Data Adapter**
  Xây dựng `client.ts` bọc interceptor xử lý mã lỗi HTTP 429 (Debounce) và timeout.
- [ ] **Step 3: Xây dựng Mock Data Service thông minh**
  Cung cấp dữ liệu mẫu phong phú (Laptop ASUS, Lenovo, iPhone 16, Samsung Galaxy S25...) khi backend chạy ở chế độ standalone dev hoặc thiếu endpoint đặc thù.
- [ ] **Step 4: Kiểm thử Adapter**
  Kiểm tra cú pháp và build: `cmd /c npm run build`.
- [ ] **Step 5: Commit**
  `git add frontend/src/types/ frontend/src/api/`  
  `git commit -m "feat(frontend): implement typed api client adapters and mock service"`

---

### Task 3: Màn Hình 1 — Price Matrix Dashboard (So Sánh Giá 3 Bên & On-Demand Crawl)

**Files:**
- Create: `frontend/src/components/matrix/MetricKpiCards.tsx`
- Create: `frontend/src/components/matrix/DebounceTriggerBar.tsx`
- Create: `frontend/src/components/matrix/MatrixFilterToolbar.tsx`
- Create: `frontend/src/components/matrix/PriceMatrixTable.tsx`
- Create: `frontend/src/pages/PriceMatrixPage.tsx`

**Interfaces:**
- Consumes: `getPriceMatrixApi`, `triggerCrawlApi` từ Task 2.
- Produces: Màn hình Dashboard phân tích giá 3 bên hoàn chỉnh (PBI-004, PBI-013, PBI-014).

- [ ] **Step 1: Xây dựng MetricKpiCards**
  Hiển thị 4 thẻ KPI: Tổng mã theo dõi, FPT đắt hơn (badge đỏ), Win Rate % (badge xanh), Đề xuất chờ duyệt.
- [ ] **Step 2: Xây dựng DebounceTriggerBar**
  Nút "Trigger Crawl" kết nối API `/crawl/trigger`, có bộ đếm ngược 30 giây (Debounce 30s) chống spam và thanh progress bar.
- [ ] **Step 3: Xây dựng MatrixFilterToolbar**
  Lọc theo ngành hàng (Tất cả / Điện thoại / Laptop), lọc mức chênh lệch (≥ 5%), lọc tồn kho DOH > 30 ngày, lọc đối thủ còn hàng.
- [ ] **Step 4: Xây dựng PriceMatrixTable với TanStack Table**
  Bảng so sánh 3 bên FPT vs CellphoneS vs Hoàng Hà. Mã hóa màu: Đỏ/Cam (FPT đắt hơn), Xanh lá (FPT rẻ hơn), Xanh dương (bằng giá). Cột Confidence Score và Tồn kho DOH.
- [ ] **Step 5: Ghép trang PriceMatrixPage và kiểm thử build**
  Chạy `cmd /c npm run build`.
- [ ] **Step 6: Commit**
  `git commit -am "feat(frontend): implement price matrix dashboard with debounce crawl trigger"`

---

### Task 4: Màn Hình 2 — Pricing Approvals (Duyệt Điều Chỉnh Giá & Bảo Vệ Giá Sàn)

**Files:**
- Create: `frontend/src/components/recommendations/ApprovalFilterTabs.tsx`
- Create: `frontend/src/components/recommendations/BatchActionBar.tsx`
- Create: `frontend/src/components/recommendations/RecommendationTable.tsx`
- Create: `frontend/src/pages/PricingApprovalsPage.tsx`

**Interfaces:**
- Consumes: `getRecommendationsApi`, `approveRecommendationApi`, `rejectRecommendationApi`.
- Produces: Màn hình duyệt giá và bảo vệ giá sàn (PBI-010, PBI-011, PBI-012).

- [ ] **Step 1: Xây dựng ApprovalFilterTabs**
  Tab lọc: Chờ duyệt (Pending) | Đã duyệt (Approved) | Đã từ chối (Rejected) kèm số lượng badge.
- [ ] **Step 2: Xây dựng RecommendationTable**
  Hiển thị Giá hiện tại $\rightarrow$ Giá đề xuất mới $\rightarrow$ Giá sàn (Floor Price). Nếu giá đề xuất $\le$ sàn $\rightarrow$ hiển thị huy hiệu `Floor Protected`.
- [ ] **Step 3: Xây dựng BatchActionBar**
  Hỗ trợ chọn nhiều dòng sản phẩm để Batch Approve hoặc Batch Reject đồng thời.
- [ ] **Step 4: Kiểm thử logic duyệt giá và build**
  Chạy `cmd /c npm run build`.
- [ ] **Step 5: Commit**
  `git commit -am "feat(frontend): implement pricing recommendations and floor protection approvals"`

---

### Task 5: Màn Hình 3 — Manual SKU Mapping Queue (Đối Soát Khớp Sản Phẩm)

**Files:**
- Create: `frontend/src/components/mapping/SkuDiffCard.tsx`
- Create: `frontend/src/components/mapping/ConfidenceMeter.tsx`
- Create: `frontend/src/pages/SkuMatchingPage.tsx`

**Interfaces:**
- Consumes: `getSkuMappingQueueApi`, `approveSkuMappingApi`.
- Produces: Màn hình đối soát SKU 60% – 79% confidence (PBI-008).

- [ ] **Step 1: Xây dựng SkuDiffCard (Side-by-side Diff)**
  Cột trái (FPT Shop) và Cột phải (Đối thủ CellphoneS/Hoàng Hà). Highlight các trường trùng khớp (xanh lá mờ) và khác biệt (vàng cam mờ).
- [ ] **Step 2: Tích hợp thao tác xác nhận khớp**
  Nút "Xác nhận Ghép Cặp" (Lưu 100% confidence) và "Từ chối Ghép Cặp" (Loại bỏ).
- [ ] **Step 3: Ghép trang SkuMatchingPage và kiểm thử build**
  Chạy `cmd /c npm run build`.
- [ ] **Step 4: Commit**
  `git commit -am "feat(frontend): implement manual sku mapping queue with side-by-side diff"`

---

### Task 6: Màn Hình 4 — Crawl Operations & Raw Inspector (Giám Sát Cào & Dữ Liệu Thô)

**Files:**
- Create: `frontend/src/components/crawler/SourceStatusCard.tsx`
- Create: `frontend/src/components/crawler/CronSchedulePanel.tsx`
- Create: `frontend/src/components/crawler/RawDataInspector.tsx`
- Create: `frontend/src/pages/CrawlManagerPage.tsx`

**Interfaces:**
- Consumes: `getCrawlResultsApi`.
- Produces: Màn hình quản lý cào dữ liệu và kiểm tra dữ liệu thô (PBI-001, PBI-002, PBI-003, PBI-005, PBI-015).

- [ ] **Step 1: Xây dựng SourceStatusCard**
  Thẻ giám sát 3 nguồn: FPT Shop, CellphoneS, Hoàng Hà Mobile (Thời điểm cào gần nhất, số item thành công, tỉ lệ lỗi).
- [ ] **Step 2: Xây dựng CronSchedulePanel**
  Cấu hình lịch tự động chạy 2 lần/ngày: 08:00 và 18:00.
- [ ] **Step 3: Xây dựng RawDataInspector**
  Bảng xem dữ liệu thô, tìm kiếm theo tên hoặc URL, link mở tab mới sang trang gốc đối thủ để kiểm tra thực tế.
- [ ] **Step 4: Ghép trang CrawlManagerPage và kiểm thử build**
  Chạy `cmd /c npm run build`.
- [ ] **Step 5: Commit**
  `git commit -am "feat(frontend): implement crawl operations monitoring and raw data inspector"`

---

### Task 7: Phân Hệ 5 — Trợ Lý AI Định Giá Đa Trạng Thái (Popup Nhỏ $\rightarrow$ Phóng Rộng Drawer)

**Files:**
- Create: `frontend/src/components/ai/AiFloatingButton.tsx`
- Create: `frontend/src/components/ai/CompactChatPopup.tsx`
- Create: `frontend/src/components/ai/ExpandedAiDrawer.tsx`
- Create: `frontend/src/components/ai/ExplainableCard.tsx`
- Create: `frontend/src/components/ai/AiAssistantManager.tsx`
- Create: `frontend/src/context/AiChatContext.tsx`

**Interfaces:**
- Consumes: `sendAiMessageApi`, ngữ cảnh sản phẩm đang chọn.
- Produces: Trợ lý AI toàn cục đa trạng thái (PBI-017, PBI-018).

- [ ] **Step 1: Xây dựng AiChatContext quản lý trạng thái**
  Quản lý 3 trạng thái: `minimized` (nút FAB), `compact` (popup nhỏ 380px), `expanded` (drawer rộng 750px). Lưu giữ lịch sử hội thoại xuyên suốt.
- [ ] **Step 2: Xây dựng CompactChatPopup (Khung nhỏ mặc định)**
  Khung chat neo góc dưới phải (`bottom-6 right-6`), kích thước 380x520px, có nút **Maximize2** để bung rộng và các prompt gợi ý nhanh.
- [ ] **Step 3: Xây dựng ExpandedAiDrawer (Khung rộng chuyên sâu)**
  Ngăn kéo rộng 750px trượt từ phải sang, có nút **Minimize2** để co về popup nhỏ, hỗ trợ hiển thị bảng biểu so sánh và Thẻ giải thích 3 lớp (Explainable AI Card).
- [ ] **Step 4: Xây dựng ExplainableCard (Giải thích 3 tầng)**
  Card giải thích trực quan: (1) Biến động đối thủ $\rightarrow$ (2) Tồn kho & DOH FPT $\rightarrow$ (3) Biên an toàn giá sàn.
- [ ] **Step 5: Nhúng AiAssistantManager vào AppLayout và kiểm thử build**
  Chạy `cmd /c npm run build`.
- [ ] **Step 6: Commit**
  `git commit -am "feat(frontend): implement multi-state ai pricing assistant popup and expanded drawer"`

---

### Task 8: Modal Chi Tiết Sản Phẩm & Kiểm Thử Toàn Diện (End-to-End Build Verification)

**Files:**
- Create: `frontend/src/components/common/ProductDetailModal.tsx`
- Modify: `frontend/src/pages/PriceMatrixPage.tsx`
- Modify: `frontend/src/README.md`

**Interfaces:**
- Consumes: Product Item được click từ bảng Ma trận giá.
- Produces: Modal xem đầy đủ thông số kỹ thuật (PBI-016) và gói build hoàn chỉnh.

- [ ] **Step 1: Xây dựng ProductDetailModal**
  Xem chi tiết thông số bóc tách: CPU, RAM, ROM, Màu, Part-number, link web đối thủ mở tab mới.
- [ ] **Step 2: Tích hợp Modal vào PriceMatrixPage**
  Click vào dòng sản phẩm hoặc nút "Chi tiết" sẽ mở modal.
- [ ] **Step 3: Kiểm thử toàn diện Build & Responsive**
  Chạy `cmd /c npm run build` để xác nhận 100% TypeScript compile không có cảnh báo/lỗi.
- [ ] **Step 4: Commit**
  `git commit -am "feat(frontend): implement product detail modal and finalize production build"`

---

## Verification Plan

### Automated Build & Typecheck
- **Command:** `cmd /c npm run build` (tại thư mục `frontend/`)
- **Success Criteria:** TypeScript compiler thoát mã 0, sinh bundle trong `frontend/dist/` không có lỗi cú pháp.

### Manual Verification
1. **Kiểm tra Giao diện & Đổi Theme:**
   - Mở trình duyệt tại `http://localhost:5173`.
   - Click nút chuyển đổi Dark / Light mode: Nền và màu chữ chuyển đổi mượt mà.
2. **Kiểm tra Debounce 30s:**
   - Tại trang Price Matrix, click nút "Trigger Crawl". Nút chuyển sang trạng thái disabled và đếm ngược từ 30s về 0s.
3. **Kiểm tra Bộ Lọc Nghiệp Vụ:**
   - Đổi lọc sang "Laptop", lọc "FPT đắt hơn ≥ 5%": Bảng dữ liệu tự động cập nhật đúng điều kiện.
4. **Kiểm tra Phê Duyệt Giá & Bảo Vệ Giá Sàn:**
   - Vào tab "Pricing Approvals", kiểm tra các sản phẩm có huy hiệu `Floor Protected`. Click "Approve" hoặc "Reject", sản phẩm chuyển trạng thái tức thì.
5. **Kiểm tra Khung Chat AI Đa Trạng Thái:**
   - Click biểu tượng AI góc dưới phải: Popup nhỏ 380px mở lên tại góc phải.
   - Click nút Phóng to (Maximize): Khung chat mở rộng thành ngăn kéo lớn 750px.
   - Click nút Thu nhỏ (Minimize): Khung chat co lại thành Popup nhỏ 380px mà lịch sử chat không bị mất.
