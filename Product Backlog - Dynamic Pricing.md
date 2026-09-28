# **PRODUCT BACKLOG — DYNAMIC PRICING SYSTEM**

## **1\. Product Goal**

Xây dựng hệ thống **Dynamic Pricing** tự động hóa việc thu thập giá đối thủ (CellphoneS, Hoàng Hà Mobile), so khớp sản phẩm với FPT Shop, đề xuất điều chỉnh giá dựa trên quy tắc nghiệp vụ kết hợp tồn kho, và cung cấp trợ lý AI Chat hỗ trợ tra cứu nhanh — nhằm thay thế quy trình dò giá thủ công bằng Excel, tăng tốc phản ứng giá và bảo vệ biên lợi nhuận.  
**Đối tượng sử dụng chính (Primary Actor):** Pricing Analyst (Chuyên viên phân tích giá) — Đóng vai trò người dùng duy nhất (Single User / All-in-one) vận hành toàn bộ chu trình trên hệ thống trong phạm vi MVP (từ kích hoạt cào dữ liệu, đối soát SKU, theo dõi ma trận giá, duyệt gợi ý giá đến khai thác trợ lý AI).

## ---

**2\. Tiêu chuẩn & Quy ước Backlog**

> * Mỗi PBI tuân thủ tiêu chuẩn **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable).  
> * Backlog tổng thể tuân thủ tiêu chuẩn **DEEP** (Detailed appropriately, Estimated, Emergent, Prioritized).  
> * Ưu tiên theo **MoSCoW**: Must / Should / Could / Won't.  
> * Ước lượng bằng Story Points theo thang Fibonacci (1, 2, 3, 5, 8, 13).  
> * Acceptance Criteria dùng kết hợp: Given-When-Then và Checklist.  
> * **Definition of Ready (DoR):** User Story/mô tả rõ ràng, AC ≥ 2 điều kiện, SP đã ước lượng, không còn blocker.  
> * **Definition of Done (DoD):** Code pass review, chạy đúng trên môi trường test, tất cả AC đều PASS, code push Git repo.  
> * **Refinement:** Dành \~10% thời gian Sprint để rà soát và cập nhật backlog.  
> * **Mô hình Actor (Single User Scope):** Quy chuẩn về 1 Actor duy nhất là Pricing Analyst thao tác trên Dashboard tập trung, chưa triển khai RBAC/Auth phức tạp.  
> * **Loại bỏ Epic kỹ thuật:** PBI-019 (DB) và PBI-020 (API) được nhúng thành sub-task kỹ thuật trong các PBI nghiệp vụ, tuân thủ nguyên tắc INVEST.

## ---

**3\. Chi tiết Product Backlog Items (PBI)**

### **EPIC 1: Thu thập Dữ liệu**

#### **PBI-001 — Cào giá sản phẩm FPT Shop (Điện thoại & Laptop)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 8 | **Sprint:** Sprint 1  
*User Story:* As a pricing analyst, I want to automatically scrape product prices and availability from fptshop.com.vn so that I have the baseline data to compare against competitors.  
**Acceptance Criteria:**

> * Given script cào được kích hoạt, When chạy trên danh mục Điện thoại và Laptop, Then trả về danh sách sản phẩm gồm: tên sản phẩm, giá bán lẻ hiển thị, URL gốc, trạng thái còn/hết hàng, thời điểm crawl.  
> * Dữ liệu crawl được lưu vào database với timestamp.  
> * Áp dụng request throttling (delay ngẫu nhiên 2-5s) và User-Agent rotation.  
> * Tỉ lệ crawl thành công ≥ 95% trên tập mẫu 100 sản phẩm.

#### **PBI-002 — Cào giá sản phẩm CellphoneS**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 8 | **Sprint:** Sprint 1  
*User Story:* As a pricing analyst, I want to automatically scrape product prices from cellphones.com.vn so that I can compare CellphoneS prices against FPT Shop.  
**Acceptance Criteria:**

> * Given script chạy trên danh mục Điện thoại/Laptop CellphoneS, When crawl hoàn tất, Then trả về: tên sản phẩm, giá hiển thị (cash price trên web), trạng thái (Còn hàng / Tạm hết / Sắp về hàng), URL gốc.  
> * Sản phẩm có trạng thái "Sắp về hàng" được đánh dấu là Out-of-stock.  
> * Lọc bỏ sản phẩm "Đã kích hoạt" / "Hàng cũ" / "Đổi trả" khỏi tập so sánh chính.  
> * Request throttling và User-Agent rotation được cấu hình.

#### **PBI-003 — Cào giá sản phẩm Hoàng Hà Mobile**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 8 | **Sprint:** Sprint 1  
*User Story:* As a pricing analyst, I want to automatically scrape product prices from hoanghamobile.com so that I can compare Hoàng Hà prices against FPT Shop.  
**Acceptance Criteria:**

> * Given script chạy trên danh mục Điện thoại/Laptop Hoàng Hà, When crawl hoàn tất, Then trả về: tên sản phẩm, giá hiển thị, trạng thái nút mua hàng (Online / Tại shop / Hết hàng), URL gốc.  
> * Sản phẩm có trạng thái "Ngừng kinh doanh", "Dừng nhận đơn online" → đánh dấu Out-of-stock.  
> * Bóc tách Part-Number từ tiêu đề/URL (đặc biệt Laptop) để phục vụ SKU Matching.

#### **PBI-004 — Nút kích hoạt cào tức thời (On-demand Trigger)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 3 | **Sprint:** Sprint 1  
*User Story:* As a pricing analyst, I want to trigger a scraping job immediately via a button on the UI so that I can quickly refresh price data and demonstrate/test the system without waiting for the scheduled job.  
**Acceptance Criteria:**

> * Given người dùng ở trang Dashboard, When nhấn nút "Trigger Crawl", Then hệ thống chạy job cào tức thì cho danh mục đã chọn và hiển thị trạng thái tiến trình (đang chạy / hoàn tất / lỗi).  
> * Có cơ chế debounce — không cho phép nhấn liên tục trong vòng 30s.  
> * Kết quả crawl mới hiển thị trên bảng so sánh ngay sau khi hoàn tất.

#### **PBI-005 — Lịch cào tự động (Scheduled Scraping)**

**Loại:** Feature | **Ưu tiên:** Should Have | **Story Points:** 3 | **Sprint:** Sprint 1  
*User Story:* As a pricing analyst, I want to configure the scraping schedule to run automatically twice a day so that the price data stays current without manual intervention.  
**Acceptance Criteria:**

> * Cron job chạy 2 lần/ngày (ví dụ: 08:00 và 18:00).  
> * Log ghi nhận thời điểm bắt đầu, kết thúc, số sản phẩm crawl thành công/thất bại.  
> * Nếu job thất bại, retry tự động 1 lần sau 10 phút.

### ---

**EPIC 2: So khớp Sản phẩm (SKU Matching Engine)**

#### **PBI-006 — Khớp chính xác bằng Part-Number (Exact Match)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 5 | **Sprint:** Sprint 1  
*User Story:* As a pricing analyst, I want the system to automatically match competitor products to FPT Shop products using manufacturer part-numbers so that I can trust the price comparison is between identical products.  
**Acceptance Criteria:**

> * Given sản phẩm Hoàng Hà/CellphoneS có Part-Number trong tiêu đề/URL, When hệ thống chạy matching, Then match với mã Part-Number trong cơ sở dữ liệu FPT Shop với Confidence Score \= 100%.  
> * Regex parser bóc tách đúng mã Part-Number Laptop (ví dụ: 83JC00LVVN, EB355W).  
> * Kết quả match lưu vào bảng mapping SKU với trường: FPT\_SKU, Competitor\_SKU, Confidence, Source, Matched\_At.

#### **PBI-007 — Khớp thuộc tính chuẩn hóa (Normalized Attribute Match)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 8 | **Sprint:** Sprint 1  
*User Story:* As a pricing analyst, I want the system to match products by normalized attributes (brand \+ model \+ CPU \+ RAM \+ storage \+ color) when part-numbers are unavailable, so that the majority of products can still be compared.  
**Acceptance Criteria:**

> * Chuẩn hóa tên: xóa từ khóa rác ("Chính hãng", "Đã kích hoạt", "Cũ", "Đổi trả", "Quà tặng").  
> * Trích xuất thuộc tính cứng: Dòng máy \+ CPU \+ RAM \+ ROM/SSD \+ Màu sắc.  
> * Tính Confidence Score (80%–95%) bằng thuật toán Levenshtein / Cosine Similarity kết hợp so sánh thuộc tính.  
> * Ngưỡng khớp: ≥ 95% → tự động chấp nhận, 80%–94% → cần review, \< 80% → không match.

#### **PBI-008 — Giao diện duyệt khớp thủ công (Manual Mapping Queue)**

**Loại:** Feature | **Ưu tiên:** Should Have | **Story Points:** 5 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want to review and manually approve/reject product matches with medium confidence scores (60%–79%) so that no incorrect price comparisons enter the system.  
**Acceptance Criteria:**

> * Given hệ thống có sản phẩm match với confidence 60%–79%, When pricing analyst mở queue, Then hiển thị cặp sản phẩm song song (FPT Shop vs Đối thủ) kèm confidence score và link URL gốc.  
> * Người dùng có thể Approve (xác nhận match) hoặc Reject (hủy match).  
> * Kết quả Approve được lưu lại — lần match sau sẽ tự nhận diện với 100% confidence.

### ---

**EPIC 3: Chiến lược & Gợi ý Giá (Pricing Strategy Engine)**

#### **PBI-009 — Nạp dữ liệu tồn kho giả lập FPT Shop**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 3 | **Sprint:** Sprint 1  
*User Story:* As a system, I need to ingest mock inventory data from FPT Shop (provided by Mentor) so that the pricing engine can factor in stock levels and floor prices.  
**Acceptance Criteria:**

> * Đọc file dữ liệu giả lập gồm các trường: Mã SKU, Số lượng tồn khả dụng, Số ngày lưu kho (DOH), Giá vốn, Giá sàn (Floor Price).  
> * Dữ liệu được lưu vào database và liên kết với bảng sản phẩm FPT Shop.  
> * Hỗ trợ cập nhật lại khi mentor đưa file mới.

#### **PBI-010 — Quy tắc bảo vệ giá sàn (Floor Price Protection)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 3 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want the system to never recommend a price below Cost \+ Minimum Margin so that profitability is always protected.  
**Acceptance Criteria:**

> * Given giá sàn \= Giá vốn \+ Biên lợi nhuận tối thiểu, When hệ thống tính giá đề xuất, Then KHÔNG BAO GIỜ đề xuất giá dưới giá sàn.  
> * Nếu giá đề xuất theo logic \< giá sàn → hệ thống tự cap về giá sàn và ghi log cảnh báo.

#### **PBI-011 — Quy tắc gợi ý giá theo tồn kho (DOH-based Recommendation)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 5 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want the system to recommend price adjustments based on inventory age (DOH) and competitor stock status so that slow-moving stock is cleared faster and scarce items maximize profit.  
**Acceptance Criteria:**

> * DOH \> 45 ngày \+ đối thủ còn hàng → đề xuất giảm giá bám sát đối thủ (trong biên giá sàn).  
> * DOH thấp \+ đối thủ hết hàng → đề xuất giữ giá hoặc tăng nhẹ.  
> * Đối thủ có trạng thái Out-of-stock → KHÔNG kích hoạt luật hạ giá theo.  
> * Phân cấp trọng số: CellphoneS \= trọng số chính; Hoàng Hà \= trọng số phụ (cho phép FPT cao hơn 2%–5%).

#### **PBI-012 — Luồng phê duyệt giả lập (Approval Workflow)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 3 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want to approve or reject each price recommendation via an Approve/Reject button so that no price change is applied without human review.  
**Acceptance Criteria:**

> * Given hệ thống đã tạo đề xuất giá cho sản phẩm X, When người dùng nhấn Approve, Then trạng thái chuyển sang "Approved" và ghi log ai duyệt \+ thời điểm.  
> * Nhấn Reject → trạng thái "Rejected".  
> * Giao diện lọc được: Chờ duyệt / Đã duyệt / Đã từ chối.  
> * Đây là giả lập — KHÔNG ghi đè lên giá ERP/POS thật.

### ---

**EPIC 4: Giao diện & Bảng so sánh Giá (Dashboard & Analytics)**

#### **PBI-013 — Bảng so sánh giá 3 bên (Price Comparison Matrix)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 8 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want to view a side-by-side price comparison table of FPT Shop, CellphoneS, and Hoàng Hà so that I can quickly identify products where FPT Shop is more expensive.  
**Acceptance Criteria:**

> * Bảng hiển thị: Mã SKU FPT, Tên sản phẩm, Giá FPT, Giá CellphoneS, Giá Hoàng Hà, Chênh lệch (số tiền \+ %), Confidence Score, Trạng thái tồn kho FPT, Trạng thái đối thủ.  
> * Mã màu: Đỏ/Cam \= FPT đắt hơn, Xanh lá \= FPT cạnh tranh tốt, Xanh dương \= bằng giá.  
> * Hỗ trợ sắp xếp theo: chênh lệch giá, tên sản phẩm, confidence score.  
> * Responsive trên desktop (tối thiểu 1280px).

#### **PBI-014 — Bộ lọc nghiệp vụ nâng cao**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 5 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want to filter the comparison table by category, price gap threshold, inventory risk, and recommendation status so that I can focus on the most critical items first.  
**Acceptance Criteria:**

> * Lọc theo ngành hàng: Điện thoại / Laptop.  
> * Lọc theo mức chênh lệch: FPT đắt hơn đối thủ từ X% trở lên (mặc định: 5%).  
> * Lọc theo rủi ro tồn kho: DOH \> 30 ngày.  
> * Lọc theo trạng thái đề xuất: Chờ duyệt / Đã duyệt / Đã từ chối.  
> * Lọc chỉ xem đối thủ đang thực sự còn hàng online.  
> * Các bộ lọc có thể kết hợp cùng lúc.

#### **PBI-015 — Màn hình xem kết quả cào (Crawl Results View)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 5 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want to view the raw crawled data in a dedicated screen so that I can verify what the scraper actually collected before it enters the comparison engine.  
**Acceptance Criteria:**

> * Hiển thị bảng dữ liệu raw: nguồn (FPT/CellphoneS/Hoàng Hà), tên sản phẩm, giá, trạng thái, URL, thời điểm cào.  
> * Hỗ trợ tìm kiếm theo tên sản phẩm.  
> * Hiển thị lịch sử các lần cào gần nhất (chọn theo ngày/giờ).  
> * Link URL gốc mở tab mới để kiểm tra chéo trên web đối thủ.

#### **PBI-016 — Modal xem chi tiết sản phẩm (Detail Modal)**

**Loại:** Feature | **Ưu tiên:** Should Have | **Story Points:** 3 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want to click on a product row to see full details including extracted specs and source links so that I can verify the match accuracy.  
**Acceptance Criteria:**

> * Modal hiển thị: thông số kỹ thuật bóc tách được (CPU, RAM, ROM/SSD, Màu), URL nguồn, confidence score, lịch sử giá nếu có.  
> * Link URL nguồn clickable → mở tab mới.

### ---

**EPIC 5: Trợ lý AI Chat (AI Pricing Assistant)**

#### **PBI-017 — Chatbot hỏi đáp nghiệp vụ (RAG-based Chat)**

**Loại:** Feature | **Ưu tiên:** Must Have | **Story Points:** 8 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want to ask natural language questions about product prices, stock levels, and competitor positioning so that I can get instant answers without querying the database manually.  
**Acceptance Criteria:**

> * Khung chat giao diện đơn giản, nhập câu hỏi → nhận câu trả lời.  
> * Trả lời đúng các câu hỏi mẫu: "Liệt kê 5 mẫu laptop ASUS FPT Shop đang đắt hơn CellphoneS", "Mã iPhone nào đang có nguy cơ tồn kho cao?", "So sánh giá Samsung Galaxy S25 giữa 3 bên".  
> * Dữ liệu truy vấn là dữ liệu crawl \+ tồn kho hiện tại trong database.  
> * Thời gian phản hồi ≤ 10 giây cho câu hỏi thông thường.

#### **PBI-018 — Giải thích minh bạch lý do đề xuất (Explainable AI)**

**Loại:** Feature | **Ưu tiên:** Should Have | **Story Points:** 5 | **Sprint:** Sprint 2  
*User Story:* As a pricing analyst, I want to ask the AI why it recommended a specific price change so that I can make an informed approval decision.  
**Acceptance Criteria:**

> * Given người dùng hỏi "Tại sao đề xuất giảm giá sản phẩm X?", When AI xử lý, Then trả lời có cấu trúc 3 lớp:  
  * **Biến động giá đối thủ:** Tên đối thủ vừa giảm, mức giảm cụ thể, trạng thái còn hàng.  
  * **Hiện trạng tồn kho FPT:** Số lượng tồn, DOH hiện tại.  
  * **Kiểm tra an toàn:** Mức giá mới vẫn trên giá sàn bao nhiêu %.

## ---

**4\. Backlog tương lai (Could Have / Extended)**

| ID | Mô tả | Ưu tiên   |
| :---- | :---- | :---- |
| PBI-021 | Bóc tách đa tầng giá (giá sau voucher VNPAY/MoMo, giá Smember) | Could Have |
| PBI-022 | Nhận diện & quy đổi giá trị quà tặng kèm Laptop (balo, chuột) | Could Have |
| PBI-023 | Lưu HTML Snapshot/Screenshot để đối soát | Could Have |
| PBI-024 | Vector Embedding NLP cho SKU matching nâng cao | Could Have |
| PBI-025 | Biểu đồ biến động giá lịch sử (7d/30d/90d) | Could Have |
| PBI-026 | Bản đồ nhiệt cạnh tranh theo phân khúc | Could Have |
| PBI-027 | Xuất báo cáo Excel/PDF | Could Have |
| PBI-028 | Bản tin thị trường tóm tắt đầu ngày (Daily Briefing) | Won't Have (this time) |
| PBI-029 | Cảnh báo chủ động bất thường giá | Won't Have (this time) |
| PBI-030 | Phân tích chiến lược đối thủ bằng AI | Won't Have (this time) |

