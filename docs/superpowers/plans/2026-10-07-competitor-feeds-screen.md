# Màn hình Dữ liệu Đối thủ (Competitor Feeds) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng màn hình chuyên biệt "Dữ liệu Đối thủ" (Competitor Feeds) trên Sidebar để hiển thị, tìm kiếm, lọc và xem thông số kỹ thuật chi tiết của dữ liệu cào từ CellphoneS và Hoàng Hà Mobile.

**Architecture:** Màn hình `CompetitorFeedsPage` được xây dựng theo kiến trúc Deep Modules với 4 thành phần tách biệt: `CompetitorSummaryCards` (KPIs), `CompetitorFilterBar` (Tìm kiếm & Bộ lọc), `CompetitorDataTable` (Bảng dữ liệu + Phân trang), và `CompetitorSpecsDrawer` (Drawer xem chi tiết thông số kỹ thuật & Raw JSON). Tích hợp đồng bộ vào hệ thống điều hướng `Sidebar.tsx` và `App.tsx`.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Lucide React, Axios / Custom API Client.

**Spec:** [`docs/superpowers/specs/2026-10-07-competitor-scraped-data-ui-design.md`](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/docs/superpowers/specs/2026-10-07-competitor-scraped-data-ui-design.md)

## Global Constraints
- Tuân thủ nghiêm ngặt PEP 8 / Clean Code và TypeScript strict typing; không dùng `any` bừa bãi.
- Không để lại unused imports trong bất kỳ file nào.
- Hỗ trợ hoàn hảo cả 2 chế độ Dark Mode và Light Mode kế thừa từ `ThemeContext`.
- Bảng màu phân định rõ ràng giữa các nguồn: CellphoneS (Tone Đỏ/Rose), Hoàng Hà Mobile (Tone Cam/Amber), FPT Shop (Tone Cam FPT).
- Cơ chế Fallback an toàn tới mock data khi backend API chưa khởi chạy hoặc ngoại lệ kết nối.

## Review Focus
- Trường hợp `specifications` hoặc `raw_specs` bị rỗng / null / sai định dạng: Drawer không được crash, phải hiển thị empty state "Không có thông số kỹ thuật bóc tách".
- Dữ liệu giá = 0 hoặc null từ web đối thủ (hết hàng hoặc cần liên hệ): Hiển thị nhãn "Liên hệ" thay vì "0 ₫".
- Phân trang khi kết quả lọc = 0: Hiển thị Empty State rõ ràng kèm nút "Đặt lại bộ lọc".
- Tràn chữ (Text overflow) ở tên sản phẩm hoặc URL rất dài: Phải có `truncate` và `title` tooltip đầy đủ.
- Sao chép JSON vào clipboard: Phải xử lý an toàn với fallback nếu trình duyệt chặn quyền clipboard.

---

### Task 1: Cập nhật Types Definition và Dữ liệu Mock
**Files:**
- Modify: `frontend/src/types/crawl.ts:1-27`
- Modify: `frontend/src/api/mockData.ts:607-652`
- Modify: `frontend/src/api/crawlerApi.ts:62-95`

**Interfaces:**
- Consumes: Backend ORM schema `backend/app/models/crawl_result.py`
- Produces: `CrawlResult` interface mở rộng có `original_price`, `stock_status_text`, `category`; hàm `getCrawlResultsApi` chuẩn hóa adapter.

- [ ] **Step 1: Cập nhật `frontend/src/types/crawl.ts`**
  Thêm các trường `original_price?: number`, `stock_status_text?: string`, `category?: string` và hỗ trợ `id: string | number`.
- [ ] **Step 2: Làm giàu dữ liệu `mockCrawlResults` trong `frontend/src/api/mockData.ts`**
  Bổ sung tối thiểu 10+ bản ghi thực tế từ CellphoneS và Hoàng Hà Mobile với đầy đủ `specifications` (CPU, RAM, ROM, Kích thước màn hình, Dung lượng pin) và phân bổ trạng thái còn hàng/hết hàng.
- [ ] **Step 3: Cập nhật API Adapter trong `frontend/src/api/crawlerApi.ts`**
  Map chuẩn các trường từ backend (`raw_name` -> `product_name`, `current_price` -> `price`, `raw_specs` -> `specifications`).

---

### Task 2: Xây dựng Component Thẻ Thống kê KPI (`CompetitorSummaryCards.tsx`)
**Files:**
- Create: `frontend/src/components/competitor/CompetitorSummaryCards.tsx`

**Interfaces:**
- Consumes: `items: CrawlResult[]`
- Produces: UI component hiển thị 4 KPI cards: Tổng số bản ghi, CellphoneS (số lượng & %), Hoàng Hà (số lượng & %), Tỷ lệ còn hàng & thời gian cào mới nhất.

- [ ] **Step 1: Định nghĩa interface `CompetitorSummaryCardsProps`**
- [ ] **Step 2: Tính toán các chỉ số thống kê từ props `items`**
  (tổng số, count CellphoneS, count Hoàng Hà, % in-stock, latest crawled date).
- [ ] **Step 3: Render 4 cards giao diện hiện đại, icon nổi bật, tương thích Dark/Light mode**

---

### Task 3: Xây dựng Component Thanh Công cụ Lọc (`CompetitorFilterBar.tsx`)
**Files:**
- Create: `frontend/src/components/competitor/CompetitorFilterBar.tsx`

**Interfaces:**
- Consumes: State filters (search, source, stock, sort), handlers, total filtered count.
- Produces: UI component thanh tìm kiếm và bộ lọc nâng cao.

- [ ] **Step 1: Tạo component `CompetitorFilterBar` với input tìm kiếm tức thì**
- [ ] **Step 2: Tạo dropdown / tab pills lọc Nguồn (ALL / CELLPHONES / HOANGHA)**
- [ ] **Step 3: Tạo bộ lọc trạng thái kho (ALL / IN_STOCK / OUT_OF_STOCK) và sắp xếp (LATEST / PRICE_ASC / PRICE_DESC)**
- [ ] **Step 4: Hiển thị badge số lượng kết quả đã lọc**

---

### Task 4: Xây dựng Component Drawer Xem Chi tiết Kỹ thuật (`CompetitorSpecsDrawer.tsx`)
**Files:**
- Create: `frontend/src/components/competitor/CompetitorSpecsDrawer.tsx`

**Interfaces:**
- Consumes: `item: CrawlResult | null`, `onClose: () => void`
- Produces: Slide-over Drawer với 2 tab: Tab 1 Specs Bóc tách, Tab 2 Raw JSON có tính năng Copy to clipboard.

- [ ] **Step 1: Tạo layout Drawer trượt từ phải sang với backdrop overlay**
- [ ] **Step 2: Hiển thị thông tin tổng quan sản phẩm (Tên, nguồn, giá, link gốc)**
- [ ] **Step 3: Tab 1: Render bảng thông số kỹ thuật cấu hình dạng Key - Value**
- [ ] **Step 4: Tab 2: Render Raw JSON với highlight và nút Copy JSON kèm feedback state**

---

### Task 5: Xây dựng Component Bảng Dữ liệu Đối thủ (`CompetitorDataTable.tsx`)
**Files:**
- Create: `frontend/src/components/competitor/CompetitorDataTable.tsx`

**Interfaces:**
- Consumes: `items: CrawlResult[]`, `onSelectProduct: (item: CrawlResult) => void`
- Produces: Bảng dữ liệu sản phẩm cào được, phân biệt badge nguồn, giá VND font monospace, nút mở link gốc và nút xem specs.

- [ ] **Step 1: Tạo table header và row rendering theo thiết kế chuẩn Enterprise**
- [ ] **Step 2: Render badge nguồn đối thủ (CellphoneS đỏ, Hoàng Hà cam)**
- [ ] **Step 3: Hiển thị giá và định dạng VND, trạng thái kho**
- [ ] **Step 4: Thao tác: Nút xem specs (gọi `onSelectProduct`) và link bài viết gốc (`ExternalLink`)**
- [ ] **Step 5: Xử lý Empty State khi không có kết quả lọc**

---

### Task 6: Tích hợp Toàn diện Màn hình `CompetitorFeedsPage.tsx`
**Files:**
- Create: `frontend/src/pages/CompetitorFeedsPage.tsx`

**Interfaces:**
- Consumes: `categoryFilter: string`
- Produces: Page component hoàn chỉnh kết hợp Filter, Table, Pagination, Summary Cards và Specs Drawer.

- [ ] **Step 1: Quản lý state dữ liệu, loading, bộ lọc và phân trang**
- [ ] **Step 2: Logic lọc (`useMemo`) theo từ khóa, nguồn, kho hàng, danh mục**
- [ ] **Step 3: Ghép nối các components: `CompetitorSummaryCards`, `CompetitorFilterBar`, `CompetitorDataTable`, `Pagination`, `CompetitorSpecsDrawer`**
- [ ] **Step 4: Nút Refresh dữ liệu tức thì**

---

### Task 7: Đăng ký Điều hướng vào `Sidebar.tsx` và `App.tsx`
**Files:**
- Modify: `frontend/src/components/layout/Sidebar.tsx:13,28-58`
- Modify: `frontend/src/App.tsx:1-45`

**Interfaces:**
- Consumes: `NavTab` type
- Produces: Menu item "Dữ liệu Đối thủ" trên Sidebar kèm badge tổng số lượng bản ghi và định tuyến tab trong `App.tsx`.

- [ ] **Step 1: Thêm `'feeds'` vào `NavTab` trong `Sidebar.tsx`**
- [ ] **Step 2: Thêm nav item vào danh sách điều hướng trong `Sidebar.tsx` với icon `Database`**
- [ ] **Step 3: Đăng ký nhánh render `{activeTab === 'feeds' && <CompetitorFeedsPage ... />}` trong `App.tsx`**

---

### Task 8: Kiểm tra & Xác minh Toàn diện
**Files:**
- Verify: Toàn bộ codebase frontend

- [ ] **Step 1: Chạy kiểm tra TypeScript (`npx tsc --noEmit` hoặc `npm run build` trong `frontend/`)**
- [ ] **Step 2: Xác nhận không còn type error, không còn unused imports**
- [ ] **Step 3: Kiểm tra chuyển đổi Dark Mode / Light Mode và tương tác giữa các tab**
