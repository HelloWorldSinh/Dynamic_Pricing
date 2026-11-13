# KẾ HOẠCH TỔNG THỂ THIẾT KẾ LẠI GIAO DIỆN (FRONTEND REDESIGN PLAN)

> **Dự án:** Dynamic Pricing System — FPT Retail Analytics  
> **Căn cứ:** Báo cáo kiểm toán [FRONTEND_UI_AUDIT.md](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/FRONTEND_UI_AUDIT.md)  
> **Định hướng:** Modern Enterprise SaaS UI — Tối giản, Chuyên nghiệp, Tối ưu Mật độ Dữ liệu  
> **Nguyên tắc kỹ thuật:** Tuân thủ tuyệt đối **Quy tắc dự án số 9** (Không emoji & icon trang trí), tận dụng stack hiện có (React 18 + Tailwind CSS + TanStack Query), zero-bundle bloat.

---

## 1. ĐỊNH HƯỚNG THIẾT KẾ THỐNG NHẤT (UNIFIED DESIGN DIRECTION)

### 1.1. Triết lý Thiết kế: "Data-Dense, Content-First, Zero-Clutter"
Hệ thống Dynamic Pricing là một công cụ phân tích và ra quyết định tài chính quan trọng của FPT Retail. Người dùng trực tiếp là các chuyên viên định giá (Pricing Analysts) và nhà quản lý bán lẻ, những người cần theo dõi hàng trăm biến động giá, tỷ lệ tồn kho (DOH) và tín hiệu đối thủ trong thời gian thực.

- **Content-First (Ưu tiên Nội dung):** Mọi pixel trên màn hình phải phục vụ việc đọc hiểu dữ liệu số và trạng thái. Cắt bỏ hoàn toàn các thành phần trang trí không mang giá trị thông tin.
- **Tuân thủ Quy tắc số 9 (Strict Typography & Semantic Color Coding):**
  - Tuyệt đối không dùng emoji, icon trang trí rác trên nhãn, nút bấm, menu, badge và bảng số liệu.
  - Sử dụng **phân cấp kiểu chữ (Typographic Hierarchy)** và **mã màu bán trong suốt (Subtle Color Coding)** để diễn đạt trạng thái:
    - Trạng thái tích cực: Nền ngọc bích nhạt 10% + chữ ngọc bích đậm (`bg-emerald-50 text-emerald-700 border-emerald-200`).
    - Trạng thái rủi ro/chênh lệch cao: Nền đỏ nhạt 10% + chữ đỏ thẫm (`bg-rose-50 text-rose-700 border-rose-200`).
    - Trạng thái chờ/nghi vấn: Nền hổ phách nhạt 10% + chữ hổ phách đậm (`bg-amber-50 text-amber-700 border-amber-200`).
    - Giá chạm sàn: Nền cánh sen nhạt + chữ cánh sen (`bg-pink-50 text-pink-700 border-pink-200`).
  - Sử dụng phông chữ đơn cách (**Monospace**) cho toàn bộ số tiền, phần trăm và mã SKU để các cột số luôn thẳng hàng thẳng cột, giúp đối soát thị giác tức thì.
- **Tối ưu Chiều cao Khung nhìn (Vertical Real Estate):** Gom các thanh công cụ, lọc, thống kê rời rạc thành một thanh **Unified Action Bar** duy nhất (1 dòng), đảm bảo người dùng nhìn thấy ít nhất 12-15 dòng dữ liệu ngay khi mở trang mà không cần cuộn.

---

## 2. HỆ THỐNG DESIGN TOKENS CHI TIẾT (DESIGN TOKENS SPECIFICATION)

### 2.1. Colors (Bảng màu Chuẩn hóa)

Hệ thống màu được quản lý qua CSS Custom Properties tại `frontend/src/index.css` và ánh xạ trực tiếp sang `frontend/tailwind.config.js`:

```css
/* ==========================================================================
   DESIGN TOKENS - LIGHT MODE (Mặc định)
   ========================================================================== */
:root {
  /* Canvas & Surfaces */
  --surface-canvas:        #f8fafc; /* slate-50: Nền tổng thể ứng dụng */
  --surface-card:          #ffffff; /* Trắng tinh: Nền bảng, card, modal */
  --surface-subtle:        #f1f5f9; /* slate-100: Nền hàng bảng xen kẽ, toolbar */
  --surface-hover:         #f8fafc; /* slate-50: Trạng thái hover nhẹ của hàng */
  --surface-active:        #fff7ed; /* orange-50: Hàng được chọn (FPT tint) */

  /* Borders & Dividers */
  --border-subtle:         #e2e8f0; /* slate-200: Viền hairline phân tách */
  --border-strong:         #cbd5e1; /* slate-300: Viền input, controls */
  --border-focus:          #ea580c; /* orange-600: Viền tiêu điểm bàn phím */

  /* Typography / Text */
  --text-primary:          #0f172a; /* slate-900: Tiêu đề, số tiền chính (Contrast 15.8:1) */
  --text-secondary:        #334155; /* slate-700: Nhãn, nội dung chính (Contrast 9.6:1) */
  --text-muted:            #64748b; /* slate-500: Nhãn phụ, timestamp (Contrast 4.6:1 - WCAG AA pass) */

  /* Brand FPT */
  --brand-primary:         #ea580c; /* FPT Orange chuẩn nhận diện */
  --brand-hover:           #c2410c; /* orange-700 */
  --brand-soft:            #fff7ed; /* orange-50 (alpha ~10%) */
  --brand-border:          #fed7aa; /* orange-200 */

  /* Semantic Status: Success (Duyệt, Còn hàng, Khớp 100%) */
  --status-success-text:   #065f46; /* emerald-800 */
  --status-success-bg:     #ecfdf5; /* emerald-50 */
  --status-success-border: #a7f3d0; /* emerald-200 */

  /* Semantic Status: Warning (Chờ duyệt, Chênh lệch 2-5%, Nghi vấn 60-79%) */
  --status-warning-text:   #92400e; /* amber-800 */
  --status-warning-bg:     #fffbeb; /* amber-50 */
  --status-warning-border: #fde68a; /* amber-200 */

  /* Semantic Status: Danger (Từ chối, Chênh lệch >=5%, Lỗi hệ thống, Hết hàng) */
  --status-danger-text:    #991b1b; /* red-800 */
  --status-danger-bg:      #fef2f2; /* red-50 */
  --status-danger-border:  #fecaca; /* red-200 */

  /* Semantic Status: Floor Cap (Bảo vệ giá sàn vốn + 5%) */
  --status-floor-text:     #9d174d; /* pink-800 */
  --status-floor-bg:       #fdf2f8; /* pink-50 */
  --status-floor-border:   #fbcfe8; /* pink-200 */

  /* Semantic Status: AI / Informational */
  --status-info-text:      #1e40af; /* blue-800 */
  --status-info-bg:        #eff6ff; /* blue-50 */
  --status-info-border:    #bfdbfe; /* blue-200 */
}

/* ==========================================================================
   DESIGN TOKENS - DARK MODE (.dark)
   ========================================================================== */
.dark {
  --surface-canvas:        #090d16; /* Slate sâu gần đen */
  --surface-card:          #0f172a; /* slate-900: Nền thẻ, bảng */
  --surface-subtle:        #1e293b; /* slate-800: Toolbar, header bảng */
  --surface-hover:         #1e293b; /* slate-800: Hover hàng */
  --surface-active:        #2d1b0d; /* Cam mờ sâu */

  --border-subtle:         #1e293b; /* slate-800 */
  --border-strong:         #334155; /* slate-700 */
  --border-focus:          #f97316; /* orange-500 */

  --text-primary:          #f8fafc; /* slate-50: Contrast 16.1:1 */
  --text-secondary:        #cbd5e1; /* slate-300: Contrast 9.8:1 */
  --text-muted:            #94a3b8; /* slate-400: Contrast 5.2:1 - WCAG AA pass */

  --brand-primary:         #f97316; /* orange-500 sáng cho Dark */
  --brand-hover:           #ea580c;
  --brand-soft:            #431407; /* Cam mờ đậm */
  --brand-border:          #7c2d12;

  --status-success-text:   #6ee7b7; /* emerald-300 */
  --status-success-bg:     #064e3b; /* emerald-950/60 */
  --status-success-border: #047857;

  --status-warning-text:   #fcd34d; /* amber-300 */
  --status-warning-bg:     #78350f; /* amber-950/60 */
  --status-warning-border: #b45309;

  --status-danger-text:    #fca5a5; /* red-300 */
  --status-danger-bg:      #7f1d1d; /* red-950/60 */
  --status-danger-border:  #b91c1c;

  --status-floor-text:     #f472b6; /* pink-400 */
  --status-floor-bg:       #831843;
  --status-floor-border:   #be185d;

  --status-info-text:      #93c5fd; /* blue-300 */
  --status-info-bg:        #1e3a8a;
  --status-info-border:    #1d4ed8;
}
```

---

### 2.2. Typography (Sửa Triệt để Lỗi Cấu hình và Thống nhất Thang đo)

**Cấu hình sửa đổi trong `frontend/tailwind.config.js`:**
Khắc phục lỗi `'base': ['1.25rem']` (20px) hiện tại. Thiết lập thang đo 8 bậc chuẩn mực quốc tế cho SaaS Dashboard:

```javascript
// tailwind.config.js (Bản sửa đổi đề xuất)
fontFamily: {
  sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
  mono: ['"JetBrains Mono"', '"Fira Code"', 'ui-monospace', 'monospace'],
},
fontSize: {
  '2xs':  ['0.6875rem', { lineHeight: '0.875rem', letterSpacing: '0.02em' }], // 11px: Mã part, SKU, micro badges
  'xs':   ['0.75rem',   { lineHeight: '1rem',     letterSpacing: '0.01em' }], // 12px: Dữ liệu bảng phụ, timestamps
  'sm':   ['0.8125rem', { lineHeight: '1.125rem' }],                          // 13px: Giá tiền, nội dung bảng chính, text input
  'base': ['0.875rem',  { lineHeight: '1.25rem' }],                           // 14px: Chuẩn Body text toàn hệ thống (Sửa từ 20px -> 14px)
  'md':   ['0.9375rem', { lineHeight: '1.375rem' }],                          // 15px: Tiêu đề card, nhãn nút bấm chính
  'lg':   ['1.125rem',  { lineHeight: '1.5rem',   letterSpacing: '-0.01em'}], // 18px: Tiêu đề phân đoạn, metric lớn
  'xl':   ['1.25rem',   { lineHeight: '1.75rem',  letterSpacing: '-0.02em'}], // 20px: Tiêu đề Modal, tiêu đề trang con
  '2xl':  ['1.5rem',    { lineHeight: '2rem',     letterSpacing: '-0.02em'}], // 24px: Tiêu đề màn hình chính
}
```

---

### 2.3. Spacing (Quy chuẩn Nhịp điệu Không gian 4pt/8pt)

| Token Tailwind | Giá trị Pixel | Mục đích Sử dụng |
| :--- | :--- | :--- |
| `p-1` / `gap-1` | 4px | Khoảng cách giữa các chip, tags siêu nhỏ |
| `p-2` / `gap-2` | 8px | Khoảng cách giữa nhãn và input, khoảng cách icon/text |
| `p-2.5 px-3` | 10px x 12px | **Paddings tiêu chuẩn cho Table Cell** (Mật độ cao, vừa vặn) |
| `p-3` / `gap-3` | 12px | Padding của Action Toolbar, khoảng cách giữa các trường lọc |
| `p-4` / `gap-4` | 16px | Padding của Content Card, khoảng cách lưới (Grid gap) |
| `p-6` / `gap-6` | 24px | Padding của Modal Dialog, Header chính |
| `px-6 py-4` | 24px x 16px | Padding container bao quanh toàn trang |

---

### 2.4. Border Radius (Quy tắc Phân cấp Hình khối Cha - Con)

Tránh việc dùng hỗn loạn các bo góc; áp dụng định luật hình học lồng nhau: **Bán kính khối con = Bán kính khối cha trừ đi khoảng cách đệm (Padding)**:

- `rounded-2xl` (**16px**): Khung ngoài cùng của Modal Dialog, cửa sổ AI Studio Drawer.
- `rounded-xl` (**12px**): Khung thẻ Card độc lập, khung viền bao quanh Data Table, Panel điều khiển.
- `rounded-lg` (**8px**): Nút bấm (Button), Hộp nhập liệu (Input), Hộp chọn (Select), Dropdown menu.
- `rounded-md` (**6px**): Hộp kiểm (Checkbox), Tabs chuyển trạng thái nhỏ, code block.
- `rounded-full` (**9999px**): Badge trạng thái dạng viên thuốc (Status Pills), Dot chỉ thị trực quan.

---

### 2.5. Shadows (Hệ thống Độ nổi Elevation Tiers)

Giao diện phẳng hóa tối đa, chỉ dùng shadow rất nhẹ để phân tách lớp theo chiều sâu z-index:
- `shadow-none`: Hàng trong bảng, input mặc định, thẻ phẳng.
- `shadow-xs` (`0 1px 2px rgba(0, 0, 0, 0.04)`): Thẻ Card, Thanh Action Bar, Nút bấm phụ.
- `shadow-sm` (`0 2px 4px rgba(0, 0, 0, 0.06)`): Nút bấm Primary FPT, Popover lọc nhanh.
- `shadow-md` (`0 4px 12px rgba(0, 0, 0, 0.08)`): Toast notification, Dropdown menu khi mở.
- `shadow-2xl` (`0 25px 50px -12px rgba(0, 0, 0, 0.25)`): Lớp Modal Dialog nổi trên Backdrop mờ.

---

### 2.6. Breakpoints (Quy chuẩn Đáp ứng Đa thiết bị)

| Điểm ngắt | Kích thước | Hành vi Giao diện |
| :--- | :--- | :--- |
| **Mobile (`< 768px`)** | 375px - 767px | Navbar chuyển thành thanh trượt ngang không thanh cuộn (`overflow-x-auto`). Action Toolbar xếp dọc 1 cột. Bảng dữ liệu hỗ trợ cuộn ngang mượt mà. Modal chiếm full-screen. |
| **Tablet (`768px - 1023px`)** | 768px - 1023px | Navbar hiển thị đầy đủ 5 tab. Bố cục `SkuMatchingPage` chuyển thành dạng Master -> Detail có nút back, không ép chia 2 cột dọc gây nghẽn. |
| **Desktop (`1024px - 1439px`)** | 1024px - 1439px | Giao diện chuẩn Enterprise. Bố cục chia 2 cột 32% - 68% trên SKU Queue. Action toolbar thu gọn trên 1 dòng duy nhất. |
| **Wide Screen (`>= 1440px`)** | 1440px+ | Khống chế độ rộng tối đa `max-w-[1600px]` căn giữa để mắt người dùng không phải đảo quá xa từ mép trái sang mép phải màn hình. |

---

## 3. KIẾN TRÚC THÀNH PHẦN (COMPONENT INVENTORY & ARCHITECTURE)

Toàn bộ các component dùng chung sẽ được đặt tại `frontend/src/components/common/`, đảm bảo tính đóng gói độc lập, có Type Hint rõ ràng và đạt chuẩn A11y:

```text
frontend/src/components/common/
├── Button.tsx           # Thay thế hàng trăm thẻ <button> thủ công
├── Badge.tsx            # Thay thế các class badge tự phát (Chuẩn Rule 9: Zero icon)
├── Input.tsx            # Ô nhập liệu chuẩn hóa viền hairline & focus ring
├── Select.tsx           # Dropdown native bọc chuẩn giao diện enterprise
├── Modal.tsx            # Accessible Dialog Wrapper (Focus trap, role dialog, ESC)
├── TableSkeleton.tsx    # Xung nhịp animation chống giật layout (CLS = 0)
├── EmptyState.tsx       # Khung thông báo dữ liệu trống kèm CTA Reset
├── ErrorBanner.tsx      # Cảnh báo lỗi API kèm nút Thử lại (Xử lý dứt điểm Silent Fail)
├── Pagination.tsx       # Tối ưu lại component phân trang hiện có
└── ToastContainer.tsx   # Hệ thống thông báo kết quả toàn cục
```

### 3.1. Đặc tả Chi tiết Các Component Mới

#### 1. `Button.tsx` (Component Nút bấm Thống nhất)
- **Props:**
  - `variant`: `'primary'` (Cam FPT), `'secondary'` (Xám slate viền), `'destructive'` (Đỏ bác bỏ), `'ghost'` (Nền trong suốt).
  - `size`: `'sm'` (Chiều cao 30px, `text-xs`), `'md'` (Chiều cao 36px, `text-sm`).
  - `isLoading`: Hiển thị vòng xoay CSS tinh tế và disable nút (không dùng icon rác).
  - `fullWidth`: boolean.
- **Ràng buộc Rule 9:** Không nhận icon prop làm trang trí mặc định.

#### 2. `Badge.tsx` (Thẻ Trạng thái Chuẩn mực Không Icon)
- **Props:**
  - `variant`: `'success'` (Xanh ngọc), `'warning'` (Hổ phách), `'danger'` (Đỏ), `'floor'` (Hồng cánh sen bảo vệ sàn), `'info'` (Xanh dương), `'neutral'` (Xám đá SKU).
  - `size`: `'xs'` (text 11px font-mono, padding `px-2 py-0.5`), `'sm'` (text 12px, padding `px-2.5 py-1`).
- **Thiết kế thị giác:** Chữ viết in hoa hoặc đậm rõ ràng (ví dụ: `[ ĐÃ DUYỆT ]`, `[ SÀN VỐN+5% ]`, `[ +1.9% ]`, `[ CHỜ DUYỆT ]`). Nền nhạt 10% kết hợp viền 1px cùng hệ màu.

#### 3. `TableSkeleton.tsx` (Khung xương Chống Giật Layout)
- **Props:** `rows?: number` (Mặc định 8 dòng), `cols?: number` (Mặc định 6 cột).
- **Hành vi:** Render các khối `div` có hiệu ứng sóng mờ `animate-pulse` với chiều cao 40px mỗi hàng, khớp chính xác với kích thước thật của bảng dữ liệu.

#### 4. `ErrorBanner.tsx` (Xử lý Triệt để Lỗi Nuốt API)
- **Props:** `title: string`, `message?: string`, `onRetry?: () => void`.
- **Hành vi:** Xuất hiện ngay trên đầu trang khi TanStack Query trả về `isError = true`. Cung cấp nút *"Thử tải lại dữ liệu"* thay vì để giao diện hiển thị "Dữ liệu trống".

#### 5. `Modal.tsx` (Khung Cửa sổ Trợ năng)
- **Hành vi:**
  - Lắng nghe sự kiện bàn phím phím `Escape` để đóng.
  - Quản lý tiêu điểm bàn phím (Focus Trap): phím Tab chỉ di chuyển bên trong modal.
  - Tự động gán `role="dialog"` và `aria-modal="true"`.
  - Nút đóng `X` có nhãn ẩn `aria-label="Đóng cửa sổ"`.

#### 6. `ToastContext.tsx` & `ToastContainer.tsx` (Hệ thống Thông báo Toàn cục)
- Cung cấp hook `useToast()` dùng chung cho toàn bộ app:
  `showToast({ title: 'Đã phê duyệt', message: 'Mã FPT-IP16-PRO đã được áp dụng giá mới', type: 'success' })`.
  Giải quyết tình trạng chỉ có mỗi trang `SkuMatchingPage` tự làm popup toast.

---

### 3.2. Danh mục Dọn dẹp & Tái cấu trúc
- **Xóa bỏ (Dead Code):**
  - [frontend/src/components/MatchingReviewTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/MatchingReviewTable.tsx)
  - [frontend/src/components/layout/Sidebar.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/layout/Sidebar.tsx)
- **Di chuyển vị trí:**
  - [frontend/src/components/CrawlControlPanel.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/CrawlControlPanel.tsx) -> `frontend/src/components/crawler/CrawlControlPanel.tsx`.
- **Đồng bộ thư mục:**
  - Thư mục `components/competitor/` được đồng bộ sang đúng quy ước ngữ nghĩa.

---

## 4. CẢI TIẾN BỐ CỤC & ĐIỀU HƯỚNG (LAYOUT & NAVIGATION REDESIGN)

### 4.1. Cải tiến Header & Thanh Điều hướng Chính (`Navbar.tsx`)
- **Khắc phục lỗi Mobile:**
  - Thay thế `className="hidden md:flex"` bằng thanh trượt ngang linh hoạt:
    `className="flex items-center gap-1.5 overflow-x-auto no-scrollbar scroll-smooth py-1"`.
  - Trên mobile, người dùng có thể vuốt ngón tay nhẹ để chọn nhanh bất kỳ tab nào trong số 5 tab.
- **Tuân thủ Rule 9:**
  - Loại bỏ các icon `BarChart3`, `CheckCheck`, `GitCompare`, `Database`, `RefreshCw` chèn trước tên tab.
  - Tab được thiết kế dưới dạng Text Pill tinh xảo:
    - Tab Đang chọn: Nền cam nhạt `bg-orange-500/10`, chữ cam đậm `text-orange-600 dark:text-orange-400`, viền `border-orange-500/30`, thanh gạch chân mảnh (Indicator bar) ở đáy.
    - Tab Chưa chọn: Chữ xám đậm `text-slate-600 dark:text-slate-400`, hover êm ái `hover:bg-slate-100 dark:hover:bg-slate-800`.
- **Tích hợp Nhãn Người dùng & Chuyển Theme:** Giữ nút chuyển Dark/Light mode gọn gàng ở góc phải cùng User Pill tinh giản.

---

### 4.2. Khái niệm Thanh Công Cụ Hợp Nhất (Unified Action Toolbar)
Thay vì xếp chồng 4 tầng thanh công cụ làm chật chội màn hình như hiện tại, gom toàn bộ vào **1 hàng ngang duy nhất (Single-tier Unified Toolbar)**:

```text
+--------------------------------------------------------------------------------------------------------------------+
| [Tất cả | Điện thoại | Laptop]  |  [ Tìm theo tên, part, SKU... ]  [ Mọi mức giá v ] [ Chỉ còn hàng ]             |
|                                                     (Phải): Cập nhật: 10:15 14/10  |  [ NÚT: CÀO DỮ LIỆU (30s) ]   |
+--------------------------------------------------------------------------------------------------------------------+
```

- **Tiết kiệm chiều cao:** Giảm từ 260px xuống chỉ còn **52px**, giải phóng ngay lập tức hơn 200px chiều cao cho bảng dữ liệu.
- **Tiến trình cào thu gọn:** Khi cào dữ liệu, thanh tiến độ mini hiển thị inline mượt mà ngay bên cạnh nút kích hoạt thay vì bung ra cả một khối hộp to lớn đè mất giao diện.
- **Loại bỏ dữ liệu lỗi:** Sửa dứt điểm việc in chữ `'error'` và số liệu hardcode tĩnh tại `DebounceTriggerBar.tsx`.

---

## 5. KẾ HOẠCH REDESIGN CHI TIẾT THEO TỪNG MODULE / PAGE

### Module 1: Price Matrix ([PriceMatrixPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PriceMatrixPage.tsx))
- **Mục tiêu:** Màn hình phân tích đối soát giá 3 bên (FPT vs CellphoneS vs Hoàng Hà Mobile) trực quan, có độ tương phản cao, cuộn mượt mà.
- **Thay đổi chi tiết:**
  - Gộp `DebounceTriggerBar` và `MatrixFilterToolbar` thành `UnifiedMatrixToolbar`.
  - Tích hợp `TableSkeleton` (10 hàng) khi `isLoading = true`.
  - Thêm `ErrorBanner` có nút *"Thử lại"* khi `isError = true`.
  - [PriceMatrixTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/matrix/PriceMatrixTable.tsx):
    - Thêm `sticky top-0 bg-white dark:bg-slate-900 z-10` cho hàng tiêu đề `<thead>`.
    - Loại bỏ toàn bộ icon `TrendingUp`, `TrendingDown`, `Equal` trong cột Chênh lệch giá. Thay bằng `Badge` số liệu font-mono có màu nền tương ứng.
    - Cố định cột 1 (Mã SKU & Tên sản phẩm) khi cuộn ngang trên màn hình vừa.
    - Thêm link thao tác chữ đơn giản *"Giải trình AI"* và *"Chi tiết"* không rườm rà.

---

### Module 2: Pricing Approvals ([PricingApprovalsPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/PricingApprovalsPage.tsx))
- **Mục tiêu:** Quy trình phê duyệt giá đề xuất an toàn, minh bạch căn cứ 3 lớp (Demand, Inventory, Competitor) và bảo vệ giá sàn.
- **Thay đổi chi tiết:**
  - Bổ sung cụm chọn danh mục (`Tất cả | Điện thoại | Laptop`) trực tiếp trên thanh toolbar (giải quyết lỗi bị khóa cứng `ALL`).
  - [ApprovalFilterTabs.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/ApprovalFilterTabs.tsx): Loại bỏ icon `Clock`, `CheckCheck`, `XCircle`, `History`. Thiết kế lại dạng Tab tối giản với con số đếm (Badge count) rõ nét.
  - [RecommendationTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/RecommendationTable.tsx):
    - Thêm nhãn trợ năng cho toàn bộ checkbox chọn hàng loạt.
    - Bỏ icon `ShieldCheck` và `TrendingDown`, thay bằng Tag viền cánh sen `[ SÀN VỐN+5% ]` nổi bật.
    - Bổ sung `sticky top-0` cho Header.
  - [PricingDetailModal.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/PricingDetailModal.tsx):
    - Chuyển sang sử dụng component `Modal` chuẩn (hỗ trợ phím ESC, quản lý focus).
    - Dọn sạch 10 loại icon trang trí.
    - Sửa lỗi font chữ `text-base: 20px` tại ô nhập giá chỉnh tay sang cỡ chuẩn 14px/16px.
    - Làm gọn thanh thước định vị 6 điểm giá cốt lõi, tinh chỉnh độ tương phản chữ đạt chuẩn WCAG AA.
  - [ProductPriceHistoryModal.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/recommendations/ProductPriceHistoryModal.tsx): Bổ sung biểu đồ đường SVG Sparkline siêu nhẹ ở đầu trang để xem xu hướng tăng giảm giá qua các lần điều chỉnh.

---

### Module 3: SKU Mapping Queue ([SkuMatchingPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/SkuMatchingPage.tsx))
- **Mục tiêu:** Môi trường đối soát bán tự động phân giải nghi vấn (độ tin cậy 60% - 79%) trực quan, hiển thị rõ từ ngữ sai khác (Token Diff).
- **Thay đổi chi tiết:**
  - **Sửa lỗi vỡ layout trên Tablet/Mobile:** Chuyển `h-[calc(100vh-140px)]` cứng nhắc sang cơ chế cuộn linh hoạt hoặc hỗ trợ nút chuyển nhanh giữa *"Danh sách hàng đợi"* và *"Bảng so sánh chi tiết"* khi độ rộng `< 1024px`.
  - [SkuQueueCard.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/mapping/SkuQueueCard.tsx):
    - Tối ưu thẻ SKU: làm rõ độ tin cậy bằng con số font-mono đậm, dọn dẹp các đường viền thừa.
  - [SkuDetailInspector.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/mapping/SkuDetailInspector.tsx):
    - Thiết kế lại bảng đối soát 3 cột (Thuộc tính | FPT Shop | Đối thủ).
    - Cải tiến hiệu ứng làm nổi bật từ ngữ sai lệch (Token Diff): Nền đỏ nhạt cho từ ngữ khác biệt của đối thủ, nền hổ phách cho từ ngữ FPT, không dùng icon rác.
  - Chuyển đổi popup Toast thủ công ở góc màn hình sang sử dụng hệ thống `useToast()` toàn cục.

---

### Module 4: Competitor Feeds ([CompetitorFeedsPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/CompetitorFeedsPage.tsx))
- **Mục tiêu:** Quản lý kho dữ liệu cào đối thủ thô (hơn 4.000 sản phẩm) với tốc độ tìm kiếm và lọc tức thì.
- **Thay đổi chi tiết:**
  - Đồng bộ tên thư mục component thành `components/competitor/` chuẩn mực.
  - [CompetitorSummaryCards.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/competitor/CompetitorSummaryCards.tsx): Bỏ các icon minh họa, thiết kế lại thành 4 thẻ chỉ số KPI tài chính (MetricStatCard) phẳng, thanh lịch.
  - [CompetitorDataTable.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/competitor/CompetitorDataTable.tsx): Bổ sung `TableSkeleton`, `sticky top-0`, và làm rõ nhãn tình trạng kho hàng (`Còn hàng` / `Hết hàng`) bằng Badge text chuẩn.
  - [CompetitorSpecsDrawer.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/competitor/CompetitorSpecsDrawer.tsx): Tối ưu khung xem chi tiết thông số và JSON Viewer, tăng độ tương phản của code block.

---

### Module 5: Crawl Operations ([CrawlManagerPage.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/pages/CrawlManagerPage.tsx))
- **Mục tiêu:** Trung tâm giám sát tình trạng vận hành và kích hoạt cào Full Pipeline.
- **Thay đổi chi tiết:**
  - Di chuyển [CrawlControlPanel.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/CrawlControlPanel.tsx) vào đúng thư mục `components/crawler/`.
  - Loại bỏ các icon `Zap`, `Play`, `Check`, `AlertCircle`. Thiết kế lại nút kích hoạt pipeline thành nút bấm Enterprise rõ ràng với văn bản trạng thái: `[ BẮT ĐẦU CÀO TOÀN DIỆN ]` hoặc `[ ĐANG CHẠY CÀO 45% ]`.
  - [SourceStatusCard.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/crawler/SourceStatusCard.tsx): Tinh gọn lại 3 thẻ trạng thái nguồn (CellphoneS, Hoàng Hà, FPT Baseline) với dot chỉ thị trạng thái nhịp tim (pulse) tối giản.
  - [CronSchedulePanel.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/crawler/CronSchedulePanel.tsx): Thiết kế lại lịch trình cronjob tự động dưới dạng lưới thời gian rõ ràng, dễ bật/tắt.

---

### Module 6: Global AI Assistant ([AiAssistantManager.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/ai/AiAssistantManager.tsx))
- **Mục tiêu:** Không gian phân tích chuyên sâu (Pricing Copilot Studio) liền mạch, hỗ trợ giải trình 3 lớp và tra cứu tức thì.
- **Thay đổi chi tiết:**
  - [AiFloatingButton.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/ai/AiFloatingButton.tsx): Tinh giản nút nổi tròn ở góc dưới bên phải màn hình thành một nút bấm mang phong cách Minimalist (chữ `AI` font-mono đậm nét trên nền cam FPT, dot báo hiệu tinh tế).
  - [ExpandedAiDrawer.tsx](file:///d:/hoctap/thuc%20tap/fpt/Dynamic_Pricing/frontend/src/components/ai/ExpandedAiDrawer.tsx): Tối ưu cột lịch sử phiên hội thoại bên trái và không gian trò chuyện bên phải; tinh chỉnh phông chữ markdown và bảng dữ liệu nhúng trong phản hồi AI theo đúng thang đo design tokens mới.

---

## 6. ĐÁNH GIÁ THƯ VIỆN UI (UI LIBRARY EVALUATION)

### 6.1. Quyết định Kiến trúc: TẬN DỤNG TỐI ĐA STACK HIỆN TẠI
- **Dự án hiện có:**
  - `react` 18.3.1 + `typescript` 5.6.3 + `vite` 5.4.11
  - `tailwindcss` 3.4.16 + `postcss` + `autoprefixer`
  - `@tanstack/react-query` 5.104.5 + `@tanstack/react-table` 8.20.5
  - `clsx` + `tailwind-merge` (đã có sẵn để viết hàm nối class `cn(...)`)
- **Kết luận:** **TUYỆT ĐỐI KHÔNG CÀI ĐẶT THƯ VIỆN UI NẶNG** (như Ant Design, MUI, Mantine, hay Chakra UI).

### 6.2. Lý do Kỹ thuật & Nghiệp vụ:
1. **Tránh xung đột CSS & Đội dung lượng Bundle:** Các thư viện giao diện trọn gói (MUI/Antd) thường mang theo hệ thống theme và CSS reset riêng, gây xung đột trực tiếp với Tailwind CSS và làm phình kích thước bundle tải về thêm từ 300KB đến 800KB.
2. **Khó tuân thủ Rule 9:** Các thư viện lớn thường mặc định gắn chặt các bộ icon riêng vào nút bấm, bảng, modal, rất khó kiểm soát và loại bỏ triệt để.
3. **Sức mạnh vượt trội của Headless Patterns:** Với Tailwind CSS và `clsx`/`tailwind-merge`, việc xây dựng một bộ Atomic UI Component riêng (`Button`, `Badge`, `Input`, `Modal`, `TableSkeleton`) hoàn toàn chỉ tốn chưa tới 300 dòng code sạch, siêu nhẹ, không tốn thêm bất kỳ dependency nào từ bên thứ ba, bảo đảm 100% khả năng kiểm soát và tùy biến.

---

## 7. TIÊU CHÍ NGHIỆM THU TỪNG GIAI ĐOẠN (ACCEPTANCE CRITERIA)

Kế hoạch thực thi sau khi được phê duyệt sẽ được đánh giá theo các tiêu chuẩn nghiệm thu định lượng khắt khe:

### Giai đoạn 1: Nền tảng & Tokens (Foundation & Cleanup)
- [ ] `npm run build` chạy thành công không có lỗi TypeScript hay CSS syntax.
- [ ] Lỗi `fontSize.base: 20px` được sửa dứt điểm, text body quay về đúng 14px (`0.875rem`).
- [ ] Biến CSS tokens được định nghĩa đầy đủ tại `index.css` cho cả 2 mode: Light và Dark.
- [ ] 2 file dead code (`MatchingReviewTable.tsx`, `Sidebar.tsx`) được loại bỏ an toàn khỏi repo.
- [ ] File `CrawlControlPanel.tsx` được chuyển vào `components/crawler/` với đường dẫn import chính xác.

### Giai đoạn 2: Xây dựng Bộ UI Kit Dùng Chung (Shared UI Kit & A11y)
- [ ] Toàn bộ 7 component nền tảng (`Button`, `Badge`, `Input`, `Select`, `Modal`, `TableSkeleton`, `EmptyState`) được tạo mới trong `frontend/src/components/common/` và có kiểm thử type TypeScript đầy đủ.
- [ ] `ToastProvider` hoạt động mượt mà, gọi được qua hook `useToast()` từ bất kỳ component con nào.
- [ ] Độ tương phản màu chữ phụ (mã part, ngày tháng, nhãn phụ) đạt tối thiểu **4.5:1** trên nền trắng và **5.0:1** trên nền Dark Mode (đạt chuẩn WCAG 2.1 AA).
- [ ] Toàn bộ các hộp kiểm (checkbox) và nút thao tác có thuộc tính `aria-label` rõ ràng.

### Giai đoạn 3: Tái thiết Kế Bố cục & Điều hướng (Layout & Navigation)
- [ ] Thanh `Navbar.tsx` hiển thị và vuốt trượt ngang mượt mà trên Mobile (độ rộng viewport 375px - 767px), không bị ẩn menu.
- [ ] Thanh `UnifiedMatrixToolbar` trên trang Price Matrix chỉ chiếm đúng 1 hàng ngang, giảm chiều cao tối thiểu 180px so với trước.
- [ ] Khi ngắt kết nối mạng hoặc server trả về mã lỗi 500/404, màn hình hiển thị banner cảnh báo lỗi đỏ (`ErrorBanner`) kèm nút *"Thử lại"*, chấm dứt hoàn toàn tình trạng nuốt lỗi (Silent Fail).

### Giai đoạn 4: Redesign Toàn diện 5 Module Nghiệp vụ (Page-by-Page Polish)
- [ ] Toàn bộ 5 trang (`PriceMatrixPage`, `PricingApprovalsPage`, `SkuMatchingPage`, `CompetitorFeedsPage`, `CrawlManagerPage`) được làm sạch: **100% không còn icon hoặc emoji trang trí rác** theo đúng Quy tắc số 9.
- [ ] 100% các bảng dữ liệu có `sticky top-0` cho Header khi cuộn dọc và có `TableSkeleton` khi tải trang.
- [ ] Trang `PricingApprovalsPage` có bộ lọc ngành hàng (Điện thoại / Laptop) hoạt động độc lập và chính xác.
- [ ] Trang `SkuMatchingPage` hiển thị co giãn tốt trên màn hình Tablet (768px - 1024px), không bị mất cột chi tiết.
- [ ] Toàn bộ ứng dụng hoạt động trơn tru với API Backend hiện có, **không làm thay đổi hay phá vỡ bất kỳ logic nghiệp vụ tính toán giá nào**.

---

## 8. KẾT LUẬN & YÊU CẦU PHÊ DUYỆT

Kế hoạch này vạch ra một lộ trình chuẩn mực, an toàn và bài bản để nâng tầm toàn diện giao diện Frontend của dự án Dynamic Pricing thành một sản phẩm SaaS Enterprise đẳng cấp, tinh tế và tối ưu hiệu suất làm việc cho chuyên viên giá FPT Retail.

Kính trình bạn xem xét bản kế hoạch trên. Sau khi nhận được sự đồng thuận và phê duyệt từ bạn, tôi sẽ tiến hành triển khai chi tiết theo đúng thứ tự 4 giai đoạn!

