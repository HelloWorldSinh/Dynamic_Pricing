# BÁO CÁO KIỂM TOÁN GIAO DIỆN & TRẢI NGHIỆM NGƯỜI DÙNG (FRONTEND UI/UX AUDIT)
**Dự án:** Dynamic Pricing System — FPT Retail Analytics  
**Vai trò thực hiện:** Senior Frontend Engineer & UI/UX Specialist  
**Ngày thực hiện:** Tháng 11/2026  
**Phạm vi áp dụng:** Toàn bộ tầng giao diện React (`frontend/src/`)

---

## 1. TỔNG QUAN HIỆN TRẠNG (CURRENT STATE)

### 1.1. Công nghệ & Thư viện Frontend
- **Core Framework:** React 18.3.1 + TypeScript 5.6.3 + Vite 5.4.11.
- **Styling Engine:** Tailwind CSS 3.4.16, PostCSS 8.4.49, Autoprefixer.
- **State & Data Fetching:** `@tanstack/react-query` v5.104.5 (Server State, Caching, Revalidation).
- **Table & Helpers:** `@tanstack/react-table` v8.20.5 (đã cài đặt trong `package.json` nhưng hầu hết các trang vẫn đang render thẻ `<table>` HTML truyền thống thủ công), `clsx`, `tailwind-merge`.
- **Biểu tượng:** `lucide-react` v0.468.0 (đang bị lạm dụng dày đặc trên mọi trang và bảng dữ liệu).
- **Kiến trúc Routing:** Không dùng `react-router-dom`; điều hướng dựa trên Hash Routing thủ công (`window.location.hash`) kết hợp lưu trạng thái vào `localStorage` tại [AppLayout.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/layout/AppLayout.tsx#L8-L30). Quản lý chuyển tab qua cơ chế keep-alive nhẹ (`TabContainer` ẩn/hiện bằng `block` / `hidden`).

---

### 1.2. Danh sách Pages, Routes và Layout

| Tab ID | URL Hash | Tên Màn Hình | Component Đại Diện | Chức Năng Chính |
| :--- | :--- | :--- | :--- | :--- |
| `matrix` | `#matrix` | Price Matrix | [PriceMatrixPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PriceMatrixPage.tsx) | Bảng đối soát giá 3 bên (FPT, CellphoneS, Hoàng Hà), thanh trigger cào dữ liệu, bộ lọc chênh lệch giá, DOH. |
| `approvals` | `#approvals` | Pricing Approvals | [PricingApprovalsPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PricingApprovalsPage.tsx) | Quy trình phê duyệt/từ chối đề xuất giá của AI, xem chi tiết modal tính giá sàn, lịch sử thay đổi giá theo SKU. |
| `mapping` | `#mapping` | SKU Mapping Queue | [SkuMatchingPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/SkuMatchingPage.tsx) | Workspace 2 cột (Master-Detail): Hàng đợi nghi vấn (60%-79%), bảng so sánh thuộc tính sai khác token diff (FPT vs Đối thủ). |
| `feeds` | `#feeds` | Competitor Feeds | [CompetitorFeedsPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/CompetitorFeedsPage.tsx) | Quản lý dữ liệu cào đối thủ thô, thống kê số lượng bản ghi, bộ lọc nguồn cào, drawer thông số kỹ thuật & raw JSON. |
| `crawler` | `#crawler` | Crawl Operations | [CrawlManagerPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/CrawlManagerPage.tsx) | Bảng điều khiển tiến trình Full Pipeline, thẻ tình trạng 3 nguồn cào, lịch trình cronjob tự động, raw data inspector. |
| *Toàn cục* | *N/A* | Global AI Studio | [AiAssistantManager.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/ai/AiAssistantManager.tsx) | Nút bấm nổi FAB chuyển thành cửa sổ Studio 2 cột phân tích giải trình định giá 3 lớp và lịch sử trò chuyện. |

---

### 1.3. Cấu trúc Thư mục & Component Kiến trúc

```text
frontend/src/
├── api/                   # API clients (axios), mock data, endpoints
├── components/
│   ├── ai/                # Trợ lý Copilot: Floating FAB, Studio Drawer, Chat Cards
│   ├── common/            # Component dùng chung: CHỈ CÓ Pagination.tsx và ProductDetailModal.tsx
│   ├── competitor/        # (Tên số ít): CompetitorDataTable, SpecsDrawer, FilterBar, SummaryCards
│   ├── crawler/           # CronSchedulePanel, RawDataInspector, SourceStatusCard
│   ├── layout/            # Navbar.tsx, AppLayout.tsx, Sidebar.tsx (dead code)
│   ├── mapping/           # SkuDetailInspector, SkuQueueList, SkuQueueCard, ConfidenceMeter
│   ├── matrix/            # DebounceTriggerBar, MatrixFilterToolbar, PriceMatrixTable
│   ├── recommendations/   # ApprovalFilterTabs, RecommendationTable, PriceHistoryTable, PricingDetailModal
│   ├── CrawlControlPanel.tsx # Nằm lẻ loi ngoài thư mục gốc components/ (lỗi cấu trúc)
│   └── MatchingReviewTable.tsx # Dead code (lạc hậu, không ai gọi)
├── context/               # ThemeContext.tsx (Dark/Light), AiChatContext.tsx
├── hooks/                 # TanStack Query custom hooks (usePricingQueries, useSkuQueries, useFeedsQueries)
├── types/                 # TypeScript interfaces (pricing, crawl, matching, product, theme)
└── utils/                 # formatters.ts, productSpecParser.ts
```

---

### 1.4. Đánh giá Design System Hiện Tại

1. **Bảng màu (Color Palette):**
   - File cấu hình [tailwind.config.js](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/tailwind.config.js#L10-L23) định nghĩa các token: `brand.fpt: '#F26F21'`, `brand.fpt-dark: '#D9580F'`, `brand.fpt-light: '#FFF5EE'`, cùng cụm `status` (danger, warning, success, info, floor).
   - **Thực tế:** Các trang **gần như không sử dụng** token `brand.fpt` mà hardcode tràn lan các class màu gốc của Tailwind như `bg-orange-600`, `text-orange-600`, `bg-orange-500/10`, `bg-red-600`, `bg-rose-500`, `bg-emerald-600`, `bg-blue-600`, `bg-purple-600`.
   - Các biến CSS trong [index.css](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/index.css#L5-L23) (`--bg-primary`, `--bg-surface`, `--text-primary`) bị bỏ quên, hầu như không component nào tham chiếu.

2. **Typography (Lỗi cấu hình nghiêm trọng):**
   - Font chữ chuẩn: **Plus Jakarta Sans** được nhúng qua Google Fonts tại [index.html](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/index.html#L10).
   - **Lỗi bất thường tại [tailwind.config.js:30](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/tailwind.config.js#L30):** Token `'base'` bị ghi đè thành `['1.25rem', { lineHeight: '1.75rem' }]` (tương đương **20px** thay vì 16px mặc định).
   - **Hậu quả:** Khi một lập trình viên sử dụng `text-base`, cỡ chữ nhảy vọt lên 20px (quá khổ). Để chữa cháy, các component hiện tại lạm dụng vô tội vạ các class cỡ chữ tự phát: `text-[9px]`, `text-[10px]`, `text-[11px]`, `text-xs` (12px), `text-sm` (14px). Không có hệ thống nấc thang typography (Typographic Scale) chặt chẽ.

3. **Khoảng cách (Spacing) & Hình khối (Border Radius):**
   - Border radius bị phân mảnh: `rounded-md`, `rounded-lg`, `rounded-xl`, `rounded-2xl`, `rounded-full` xuất hiện hỗn loạn trong cùng một view mà không theo quy tắc phân cấp cha-con (container > card > button/input > badge).
   - Spacing: Paddings của table cell không đồng bộ (`py-2.5 px-3` ở Crawl, `py-3 px-3` ở Matrix, `py-3.5 px-4` ở Feeds).

4. **Component Tái Sử Dụng (Shared UI Kit):**
   - Dự án **hoàn toàn thiếu vắng** một thư viện component nguyên tử (Atomic / Shared UI Components): không có `Button`, `Input`, `Select`, `Modal`, `Card`, `Badge`, `Table`, `Toast`.
   - Mỗi file màn hình tự viết lại mã HTML thô với hàng chục dòng class Tailwind dài dòng, dẫn đến trùng lặp mã (DRY violation) và cực kỳ khó bảo trì khi cần đổi phong cách.

---

## 2. CHI TIẾT CÁC VẤN ĐỀ UI/UX (UI/UX ISSUES)

### 2.1. Visual Design & Design System

#### Issue VD-01: Lỗi vỡ thang đo Typography do ghi đè `fontSize.base` = 20px
- **Vị trí:** [tailwind.config.js (Dòng 30)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/tailwind.config.js#L30).
- **Mô tả:** `'base': ['1.25rem', { lineHeight: '1.75rem' }]` biến `text-base` thành 20px. Thông thường `text-base` của web tiêu chuẩn là 16px (1rem).
- **Ảnh hưởng:** Các component dùng `text-base` (như tiêu đề card hoặc input giá trong modal) bị phóng đại bất thường. Trái lại, các bảng dữ liệu phải ép dùng `text-[9px]`, `text-[10px]` để nhét vừa thông tin, gây mỏi mắt và vi phạm tiêu chuẩn dễ đọc.
- **Đề xuất:** Khôi phục `base` về chuẩn 16px (`1rem`), thiết lập scale chuẩn: `xs: 12px`, `sm: 13px`, `base: 14px` (chuẩn Enterprise Dashboard), `md: 16px`, `lg: 18px`, `xl: 20px`, `2xl: 24px`.

#### Issue VD-02: Bảng màu không tập trung, phân mảnh token và hardcode tùy tiện
- **Vị trí:** Rải rác trên toàn bộ các file trong `frontend/src/components/`.
- **Mô tả:** Mặc dù đã có token `brand.fpt` (`#F26F21`), code thực tế dùng hỗn hợp `bg-orange-600` (`#ea580c`), `bg-orange-500`, `bg-red-600`, `bg-rose-500`, `bg-emerald-500`, `bg-emerald-600`, `bg-blue-600`, `bg-purple-600`, `bg-pink-500`.
- **Ảnh hưởng:** Giao diện thiếu tính nhận diện thương hiệu nhất quán; khi muốn điều chỉnh theme hoặc chuyển sang chế độ in/dark mode, các mảng màu bị lệch sắc độ.
- **Đề xuất:** Chuẩn hóa CSS Variables tại `index.css` (`--primary`, `--primary-hover`, `--bg-surface`, `--border-subtle`, `--text-main`, `--text-muted`) và ánh xạ đồng bộ sang Tailwind Theme.

#### Issue VD-03: Vi phạm Quy tắc dự án số 9 — Lạm dụng Emoji & Icon trang trí
- **Vị trí:** 
  - [Navbar.tsx (Dòng 30-50)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/layout/Navbar.tsx#L30-L50): Chèn icon vào từng tab menu (`BarChart3`, `CheckCheck`, `GitCompare`, `Database`, `RefreshCw`).
  - [ApprovalFilterTabs.tsx (Dòng 25-46)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/ApprovalFilterTabs.tsx#L25-L46): Chèn `Clock`, `CheckCheck`, `XCircle`, `History` vào tab duyệt.
  - [PriceMatrixTable.tsx (Dòng 171-176)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/matrix/PriceMatrixTable.tsx#L171-L176): Chèn `TrendingUp`, `TrendingDown`, `Equal` vào từng hàng bảng giá.
  - [RecommendationTable.tsx (Dòng 111-118)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/RecommendationTable.tsx#L111-L118): Chèn `ShieldCheck`, `TrendingDown`.
  - [CrawlControlPanel.tsx (Dòng 98-137)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/CrawlControlPanel.tsx#L98-L137): Chèn `Zap`, `Play`, `Check`, `AlertCircle`.
  - [PricingDetailModal.tsx (Dòng 2-13)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/PricingDetailModal.tsx#L2-L13): Nhúng 10 loại icon khác nhau.
- **Mô tả:** Quy tắc cốt lõi của dự án (Rule 9 trong `AGENTS.md`) yêu cầu: *"Tuyệt đối không dùng emoji, icon trang trí trong giao diện. Giữ phong cách tối giản, tinh tế, chuẩn mực doanh nghiệp (enterprise-grade). Sử dụng phân cấp kiểu chữ và màu sắc tinh tế để biểu đạt trạng thái thay vì biểu tượng minh họa."* Hiện tại codebase đang vi phạm điều này trên diện rộng.
- **Ảnh hưởng:** Bảng dữ liệu bị rối rắm về mặt thị giác, giảm tốc độ quét dữ liệu số của chuyên viên tài chính/định giá, tạo cảm giác giao diện "chắp vá" nghiệp dư.
- **Đề xuất:** Triệt tiêu toàn bộ icon trang trí. Chuyển đổi trạng thái bằng Typography (font-weight, uppercase micro-labels) kết hợp viền/nền màu bán trong suốt (Clean Pill Badges). Chỉ giữ lại tối đa các biểu tượng điều hướng chức năng thực sự cần thiết (mũi tên đóng/mở accordion hoặc pagination).

---

### 2.2. Layout & Bố cục Phân cấp Thông tin

#### Issue LO-01: Thanh điều hướng (Navbar) biến mất hoàn toàn trên Mobile
- **Vị trí:** [Navbar.tsx (Dòng 77)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/layout/Navbar.tsx#L77).
- **Mô tả:** Khối `<nav className="hidden md:flex items-center gap-1">` ẩn toàn bộ menu khi màn hình dưới `768px`. Dự án không hề có Mobile Drawer, Hamburger menu hay Bottom Tabbar thay thế.
- **Ảnh hưởng:** Người dùng khi mở ứng dụng trên điện thoại hoặc màn hình dọc hoàn toàn không thể chuyển trang; bị kẹt tại tab mặc định.
- **Đề xuất:** Thêm thanh điều hướng trượt ngang (Horizontal Scrollable Tabs) hoặc Dropdown menu điều hướng tinh gọn cho thiết bị di động.

#### Issue LO-02: Xếp chồng quá nhiều tầng Toolbar trước bảng dữ liệu (Visual Stacking)
- **Vị trí:** [PriceMatrixPage.tsx (Dòng 102-125)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PriceMatrixPage.tsx#L102-L125).
- **Mô tả:** Màn hình xếp liên tiếp 4 khối ngang dày đặc:
  1. Header Top Navbar (64px)
  2. `DebounceTriggerBar` (Thanh tiến độ cào + thời gian + số liệu tổng)
  3. `MatrixFilterToolbar` (Nhóm nút danh mục + Ô tìm kiếm + Dropdown giá + 2 Checkbox DOH/Kho)
  4. Thông báo Revalidation badge
- **Ảnh hưởng:** Chiếm tới hơn 260px chiều cao màn hình trước khi người dùng nhìn thấy dòng dữ liệu đầu tiên. Trên laptop (1366x768 hoặc MacBook 13"), không gian hiển thị bảng bị co hẹp nghiêm trọng, phải cuộn liên tục.
- **Đề xuất:** Gộp `DebounceTriggerBar` và `MatrixFilterToolbar` thành một khối **Unified Action Header** duy nhất (1 tầng tinh gọn), đẩy trạng thái cào và nút kích hoạt vào góc phải cùng dòng với ô tìm kiếm.

#### Issue LO-03: Lỗi vỡ giao diện chia cột (Split View) trên màn hình Tablet/Mobile
- **Vị trí:** [SkuMatchingPage.tsx (Dòng 369-371)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/SkuMatchingPage.tsx#L369-L371).
- **Mô tả:** Layout sử dụng `className="h-[calc(100vh-140px)] min-h-[580px] flex flex-col lg:flex-row gap-3.5 overflow-hidden"`.
- **Ảnh hưởng:** Trên màn hình dưới `1024px` (Tablet / iPad), class `flex-col` kích hoạt xếp cột danh sách lên trên cột chi tiết, nhưng do bị bọc trong `overflow-hidden` và chiều cao cố định, cột chi tiết phía dưới bị đè bẹp hoặc biến mất ngoài khung nhìn, không thể thao tác đối soát.
- **Đề xuất:** Tự động chuyển đổi thành dạng 2 màn hình tuần tự (Master -> Detail) hoặc cho phép cuộn tự nhiên (`overflow-y-auto`, bỏ giới hạn cố định `calc(100vh-140px)`) trên màn hình `< lg`.

---

### 2.3. Trải nghiệm Người dùng (UX & Interaction)

#### Issue UX-01: Nuốt lỗi API âm thầm — Lỗi hệ thống biến thành "Dữ liệu trống" (Silent Failure)
- **Vị trí:** 
  - [PriceMatrixPage.tsx (Dòng 26-29)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PriceMatrixPage.tsx#L26-L29): Không trích xuất `isError`, `error` từ `usePriceMatrixQuery`.
  - [PricingApprovalsPage.tsx (Dòng 30-39)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PricingApprovalsPage.tsx#L30-L39): Tương tự.
  - [SkuMatchingPage.tsx (Dòng 15)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/SkuMatchingPage.tsx#L15): Tương tự.
- **Mô tả:** Khi Backend sập, mất mạng hoặc trả về mã lỗi 500/403, dữ liệu query fallback về mảng rỗng `[]`. Lúc này giao diện thản nhiên hiển thị màn hình Empty State: *"Không tìm thấy sản phẩm nào"* hoặc *"Hàng đợi trống! Toàn bộ SKU đã được xử lý xong"*.
- **Ảnh hưởng:** **Cực kỳ nguy hiểm về mặt nghiệp vụ**. Chuyên viên định giá sẽ hiểu lầm rằng hệ thống đã hoàn tất công việc hoặc không có mặt hàng nào cần duyệt, trong khi thực tế server đang gặp lỗi nghiêm trọng.
- **Đề xuất:** Bổ sung Error State toàn diện: hiển thị banner cảnh báo lỗi đỏ kèm nút *"Thử lại (Retry)"* và chi tiết thông báo lỗi kỹ thuật khi `isError = true`.

#### Issue UX-02: Thiếu hoàn toàn Skeleton Loading — Trải nghiệm giật cục (Layout Shift)
- **Vị trí:** Toàn bộ 5 trang (`PriceMatrixPage`, `PricingApprovalsPage`, `SkuMatchingPage`, `CompetitorFeedsPage`, `CrawlManagerPage`).
- **Mô tả:** Tất cả các trang đều dùng một chuỗi văn bản đơn điệu: `<div className="p-12 text-center text-slate-400 text-xs">Đang nạp dữ liệu...</div>`.
- **Ảnh hưởng:** Khi dữ liệu tải xong (sau 0.5s - 1.5s), toàn bộ cấu trúc bảng và DOM bất ngờ xuất hiện, làm giật cục giao diện (Cumulative Layout Shift), tạo cảm giác ứng dụng chậm chạp và thiếu chuyên nghiệp.
- **Đề xuất:** Xây dựng component `TableSkeleton` (các hàng xung nhịp animation mờ `animate-pulse`) và `CardSkeleton` mô phỏng chính xác khung lưới trước khi dữ liệu đổ về.

#### Issue UX-03: Trạng thái thông báo Toast phân mảnh và thiếu đồng bộ
- **Vị trí:** [SkuMatchingPage.tsx (Dòng 399-414)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/SkuMatchingPage.tsx#L399-L414).
- **Mô tả:** Chỉ duy nhất trang `SkuMatchingPage` tự code một popup Toast thủ công ở góc dưới màn hình. Các thao tác quan trọng ở các trang khác (Duyệt hàng loạt đề xuất giá trong `PricingApprovalsPage`, Kích hoạt cào trong `CrawlManagerPage` hay `PriceMatrixPage`) hoàn toàn không có Toast thông báo kết quả thành công/thất bại.
- **Ảnh hưởng:** Người dùng không nhận được phản hồi hệ thống (System Feedback) sau khi thực hiện thao tác nhạy cảm liên quan đến tài chính.
- **Đề xuất:** Xây dựng `ToastContext` / `ToastProvider` toàn cục, cung cấp hook `useToast()` để gọi `showToast({ title, message, type })` nhất quán trên toàn hệ thống.

#### Issue UX-04: Bộ lọc ngành hàng (Category Filter) bị "đóng băng" tại `PricingApprovalsPage`
- **Vị trí:** [AppLayout.tsx (Dòng 42)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/layout/AppLayout.tsx#L42) và [PricingApprovalsPage.tsx (Dòng 26-28)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PricingApprovalsPage.tsx#L26-L28).
- **Mô tả:** `AppLayout` khai báo `const [categoryFilter] = useState<string>('ALL');` nhưng không có cơ chế nào trong Navbar cho phép thay đổi giá trị này. Trong khi đó, `PricingApprovalsPage` lại nhận `categoryFilter` làm prop từ `AppLayout` và lọc theo biến này, đồng thời trên trang cũng không có nút chọn danh mục (Điện thoại / Laptop).
- **Ảnh hưởng:** Người dùng vào trang Duyệt giá chỉ xem được toàn bộ danh mục mà không thể lọc riêng theo nhóm Điện thoại hay Laptop như ở trang Price Matrix.
- **Đề xuất:** Tích hợp bộ lọc phân nhóm danh mục trực tiếp vào thanh toolbar của `PricingApprovalsPage` tương tự như `MatrixFilterToolbar`.

#### Issue UX-05: Dữ liệu fallback bị lỗi hiển thị chuỗi 'error' và hardcode số liệu giả
- **Vị trí:** [DebounceTriggerBar.tsx (Dòng 239, 255, 285, 290)](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/matrix/DebounceTriggerBar.tsx#L239).
- **Mô tả:** 
  ```tsx
  {matchingStats ? `${matchingStats.matched_skus}/${matchingStats.total_skus}` : 'error'}
  {matchingStats ? `${matchingStats.match_rate}%` : 'error'}
  lastUpdated ? formatTimestamp(lastUpdated) : '10:15 14/10/2026'
  ```
- **Ảnh hưởng:** Nếu API thống kê chưa phản hồi hoặc trả về null, chữ `'error'` thô thiển hiển thị thẳng lên màn hình chính của người dùng. Ngày giờ và số liệu SP cào cũng hiển thị ngày tháng tĩnh của năm 2026 gây hoang mang.
- **Đề xuất:** Dùng placeholder tinh tế (`—/—` hoặc thanh skeleton mini) thay vì hiển thị chữ `'error'`.

---

### 2.4. Khả năng Tiếp cận (Accessibility - A11y)

#### Issue A11Y-01: Độ tương phản màu sắc không đạt chuẩn WCAG 2.1 AA (Contrast Failures)
- **Vị trí:** Hầu hết các nhãn phụ, ngày tháng, thông số SKU dùng `text-slate-400` (#94a3b8) trên nền trắng (#ffffff).
- **Mô tả:** Tỉ lệ tương phản của `#94a3b8` trên nền `#ffffff` chỉ đạt **2.5:1** (tiêu chuẩn tối thiểu của WCAG AA là **4.5:1** đối với văn bản thông thường).
- **Tương tự trong Dark Mode:** `text-slate-500` (#64748b) trên nền `bg-slate-900` (#0f172a) chỉ đạt **3.1:1** (thất bại).
- **Ảnh hưởng:** Chữ quá mờ, người dùng làm việc trong môi trường ánh sáng mạnh hoặc người có thị lực kém không thể đọc được mã part, ngày cào, dung lượng tồn kho.
- **Đề xuất:** Nâng cấp các text phụ lên tối thiểu `text-slate-600` ở Light Mode (đạt 5.7:1) và `text-slate-400` ở Dark Mode (đạt 5.2:1).

#### Issue A11Y-02: Thiếu nhãn ARIA trên các nút bấm biểu tượng và hộp kiểm (Checkboxes)
- **Vị trí:**
  - Checkbox chọn sản phẩm trong [RecommendationTable.tsx:44-49](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/RecommendationTable.tsx#L44-L49), [SkuQueueCard.tsx:57-63](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/mapping/SkuQueueCard.tsx#L57-L63).
  - Nút đóng modal `X` trong [PricingDetailModal.tsx:203](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/PricingDetailModal.tsx#L203), [ProductDetailModal.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/common/ProductDetailModal.tsx).
- **Mô tả:** Các thẻ `<input type="checkbox">` và `<button>` không có thuộc tính `aria-label` hoặc `<label>` tương ứng.
- **Ảnh hưởng:** Các thiết bị hỗ trợ khiếm thị (Screen Readers) chỉ đọc "checkbox unchecked" hoặc "button" mà không thể giải thích cho người dùng biết thao tác này chọn sản phẩm nào hay đóng cửa sổ gì.
- **Đề xuất:** Bổ sung `aria-label="Chọn sản phẩm [Mã SKU]"` và `aria-label="Đóng cửa sổ"`.

#### Issue A11Y-03: Modal Dialogs thiếu quản lý tiêu điểm bàn phím (Focus Trap & ARIA Roles)
- **Vị trí:** [PricingDetailModal.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/PricingDetailModal.tsx#L176), [ProductDetailModal.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/common/ProductDetailModal.tsx).
- **Mô tả:** Cửa sổ Modal hiển thị dưới dạng thẻ `<div>` thông thường, thiếu `role="dialog"`, `aria-modal="true"` và không khóa tiêu điểm bàn phím (Focus Trap).
- **Ảnh hưởng:** Người dùng bấm phím `Tab` trên bàn phím có thể vô tình focus vào các nút bấm ẩn phía sau lớp backdrop của trang chính, làm mất phương hướng.
- **Đề xuất:** Chuẩn hóa Modal Component với `role="dialog"`, tự động focus vào nút đầu tiên khi mở, khôi phục focus khi đóng và khóa phím Tab bên trong modal.

---

### 2.5. Trực quan hóa Dữ liệu (Data Visualization) & Trình bày Bảng

#### Issue DV-01: Bảng dữ liệu (Tables) thiếu thuộc tính cố định cột & tiêu đề (Sticky Headers)
- **Vị trí:** [PriceMatrixTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/matrix/PriceMatrixTable.tsx#L38), [RecommendationTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/RecommendationTable.tsx#L39), [CompetitorDataTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/competitor/CompetitorDataTable.tsx).
- **Mô tả:** Các bảng dữ liệu dài hơn 10-20 dòng không có `sticky top-0` cho hàng `<thead>` và không cố định cột Tên sản phẩm / SKU bên trái khi cuộn ngang trên màn hình vừa.
- **Ảnh hưởng:** Khi người dùng cuộn chuột xuống dòng thứ 8-10, tiêu đề cột biến mất, rất khó phân biệt giữa cột giá CellphoneS và Hoàng Hà nếu chỉ nhìn vào con số.
- **Đề xuất:** Bổ sung `sticky top-0 bg-white dark:bg-slate-900 z-10 shadow-xs` cho `<thead>` và hỗ trợ fixed column cho cột SKU đầu tiên.

#### Issue DV-02: Lịch sử giá thiếu đồ thị xu hướng (Sparkline / Trend Chart)
- **Vị trí:** [ProductPriceHistoryModal.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/ProductPriceHistoryModal.tsx#L130-L240).
- **Mô tả:** Lịch sử biến động giá của một mặt hàng được biểu diễn thuần túy bằng danh sách các card dọc nối nhau qua đường kẻ timeline.
- **Ảnh hưởng:** Chuyên viên giá phải tự đọc từng con số và tính nhẩm trong đầu để hình dung xu hướng (tăng hay giảm, biên độ dốc hay phẳng).
- **Đề xuất:** Bổ sung một mini SVG Sparkline (biểu đồ đường sóng siêu nhẹ thuần SVG, không cần cài thêm thư viện nặng) ở đầu modal để trực quan hóa quỹ đạo giá từ ban đầu tới hiện tại.

---

### 2.6. Mã Nguồn Rác & Kiến trúc Codebase (Code Hygiene)

#### Issue CH-01: Tồn tại 2 Component chết (Dead / Orphaned Components)
- **Vị trí:**
  1. [frontend/src/components/MatchingReviewTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/MatchingReviewTable.tsx): File cũ từ các phiên bản đầu, sử dụng style nội dòng với các biến CSS không tồn tại (`var(--color-bg-surface)`). Hoàn toàn không có bất kỳ file nào trong dự án import nó.
  2. [frontend/src/components/layout/Sidebar.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/layout/Sidebar.tsx): Cụm Sidebar thu gọn cũ, dự án đã chuyển hẳn sang dùng `Navbar.tsx` dạng ngang trong `AppLayout.tsx`. File này không còn được sử dụng.
- **Ảnh hưởng:** Gây nhiễu khi tìm kiếm mã nguồn (CodeGraph/Grep), tốn dung lượng bundle và gây hiểu lầm cho các kỹ sư mới tiếp cận dự án.
- **Đề xuất:** Đưa vào danh sách dọn dẹp (loại bỏ an toàn) trong giai đoạn refactor.

#### Issue CH-02: Cấu trúc thư mục chưa nhất quán (Inconsistent Directory Structure)
- **Vị trí:**
  - File [CrawlControlPanel.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/CrawlControlPanel.tsx) nằm trơ trọi tại `components/` thay vì gom vào `components/crawler/`.
  - Thư mục [components/competitor/](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/competitor/) đặt tên số ít, trong khi trang chính là [CompetitorFeedsPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/CompetitorFeedsPage.tsx) (số nhiều).
- **Đề xuất:** Di chuyển `CrawlControlPanel.tsx` vào đúng thư mục `components/crawler/` và đồng bộ quy ước đặt tên thư mục theo tính năng.

---

## 3. PHÂN LOẠI MỨC ĐỘ ƯU TIÊN (PRIORITY MATRIX)

```mermaid
quadrantChart
    title Ma Trận Phân Loại Mức Độ Ưu Tiên Xử Lý UI/UX
    x-axis Độ Khó Thực Hiện Thấp --> Độ Khó Thực Hiện Cao
    y-axis Mức Độ Ảnh Hưởng Thấp --> Mức Độ Ảnh Hưởng Cao
    quadrant-1 Triển Khai Chiến Lược (Strategic)
    quadrant-2 Ưu Tiên Hàng Đầu (Quick Wins / Critical)
    quadrant-3 Cải Tiến Thẩm Mỹ (Low Priority)
    quadrant-4 Tối Ưu Hóa Tiếp Theo (Medium Priority)
    "VD-01: Lỗi font base 20px": [0.15, 0.95]
    "UX-01: Nuốt lỗi API (Silent Fail)": [0.25, 0.90]
    "LO-01: Navbar mất trên Mobile": [0.35, 0.85]
    "VD-03: Lạm dụng Lucide Icon (Rule 9)": [0.55, 0.80]
    "UX-02: Thiếu Skeleton Loading": [0.40, 0.75]
    "LO-02: 4 tầng Toolbar đè bảng": [0.45, 0.70]
    "A11Y-01: Lỗi tương phản màu": [0.20, 0.65]
    "UX-03: Toast phân mảnh": [0.30, 0.60]
    "DV-01: Bảng thiếu Sticky Header": [0.25, 0.55]
    "CH-01: Xóa Dead Code Sidebar/Table": [0.10, 0.45]
    "DV-02: Mini Sparkline giá": [0.60, 0.40]
```

### Danh mục Ưu tiên Chi tiết:

| Nhóm Ưu Tiên | Mã Vấn Đề | Vị Trí File | Tóm Tắt Vấn Đề |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | **VD-01** | `tailwind.config.js` | Ghi đè `base: 20px` làm hỏng scale chữ toàn hệ thống. |
| **CRITICAL** | **UX-01** | `PriceMatrixPage`, `PricingApprovalsPage`, `SkuMatchingPage` | Nuốt lỗi API khiến lỗi server hiển thị thành "không có dữ liệu". |
| **CRITICAL** | **LO-01** | `Navbar.tsx` | Menu biến mất hoàn toàn trên mobile (`hidden md:flex`). |
| **CRITICAL** | **LO-03** | `SkuMatchingPage.tsx` | Layout chia 2 cột bị kẹt/cắt trên màn hình Tablet/Mobile. |
| **HIGH** | **VD-03** | Toàn bộ codebase | Vi phạm Rule 9: Lạm dụng icon Lucide dày đặc, thiếu tinh tế. |
| **HIGH** | **UX-02** | Toàn bộ các Page | Thiếu Skeleton Loading, text loading đơn điệu gây giật màn hình. |
| **HIGH** | **LO-02** | `PriceMatrixPage.tsx` | Xếp chồng 4 tầng toolbar chiếm hết không gian dữ liệu. |
| **HIGH** | **UX-04** | `AppLayout.tsx`, `PricingApprovalsPage.tsx` | Bộ lọc ngành hàng bị khoá cứng `ALL` trên trang Duyệt giá. |
| **HIGH** | **UX-03** | `SkuMatchingPage.tsx` | Thiếu hệ thống Toast thông báo toàn cục sau các tác vụ nhạy cảm. |
| **MEDIUM** | **A11Y-01** | Toàn bộ bảng dữ liệu | Màu `slate-400` trên nền trắng không đạt chuẩn tương phản WCAG AA. |
| **MEDIUM** | **DV-01** | Các bảng dữ liệu | Thiếu `sticky top-0` cho Header khi cuộn bảng danh sách dài. |
| **MEDIUM** | **A11Y-03** | `PricingDetailModal.tsx` | Modal thiếu ARIA attributes và cơ chế Focus Trap. |
| **MEDIUM** | **CH-01** | `Sidebar.tsx`, `MatchingReviewTable.tsx` | 2 component dead code không sử dụng. |
| **LOW** | **UX-05** | `DebounceTriggerBar.tsx` | Dữ liệu fallback hiển thị chuỗi `'error'` và số liệu hardcode. |
| **LOW** | **DV-02** | `ProductPriceHistoryModal.tsx` | Bổ sung SVG Sparkline trực quan hóa quỹ đạo giá. |
| **LOW** | **CH-02** | `components/` | Đồng bộ cấu trúc thư mục `crawler/` và `competitor/`. |

---

## 4. ĐỀ XUẤT THIẾT KẾ LẠI (REDESIGN PROPOSAL)

### 4.1. Định hướng Phong cách: Modern Enterprise Data-Dense UI
Tuân thủ nghiêm ngặt **Quy tắc dự án số 9** và triết lý từ skill `frontend-design`:
- **Nghiêm cấm tuyệt đối Emoji & Icon trang trí:** Loại bỏ biểu tượng hoa mỹ. Sử dụng vẻ đẹp của kiểu chữ (Typography Hierarchy), độ co giãn khoảng trắng (Whitespace Rhythm) và các đường viền hairline tinh xảo để dẫn dắt thị giác.
- **Thiết kế tập trung vào mật độ dữ liệu (Data Density):** Chuyên viên phân tích giá cần bao quát nhiều thông số trên 1 màn hình mà không bị choáng ngợp.
- **Ngôn ngữ màu sắc tinh tế (Subtle Semantic Color Coding):** Dùng nền màu nhạt pha độ mờ (`alpha 10% - 15%`) kết hợp viền bán trong suốt để làm nổi bật trạng thái thay vì đổ các khối màu đặc chói lọi.

---

### 4.2. Hệ thống Design Tokens Đề Xuất

#### Bảng Màu Chuẩn (Semantic Color Palette)

```css
/* Light Mode Tokens */
--surface-canvas:      #f8fafc;  /* slate-50: Nền tổng thể trang */
--surface-card:        #ffffff;  /* Trắng tinh: Nền card/bảng */
--surface-hover:       #f1f5f9;  /* slate-100: Hover nhẹ */
--surface-subtle:      #f8fafc;  /* Nền toolbar / thead */

--border-subtle:       #e2e8f0;  /* slate-200: Viền hairline thanh lịch */
--border-focus:        #ea580c;  /* orange-600: Viền tiêu điểm thương hiệu FPT */

--text-primary:        #0f172a;  /* slate-900: Chữ tiêu đề, giá tiền */
--text-secondary:      #334155;  /* slate-700: Nhãn, nội dung chính */
--text-muted:          #64748b;  /* slate-500: Chữ phụ (đạt chuẩn WCAG 4.5:1) */

--brand-fpt:           #ea580c;  /* FPT Orange chuẩn nhận diện */
--brand-fpt-soft:      #fff7ed;  /* Nền cam nhạt 10% */

--status-success:      #059669;  /* emerald-600 */
--status-success-bg:   #ecfdf5;  /* emerald-50 */
--status-danger:       #dc2626;  /* red-600 */
--status-danger-bg:    #fef2f2;  /* red-50 */
--status-warning:      #d97706;  /* amber-600 */
--status-warning-bg:   #fffbeb;  /* amber-50 */
--status-info:         #2563eb;  /* blue-600 */
--status-info-bg:      #eff6ff;  /* blue-50 */
--status-floor:        #db2777;  /* pink-600 (Bảo vệ giá sàn) */
--status-floor-bg:     #fdf2f8;  /* pink-50 */
```

#### Thang Đo Typography Chuẩn (Chuẩn hóa `tailwind.config.js`)

```javascript
// Cấu hình fontSize chuẩn thay thế cho file tailwind.config.js
fontSize: {
  '2xs':  ['0.6875rem', { lineHeight: '0.875rem' }], // 11px (Micro badge, part number)
  'xs':   ['0.75rem',   { lineHeight: '1rem' }],      // 12px (Table secondary data)
  'sm':   ['0.8125rem', { lineHeight: '1.125rem' }], // 13px (Table primary text, inputs)
  'base': ['0.875rem',  { lineHeight: '1.25rem' }],   // 14px (Standard Body Text)
  'md':   ['1rem',      { lineHeight: '1.5rem' }],     // 16px (Card titles, large buttons)
  'lg':   ['1.125rem',  { lineHeight: '1.625rem' }],  // 18px (Section titles)
  'xl':   ['1.25rem',   { lineHeight: '1.75rem' }],   // 20px (Modal titles)
  '2xl':  ['1.5rem',    { lineHeight: '2rem' }],      // 24px (Page main headings)
}
```

---

### 4.3. Đề xuất Tái Cấu Trúc Bố Cục (Layout Architecture)

```
+---------------------------------------------------------------------------------------+
| TOP NAVBAR (Sticky h-14): FPT Retail Analytics | [Tabs: Matrix | Approvals | Mapping | Feeds | Ops] | Theme | User |
+---------------------------------------------------------------------------------------+
| MAIN CONTAINER (max-w-screen-2xl px-6 py-4):                                          |
|                                                                                       |
| +-[ UNIFIED TOOLBAR: 1 DÒNG DUY NHẤT ]----------------------------------------------+ |
| | [Danh mục: Tất cả | ĐT | Laptop]  [ Ô tìm kiếm SKU... ] [ Bộ lọc giá ] [ Kho ]   | |
| |                                     (Phải): Cập nhật: 10:15 | [ Nút: Cào dữ liệu ]| |
| +-----------------------------------------------------------------------------------+ |
|                                                                                       |
| +-[ DATA WORKBENCH (Table / Split-view) ]--------------------------------------------+ |
| | (Sticky Header Thead) Sản phẩm | Giá FPT | CellphoneS | Hoàng Hà | Chênh lệch | Đ.Cậy| |
| | [Skeleton Loading khi đang nạp]                                                    | |
| | Dòng 1: iPhone 16 Pro Max 256GB   | 31.990.000 | 31.490.000 | 31.390.000 | +1.9% | 100% | |
| | Dòng 2: Asus Vivobook 15          | 16.490.000 | 16.890.000 | 16.790.000 | -1.8% | 85%  | |
| +-----------------------------------------------------------------------------------+ |
| | PHÂN TRANG (Pagination: 1-10 của 329 bản ghi | Số dòng: 10, 20, 50)                 | |
+---------------------------------------------------------------------------------------+
```

---

### 4.4. Bộ Thư Viện Thành Phần Dùng Chung Cần Xây Dựng (Shared Component Kit)

Để chấm dứt tình trạng trùng lặp mã và thiếu nhất quán, cần xây dựng các thành phần nền tảng đặt tại `frontend/src/components/common/`:

1. **`Button`:** Hỗ trợ các biến thể chuẩn (`primary`, `secondary`, `destructive`, `ghost`), các kích thước (`sm`, `md`), trạng thái loading tích hợp mà không cần chèn icon rác.
2. **`Input` & `Select`:** Thiết kế viền hairline `border-slate-200`, focus ring `ring-1 ring-orange-500`, tích hợp nhãn trợ năng ARIA ngầm định.
3. **`Badge` (Thẻ trạng thái chuẩn Rule 9):**
   - Không chứa icon.
   - Định dạng text đậm, nền màu nhạt có độ mờ (`bg-emerald-50 text-emerald-700 border-emerald-200`).
   - Các biến thể: `success` (Đã duyệt / Còn hàng), `warning` (Chờ duyệt / Chênh lệch thấp), `danger` (Từ chối / Chênh lệch cao), `floor` (Chạm sàn), `neutral` (SKU / Part Number).
4. **`TableSkeleton`:** Bộ khung giả lập hiệu ứng sóng mờ (`animate-pulse`) hiển thị 5-10 dòng trước khi dữ liệu xuất hiện.
5. **`EmptyState` & `ErrorBanner`:** Thông báo dữ liệu trống có CTA xoá bộ lọc, và Banner báo lỗi API kèm nút Thử lại (Retry).
6. **`Modal` (Accessible Dialog Wrapper):** Bọc sẵn logic backdrop, phím ESC, `role="dialog"`, khóa tiêu điểm Tab và `aria-modal="true"`.
7. **`Toast` (Hệ thống thông báo toàn cục):** Quản lý qua React Context, thông báo mượt mà ở góc phải dưới mà không cần tự viết state trong từng màn hình.

---

## 5. LỘ TRÌNH THỰC THI CHI TIẾT (IMPLEMENTATION ROADMAP)

Quá trình redesign được phân tách thành **4 giai đoạn tuần tự**, đảm bảo không làm gián đoạn API hay thay đổi logic tính toán nghiệp vụ:

### Giai đoạn 1: Chuẩn hóa Design System & Dọn dẹp Mã Rác (Foundation & Cleanup)
- **Mục tiêu:** Sửa tận gốc cấu hình Tailwind, thiết lập bộ CSS Variables chuẩn và loại bỏ dead code.
- **Phạm vi tác động:**
  - Sửa `frontend/tailwind.config.js`: Khôi phục `fontSize.base` = 14px/16px, định nghĩa lại bảng token `fontSize` và `colors`.
  - Cập nhật `frontend/src/index.css`: Khai báo bảng biến CSS semantic chuẩn cho cả Light Mode và Dark Mode.
  - Xóa bỏ an toàn 2 file dead code: `frontend/src/components/MatchingReviewTable.tsx` và `frontend/src/components/layout/Sidebar.tsx`.
  - Di chuyển `frontend/src/components/CrawlControlPanel.tsx` vào `frontend/src/components/crawler/`.

### Giai đoạn 2: Xây dựng Bộ UI Kit Dùng Chung & Trợ Năng (Shared Atomic Kit & A11y)
- **Mục tiêu:** Xây dựng các component nguyên tử dùng chung đạt chuẩn Rule 9 (không icon rác, tương phản WCAG AA).
- **Phạm vi tạo mới/cập nhật:**
  - `frontend/src/components/common/Button.tsx`
  - `frontend/src/components/common/Badge.tsx`
  - `frontend/src/components/common/Input.tsx`
  - `frontend/src/components/common/TableSkeleton.tsx`
  - `frontend/src/components/common/Modal.tsx`
  - `frontend/src/context/ToastContext.tsx` & `frontend/src/components/common/ToastContainer.tsx`

### Giai đoạn 3: Tái thiết Kế Bố Cục Trang & Tinh Gọn Thanh Điều Hướng (Layout & Header Redesign)
- **Mục tiêu:** Giải quyết lỗi vỡ giao diện trên Mobile/Tablet và tinh giản thanh công cụ.
- **Phạm vi tác động:**
  - `frontend/src/components/layout/Navbar.tsx`: Bổ sung menu trượt ngang/dropdown trên mobile thay vì ẩn hoàn toàn (`hidden md:flex`). Loại bỏ các Lucide icon trong tabs.
  - `frontend/src/components/layout/AppLayout.tsx`: Đưa logic quản lý `categoryFilter` và `toast` thành context toàn cục.
  - `frontend/src/pages/PriceMatrixPage.tsx` & `DebounceTriggerBar.tsx` & `MatrixFilterToolbar.tsx`: Gộp 2 thanh bar thành 1 hàng **Unified Filter Toolbar** duy nhất. Bổ sung Error State khi API lỗi.

### Giai đoạn 4: Redesign Toàn Diện Từng Màn Hình Nghiệp Vụ (Page-by-Page Polish)
- **Mục tiêu:** Áp dụng UI Kit mới, thay thế toàn bộ icon rác bằng typography/badge tinh tế, thêm Sticky Headers cho bảng.
- **Phạm vi tác động:**
  - **Màn hình 1 (Price Matrix):** [PriceMatrixTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/matrix/PriceMatrixTable.tsx) — Sticky header, loại bỏ icon tăng/giảm giá, đổi sang pill badge màu sắc thanh lịch.
  - **Màn hình 2 (Pricing Approvals):** [PricingApprovalsPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PricingApprovalsPage.tsx), [RecommendationTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/RecommendationTable.tsx), [PricingDetailModal.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/PricingDetailModal.tsx) — Thêm bộ lọc danh mục trực tiếp, loại bỏ icon trong tab duyệt và bảng, làm sạch modal định vị giá.
  - **Màn hình 3 (SKU Matching Queue):** [SkuMatchingPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/SkuMatchingPage.tsx), [SkuDetailInspector.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/mapping/SkuDetailInspector.tsx) — Tối ưu layout cuộn mượt mà trên màn hình nhỏ/tablet, tinh chỉnh bảng token diff.
  - **Màn hình 4 (Competitor Feeds):** [CompetitorFeedsPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/CompetitorFeedsPage.tsx), [CompetitorDataTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/competitor/CompetitorDataTable.tsx) — Bổ sung Skeleton loading và Sticky header.
  - **Màn hình 5 (Crawl Operations):** [CrawlManagerPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/CrawlManagerPage.tsx), [CronSchedulePanel.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/crawler/CronSchedulePanel.tsx) — Dọn sạch icon minh họa, dùng typographic status tags.

---

## 6. KẾT LUẬN & ĐỀ NGHỊ

Báo cáo kiểm toán này đã nhận diện đầy đủ các "điểm nghẽn" thị giác và cấu trúc kỹ thuật của hệ thống Frontend hiện tại:
1. **Lỗi nghiêm trọng nhất:** Scale chữ `base: 20px` làm lệch lạc thẩm mỹ; nuốt lỗi API gây rủi ro phán đoán sai lệch nghiệp vụ; và giao diện bị cô lập hoàn toàn trên màn hình Mobile.
2. **Vi phạm tiêu chuẩn thiết kế:** Tình trạng lạm dụng hàng trăm icon trang trí vi phạm trực tiếp Quy tắc dự án số 9.
3. **Thiếu thốn hạ tầng:** Chưa có Shared Component Kit dẫn đến việc code trùng lặp và không có Skeleton loading.

Báo cáo này được bảo toàn dưới dạng kiểm toán thuần túy — **chưa có bất kỳ dòng code nào bị sửa đổi hay xóa bỏ**. Kính trình Quản lý Dự án và Lập trình viên xem xét, phê duyệt định hướng trên để bắt đầu triển khai Giai đoạn 1 của kế hoạch Redesign.

