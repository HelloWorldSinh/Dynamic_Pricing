# Dynamic Pricing Recommendation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng động cơ gợi ý tăng/giảm giá (Pricing Recommendation Engine) đa tín hiệu (Nhu cầu, Tồn kho, Đối thủ), kiểm soát rào cản an toàn và quy trình phê duyệt giả lập (PBI-010, PBI-011, PBI-012).

**Architecture:** Áp dụng Clean Service Layer phân tách 4 module chuyên biệt (`signals.py`, `matrix.py`, `guardrails.py`, `engine.py`), giao tiếp qua các dataclass DTO chuẩn hóa, lưu trữ đề xuất tại bảng `PriceRecommendation` và cung cấp bộ RESTful API router `/api/v1/pricing`.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.x, Pydantic v2, pytest.

**Spec:** `docs/superpowers/specs/2026-10-05-pricing-engine-design.md`

## Global Constraints

- Trọng số chuẩn: Demand $w_D = 0.40$, Inventory $w_I = 0.35$, Competitor $w_C = 0.25$.
- Điểm số thành phần $D, I, C \in [-2.0, +2.0]$.
- Rào cản giá sàn (Margin Floor): $\text{recommended_price} \ge \text{floor_price}$.
- Rào cản bước nhảy (Rate-of-Change Cap): Giới hạn tối đa $\pm 10\%$ (mặc định) và $\pm 15\%$ (kịch bản đặc biệt).
- Tuyệt đối không dùng emoji hoặc icon trong mã nguồn API responses, text labels hoặc reasoning copy.
- Toàn bộ thay đổi phải tuân thủ chu trình TDD (Red -> Green -> Refactor) với độ phủ kiểm thử $\ge 80\%$.

## Review Focus

1. Sản phẩm không có dữ liệu kho hoặc đối thủ: Hệ thống phải fallback điểm trung tính $0.0$, không crash hoặc division-by-zero.
2. Giá đề xuất sau khi áp % thấp hơn Floor Price: Guardrail phải ép đúng bằng `floor_price` và bật cờ `is_floor_capped = True`.
3. Đối thủ bán phá giá ($>20\%$ dưới giá vốn FPT): Bộ lọc Predatory Pricing phải loại bỏ đối thủ này khỏi điểm $C$.
4. Chạy lại engine cho sản phẩm đã có đề xuất `PENDING`: Phải cập nhật đề xuất hiện có (in-place) thay vì tạo nhiều bản ghi rác.
5. Gửi action duyệt cho đề xuất đã qua xử lý (`APPROVED`/`REJECTED`): Phải trả về lỗi 400 Bad Request rõ ràng.

---

### Task 1: Pricing Data Structures & Config DTOs

**Files:**
- Create: `backend/app/services/pricing/schemas.py`
- Test: `backend/tests/test_pricing_schemas.py`

**Interfaces:**
- Produces:
  - `SignalScores(demand_score: float, inventory_score: float, competitor_score: float)`
  - `ScenarioMatch(scenario_name: str, target_delta_pct: float, action_type: str, rationale: str)`
  - `GuardrailResult(final_price: int, price_delta_amount: int, price_delta_pct: float, is_floor_capped: bool, guardrail_notes: List[str])`
  - `PricingRecommendationDTO(...)`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_pricing_schemas.py
from backend.app.services.pricing.schemas import SignalScores, ScenarioMatch, GuardrailResult

def test_signal_scores_validation():
    scores = SignalScores(demand_score=1.5, inventory_score=-1.0, competitor_score=0.5)
    assert scores.demand_score == 1.5
    assert scores.composite(weights={"D": 0.4, "I": 0.35, "C": 0.25}) == 0.38
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_pricing_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.services.pricing'`

- [ ] **Step 3: Implement data structures in `backend/app/services/pricing/schemas.py`**

Triển khai các dataclass/Pydantic models DTO với phương thức tính `composite()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_pricing_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pricing/schemas.py backend/tests/test_pricing_schemas.py
git commit -m "feat(pricing): add pricing domain dataclasses and signal DTOs"
```

---

### Task 2: Signal Extraction Service (`signals.py`)

**Files:**
- Create: `backend/app/services/pricing/signals.py`
- Test: `backend/tests/test_pricing_signals.py`

**Interfaces:**
- Consumes:
  - `SignalScores` từ `backend/app/services/pricing/schemas.py`
  - SQLAlchemy models: `Product`, `InventorySnapshot`, `InventoryMock`, `CrawlResult`, `SKUMapping`, `DemandHourlyAggregate`, `DemandEvent`
- Produces:
  - `SignalsExtractor.extract_signals(db: Session, product_id: UUID) -> SignalScores`
  - `SignalsExtractor.extract_reasoning_details(db: Session, product_id: UUID) -> Dict[str, Any]`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_pricing_signals.py
def test_calculate_inventory_score_doh_less_than_7_days(db_session, sample_product):
    # Setup stock DOH = 5 days -> Expected I = +2.0 (khan hàng)
    extractor = SignalsExtractor()
    score = extractor.calculate_inventory_score(db_session, sample_product.id)
    assert score == 2.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_pricing_signals.py -v`
Expected: FAIL with `NameError: name 'SignalsExtractor' is not defined`

- [ ] **Step 3: Implement `SignalsExtractor` in `backend/app/services/pricing/signals.py`**

Triển khai trích xuất tín hiệu:
- `calculate_demand_score`: Phân tích lượt tìm kiếm, tăng giỏ hàng, CVR.
- `calculate_inventory_score`: DOH, tỷ lệ tồn so với target stock, nguy cơ lỗi thời, đối thủ hết hàng.
- `calculate_competitor_score`: Chênh lệch giá min của đối thủ còn hàng so với giá FPT.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_pricing_signals.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pricing/signals.py backend/tests/test_pricing_signals.py
git commit -m "feat(pricing): implement market signals extraction service"
```

---

### Task 3: Scenario Matrix & Composite Score (`matrix.py`)

**Files:**
- Create: `backend/app/services/pricing/matrix.py`
- Test: `backend/tests/test_pricing_matrix.py`

**Interfaces:**
- Consumes: `SignalScores` từ `backend/app/services/pricing/schemas.py`
- Produces:
  - `ScenarioMatrix.evaluate(scores: SignalScores, weights: Optional[Dict[str, float]]) -> ScenarioMatch`
  - `ScenarioMatrix.calculate_composite(scores: SignalScores, weights: Optional[Dict[str, float]]) -> float`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_pricing_matrix.py
def test_scenario_matrix_evaluates_9_scenarios():
    matrix = ScenarioMatrix()
    # Scenario 1: Festival D=+2, I=+2, C=+2 -> Strong raise (+12% to +15%)
    match_s1 = matrix.evaluate(SignalScores(2.0, 2.0, 2.0))
    assert match_s1.scenario_name == "Kịch bản 1: Festival / Sự kiện lớn"
    assert match_s1.target_delta_pct == 0.12
    assert match_s1.action_type == "Strong raise"

    # Scenario 3: Baseline D=0, I=0, C=0 -> Hold (0%)
    match_s3 = matrix.evaluate(SignalScores(0.0, 0.0, 0.0))
    assert match_s3.target_delta_pct == 0.0
    assert match_s3.action_type == "Hold"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_pricing_matrix.py -v`
Expected: FAIL with `NameError: name 'ScenarioMatrix' is not defined`

- [ ] **Step 3: Implement `ScenarioMatrix` in `backend/app/services/pricing/matrix.py`**

Triển khai ma trận 9 kịch bản chi tiết và fallback phân loại theo 7 dải Composite Score (Strong raise, Moderate raise, Mild raise, Hold, Mild lower, Moderate lower, Strong lower).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_pricing_matrix.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pricing/matrix.py backend/tests/test_pricing_matrix.py
git commit -m "feat(pricing): implement 9 scenarios and 7-band pricing matrix"
```

---

### Task 4: Safety Guardrails (`guardrails.py`)

**Files:**
- Create: `backend/app/services/pricing/guardrails.py`
- Test: `backend/tests/test_pricing_guardrails.py`

**Interfaces:**
- Consumes:
  - `current_price: int`, `target_delta_pct: float`, `floor_price: int`, `cost_price: int`
- Produces:
  - `SafetyGuardrails.apply(current_price: int, target_delta_pct: float, floor_price: int, cost_price: int, competitor_price: Optional[int]) -> GuardrailResult`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_pricing_guardrails.py
def test_margin_floor_protection_caps_price():
    guard = SafetyGuardrails()
    # current = 10,000,000, delta = -20% -> raw = 8,000,000; floor = 9,000,000
    res = guard.apply(current_price=10_000_000, target_delta_pct=-0.20, floor_price=9_000_000, cost_price=8_500_000)
    assert res.final_price == 9_000_000
    assert res.is_floor_capped is True
    assert res.price_delta_pct == -0.10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_pricing_guardrails.py -v`
Expected: FAIL with `NameError: name 'SafetyGuardrails' is not defined`

- [ ] **Step 3: Implement `SafetyGuardrails` in `backend/app/services/pricing/guardrails.py`**

Triển khai:
1. Rate-of-Change Cap: Kẹp bước nhảy tối đa $\pm 10\%$ (hoặc $\pm 15\%$).
2. Margin Floor: Kiểm tra $\text{price} \ge \text{floor_price}$. Nếu vi phạm, ép về `floor_price` và gắn cờ `is_floor_capped = True`.
3. Predatory Pricing Check: Nếu `competitor_price < 0.8 * cost_price`, trả về ghi chú cảnh báo.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_pricing_guardrails.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pricing/guardrails.py backend/tests/test_pricing_guardrails.py
git commit -m "feat(pricing): implement margin floor and safety guardrails"
```

---

### Task 5: Pricing Engine Facade (`engine.py` & `__init__.py`)

**Files:**
- Create: `backend/app/services/pricing/engine.py`
- Create: `backend/app/services/pricing/__init__.py`
- Test: `backend/tests/test_pricing_engine.py`

**Interfaces:**
- Consumes:
  - `SignalsExtractor` (`signals.py`)
  - `ScenarioMatrix` (`matrix.py`)
  - `SafetyGuardrails` (`guardrails.py`)
  - Database Session & `PriceRecommendation` model
- Produces:
  - `PricingEngine.generate_for_product(db: Session, product_id: UUID, custom_weights: Optional[Dict]) -> PriceRecommendation`
  - `PricingEngine.generate_batch(db: Session, custom_weights: Optional[Dict]) -> List[PriceRecommendation]`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_pricing_engine.py
def test_pricing_engine_end_to_end_persists_recommendation(db_session, sample_product_with_inventory):
    engine = PricingEngine()
    rec = engine.generate_for_product(db_session, sample_product_with_inventory.id)
    assert rec.id is not None
    assert rec.status == "PENDING"
    assert "competitor_factor" in rec.reasoning_3layers
    assert rec.recommended_price >= sample_product_with_inventory.inventory.floor_price
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_pricing_engine.py -v`
Expected: FAIL with `NameError: name 'PricingEngine' is not defined`

- [ ] **Step 3: Implement `PricingEngine` in `backend/app/services/pricing/engine.py`**

Điều phối toàn bộ:
1. Đọc dữ liệu Product + Inventory + Competitor crawl.
2. Trích xuất $D, I, C$ scores.
3. Tính Composite Score và khớp Scenario.
4. Áp dụng Guardrails (Floor, Rate Cap).
5. Sinh 3-layer reasoning JSON.
6. Lưu hoặc cập nhật `PriceRecommendation` trong DB.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_pricing_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/pricing/engine.py backend/app/services/pricing/__init__.py backend/tests/test_pricing_engine.py
git commit -m "feat(pricing): implement end-to-end pricing engine facade"
```

---

### Task 6: Pricing API Endpoints & Approval Workflow

**Files:**
- Create: `backend/app/schemas/pricing.py`
- Create: `backend/app/api/v1/endpoints/pricing.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_pricing_api.py`

**Interfaces:**
- Consumes: `PricingEngine`, `PriceRecommendation`, `PricingAuditLog`
- Produces:
  - `POST /api/v1/pricing/recommendations/generate`
  - `GET /api/v1/pricing/recommendations`
  - `GET /api/v1/pricing/recommendations/{id}`
  - `POST /api/v1/pricing/recommendations/{id}/action` (Approve/Reject + audit log)
  - `GET /api/v1/pricing/audit-logs`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_pricing_api.py
def test_api_generate_and_approve_recommendation(client, sample_product_with_inventory):
    # 1. Trigger generate
    res = client.post("/api/v1/pricing/recommendations/generate", json={"fpt_product_id": str(sample_product_with_inventory.id)})
    assert res.status_code == 200
    rec_id = res.json()["items"][0]["id"]

    # 2. Action Approve
    act_res = client.post(f"/api/v1/pricing/recommendations/{rec_id}/action", json={"action": "APPROVE", "reviewed_by": "HaiNN58"})
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "APPROVED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_pricing_api.py -v`
Expected: FAIL with `404 Not Found` (endpoint chưa đăng ký)

- [ ] **Step 3: Implement schemas, endpoints, and register router**

- Viết schemas tại `backend/app/schemas/pricing.py`.
- Viết endpoints tại `backend/app/api/v1/endpoints/pricing.py`.
- Đăng ký `pricing.router` vào `backend/app/api/v1/router.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_pricing_api.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite with coverage**

Run: `pytest backend/tests/ -v --cov=app/services/pricing --cov=app/api/v1/endpoints/pricing`
Expected: All tests PASS, coverage $\ge 80\%$.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/pricing.py backend/app/api/v1/endpoints/pricing.py backend/app/api/v1/router.py backend/tests/test_pricing_api.py
git commit -m "feat(pricing): add pricing recommendation and approval API endpoints"
```
