# Kế Hoạch Triển Khai: Executive Overview Dashboard (Phương Án 1)

> **Dành cho agent:** KỸ NĂNG BẮT BUỘC: Sử dụng `superpowers:executing-plans` để thực thi kế hoạch này theo từng task. Các bước sử dụng cú pháp checkbox (`- [ ]`) để theo dõi tiến độ.

**Mục tiêu (Goal):** Xây dựng trang Executive Overview Dashboard hoàn chỉnh gồm backend aggregation API và frontend UI cao cấp (4 thẻ KPI, biểu đồ tỷ lệ cạnh tranh giá 3 bên, luồng đề xuất cấp bách, bảng cảnh báo tồn kho rủi ro), đặt làm tab mặc định đầu tiên của hệ thống.

**Kiến trúc (Architecture):**
1. **Backend Layer:** FastAPI endpoint `GET /api/v1/dashboard/summary` thực hiện tổng hợp dữ liệu trực tiếp từ DB (`Product`, `InventoryMock`, `SkuMapping`, `PriceRecommendation`) với bộ lọc `category: ALL | PHONE | LAPTOP`.
2. **Frontend Data Layer:** TanStack Query hook `useDashboardSummaryQuery(category)` với `staleTime: 5 phút`, hỗ trợ tải nhanh 0ms khi chuyển tab và tự động cập nhật khi có mutation.
3. **Frontend UI Components:** 4 thành phần giao diện tách bạch (KPI Cards, 3-Way Competitiveness Bar, Actionable Approval Stream, High Risk Inventory Table) theo chuẩn doanh nghiệp tối giản, không dùng emoji/icon trang trí.
4. **Navigation-First Workflow:** Dashboard đặt ở vị trí tab đầu tiên (#dashboard); tương tác bấm vào các mục cảnh báo sẽ chuyển hướng mượt mà sang tab nghiệp vụ sâu (`approvals`, `matrix`).

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, pytest, React 18, TypeScript, TailwindCSS, TanStack Query v5.

---

## Global Constraints

- Tuân thủ quy tắc thiết kế giao diện (AGENTS.md Rule 9): Tuyệt đối không dùng emoji hoặc icon trang trí trong các badge, thẻ trạng thái, nút bấm (chuẩn Enterprise tối giản).
- Quy chuẩn kiểm thử (AGENTS.md Rule 10): Kiểm thử trực tiếp qua API và unit test (`pytest`), không dùng browser automation.
- CodeGraph First (AGENTS.md Rule 1): Kiểm tra tác động và đồng bộ `codegraph sync` sau khi hoàn thành.
- Đảm bảo kiểm thử TypeScript `npm run build` trong `frontend/` đạt 0 lỗi.

---

## Kế Hoạch Chi Tiết Từng Task

### Task 1: Xây dựng Backend Schemas & Endpoint `GET /api/v1/dashboard/summary` (TDD)

**Files:**
- Create: `backend/app/schemas/dashboard.py`
- Create: `backend/app/api/v1/endpoints/dashboard.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/tests/test_dashboard_api.py`

- [x] **Step 1: Viết test kiểm thử API thất bại (RED)**
  Tạo `backend/tests/test_dashboard_api.py` kiểm tra:
  - `GET /api/v1/dashboard/summary` trả về status 200 và cấu trúc payload hợp lệ.
  - Lọc theo `category=PHONE` và `category=LAPTOP`.
  - Các trường dữ liệu: `total_skus`, `competitive_win_rate`, `pending_approvals_count`, `high_doh_risk_count`, `price_competitiveness`, `actionable_approvals`, `high_risk_inventory`.

- [x] **Step 2: Chạy test để xác nhận FAIL**
  Chạy: `pytest backend/tests/test_dashboard_api.py -v`
  Kết quả: FAIL (404 Not Found vì endpoint chưa tồn tại).

- [x] **Step 3: Tạo Pydantic Schemas trong `backend/app/schemas/dashboard.py`**
  Định nghĩa:
  - `CompetitivenessStats` (cheaper_count, cheaper_pct, equal_count, equal_pct, higher_count, higher_pct)
  - `ActionableApprovalItem` (id, sku, product_name, category, current_price, suggested_price, floor_price, is_floor_capped, scenario)
  - `HighRiskInventoryItem` (sku, product_name, category, doh, stock_quantity, current_price, competitor_min_price, price_gap, recommended_action)
  - `DashboardSummaryResponse` chứa toàn bộ các khối trên.

- [x] **Step 4: Hiện thực endpoint `GET /summary` trong `backend/app/api/v1/endpoints/dashboard.py`**
  Truy vấn CSDL:
  - Lấy danh sách sản phẩm active theo category.
  - Tính `total_skus`.
  - Tính toán cạnh tranh 3 bên (cheaper/equal/higher so với đối thủ còn hàng).
  - Đếm đề xuất giá có status `PENDING` và lấy top 5 đề xuất cấp thiết.
  - Đếm sản phẩm có `doh > 30` và lấy top 5 sản phẩm tồn kho rủi ro cao.

- [x] **Step 5: Đăng ký router `/dashboard` trong `backend/app/api/v1/router.py`**
  Gắn router vào `api_router`.

- [x] **Step 6: Chạy lại test xác nhận PASS (GREEN)**
  Chạy: `pytest backend/tests/test_dashboard_api.py -v`
  Kết quả: PASS 100%.

---

### Task 2: Tạo Frontend Types, API Client & TanStack Query Hook

**Files:**
- Create: `frontend/src/types/dashboard.ts`
- Create: `frontend/src/api/dashboardApi.ts`
- Create: `frontend/src/hooks/useDashboardQueries.ts`

- [x] **Step 1: Tạo types trong `frontend/src/types/dashboard.ts`**
  Khai báo TypeScript interfaces ánh xạ 1:1 với schema backend:
  - `DashboardSummaryResponse`
  - `CompetitivenessStats`
  - `ActionableApprovalItem`
  - `HighRiskInventoryItem`

- [x] **Step 2: Tạo API client trong `frontend/src/api/dashboardApi.ts`**
  Hàm `getDashboardSummaryApi(category?: string)` gọi `apiClient.get('/dashboard/summary', { params: { category } })` kèm fallback mock data nếu offline.

- [x] **Step 3: Tạo TanStack Query hook trong `frontend/src/hooks/useDashboardQueries.ts`**
  - Hook `useDashboardSummaryQuery(category?: string)` với queryKey `['dashboard', 'summary', category || 'ALL']`.
  - Helper `invalidateDashboardQueries(queryClient)`.

- [x] **Step 4: Kiểm tra build TypeScript**
  Chạy: `cmd.exe /c "npm run build"` trong `frontend/`.

---

### Task 3: Xây dựng các UI Components của Dashboard

**Files:**
- Create: `frontend/src/components/dashboard/DashboardKpiCards.tsx`
- Create: `frontend/src/components/dashboard/CompetitivenessBar.tsx`
- Create: `frontend/src/components/dashboard/ActionableApprovalStream.tsx`
- Create: `frontend/src/components/dashboard/HighRiskInventoryTable.tsx`

- [x] **Step 1: Xây dựng `DashboardKpiCards.tsx`**
  - 4 thẻ thống kê: Tổng SKU theo dõi, Tỷ lệ thắng giá (% Win Rate), Đề xuất chờ duyệt, Cảnh báo tồn kho DOH > 30.
  - Hỗ trợ click vào thẻ để chuyển nhanh sang tab tương ứng.

- [x] **Step 2: Xây dựng `CompetitivenessBar.tsx`**
  - Thanh tỷ lệ phân bổ nằm ngang hiển thị % Rẻ hơn (Cam FPT), % Bằng giá (Xanh ngọc), % Đắt hơn (Xám/Đỏ) so với CellphoneS và Hoàng Hà.
  - Chú giải và số lượng SKU cụ thể cho từng khoảng.

- [x] **Step 3: Xây dựng `ActionableApprovalStream.tsx`**
  - Danh sách thẻ đề xuất giá ưu tiên: SKU, tên sản phẩm, giá hiện tại vs giá gợi ý, huy hiệu bảo vệ giá sàn, lý do kịch bản.
  - Nút bấm điều hướng chuyển sang tab Duyệt Giá.

- [x] **Step 4: Xây dựng `HighRiskInventoryTable.tsx`**
  - Bảng top SKU tồn kho cao (DOH > 30): SKU, tên, DOH (ngày), tồn kho, chênh lệch giá, khuyến nghị hành động.
  - Nút điều hướng sang Ma trận giá.

---

### Task 4: Chuyển đổi và Hoàn thiện `DashboardPage.tsx`

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`

- [x] **Step 1: Refactor `DashboardPage.tsx`**
  - Tích hợp hook `useDashboardSummaryQuery(categoryFilter)`.
  - Bộ chọn ngành hàng (Segmented Control: Tất cả, Điện thoại, Laptop) trên thanh tiêu đề.
  - Hiển thị badge đồng bộ ngầm khi `isFetching && !isLoading`.
  - Nhận props `onNavigateTab: (tab: NavTab, filterOptions?: any) => void` để điều hướng mượt mà sang các tab `approvals` và `matrix`.

- [x] **Step 2: Kiểm tra build TypeScript**
  Chạy: `cmd.exe /c "npm run build"`.

---

### Task 5: Tích hợp Thanh Điều Hướng (Navbar) & Tuyến Đường Mặc Định

**Files:**
- Modify: `frontend/src/components/layout/Navbar.tsx`
- Modify: `frontend/src/components/layout/AppLayout.tsx`
- Modify: `frontend/src/App.tsx`

- [x] **Step 1: Cập nhật `Navbar.tsx`**
  - Thêm tab `dashboard` vào vị trí đầu tiên của `navItems` (mã `dashboard`, nhãn `"Dashboard"`, icon `LayoutDashboard`).
  - Đẩy `matrix` sang vị trí thứ 2.

- [x] **Step 2: Cập nhật `AppLayout.tsx`**
  - Thêm `'dashboard'` vào `VALID_TABS`.
  - Đặt `'dashboard'` làm tab khởi tạo mặc định thay vì `'matrix'`.

- [x] **Step 3: Cập nhật `App.tsx`**
  - Nhập `DashboardPage`.
  - Mount `DashboardPage` trong `TabContainer` với `visitedTabs` và CSS `hidden`.
  - Truyền callback `onNavigateTab` từ `AppLayout` để chuyển tab khi click từ Dashboard.

---

### Task 6: Kiểm Thử Toàn Diện & Đồng Bộ Chỉ Mục

**Files:**
- Toàn bộ codebase backend & frontend.

- [x] **Step 1: Chạy toàn bộ test backend**
  `pytest backend/tests/test_dashboard_api.py -v` (Đạt 2/2 PASS).
- [x] **Step 2: Chạy build production frontend**
  `npm run build` trong `frontend/` (Đạt 0 lỗi TypeScript, 1736 modules transformed).
- [x] **Step 3: Đồng bộ CodeGraph**
  Chạy `codegraph sync` (Chỉ mục đồng bộ).
