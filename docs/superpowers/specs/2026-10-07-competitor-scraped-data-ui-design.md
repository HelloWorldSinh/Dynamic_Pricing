# Design Spec: Màn hình Hiển thị Kết quả Cào Dữ liệu Đối thủ (Competitor Feeds)

- **Ngày tạo:** 2026-10-07
- **Tác giả:** Antigravity AI & Pricing Analyst
- **Trạng thái:** Approved by User
- **Phạm vi:** Frontend React Application (`frontend/`)

---

## 1. Bối cảnh & Mục tiêu

Hệ thống Dynamic Pricing liên tục cào dữ liệu giá và cấu hình từ 2 đối thủ cạnh tranh chính (CellphoneS và Hoàng Hà Mobile). Hiện tại, dữ liệu cào thô chỉ được hiển thị ở dạng bảng nhỏ đơn giản cuối trang quản trị Crawler (`CrawlManagerPage`), gây khó khăn cho chuyên viên định giá (Pricing Analyst) khi muốn:
1. Quan sát toàn cảnh số lượng, độ tươi mới và tình trạng kho hàng của đối thủ.
2. Tra cứu, đối soát nhanh cấu hình bóc tách chi tiết (CPU, RAM, màn hình...) của sản phẩm đối thủ.
3. Kiểm tra tính toàn vẹn của dữ liệu cào thô (JSON format) để đánh giá chất lượng bộ bóc tách.

**Mục tiêu:** Xây dựng màn hình chuyên biệt **`CompetitorFeedsPage`** trên Sidebar chính, đóng vai trò là Hub khai thác và tra cứu toàn bộ nguồn cấp dữ liệu thị trường (Market Intelligence Feeds).

---

## 2. Kiến trúc & Vị trí Điều hướng (Navigation)

### 2.1. Cập nhật Sidebar Navigation
- Thêm định danh tab mới `feeds` vào `NavTab` trong `frontend/src/components/layout/Sidebar.tsx`:
  ```typescript
  export type NavTab = 'matrix' | 'approvals' | 'mapping' | 'feeds' | 'crawler' | 'simulator';
  ```
- Thuộc tính mục menu:
  - **Label:** `Dữ liệu Đối thủ`
  - **Icon:** `Database` (từ `lucide-react`)
  - **Vị trí:** Giữa `SKU Mapping Queue` và `Crawl Operations`.
  - **Badge:** Hiển thị tổng số sản phẩm đối thủ thu thập được.

### 2.2. Điều hướng tại `App.tsx`
- Đăng ký nhánh render:
  ```tsx
  {activeTab === 'feeds' && (
    <CompetitorFeedsPage categoryFilter={categoryFilter} />
  )}
  ```

---

## 3. Cấu trúc Thành phần Giao diện (Deep Modules)

Toàn bộ các component liên quan được tổ chức trong thư mục `frontend/src/components/competitor/`:

### 3.1. `CompetitorSummaryCards.tsx` (Thanh KPI đầu bảng)
Hiển thị 4 thẻ thông số điều hành:
1. **Tổng bản ghi cào được (Total Crawled):** Số lượng tổng, tỷ lệ phân bổ.
2. **Dữ liệu CellphoneS:** Số lượng, tỷ trọng %, badge đỏ nhận diện (`CELLPHONES`).
3. **Dữ liệu Hoàng Hà Mobile:** Số lượng, tỷ trọng %, badge cam nhận diện (`HOANGHA`).
4. **Tỷ lệ còn hàng & Cập nhật mới nhất:** Tỷ lệ còn hàng (% in-stock), số lượng hết hàng, mốc thời gian cào mới nhất.

### 3.2. `CompetitorFilterBar.tsx` (Thanh công cụ lọc & tìm kiếm)
Cung cấp các công cụ:
- **Tìm kiếm tức thì:** Theo tên sản phẩm, đường dẫn URL hoặc mã Part/Model.
- **Bộ lọc nguồn:** Tất cả / CellphoneS / Hoàng Hà Mobile.
- **Bộ lọc trạng thái kho:** Tất cả / Chỉ còn hàng / Tạm hết hàng.
- **Sắp xếp:** Mới cào nhất / Cũ nhất / Giá cao đến thấp / Giá thấp đến cao.

### 3.3. `CompetitorDataTable.tsx` (Bảng dữ liệu trung tâm)
- **Cột Nguồn:** Badge phân biệt rõ ràng CellphoneS (đỏ) vs Hoàng Hà (cam).
- **Cột Tên sản phẩm:** Tên sản phẩm cào về kèm nút mở link trang gốc (`ExternalLink`).
- **Cột Giá bán:** Font monospace in đậm định dạng VND (`formatCurrencyVND`), hiển thị giá niêm yết gạch ngang nếu có.
- **Cột Trạng thái kho:** Badge xanh lá (*Còn hàng*) hoặc xám (*Tạm hết hàng*).
- **Cột Thời điểm cào:** Định dạng ngày giờ chuẩn (`crawled_at`).
- **Cột Thao tác:** Nút xem chi tiết thông số kỹ thuật (mở Drawer).
- Tích hợp component `Pagination.tsx` hiện có để phân trang mượt mà (chọn 10, 20, 50 bản ghi/trang).

### 3.4. `CompetitorSpecsDrawer.tsx` (Drawer chi tiết kỹ thuật)
- Trượt vào từ cạnh phải màn hình với hiệu ứng mượt mà.
- **Header:** Tên sản phẩm, nguồn đối thủ, giá bán, link bài viết gốc.
- **Tab 1: Bảng Thông số Bóc tách (Parsed Specs):** Hiển thị dạng bảng key-value có chia nhóm trực quan (Bộ vi xử lý, Bộ nhớ & Ổ cứng, Màn hình, Đồ họa...).
- **Tab 2: Dữ liệu thô (Raw JSON):** Hiển thị JSON có màu sắc cú pháp kèm nút sao chép `Copy JSON`.

---

## 4. Tầng Dữ liệu & API Contracts

### 4.1. Mở rộng Type Definition (`frontend/src/types/crawl.ts`)
```typescript
export type CrawlSource = 'FPT' | 'CELLPHONES' | 'HOANGHA';

export interface CrawlResult {
  id: string | number;
  source: CrawlSource;
  product_name: string;
  url: string;
  price: number;
  original_price?: number;
  is_in_stock: boolean;
  stock_status_text?: string;
  specifications?: Record<string, any>;
  crawled_at: string;
  category?: string;
}
```

### 4.2. API Adapter (`frontend/src/api/crawlerApi.ts`)
- Chuẩn hóa hàm `getCrawlResultsApi(source, category, limit)`.
- Adapter tự động map các trường từ backend SQLAlchemy ORM:
  - `raw_name` -> `product_name`
  - `current_price` -> `price`
  - `raw_specs` -> `specifications`
- Mock fallback phong phú sẵn sàng trong `mockData.ts` khi môi trường backend không sẵn sàng.

---

## 5. Kế hoạch Kiểm thử & Xác minh

1. **TypeScript Typecheck:** Chạy kiểm tra không có type error, không có unused imports (`npm run build` hoặc type check).
2. **Kiểm thử Giao diện:**
   - Điều hướng tab `feeds` từ Sidebar.
   - Thử nghiệm các bộ lọc tìm kiếm và phân trang.
   - Kiểm tra hiển thị Drawer specs và nút copy JSON.
   - Đảm bảo hiển thị hoàn hảo ở cả Light Mode và Dark Mode.
