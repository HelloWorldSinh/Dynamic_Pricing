# KẾ HOẠCH TRIỂN KHAI: THU THẬP DỮ LIỆU & ĐỐI SOÁT GHÉP CẶP SKU XUẤT FILE EXCEL

> **Mục tiêu chính:** Xuất ra 1 file Excel duy nhất (`data/crawl_and_sku_mapping_output.xlsx`) gồm:
> - **Sheet 1 (`Scraped_All_Data`):** Lưu trữ toàn bộ dữ liệu cào thô thu thập được từ website đối thủ (CellphoneS, Hoàng Hà).
> - **Sheet 2 (`SKU_Mapping`):** Bảng đối soát ghép cặp sản phẩm cào được với danh mục chuẩn 329 SKU của FPT Shop trong `data/dim_product.xlsx`.

---

## 📚 CÁC SKILL ECC ÁP DỤNG TRONG KẾ HOẠCH

| STT | Skill ECC | Vai trò trong quy trình |
|:---:|---|---|
| **1** | [`data-scraper-agent`](.agents/skills/data-scraper-agent/SKILL.md) | Triển khai tầng **Collect** & **Enrich**: Gửi request kèm headers chống bot, bóc tách giá hiện tại/giá cũ, nhận diện trạng thái hết hàng và bóc tách bảng thông số kỹ thuật. |
| **2** | [`regex-vs-llm-structured-text`](.agents/skills/regex-vs-llm-structured-text/SKILL.md) | Xây dựng thuật toán SKU Matching 2 tầng: Dùng Regex trích xuất mã Part-Number (100% confidence) kết hợp bóc tách thuộc tính cứng (RAM, ROM, CPU, màu) bằng RapidFuzz/Levenshtein. |
| **3** | [`python-patterns`](.agents/skills/python-patterns/SKILL.md) & [`inventory-demand-planning`](.agents/skills/inventory-demand-planning/SKILL.md) | Xử lý dữ liệu bảng với Pandas & OpenPyXL: Tự động format file Excel chuyên nghiệp (căn lề, autofit độ rộng cột, định dạng tiền tệ VND, tô màu trạng thái). |
| **4** | [`verification-loop`](.agents/skills/verification-loop/SKILL.md) | Kiểm thử chất lượng dữ liệu: Đảm bảo không bị null giá, đo lường tỷ lệ ghép cặp thành công (% Exact Match, % Fuzzy Match, % Cần review). |

---

## 🗺️ LỘ TRÌNH 4 BƯỚC TRIỂN KHAI CHI TIẾT

```
  ┌──────────────────────────────────────────────────────────────┐
  │ BƯỚC 1: Thu thập Dữ liệu Cào (Data Scraping - All Data)      │
  │ └─ Cào danh sách sản phẩm thực tế từ đối thủ (CellphoneS,..) │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
  ┌──────────────────────────────▼──────────────────────────────┐
  │ BƯỚC 2: Xây dựng Thuật toán So khớp SKU (Matching Engine)   │
  │ └─ Đối soát với 329 SKU trong dim_product.xlsx               │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
  ┌──────────────────────────────▼──────────────────────────────┐
  │ BƯỚC 3: Đóng gói & Xuất File Excel 2 Sheet Chuẩn Báo Cáo    │
  │ └─ Sheet 1: Scraped_All_Data  |  Sheet 2: SKU_Mapping        │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
  ┌──────────────────────────────▼──────────────────────────────┐
  │ BƯỚC 4: Kiểm Thử, Đánh Giá Tỷ Lệ Khớp & Bàn Giao             │
  │ └─ Đo lường tỷ lệ khớp và xuất báo cáo nghiệm thu            │
  └─────────────────────────────────────────────────────────────┘
```

---

### 🔹 BƯỚC 1: Thu Thập Dữ Liệu Cào (Data Scraping - All Data)
- **Mục tiêu:** Thu thập dữ liệu sản phẩm từ website đối thủ (CellphoneS) cho các ngành hàng Laptop & Điện thoại.
- **Nội dung công việc:**
  1. Viết script/service crawler mở rộng thu thập danh sách sản phẩm (Laptop / Smartphone).
  2. Bóc tách đầy đủ các trường thông tin:
     - `source`: Tên nguồn cào (ví dụ: `CELLPHONES`).
     - `scraped_product_name`: Tên đầy đủ hiển thị trên website đối thủ.
     - `url`: Đường dẫn link sản phẩm gốc.
     - `current_price`: Giá bán thực tế (số nguyên VND).
     - `original_price`: Giá niêm yết cũ (nếu có).
     - `is_in_stock`: Trạng thái còn hàng (`True` / `False`).
     - `specifications`: Bảng thông số kỹ thuật (dạng chuỗi/JSON tóm tắt CPU, RAM, ROM, Card...).
- **Tiêu chí hoàn thành (DoD):**
  - Trích xuất thành công tối thiểu 20-30 sản phẩm thực tế từ website đối thủ.
  - Dữ liệu giá được làm sạch thành số nguyên chuẩn, không bị lỗi encoding hay lỗi null tên sản phẩm.

---

### 🔹 BƯỚC 2: Thuật Toán Đối Soát & Ghép Cặp SKU (SKU Matching Engine)
- **Mục tiêu:** Đối chiếu dữ liệu cào ở Bước 1 với 329 SKU chuẩn trong `data/dim_product.xlsx` và gán nhãn độ tin cậy theo cấu trúc model `app/models/sku_mapping.py`.
- **Cơ chế 2 tầng so khớp:**
  1. **Tầng 1 (Exact Match bằng Regex Part-Number):**
     - Áp dụng biểu thức chính quy Regex để bóc tách mã hiệu Part-Number (ví dụ: `A715-59G-57TU`, `83JC00LVVN`, `FA506NC-HN011W`).
     - Nếu trùng khớp Part-Number $\to$ Gán `match_type = EXACT_PART_NUMBER`, `confidence_score = 1.0` (100%), `status = APPROVED`.
  2. **Tầng 2 (Fuzzy Attribute Matching bằng RapidFuzz/Levenshtein):**
     - Làm sạch chuỗi tên (loại bỏ từ rác: "Chính hãng", "VN/A", "Đã kích hoạt", v.v.).
     - Trích xuất và so khớp các thuộc tính cứng: **Dòng máy + Chip CPU + Dung lượng RAM + Dung lượng Ổ cứng/Bộ nhớ trong**.
     - Tính điểm tương đồng `confidence_score`:
       - Điểm $\ge 0.85$: Gán `match_type = NORMALIZED_ATTRIBUTE`, `status = APPROVED`.
       - Điểm từ $0.60$ đến $0.84$: Gán `match_type = NORMALIZED_ATTRIBUTE`, `status = PENDING` (Hàng đợi cần duyệt thủ công).
       - Điểm $< 0.60$: Không khớp (Unmatched).
- **Tiêu chí hoàn thành (DoD):**
  - Mọi sản phẩm cào về đều được phân loại rõ ràng: Khớp chính xác, Khớp gần đúng (kèm điểm số %) hoặc Không tìm thấy SKU tương ứng.

---

### 🔹 BƯỚC 3: Đóng Gói & Xuất File Excel 2 Sheet Chuẩn Báo Cáo
- **Mục tiêu:** Tạo file Excel hoàn chỉnh `data/crawl_and_sku_mapping_output.xlsx` gồm 2 sheet rõ ràng.
- **Quy cách định dạng:**
  - **Sheet 1: `Scraped_All_Data`**
    - Các cột: `STT`, `Nguồn Cào`, `Tên Sản Phẩm Cào Được`, `Giá Bán (VND)`, `Giá Niêm Yết (VND)`, `Tình Trạng Hàng`, `Thông Số Kỹ Thuật Tóm Tắt`, `URL Sản Phẩm`, `Thời Gian Cào`.
  - **Sheet 2: `SKU_Mapping`**
    - Các cột: `STT`, `Mã SKU Chuẩn (FPT)`, `Tên Sản Phẩm Chuẩn (FPT)`, `Nguồn Đối Thủ`, `Tên Sản Phẩm Đối Thủ Cào Về`, `Giá Đối Thủ (VND)`, `Loại Khớp (Match Type)`, `Độ Tin Cậy (Confidence %)`, `Trạng Thái (Status)`, `Chênh Lệch Giá (FPT vs Đối Thủ)`.
  - **Format thẩm mỹ:**
    - Cột giá tiền có định dạng phân cách hàng nghìn (`#,##0 "₫"`).
    - Cột Độ tin cậy định dạng phần trăm (`0.0%`).
    - Tự động căn chỉnh độ rộng cột vừa vặn với nội dung text (Auto-fit Column Width).
    - Highlight màu trực quan: Xanh lá (Khớp 100%), Vàng cam (Cần duyệt), Đỏ (Hết hàng).
- **Tiêu chí hoàn thành (DoD):**
  - File Excel mở được trơn tru, hiển thị đầy đủ 2 sheet với format số liệu chuẩn.

---

### 🔹 BƯỚC 4: Kiểm Thử Tự Động & Đánh Giá Tỷ Lệ Khớp (Verification & Review)
- **Mục tiêu:** Kiểm tra toàn diện chất lượng file kết quả theo `verification-loop`.
- **Nội dung công việc:**
  1. Chạy script kiểm tra tự động xem có dòng nào bị lỗi format, thiếu giá hoặc sai lệch công thức.
  2. Báo cáo thống kê:
     - Tổng số sản phẩm cào về.
     - Tỷ lệ khớp SKU (% Exact Match, % Fuzzy Match).
     - Danh sách các trường hợp cần nhân viên duyệt lại (Pending).
- **Tiêu chí hoàn thành (DoD):**
  - Có bản tóm tắt kết quả nghiệm thu chi tiết để người dùng kiểm tra chéo thực tế.

---

## 📌 NGUYÊN TẮC THỰC HIỆN
- **Làm tuần tự từng bước:** Hoàn thành và kiểm tra kỹ lưỡng Bước 1 trước khi tiến hành Bước 2.
- **Minh bạch mã nguồn:** Mọi đoạn code thực thi đều được ghi chú rõ ràng theo chuẩn thiết kế Deep Module của dự án.
