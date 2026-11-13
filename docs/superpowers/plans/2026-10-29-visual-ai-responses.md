# Visual AI Chatbot Responses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nâng cấp toàn diện trải nghiệm hiển thị trực quan của Chatbot AI (FPT Shop Pricing Copilot): hỗ trợ render Markdown chuẩn mực, bảng số liệu gắn Badge cảnh báo rủi ro DOH/Giá kèm nút tương tác 1-click, chip gợi ý làm rõ cấu hình thông minh, và thẻ giải trình 3 lớp có thanh trực quan hóa biên an toàn giá sàn không dùng icon/emoji.

**Architecture:** Tạo các component chuyên trách tách biệt (Deep Modules): `MarkdownRenderer` (render typography có cấu trúc từ `react-markdown`), `AiDataTable` (trực quan hóa dữ liệu bảng với conditional formatting DOH/Giá và action callback), `InteractivePromptChips` (trích xuất chip lựa chọn cấu hình tự động từ kết quả), và refactor `ExplainableCard` (bổ sung Safety Margin Progress Bar, loại bỏ icon theo chuẩn enterprise).

**Tech Stack:** React 18, TypeScript, Tailwind CSS, `react-markdown`.

---

## Global Constraints

- Không sử dụng bất kỳ biểu tượng cảm xúc (emoji) hay icon đồ họa trong toàn bộ giao diện (Tuân thủ nghiêm ngặt Quy tắc 9 trong AGENTS.md).
- Toàn bộ component phải có kiểu dữ liệu TypeScript chặt chẽ, không có type `any` lỏng lẻo.
- Mọi kiểm thử chức năng thực hiện qua API / Integration / Build verification, không kiểm thử qua trình duyệt (Quy tắc 10).
- Bảo đảm tương thích hoàn toàn với cả chế độ Light Mode và Dark Mode (`dark:` classes).

---

## Task 1: Cài đặt Thư viện react-markdown & Xây dựng MarkdownRenderer Component

**Files:**
- Create: `frontend/src/components/ai/MarkdownRenderer.tsx`
- Modify: `frontend/package.json`

**Steps:**
- [ ] Cài đặt `react-markdown` bằng lệnh `npm.cmd --prefix frontend install react-markdown`.
- [ ] Xây dựng component `MarkdownRenderer.tsx` với Tailwind Typography tùy biến:
  - Header (`h1`, `h2`, `h3`): font đậm, kích thước phân cấp rõ ràng, margin chuẩn.
  - Paragraph (`p`): leading-relaxed, text-slate-800 / text-slate-100.
  - Lists (`ul`, `ol`, `li`): list-disc, list-decimal, indent phù hợp.
  - Bold (`strong`): font-semibold, text-slate-900 / text-white.
  - Code inline (`code`) & code block (`pre`): font-mono, background contrast nhẹ.
  - Blockquote (`blockquote`): viền trái màu cam `border-l-2 border-orange-500`, nền xám nhạt.
- [ ] Xác minh biên dịch TypeScript không phát sinh lỗi.

---

## Task 2: Xây dựng AiDataTable với Conditional Formatting & Nút Hành Động 1-Click

**Files:**
- Create: `frontend/src/components/ai/AiDataTable.tsx`

**Steps:**
- [ ] Xây dựng component `AiDataTable` tiếp nhận `data: Record<string, any>[]` và `onAction?: (actionType: string, row: Record<string, any>) => void`.
- [ ] Tự động nhận diện các cột dữ liệu chính:
  - Cột `DOH` / `Số ngày lưu kho`: Nếu giá trị >= 45 ngày -> hiển thị badge màu đỏ/hổ phách cảnh báo (`bg-rose-50 text-rose-700 border-rose-300 dark:bg-rose-950/40 dark:text-rose-400`); nếu an toàn -> badge xanh lá/xám.
  - Cột giá tiền (`Giá FPT`, `Giá sàn`, `Đối thủ`): Căn phải (text-right), font monospace dễ so sánh chữ số.
- [ ] Bổ sung cột hành động nhanh (Action Column) ở cuối mỗi hàng:
  - Nút bấm `[Phân tích]`: 1-click kích hoạt gửi yêu cầu phân tích SKU tương ứng mà không cần gõ phím.
- [ ] Đảm bảo giao diện có thanh cuộn ngang mượt mà, sticky header, hỗ trợ Dark Mode.

---

## Task 3: Xây dựng InteractivePromptChips Làm Rõ Cấu Hình & Biến Thể

**Files:**
- Create: `frontend/src/components/ai/InteractivePromptChips.tsx`

**Steps:**
- [ ] Xây dựng component `InteractivePromptChips` nhận `suggestions?: string[]`, `tableData?: Record<string, any>[]`, và `onSelectPrompt: (prompt: string) => void`.
- [ ] Logic sinh chip thông minh:
  - Ưu tiên 1: Hiển thị danh sách `suggestions` do AI hoặc backend trả về.
  - Ưu tiên 2: Nếu có `tableData` với các dòng sản phẩm, tự động trích xuất mã SKU hoặc tên model tạo thành các chip ngắn gọn: `"Xem chi tiết [SKU]"`, `"So sánh giá [SKU]"`.
- [ ] Thiết kế chip: Nút bấm bo tròn tinh tế, viền mảnh, hover hiệu ứng màu cam, không dùng icon, hiển thị phân cấp nhãn rõ ràng.

---

## Task 4: Nâng cấp Thẻ Giải Trình 3 Lớp (ExplainableCard) với Safety Margin Progress Bar

**Files:**
- Modify: `frontend/src/components/ai/ExplainableCard.tsx`

**Steps:**
- [ ] Loại bỏ toàn bộ icon của Lucide-React (`TrendingDown`, `Package`, `ShieldCheck`) để tuân thủ 100% Rule 9.
- [ ] Thay thế bằng các tag phân loại text chuẩn doanh nghiệp:
  - Lớp 1: `[LỚP 1: THỊ TRƯỜNG ĐỐI THỦ]` (Tone màu Rose)
  - Lớp 2: `[LỚP 2: HIỆN TRẠNG TỒN KHO]` (Tone màu Amber)
  - Lớp 3: `[LỚP 3: BẢO VỆ GIÁ SÀN]` (Tone màu Emerald)
- [ ] Thêm thanh tiến trình trực quan (Visual Progress Bar) thể hiện biên độ an toàn giá sàn:
  - Thước đo phần trăm an toàn (`safety_margin_percent`): Hiển thị thanh bar với vạch giá sàn và khoảng cách biên độ lợi nhuận.
  - Cảnh báo rõ ràng nếu `is_capped` được kích hoạt (chạm ngưỡng giá sàn).

---

## Task 5: Tích hợp vào ExpandedAiDrawer, Kiểm thử & Đóng gói

**Files:**
- Modify: `frontend/src/components/ai/ExpandedAiDrawer.tsx`

**Steps:**
- [ ] Nhập `MarkdownRenderer`, `AiDataTable`, và `InteractivePromptChips` vào `ExpandedAiDrawer`.
- [ ] Thay thế khối văn bản raw `{msg.content}` bằng `<MarkdownRenderer content={msg.content} />`.
- [ ] Thay thế bảng HTML hiện tại bằng `<AiDataTable data={msg.tableData} onAction={handleTableAction} />`.
- [ ] Tích hợp `<InteractivePromptChips>` ở cuối mỗi câu trả lời của trợ lý.
- [ ] Chạy lệnh build kiểm thử: `npm.cmd --prefix frontend run build`.
- [ ] Chạy toàn bộ test suite backend xác nhận tính toàn vẹn hệ thống (`pytest`).

