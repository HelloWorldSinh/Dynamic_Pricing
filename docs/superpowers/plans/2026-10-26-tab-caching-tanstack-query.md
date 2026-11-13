# Kế Hoạch Triển Khai: Tối Ưu Cache Dữ Liệu & Trạng Thái Khi Chuyển Tab (TanStack Query + Lazy Mount)

> **Dành cho agent:** KỸ NĂNG BẮT BUỘC: Sử dụng `superpowers:executing-plans` để thực thi kế hoạch này theo từng task. Các bước sử dụng cú pháp checkbox (`- [ ]`) để theo dõi tiến độ.

**Mục tiêu (Goal):** Loại bỏ độ trễ và tình trạng gọi lại DB khi chuyển tab bằng cách kết hợp TanStack Query (@tanstack/react-query) để cache dữ liệu máy chủ (staleTime 5 phút) cùng cơ chế Lazy-Mount & CSS Hidden để giữ nguyên 100% trạng thái giao diện (scroll, pagination, filter).

**Kiến trúc (Architecture):**
1. **Server-State Caching:** Tích hợp `@tanstack/react-query` v5 với `staleTime: 5 phút`, `gcTime: 10 phút`. Mọi truy vấn chuyển tab được trả kết quả tức thì từ RAM (0ms).
2. **Cross-Tab Invalidation:** Tự động hủy cache và đồng bộ giữa các tab khi có thao tác duyệt giá (invalidation Price Matrix), duyệt SKU (invalidation Matrix & Feeds), hoặc cào dữ liệu thành công.
3. **UI Preservation (Hybrid Lazy-Mount):** Trong `App.tsx`, các tab chỉ mount khi được truy cập lần đầu và được ẩn/hiện bằng CSS `hidden` thay vì bị unmount hoàn toàn.
4. **Background Revalidation UX:** Hiển thị nhãn trạng thái tinh tế `"Đang đồng bộ..."` khi dữ liệu đang fetch ngầm, không che khuất màn hình và không dùng icon/emoji.

**Tech Stack:** React 18, TypeScript, Vite, TailwindCSS, `@tanstack/react-query` v5, Axios.

---

## Global Constraints

- Tuân thủ quy tắc thiết kế giao diện: Tuyệt đối không dùng emoji hoặc icon trang trí trong các badge/nhãn trạng thái (chuẩn Enterprise tối giản).
- Đảm bảo kiểm thử TypeScript thông qua `npm run build` không phát sinh bất kỳ lỗi compile nào.
- Giữ nguyên cấu trúc các endpoint API hiện tại trong `frontend/src/api/`.

---

## Kế Hoạch Chi Tiết Từng Task

### Task 1: Cài đặt `@tanstack/react-query` và thiết lập QueryClientProvider ở tầng gốc

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/lib/queryClient.ts`

- [x] **Step 1: Cài đặt gói `@tanstack/react-query`**
  Chạy lệnh cài đặt npm trong thư mục `frontend/`:
  `npm install @tanstack/react-query@^5`

- [x] **Step 2: Tạo module khởi tạo `queryClient.ts`**
  Tạo `frontend/src/lib/queryClient.ts` cấu hình mặc định:
  - `staleTime`: 5 phút (`5 * 60 * 1000`)
  - `gcTime`: 10 phút (`10 * 60 * 1000`)
  - `refetchOnWindowFocus`: false
  - `retry`: 1

- [x] **Step 3: Bọc `QueryClientProvider` trong `App.tsx`**
  Cập nhật `App.tsx` bao bọc cây component với `<QueryClientProvider client={queryClient}>`.

- [x] **Step 4: Kiểm tra build TypeScript**
  Chạy `npm run build` trong `frontend` để kiểm tra cài đặt và import hợp lệ.

---

### Task 2: Xây dựng các Query Hooks & Invalidation Helpers chuẩn hóa

**Files:**
- Create: `frontend/src/hooks/usePricingQueries.ts`
- Create: `frontend/src/hooks/useSkuQueries.ts`
- Create: `frontend/src/hooks/useFeedsQueries.ts`

- [x] **Step 1: Tạo `usePricingQueries.ts`**
  - Hook `usePriceMatrixQuery(category?: string)` bọc hàm `getPriceMatrixApi(category)`.
  - Hook `useRecommendationsQuery()` bọc hàm `getRecommendationsApi()`.
  - Hook `usePriceHistoryQuery()` bọc hàm `getPriceHistoryApi()`.
  - Helper functions invalidate queries: `invalidatePricingQueries(queryClient)`.

- [x] **Step 2: Tạo `useSkuQueries.ts`**
  - Hook `useSkuMappingQueueQuery()` bọc hàm `getSkuMappingQueueApi()`.
  - Invalidation helper: `invalidateSkuQueries(queryClient)`.

- [x] **Step 3: Tạo `useFeedsQueries.ts`**
  - Hook `useCompetitorFeedsQuery(category?: string)` bọc hàm `getFeedsApi(category)`.
  - Invalidation helper: `invalidateFeedsQueries(queryClient)`.

- [x] **Step 4: Kiểm tra build TypeScript**
  Chạy `npm run build` trong `frontend` để kiểm tra typing của các hooks.

---

### Task 3: Chuyển đổi `PriceMatrixPage` và `PricingApprovalsPage` sang TanStack Query

**Files:**
- Modify: `frontend/src/pages/PriceMatrixPage.tsx`
- Modify: `frontend/src/pages/PricingApprovalsPage.tsx`

- [x] **Step 1: Refactor `PriceMatrixPage.tsx`**
  - Thay thế `useEffect` gọi `fetchData` bằng hook `usePriceMatrixQuery(categoryFilter)`.
  - Sử dụng `isFetching && !isLoading` để hiển thị nhãn trạng thái `"Đang đồng bộ..."` tinh tế trên thanh công cụ.
  - Khi cào dữ liệu xong (`onCrawlCompleted`), gọi `refetch()` hoặc `invalidatePricingQueries`.

- [x] **Step 2: Refactor `PricingApprovalsPage.tsx`**
  - Thay thế `useEffect` gọi `fetchData` bằng `useRecommendationsQuery` và `usePriceHistoryQuery`.
  - Trong các hàm duyệt/từ chối giá (`handleApproveBatch`, `handleRejectBatch`), sau khi gọi API thành công:
    - Gọi invalidate `['pricing']` để tự động đồng bộ sang `PriceMatrixPage`.
  - Hiển thị nhãn `"Đang đồng bộ..."` khi dữ liệu fetch ngầm.

- [x] **Step 3: Kiểm tra build TypeScript**
  Chạy `npm run build` để đảm bảo không lỗi kiểu dữ liệu.

---

### Task 4: Chuyển đổi `SkuMatchingPage` và `CompetitorFeedsPage` sang TanStack Query với Cross-Tab Invalidation

**Files:**
- Modify: `frontend/src/pages/SkuMatchingPage.tsx`
- Modify: `frontend/src/pages/CompetitorFeedsPage.tsx`

- [x] **Step 1: Refactor `SkuMatchingPage.tsx`**
  - Dùng `useSkuMappingQueueQuery()`.
  - Khi `handleApprove` hoặc `handleReject` (đơn lẻ hoặc hàng loạt) thành công:
    - Invalidate `['sku']` (hàng đợi khớp SKU).
    - Invalidate `['pricing', 'matrix']` (vì SKU được khớp sẽ xuất hiện trong ma trận giá).
    - Invalidate `['feeds']` (cập nhật trạng thái liên kết của feed đối thủ).

- [x] **Step 2: Refactor `CompetitorFeedsPage.tsx`**
  - Dùng `useCompetitorFeedsQuery(categoryFilter)`.
  - Giữ lại nhãn trạng thái `"Đang đồng bộ..."` khi re-fetching.

- [x] **Step 3: Kiểm tra build TypeScript**
  Chạy `npm run build` xác nhận logic compile trơn tru.

---

### Task 5: Triển khai Lazy-Mount kết hợp CSS Hidden trong `App.tsx`

**Files:**
- Modify: `frontend/src/App.tsx`

- [x] **Step 1: Tạo cơ chế theo dõi các tab đã được truy cập (visited tabs set)**
  - Quản lý `visitedTabs` (danh sách các tab mà người dùng đã từng click vào ít nhất 1 lần).
  - Khi người dùng chọn tab nào, tab đó được thêm vào `visitedTabs`.

- [x] **Step 2: Cập nhật render các trang tab với CSS `hidden`**
  - Tab chưa từng được truy cập sẽ KHÔNG mount (tiết kiệm tài nguyên lúc load ban đầu).
  - Tab đã từng được truy cập sẽ mount và tồn tại trong DOM:
    `<div className={activeTab === 'matrix' ? 'block' : 'hidden'}> ... </div>`
  - Giữ nguyên toàn bộ DOM, scroll position, bộ lọc và state nội bộ của trang.

- [x] **Step 3: Kiểm tra build TypeScript và xác minh bundle**
  Chạy `npm run build` trong `frontend/` để kiểm tra đóng gói thành công.

---

### Task 6: Kiểm thử Tích hợp & Xác minh Toàn diện

**Files:**
- Verify: Toàn bộ luồng chuyển tab, gọi API, cache staleTime và cross-invalidation.

- [x] **Step 1: Chạy build production bundle**
  `npm run build` trong `frontend/` đạt kết quả 0 lỗi, 0 cảnh báo type error.
- [x] **Step 2: Xác minh quy chuẩn thiết kế UI**
  Rà soát các nhãn đồng bộ và giao diện đảm bảo 100% không dùng emoji hay icon trang trí thừa.
