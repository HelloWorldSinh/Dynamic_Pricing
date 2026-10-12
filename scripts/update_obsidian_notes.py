# -*- coding: utf-8 -*-
"""Script cap nhat cac file note chi tiet vao Obsidian Vault local."""
import os
import glob
import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8')

vault_matches = glob.glob(r'C:\Users\nguye\OneDrive\*\Obsidian Vault')
if not vault_matches:
    print("Khong tim thay thu muc Obsidian Vault!")
    sys.exit(1)

vault_root = vault_matches[0]
print(f"Obsidian Vault Root: {vault_root}")

# 1. Luồng hoạt động gợi ý giá cả sản phẩm.md
content_luong_hoat_dong = """---
title: Luồng hoạt động gợi ý giá cả sản phẩm
project: Dynamic-Pricing
tags:
  - dynamic-pricing
  - pricing-engine
  - workflow
  - architecture
date: 2026-10-08
status: completed
---

# LUỒNG HOẠT ĐỘNG GỢI Ý GIÁ CẢ SẢN PHẨM (DYNAMIC PRICING PIPELINE)

Tài liệu này đặc tả luồng xử lý toàn diện của hệ thống gợi ý giá động, bao gồm thông số đầu vào, đầu ra và chuỗi gọi hàm từ tầng API xuống cơ sở dữ liệu.

---

## 1. TỔNG QUAN INPUT VÀ OUTPUT

### 1.1. Input Đầu Vào Của Quy Trình
- **`db: Session`**: Phiên làm việc SQLAlchemy Session dùng để truy vấn dữ liệu từ các bảng `products`, `inventory_mock`, `inventory_snapshots`, `sku_mappings`, `crawl_results`, `demand_events` và commit kết quả.
- **`product_id: UUID`**: Định danh duy nhất của sản phẩm FPT Shop cần sinh đề xuất giá.
- **`custom_weights: Optional[Dict[str, float]]`**: Bộ trọng số tùy biến cho 3 trụ cột tín hiệu Nhu cầu (D), Tồn kho (I), Đối thủ (C). Nếu không truyền (giá trị `None`), hệ thống mặc định áp dụng tỷ lệ:
  - Trọng số nhu cầu ($w_D$): `0.40` (40%)
  - Trọng số tồn kho ($w_I$): `0.35` (35%)
  - Trọng số đối thủ ($w_C$): `0.25` (25%)

### 1.2. Output Đầu Ra Của Quy Trình
Đối tượng Model ORM `PriceRecommendation` đã được lưu hoặc cập nhật vào bảng `price_recommendations` với trạng thái ban đầu `"PENDING"`.

Các trường dữ liệu đầu ra chính:
- `id` (UUID): Khóa chính bản ghi đề xuất giá.
- `fpt_product_id` (UUID): ID sản phẩm FPT Shop.
- `current_fpt_price` (BigInteger): Giá bán hiện tại của FPT Shop (VND).
- `competitor_min_price` (BigInteger, nullable): Giá thấp nhất của đối thủ cạnh tranh còn hàng.
- `recommended_price` (BigInteger): Mức giá đề xuất mới sau khi qua ma trận kịch bản và rào cản an toàn Guardrails.
- `price_delta_amount` (BigInteger): Chênh lệch giá tiền tuyệt đối (`recommended_price - current_fpt_price`).
- `price_delta_pct` (Float): Tỷ lệ thay đổi phần trăm giá (ví dụ: `-0.05` tương ứng `-5%`).
- `demand_score` (Float): Điểm nhu cầu thị trường (-2.0 đến +2.0).
- `inventory_score` (Float): Điểm tồn kho / DOH (-2.0 đến +2.0).
- `competitor_score` (Float): Điểm đối thủ (-2.0 đến +2.0).
- `composite_score` (Float): Điểm tổng hợp trọng số: $0.40D + 0.35I + 0.25C$.
- `scenario_name` (String): Tên kịch bản được kích hoạt (ví dụ: `Strong Raise`, `Clearance`, `Hold`...).
- `reasoning_3layers` (JSON): Cấu trúc thuyết minh đa lớp gồm:
  - `competitor_factor`: Phân tích tác động từ giá đối thủ.
  - `inventory_factor`: Phân tích tác động từ số ngày tồn kho (DOH).
  - `market_demand_factor`: Phân tích tác động từ nhu cầu người dùng / lượt xem.
  - `floor_protection_factor`: Trạng thái bảo vệ biên lợi nhuận sàn.
  - `guardrail_notes`: Danh sách ghi chú về rào cản an toàn đã kích hoạt.
- `is_floor_capped` (Boolean): Đánh dấu mức giá đề xuất có chạm mức giá sàn hay không.
- `status` (String): Mặc định là `"PENDING"`.
- `created_at` (DateTime): Thời điểm sinh đề xuất (UTC).

---

## 2. TRÌNH TỰ LUỒNG GỌI HÀM (EXECUTION WORKFLOW)

```text
Khởi động: Yêu cầu định giá từ API hoặc Batch Scheduler
│
▼
1. [[generate_for_product]] (PricingEngine.generate_for_product)
   │
   ├── 1.1. _get_product_price(product)
   │        └── Lấy an toàn giá hiện tại từ product.price hoặc base_retail_price.
   │
   ├── 1.2. Xác định giá vốn và giá sàn bảo vệ
   │        └── Đọc InventoryMock (cost_price, floor_price) hoặc fallback từ Product.
   │
   ├── 1.3. Lọc giá đối thủ thấp nhất còn hàng
   │        └── Query SkuMapping & CrawlResult (is_in_stock = True, current_price > 0).
   │
   ├── 1.4. Gọi [[Sinals signal_extractor]] -> extract_signals(db, product_id)
   │        ├── calculate_demand_score(db, product_id)      -> Demand Score D [-2.0, +2.0]
   │        ├── calculate_inventory_score(db, product_id)   -> Inventory Score I [-2.0, +2.0]
   │        └── calculate_competitor_score(db, product_id)  -> Competitor Score C [-2.0, +2.0]
   │
   ├── 1.5. Gọi [[Extract_resoning_detail]] -> extract_reasoning_details(db, product_id)
   │        └── Sinh 3 chuỗi thuyết minh định lượng về đối thủ, tồn kho DOH, nhu cầu CVR.
   │
   ├── 1.6. Đánh giá ma trận kịch bản & điểm tổng hợp
   │        ├── ScenarioMatrix.evaluate(scores, weights) -> Khớp 10 kịch bản hoặc 7 dải Composite
   │        └── ScenarioMatrix.calculate_composite(scores, weights) -> Composite Score
   │
   ├── 1.7. Kiểm soát rào cản an toàn Guardrails
   │        └── SafetyGuardrails.apply(current_price, target_delta, floor_price, cost_price...)
   │            ├── 1. Rate-of-Change Cap: Hãm sốc giá (+-10% hoặc +-15%)
   │            ├── 2. Margin Floor Check: Khóa giá tại floor_price nếu vi phạm sàn biên lợi nhuận
   │            └── 3. Predatory Pricing Check: Cảnh báo đối thủ bán phá giá < 80% cost_price
   │
   └── 1.8. Đóng gói giải trình 3 lớp & Commit Database
            ├── Đóng gói reasoning_3layers JSON
            ├── Kiểm tra bản ghi PENDING cũ: Cập nhật in-place hoặc tạo mới PriceRecommendation
            └── db.commit() và db.refresh(rec)
```

---

## 3. CÁC NOTE THÀNH PHẦN CHI TIẾT
- Note chi tiết hàm Facade chính: [[generate_for_product]]
- Note chi tiết bộ trích xuất tín hiệu: [[Sinals signal_extractor]]
- Note chi tiết hàm sinh thuyết minh giải trình: [[Extract_resoning_detail]]
- Tài liệu kỹ thuật chuyên sâu dự án: [[02_Projects/Dynamic-Pricing/Hoạt động Gợi ý Giá và Dynamic Pricing Engine]]
"""

# 2. generate_for_product.md
content_generate_for_product = """---
title: Hàm generate_for_product
project: Dynamic-Pricing
tags:
  - dynamic-pricing
  - pricing-engine
  - python
  - function-breakdown
date: 2026-10-08
status: completed
---

# ĐẶC TẢ CHI TIẾT HÀM `generate_for_product`

- **Lớp sở hữu:** `PricingEngine`
- **Module:** `backend/app/services/pricing/engine.py` (dòng 50 - 204)
- **Vai trò kiến trúc:** Facade điều phối toàn bộ chu trình tính toán, áp dụng rào cản và lưu trữ đề xuất giá cho một sản phẩm cụ thể.

---

## 1. KHAI BÁO HÀM (SIGNATURE)

```python
def generate_for_product(
    self,
    db: Session,
    product_id: UUID,
    custom_weights: Optional[Dict[str, float]] = None,
) -> PriceRecommendation:
```

---

## 2. CHI TIẾT INPUT (THAM SỐ ĐẦU VÀO)

| Tham Số | Kiểu Dữ Liệu | Bắt Buộc | Mô Tả Chi Tiết |
| :--- | :--- | :--- | :--- |
| `self` | `PricingEngine` | Có | Instance điều phối chứa các dependency: `self.signals_extractor`, `self.scenario_matrix`, `self.guardrails`. |
| `db` | `Session` | Có | SQLAlchemy Session kết nối cơ sở dữ liệu để truy vấn danh mục, tồn kho, đối soát và commit bản ghi. |
| `product_id` | `UUID` | Có | Định danh khóa chính của sản phẩm FPT Shop trong bảng `products`. |
| `custom_weights` | `Optional[Dict[str, float]]` | Không | Dictionary trọng số tùy biến, ví dụ: `{"demand": 0.4, "inventory": 0.35, "competitor": 0.25}`. Mặc định là `None`. |

**Ngoại lệ phát sinh (Raises):**
- `ValueError`: Khi `product_id` không tìm thấy trong CSDL (`Product with id '{product_id}' not found`).
- `ValueError`: Khi giá bán hiện tại của sản phẩm `<= 0` (`Product '{product.sku}' has non-positive current price`).

---

## 3. CHI TIẾT OUTPUT (GIÁ TRỊ TRẢ VỀ)

Hàm trả về một đối tượng ORM `PriceRecommendation` đã được commit vào CSDL và đồng bộ qua `db.refresh()`.

| Tên Thuộc Tính | Kiểu Dữ Liệu | Diễn Giải Ý Nghĩa |
| :--- | :--- | :--- |
| `id` | `UUID` | Khóa chính duy nhất của đề xuất giá. |
| `fpt_product_id` | `UUID` | Khóa ngoại trỏ về sản phẩm FPT Shop. |
| `current_fpt_price` | `BigInteger` | Giá bán lẻ hiện tại của FPT Shop (VND). |
| `competitor_min_price` | `BigInteger` (nullable) | Mức giá thấp nhất của đối thủ cạnh tranh còn hàng. `None` nếu không có đối thủ còn hàng. |
| `recommended_price` | `BigInteger` | Mức giá mới được đề xuất sau ma trận và rào cản an toàn Guardrails (VND). |
| `price_delta_amount` | `BigInteger` | Chênh lệch tiền tuyệt đối: `recommended_price - current_fpt_price`. |
| `price_delta_pct` | `Float` | Tỷ lệ phần trăm điều chỉnh giá (ví dụ: `0.06` tương đương tăng 6%). |
| `demand_score` | `Float` | Điểm tín hiệu nhu cầu thị trường (-2.0 đến +2.0). |
| `inventory_score` | `Float` | Điểm tín hiệu tồn kho (-2.0 đến +2.0). |
| `competitor_score` | `Float` | Điểm tín hiệu đối thủ (-2.0 đến +2.0). |
| `composite_score` | `Float` | Điểm tổng hợp trọng số: $0.40D + 0.35I + 0.25C$. |
| `scenario_name` | `String` | Tên kịch bản nghiệp vụ (ví dụ: `Strong Raise`, `Clearance`, `Hold`...). |
| `reasoning_3layers` | `JSON` | Thuyết minh 3 lớp định lượng minh bạch: `competitor_factor`, `inventory_factor`, `market_demand_factor`, `floor_protection_factor`, `guardrail_notes`. |
| `is_floor_capped` | `Boolean` | Cờ cảnh báo giá đề xuất bị chặn bởi giá sàn bảo vệ biên lợi nhuận (Margin Floor). |
| `status` | `String` | Mặc định là `"PENDING"` chờ phê duyệt. |
| `created_at` | `DateTime` | Thời điểm tạo hoặc cập nhật đề xuất (UTC). |

---

## 4. GIẢI THÍCH CHI TIẾT TỪNG DÒNG CODE (LINE-BY-LINE CODE WALKTHROUGH)

### Khối 1: Truy vấn sản phẩm và xác thực giá hiện tại (Dòng 69 - 77)

```python
69:  product = db.query(Product).filter(Product.id == product_id).first()
70:  if not product:
71:      raise ValueError(f"Product with id '{product_id}' not found")
72:
73:  current_price = _get_product_price(product)
74:  if current_price <= 0:
75:      raise ValueError(
76:          f"Product '{product.sku}' (id={product_id}) has non-positive current price: {current_price}"
77:      )
```
- **Dòng 69 - 72:** Truy vấn bản ghi `Product` từ CSDL theo `product_id`. Nếu sản phẩm không tồn tại, lập tức ném ngoại lệ `ValueError`.
- **Dòng 73:** Gọi hàm trợ giúp `_get_product_price(product)` để lấy giá bán lẻ thực tế hiện tại từ trường `price` hoặc `base_retail_price`.
- **Dòng 74 - 77:** Kiểm tra tính hợp lệ của giá. Nếu giá `<= 0`, ném ngoại lệ `ValueError` để ngăn chặn tính toán sai lệch.

---

### Khối 2: Xác định giá vốn và giá sàn bảo vệ (Dòng 79 - 100)

```python
79:  # 1. Xac dinh cost_price va floor_price tu InventoryMock hoac fallback tu current_price
80:  inv = (
81:      db.query(InventoryMock)
82:      .filter(InventoryMock.fpt_product_id == product_id)
83:      .first()
84:  )
85:  if inv and inv.cost_price and inv.cost_price > 0:
86:      cost_price = int(inv.cost_price)
87:      floor_price = (
88:          int(inv.floor_price)
89:          if inv.floor_price and inv.floor_price > 0
90:          else int(cost_price * 1.05)
91:      )
92:  else:
93:      prod_cost = int(getattr(product, "cost_price", 0) or 0)
94:      prod_floor = int(getattr(product, "floor_price", 0) or 0)
95:      cost_price = prod_cost if prod_cost > 0 else int(current_price * 0.85)
96:      floor_price = prod_floor if prod_floor > 0 else int(current_price * 0.90)
97:
98:  if floor_price <= 0:
99:      floor_price = cost_price
```
- **Dòng 80 - 84:** Truy vấn bảng dữ liệu tồn kho `InventoryMock` của sản phẩm.
- **Dòng 85 - 91:** Nếu tìm thấy thông tin tồn kho hợp lệ có `cost_price > 0`, lấy trực tiếp `cost_price` từ kho. `floor_price` được lấy từ trường `inv.floor_price`; nếu trường này trống, hệ thống tự động thiết lập giá sàn an toàn bằng $\text{cost\_price} \times 1.05$ (đảm bảo biên lợi nhuận tối thiểu 5%).
- **Dòng 92 - 96:** Nếu chưa có dữ liệu `InventoryMock`, hệ thống thực hiện cơ chế fallback: lấy từ thuộc tính của `Product`, hoặc ước lượng an toàn với $\text{cost\_price} = 85\% \times \text{current\_price}$ và $\text{floor\_price} = 90\% \times \text{current\_price}$.
- **Dòng 98 - 99:** Đảm bảo `floor_price` luôn dương. Nếu giá sàn $\le 0$, ép bằng `cost_price`.

---

### Khối 3: Quét tìm giá đối thủ thấp nhất còn hàng (Dòng 101 - 120)

```python
101: # 2. Tim gia doi thu thap nhat con hang (in-stock)
102: mappings = (
103:     db.query(SkuMapping)
104:     .filter(SkuMapping.fpt_product_id == product_id)
105:     .all()
106: )
107: scraped_ids = [m.competitor_crawl_id for m in mappings if m.competitor_crawl_id]
108: c_items = (
109:     db.query(CrawlResult)
110:     .filter(CrawlResult.id.in_(scraped_ids))
111:     .all()
112: ) if scraped_ids else []
113:
114: in_stock_prices = [
115:     int(item.current_price)
116:     for item in c_items
117:     if item.is_in_stock and item.current_price and item.current_price > 0
118: ]
119: competitor_min_price = min(in_stock_prices) if in_stock_prices else None
```
- **Dòng 102 - 106:** Lấy danh sách các liên kết đối soát SKU từ bảng `SkuMapping` của sản phẩm FPT Shop.
- **Dòng 107 - 112:** Gom toàn bộ ID cào dữ liệu đối thủ `competitor_crawl_id` và truy vấn bảng `CrawlResult`.
- **Dòng 114 - 118:** Lọc danh sách giá của các đối thủ thỏa mãn đồng thời: còn hàng (`item.is_in_stock = True`) và có giá hợp lệ (`item.current_price > 0`).
- **Dòng 119:** Tìm mức giá thấp nhất `min(in_stock_prices)`. Nếu không có đối thủ nào còn hàng, gán `competitor_min_price = None`.

---

### Khối 4: Trích xuất điểm tín hiệu và dữ liệu giải trình (Dòng 121 - 124)

```python
121: # 3. Trich xuat diem tin hieu va thong tin giai trinh
122: scores: SignalScores = self.signals_extractor.extract_signals(db, product_id)
123: reasoning_details = self.signals_extractor.extract_reasoning_details(db, product_id)
```
- **Dòng 122:** Gọi hàm `extract_signals()` từ lớp [[Sinals signal_extractor]] để tính toán 3 điểm số chuẩn hóa: `demand_score`, `inventory_score`, `competitor_score`.
- **Dòng 123:** Gọi hàm `extract_reasoning_details()` từ lớp [[Extract_resoning_detail]] để bóc tách ngữ cảnh định lượng về đối thủ, DOH tồn kho và chỉ số CVR.

---

### Khối 5: Đánh giá ma trận kịch bản và tính Composite Score (Dòng 125 - 128)

```python
125: # 4. Danh gia ma tran kich ban va tinh Composite Score
126: scenario = self.scenario_matrix.evaluate(scores, weights=custom_weights)
127: composite_score = self.scenario_matrix.calculate_composite(scores, weights=custom_weights)
```
- **Dòng 126:** Gọi phương thức `evaluate()` của `ScenarioMatrix` để ánh xạ bộ điểm $(D, I, C)$ vào 10 kịch bản nghiệp vụ hoặc 7 dải Composite Score, xác định hành động và biên độ điều chỉnh mục tiêu `scenario.target_delta_pct`.
- **Dòng 127:** Gọi phương thức `calculate_composite()` để tính điểm tổng hợp $w_D \cdot D + w_I \cdot I + w_C \cdot C$.

---

### Khối 6: Kích hoạt rào cản an toàn Safety Guardrails (Dòng 129 - 139)

```python
129: # 5. Ap dung cac rao can an toan (Margin Floor, Rate Cap, Predatory)
130: max_rate_cap = 0.15 if "Strong" in scenario.action_type else 0.10
131: guardrail_res = self.guardrails.apply(
132:     current_price=current_price,
133:     target_delta_pct=scenario.target_delta_pct,
134:     floor_price=floor_price,
135:     cost_price=cost_price,
136:     competitor_price=competitor_min_price,
137:     max_rate_cap=max_rate_cap,
138: )
```
- **Dòng 130:** Xác định biên độ trần biến động giá `max_rate_cap`: nếu hành động thuộc nhóm `Strong` (như Strong raise, Strong lower), trần cho phép là `0.15` ($\pm 15\%$), ngược lại giới hạn an toàn là `0.10` ($\pm 10\%$).
- **Dòng 131 - 138:** Gọi phương thức `apply()` của `SafetyGuardrails`. Kiểm tra 3 rào cản: hãm biên độ nhảy giá, khóa giá tại `floor_price` nếu vi phạm sàn, và cảnh báo đối thủ bán phá giá. Kết quả trả về là đối tượng `GuardrailResult`.

---

### Khối 7: Đóng gói JSON giải trình 3 lớp (Dòng 140 - 153)

```python
140: # 6. Dong goi 3 lop giai trinh reasoning_3layers JSON
141: floor_protection_factor = (
142:     "Muc gia de xuat da duoc dieu chinh ve muc gia san de bao toan bien loi nhuan an toan."
143:     if guardrail_res.is_floor_capped
144:     else "Muc gia de xuat nam trong nguong an toan tren muc gia san."
145: )
146:
147: reasoning_3layers: Dict[str, Any] = {
148:     "competitor_factor": reasoning_details.get("competitor_factor", ""),
149:     "inventory_factor": reasoning_details.get("inventory_factor", ""),
150:     "market_demand_factor": reasoning_details.get("market_demand_factor", ""),
151:     "floor_protection_factor": floor_protection_factor,
152:     "guardrail_notes": guardrail_res.guardrail_notes,
153: }
```
- **Dòng 141 - 145:** Sinh thông điệp bảo vệ sàn dựa trên cờ `guardrail_res.is_floor_capped`.
- **Dòng 147 - 153:** Đóng gói cấu trúc từ điển `reasoning_3layers` định lượng, minh bạch, phục vụ hiển thị frontend và hệ thống RAG Chatbot.

---

### Khối 8: Cập nhật hoặc tạo mới bản ghi vào CSDL (Dòng 155 - 204)

```python
155: # 7. Luu tru hoac cap nhat ban ghi PriceRecommendation
156: existing = (
157:     db.query(PriceRecommendation)
158:     .filter(
159:         PriceRecommendation.fpt_product_id == product_id,
160:         PriceRecommendation.status == "PENDING",
161:     )
162:     .first()
163: )
164:
165: now_utc = datetime.now(timezone.utc)
166: if existing is not None:
167:     existing.current_fpt_price = current_price
168:     existing.competitor_min_price = competitor_min_price
169:     existing.recommended_price = guardrail_res.final_price
170:     existing.price_delta_amount = guardrail_res.price_delta_amount
171:     existing.price_delta_pct = guardrail_res.price_delta_pct
172:     existing.demand_score = scores.demand_score
173:     existing.inventory_score = scores.inventory_score
174:     existing.competitor_score = scores.competitor_score
175:     existing.composite_score = composite_score
176:     existing.scenario_name = scenario.scenario_name
177:     existing.reasoning_3layers = reasoning_3layers
178:     existing.is_floor_capped = guardrail_res.is_floor_capped
179:     existing.created_at = now_utc
180:     rec = existing
181: else:
182:     rec = PriceRecommendation(
183:         fpt_product_id=product_id,
184:         current_fpt_price=current_price,
185:         competitor_min_price=competitor_min_price,
186:         recommended_price=guardrail_res.final_price,
187:         price_delta_amount=guardrail_res.price_delta_amount,
188:         price_delta_pct=guardrail_res.price_delta_pct,
189:         demand_score=scores.demand_score,
190:         inventory_score=scores.inventory_score,
191:         competitor_score=scores.competitor_score,
192:         composite_score=composite_score,
193:         scenario_name=scenario.scenario_name,
194:         reasoning_3layers=reasoning_3layers,
195:         is_floor_capped=guardrail_res.is_floor_capped,
196:         status="PENDING",
197:         created_at=now_utc,
198:     )
199:     db.add(rec)
200:
201: db.commit()
202: db.refresh(rec)
203: return rec
```
- **Dòng 156 - 163:** Kiểm tra xem sản phẩm đã có bản ghi đề xuất nào đang ở trạng thái `"PENDING"` hay chưa.
- **Dòng 166 - 180:** Nếu đã có đề xuất `"PENDING"` cũ, thực hiện cập nhật tại chỗ (in-place update) các giá trị tính toán mới nhất và làm mới timestamp `created_at = now_utc`.
- **Dòng 181 - 199:** Nếu chưa có, khởi tạo một bản ghi `PriceRecommendation` mới tinh và thêm vào phiên làm việc qua `db.add(rec)`.
- **Dòng 201 - 203:** Gọi `db.commit()` để lưu vĩnh viễn vào CSDL, gọi `db.refresh(rec)` để nạp lại dữ liệu đồng bộ và trả về đối tượng `rec`.
"""

# 3. Sinals signal_extractor.md
content_signals_extractor = """---
title: SignalsExtractor - Bộ Trích Xuất Tín Hiệu Thị Trường
project: Dynamic-Pricing
tags:
  - dynamic-pricing
  - signals
  - algorithms
  - python
date: 2026-10-08
status: completed
---

# ĐẶC TẢ LỚP `SignalsExtractor`

- **Module:** `backend/app/services/pricing/signals.py`
- **Nhiệm vụ:** Thu thập và chuẩn hóa dữ liệu đa chiều (Nhu cầu, Tồn kho, Đối thủ) thành thang điểm từ **-2.0** đến **+2.0**.

---

## 1. HÀM `extract_signals()`
- **Vị trí:** `backend/app/services/pricing/signals.py:161-170`
- **Khai báo:** `def extract_signals(self, db: Session, product_id: UUID) -> SignalScores`
- **Input:**
  - `db: Session`: Phiên làm việc CSDL.
  - `product_id: UUID`: ID sản phẩm FPT Shop.
- **Output:** Đối tượng `SignalScores(demand_score: float, inventory_score: float, competitor_score: float)`.
- **Giải thích:** Triệu gọi tuần tự 3 hàm con và gom kết quả:
  ```python
  d_score = self.calculate_demand_score(db, product_id)
  i_score = self.calculate_inventory_score(db, product_id)
  c_score = self.calculate_competitor_score(db, product_id)
  return SignalScores(demand_score=d_score, inventory_score=i_score, competitor_score=c_score)
  ```

---

## 2. HÀM `calculate_demand_score()`
- **Vị trí:** `backend/app/services/pricing/signals.py:20-58`
- **Khai báo:** `def calculate_demand_score(self, db: Session, product_id: UUID) -> float`
- **Input:** `db: Session`, `product_id: UUID`.
- **Output:** Số thực `float` $\in [-2.0, +2.0]$.
- **Giải thích code chi tiết:**
  - Truy vấn 100 sự kiện gần nhất từ bảng `DemandEvent`:
    ```python
    events = db.query(DemandEvent).filter(DemandEvent.fpt_product_id == product_id).order_by(desc(DemandEvent.event_ts)).limit(100).all()
    ```
  - Tính toán các chỉ số:
    - $\text{total\_views}$: Tổng số sự kiện `event_type == "view"`.
    - $\text{purchases}$: Số lượt mua `event_type == "purchase"`.
    - $\text{cart\_adds}$: Số lượt thêm giỏ hàng `event_type == "cart_add"`.
    - $\text{bounces}$: Số lượt thoát trang `is_bounce == True`.
    - $\text{CVR} = (\text{purchases} / \text{total\_views}) \times 100.0$.
    - $\text{bounce\_rate} = (\text{bounces} / \text{total\_views}) \times 100.0$.
  - Phân loại thang điểm:
    - Nếu $\text{CVR} > 5.0\%$ hoặc $\text{cart\_adds} > 10$: Trả về `+2.0` (Cầu bùng nổ).
    - Nếu $\text{CVR} > 3.0\%$ hoặc $\text{cart\_adds} > 5$: Trả về `+1.0` (Cầu tích cực).
    - Nếu $\text{bounce\_rate} > 75.0\%$ hoặc $\text{CVR} < 0.5\%$: Trả về `-2.0` (Khủng hoảng cầu).
    - Nếu $\text{bounce\_rate} > 50.0\%$: Trả về `-1.0` (Cầu suy giảm).
    - Mặc định: Trả về `0.0` (Cân bằng).

---

## 3. HÀM `calculate_inventory_score()`
- **Vị trí:** `backend/app/services/pricing/signals.py:60-107`
- **Khai báo:** `def calculate_inventory_score(self, db: Session, product_id: UUID) -> float`
- **Input:** `db: Session`, `product_id: UUID`.
- **Output:** Số thực `float` $\in [-2.0, +2.0]$.
- **Giải thích code chi tiết:**
  - *Ưu tiên 1:* Kiểm tra `InventorySnapshot` mới nhất:
    - Nếu có cờ rủi ro lỗi thời `is_obsolescence_risk = True`: Trả về `-2.0` (Áp lực xả hàng).
    - Nếu $\text{stock\_cover\_days} > 45$: Trả về `-2.0` (Tồn kho quá nhiều).
    - Nếu $\text{stock\_cover\_days} < 7$ hoặc có đối thủ hết hàng (`competitor_oos_count > 0`): Trả về `+2.0` (Khan hàng).
    - Đánh giá tỷ lệ tồn trên mục tiêu $\text{ratio} = \text{qty\_available} / \text{target\_stock}$:
      - $\text{ratio} > 1.5 \to -2.0$; $\text{ratio} > 1.1 \to -1.0$.
      - $\text{ratio} < 0.3 \to +2.0$; $\text{ratio} < 0.6 \to +1.0$.
  - *Ưu tiên 2 (Fallback):* Đọc bảng `InventoryMock`:
    - $\text{doh} > 45 \to -2.0$; $\text{doh} \ge 35 \to -1.0$.
    - $\text{doh} < 7 \to +2.0$; $\text{doh} \le 15 \to +1.0$.
  - Mặc định: Trả về `0.0`.

---

## 4. HÀM `calculate_competitor_score()`
- **Vị trí:** `backend/app/services/pricing/signals.py:109-159`
- **Khai báo:** `def calculate_competitor_score(self, db: Session, product_id: UUID) -> float`
- **Input:** `db: Session`, `product_id: UUID`.
- **Output:** Số thực `float` $\in [-2.0, +2.0]$.
- **Giải thích code chi tiết:**
  - Lấy các bản ghi đối soát từ `SkuMapping` có trạng thái `APPROVED` hoặc `AUTO_MATCHED`.
  - Nếu tất cả đối thủ đều hết hàng (`all(not r.is_in_stock)`): Trả về `+2.0` (Độc quyền cung ứng).
  - Tìm giá đối thủ thấp nhất còn hàng `min_competitor_price`.
  - Tính tỷ lệ chênh lệch giá:
    $$\text{diff\_pct} = \frac{P_{\text{comp\_min}} - P_{\text{FPT}}}{P_{\text{FPT}}}$$
  - Phân loại ngưỡng:
    - $\text{diff\_pct} > +15\% \to +2.0$ (Đối thủ bán đắt hơn FPT rất nhiều, dư địa tăng giá lớn).
    - $\text{diff\_pct} \ge +5\% \to +1.0$ (Đối thủ bán đắt hơn FPT).
    - $-5\% \le \text{diff\_pct} < +5\% \to 0.0$ (Giá ngang bằng trong biên độ an toàn).
    - $-15\% \le \text{diff\_pct} < -5\% \to -1.0$ (Đối thủ bán rẻ hơn, cần hạ giá).
    - $\text{diff\_pct} < -15\% \to -2.0$ (Đối thủ phá giá sâu, áp lực cạnh tranh cực lớn).
"""

# 4. Extract_resoning_detail.md
content_extract_reasoning = """---
title: Hàm extract_reasoning_details
project: Dynamic-Pricing
tags:
  - dynamic-pricing
  - signals
  - reasoning
  - python
date: 2026-10-08
status: completed
---

# ĐẶC TẢ CHI TIẾT HÀM `extract_reasoning_details`

- **Module:** `backend/app/services/pricing/signals.py` (dòng 172 - 234)
- **Lớp sở hữu:** `SignalsExtractor`
- **Mục đích:** Tự động sinh ra các chuỗi văn bản giải thích định lượng, minh bạch về 3 yếu tố (Đối thủ, Tồn kho, Nhu cầu) phục vụ hiển thị trên giao diện và làm ngữ cảnh (Context) cho trợ lý AI Chatbot RAG.

---

## 1. KHAI BÁO HÀM (SIGNATURE)

```python
def extract_reasoning_details(
    self,
    db: Session,
    product_id: UUID
) -> Dict[str, Any]:
```

---

## 2. CHI TIẾT INPUT VÀ OUTPUT

### 2.1. Input
- `db: Session`: Phiên làm việc cơ sở dữ liệu SQLAlchemy.
- `product_id: UUID`: Mã sản phẩm FPT Shop cần tạo giải trình.

### 2.2. Output
Trả về từ điển `Dict[str, Any]` gồm 3 khóa:
- `"competitor_factor"`: Chuỗi text phân tích vị thế giá đối thủ.
- `"inventory_factor"`: Chuỗi text phân tích hiện trạng tồn kho và số ngày DOH.
- `"market_demand_factor"`: Chuỗi text phân tích lượng truy cập và tỷ lệ mua hàng.

---

## 3. GIẢI THÍCH CHI TIẾT TỪNG ĐOẠN CODE

### Đoạn 1: Phân tích yếu tố đối thủ (`competitor_factor`) (Dòng 174 - 205)

```python
# 1. Competitor factor
c_score = self.calculate_competitor_score(db, product_id)
product = db.query(Product).filter(Product.id == product_id).first()
fpt_price = product.base_retail_price if product else 0

mappings = db.query(SkuMapping).filter(SkuMapping.fpt_product_id == product_id).all()
scraped_ids = [m.competitor_crawl_id for m in mappings]
c_items = db.query(CrawlResult).filter(CrawlResult.id.in_(scraped_ids)).all() if scraped_ids else []

if not c_items:
    comp_factor = "Chua co du lieu gia doi thu doi soat."
else:
    in_stock = [item for item in c_items if item.is_in_stock and item.current_price]
    if not in_stock:
        comp_factor = "Tat ca doi thu chinh (CellphoneS, Hoang Ha) deu dang het hang (Out-of-Stock)."
    else:
        cheapest = min(in_stock, key=lambda x: x.current_price)
        diff_amount = cheapest.current_price - fpt_price
        diff_pct = (diff_amount / fpt_price) * 100 if fpt_price else 0
        if diff_pct < 0:
            comp_factor = f"Doi thu {cheapest.source} dang ban re hon {abs(diff_pct):.1f}% ({abs(diff_amount):,} VND)."
        else:
            comp_factor = f"Doi thu {cheapest.source} dang ban cao hon {diff_pct:.1f}% ({diff_amount:,} VND)."
```
- **Ý nghĩa:**
  - Lấy danh sách kết quả cào từ `SkuMapping` và `CrawlResult`.
  - Nếu không có đối thủ: Ghi `"Chua co du lieu gia doi thu doi soat."`.
  - Nếu tất cả đối thủ hết hàng: Ghi `"Tat ca doi thu chinh (CellphoneS, Hoang Ha) deu dang het hang (Out-of-Stock)."`.
  - Nếu có đối thủ còn hàng: Tìm đối thủ rẻ nhất `cheapest = min(...)`, tính số tiền chênh lệch `diff_amount` và phần trăm `diff_pct`. Định dạng chuỗi rõ ràng (ví dụ: `"Doi thu CELLPHONES dang ban re hon 6.5% (1,400,000 VND)."`).

---

### Đoạn 2: Phân tích yếu tố tồn kho (`inventory_factor`) (Dòng 207 - 221)

```python
# 2. Inventory factor
inv = db.query(InventoryMock).filter(InventoryMock.fpt_product_id == product_id).first()
snap = db.query(InventorySnapshot).filter(InventorySnapshot.fpt_product_id == product_id).order_by(desc(InventorySnapshot.snapshot_ts)).first()
doh = snap.stock_cover_days if snap else (inv.doh if inv else 0)
qty = snap.qty_available if snap else (inv.stock_quantity if inv else 0)

if snap and snap.is_obsolescence_risk:
    inv_factor = f"Canh bao hang ton kho loi thoi (DOH={doh} ngay, so luong={qty})."
elif doh > 45:
    inv_factor = f"Hang ton kho u dong cao (DOH={doh} ngay > 45 ngay, luong ton={qty})."
elif doh < 7 and doh > 0:
    inv_factor = f"Hang khan hiem sap het (DOH={doh} ngay < 7 ngay, luong ton={qty})."
else:
    inv_factor = f"Ton kho on dinh (DOH={doh} ngay, luong ton kha dung={qty})."
```
- **Ý nghĩa:**
  - Ưu tiên lấy thông số từ `InventorySnapshot` (ảnh chụp chi tiết đa kho), nếu không có thì đọc từ `InventoryMock`.
  - Phân tích `doh` và `qty`: Cảnh báo lỗi thời nếu `is_obsolescence_risk = True`; cảnh báo ứ đọng nếu $\text{DOH} > 45\text{ ngày}$; cảnh báo khan hiếm nếu $\text{DOH} < 7\text{ ngày}$.

---

### Đoạn 3: Phân tích yếu tố nhu cầu thị trường (`market_demand_factor`) (Dòng 223 - 233)

```python
# 3. Market demand factor
agg = db.query(DemandHourlyAggregate).filter(DemandHourlyAggregate.fpt_product_id == product_id).order_by(desc(DemandHourlyAggregate.aggregate_hour)).first()
if agg:
    demand_factor = f"Luu luong quan tam: {agg.total_views} views, {agg.cart_adds} gio hang, CVR={agg.cvr_pct:.1f}%."
else:
    demand_factor = "Nhu cau thi truong o muc tieu chuan (Neutral)."

return {
    "competitor_factor": comp_factor,
    "inventory_factor": inv_factor,
    "market_demand_factor": demand_factor,
}
```
- **Ý nghĩa:**
  - Truy vấn bản ghi tổng hợp giờ `DemandHourlyAggregate` gần nhất của sản phẩm.
  - Định dạng chuỗi lượng hóa số lượt xem `total_views`, lượt thêm giỏ `cart_adds` và tỷ lệ chuyển đổi `cvr_pct`.
  - Trả về từ điển kết hợp 3 nhân tố hoàn chỉnh.
"""

files_to_write = {
    os.path.join(vault_root, "Luồng hoạt động gợi ý giá cả sản phẩm.md"): content_luong_hoat_dong,
    os.path.join(vault_root, "generate_for_product.md"): content_generate_for_product,
    os.path.join(vault_root, "Sinals signal_extractor.md"): content_signals_extractor,
    os.path.join(vault_root, "Extract_resoning_detail.md"): content_extract_reasoning,
}

for file_path, content in files_to_write.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Da ghi thanh cong: {file_path}")

# Dong bo them vao docs/obsidian-notes/ va 02_Projects/Dynamic-Pricing
project_vault_dir = os.path.join(vault_root, "02_Projects", "Dynamic-Pricing")
source_doc = os.path.join("docs", "obsidian-notes", "Hoạt động Gợi ý Giá và Dynamic Pricing Engine.md")
dest_doc = os.path.join(project_vault_dir, "Hoạt động Gợi ý Giá và Dynamic Pricing Engine.md")

if os.path.exists(source_doc) and os.path.exists(project_vault_dir):
    shutil.copy2(source_doc, dest_doc)
    print(f"Da dong bo Hoat dong Goi y Gia sang: {dest_doc}")

print("HOAN TAT DONG BO VA GHI LOCAL OBSIDIAN!")
