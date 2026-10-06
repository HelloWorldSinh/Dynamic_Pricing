# Backend-Frontend Core Connection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect FastAPI backend and React frontend for core dynamic pricing features (Pricing Matrix, Simulation, Recommendations/Approvals, SKU Matching Review Queue, Crawl Monitoring, and Database Ingestion), excluding AI endpoints.

**Architecture:** Expose missing REST endpoints (`/matching` queue, `/pricing/recommendations/{id}/reject`, `/pricing/recommendations/{id}/apply-custom`), enrich recommendation responses with product and inventory details, run the SQLite data ingestion pipeline for 329 FPT products and 5,600+ crawled competitor items, and update frontend API client adapters to consume live backend data.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.x, Pydantic v2, SQLite, React 18, TypeScript, Axios, Vite.

**Spec:** [`docs/superpowers/specs/2026-10-06-backend-frontend-core-connection-design.md`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/docs/superpowers/specs/2026-10-06-backend-frontend-core-connection-design.md)

## Global Constraints

- CodeGraph First: check impact before modifying shared models and router definitions.
- Strict TDD: Write failing tests before modifying or creating router endpoints.
- No UI icons or emojis in code responses, logs, or UI strings.
- PEP 8 compliance, explicit type hints, zero dead code or unused imports.
- SQLite compatibility for local development (`dynamic_pricing.db`).

## Review Focus

1. **Schema Mismatch on Recommendations List:** Frontend expects `PricingRecommendation[]` containing `sku`, `product_name`, `floor_price`, `cost_price`, `doh`, while backend originally returned raw DB fields. Test that `GET /pricing/recommendations` provides these enriched fields.
2. **Missing Endpoints for Actions:** Frontend calls `/recommendations/{id}/reject` and `/apply-custom`, which previously raised 404. Test these routes return 200 and persist audit logs.
3. **Missing `/matching` Router:** Frontend calls `/matching/queue`, `/matching/queue/{id}/approve`, `/reject`. Test that `api_router` includes `matching.router` and handles pending SKU pairs.
4. **Empty Database Fallbacks:** If the database has 0 products, frontend receives empty arrays. Test that running the ingestion pipeline populates at least 300 products, mappings, and recommendations.
5. **Debounce 429 Handling:** Crawl trigger returns HTTP 429 when debounced within 30s. Test that API client surfaces the remaining wait time cleanly.

---

### Task 1: Backend Pricing API Extensions & Enriched Recommendations

**Files:**
- Modify: `backend/app/schemas/pricing.py`
- Modify: `backend/app/api/v1/endpoints/pricing.py`
- Test: `backend/tests/test_pricing_api_extensions.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/pricing/recommendations/{id}/reject` -> `PriceRecommendationResponse`
  - `POST /api/v1/pricing/recommendations/{id}/apply-custom` -> `PriceRecommendationResponse`
  - Enriched items inside `PriceRecommendationListResponse` with `sku`, `product_name`, `category`, `brand`, `floor_price`, `cost_price`, `doh`, `inventory_quantity`, `min_competitor_price`, `competitor_name`, `cellphones_price`, `hoangha_price`, `margin_impact_percent`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_pricing_api_extensions.py`:
```python
def test_reject_recommendation_endpoint(client, db_session, sample_product):
    # Tests that POST /recommendations/{id}/reject transitions status to REJECTED and creates audit log
    pass

def test_apply_custom_price_endpoint(client, db_session, sample_product):
    # Tests that POST /recommendations/{id}/apply-custom sets custom price, APPROVED status, and creates price_history entry
    pass

def test_list_recommendations_enriched_fields(client, db_session, sample_product):
    # Tests that GET /recommendations returns items containing sku, product_name, cost_price, floor_price, doh
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_pricing_api_extensions.py -v`
Expected: FAIL (routes `/reject` and `/apply-custom` not found or 404).

- [ ] **Step 3: Implement schemas and endpoints in `pricing.py`**

1. In `backend/app/schemas/pricing.py`:
   - Add `ApplyCustomPriceRequest(BaseModel)` with `custom_price: int`, `change_type: str = "MANUAL_CONFIG"`, `reviewed_by: str = "Pricing Analyst"`.
   - Update `PriceRecommendationResponse` or create `PriceRecommendationDetailItem` with enriched product fields (`sku`, `product_name`, `category`, `brand`, `floor_price`, `cost_price`, `doh`, `inventory_quantity`, `competitor_name`, `competitor_in_stock`, `cellphones_price`, `hoangha_price`, `margin_impact_percent`).
2. In `backend/app/api/v1/endpoints/pricing.py`:
   - Add `@router.post("/recommendations/{id}/reject")` handler calling `action_recommendation` with action `REJECT`.
   - Add `@router.post("/recommendations/{id}/apply-custom")` handler updating `rec.recommended_price = custom_price`, `rec.status = "APPROVED"`, creating `PricingAuditLog` and `PriceHistory`.
   - Update `list_recommendations` to populate the enriched product and inventory details onto each item before returning.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_pricing_api_extensions.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/pricing.py backend/app/api/v1/endpoints/pricing.py backend/tests/test_pricing_api_extensions.py
git commit -m "feat(pricing): add reject, apply-custom, and enriched recommendation response"
```

---

### Task 2: Backend SKU Matching Review Queue Endpoint (`/matching`)

**Files:**
- Create: `backend/app/schemas/matching.py`
- Create: `backend/app/api/v1/endpoints/matching.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_matching_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/matching/queue` -> `List[SkuMappingPairResponse]`
  - `POST /api/v1/matching/queue/{id}/approve` -> `SkuMappingPairResponse`
  - `POST /api/v1/matching/queue/{id}/reject` -> `SkuMappingPairResponse`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_matching_api.py`:
```python
def test_get_matching_queue_pending_items(client, db_session, sample_product, sample_crawl_result):
    # Tests GET /api/v1/matching/queue returns pending SKU mappings with confidence between 60-79%
    pass

def test_approve_matching_queue_item(client, db_session):
    # Tests POST /api/v1/matching/queue/{id}/approve updates mapping to APPROVED
    pass

def test_reject_matching_queue_item(client, db_session):
    # Tests POST /api/v1/matching/queue/{id}/reject updates mapping to REJECTED
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_matching_api.py -v`
Expected: FAIL with 404 (router `/matching` not registered).

- [ ] **Step 3: Implement `matching.py` router and schemas**

1. In `backend/app/schemas/matching.py`:
   - Define `SkuMappingPairResponse` with fields: `id: str`, `fpt_sku: str`, `fpt_name: str`, `fpt_part_number: Optional[str]`, `fpt_price: int`, `competitor_source: str`, `competitor_name: str`, `competitor_url: str`, `competitor_price: int`, `confidence_score: float`, `matched_attributes: List[str]`, `differing_attributes: List[str]`, `status: str`.
2. In `backend/app/api/v1/endpoints/matching.py`:
   - Implement `router = APIRouter()`.
   - Implement `GET /queue`: query `SkuMapping` where `status == "PENDING"`, joining `Product` and `CrawlResult`. Parse specs into `matched_attributes` and `differing_attributes`.
   - Implement `POST /queue/{id}/approve`: sets status to `APPROVED`, commits DB.
   - Implement `POST /queue/{id}/reject`: sets status to `REJECTED`, commits DB.
3. In `backend/app/api/v1/router.py`:
   - Include `api_router.include_router(matching.router, prefix="/matching", tags=["SKU Matching Review Queue"])`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_matching_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/matching.py backend/app/api/v1/endpoints/matching.py backend/app/api/v1/router.py backend/tests/test_matching_api.py
git commit -m "feat(matching): add matching queue api endpoints and schema"
```

---

### Task 3: Ingest Ground Truth Data into SQLite Database

**Files:**
- Execute: `backend/scripts/run_e2e_pipeline.py`
- Test: `backend/tests/test_database_populated.py`

**Interfaces:**
- Consumes: `backend/data/dim_product.xlsx`, `backend/data/crawl_and_sku_mapping_output.xlsx`, `backend/data/inventory_snapshot_20260723.xlsx`.
- Produces: Populated `dynamic_pricing.db` with >= 300 Products, >= 5,000 CrawlResults, >= 100 SkuMappings, >= 300 PriceRecommendations, >= 5 PriceHistory items.

- [ ] **Step 1: Write verification test**

Create `backend/tests/test_database_populated.py`:
```python
def test_real_database_has_sufficient_records():
    # Verifies real SQLite dynamic_pricing.db contains catalogs, inventory, mappings, and recommendations
    pass
```

- [ ] **Step 2: Run test to verify current state**

Run: `pytest backend/tests/test_database_populated.py -v`
Expected: FAIL (products count is currently 0 in `dynamic_pricing.db`).

- [ ] **Step 3: Execute `run_e2e_pipeline.py`**

Run: `python backend/scripts/run_e2e_pipeline.py`
Verify execution logs confirm 329 products ingested, crawl results mapped, pricing engine generated recommendations, and sample approvals recorded.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_database_populated.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_database_populated.py
git commit -m "chore(db): populate sqlite with 329 products and pricing pipeline data"
```

---

### Task 4: Frontend API Layer Synchronization & Data Mapping

**Files:**
- Modify: `frontend/src/api/pricingApi.ts`
- Modify: `frontend/src/api/crawlerApi.ts`

**Interfaces:**
- Consumes: Backend endpoints `/api/v1/pricing/matrix`, `/api/v1/pricing/recommendations`, `/api/v1/pricing/recommendations/{id}/approve`, `/reject`, `/apply-custom`, `/api/v1/matching/queue`, `/api/v1/crawl/*`.
- Produces: Type-safe TypeScript functions returning live data to React pages with graceful fallback only on actual network failure.

- [ ] **Step 1: Inspect `pricingApi.ts` and `crawlerApi.ts` contracts**

Check that `getRecommendationsApi()` maps the backend `{ total, items }` payload properly to `PricingRecommendation[]`, preserving all fields expected by `PricingApprovalsPage`.

- [ ] **Step 2: Update `pricingApi.ts`**

1. In `getRecommendationsApi()`: unwrap `res.data.items || res.data`, ensuring fields `sku`, `product_name`, `suggested_price`, `floor_price`, `cost_price`, `doh`, `inventory_quantity`, `min_competitor_price`, `margin_impact_percent` are mapped cleanly.
2. In `approveRecommendationApi(id)`: call `apiClient.post('/pricing/recommendations/' + id + '/approve')`.
3. In `rejectRecommendationApi(id)`: call `apiClient.post('/pricing/recommendations/' + id + '/reject')`.
4. In `applyCustomPriceApi(id, customPrice, changeType)`: call `apiClient.post('/pricing/recommendations/' + id + '/apply-custom', { custom_price: customPrice, change_type: changeType })`.
5. In `getSkuMappingQueueApi()`: call `apiClient.get('/matching/queue')`.
6. In `approveSkuMappingApi(id)`: call `apiClient.post('/matching/queue/' + id + '/approve')`.
7. In `rejectSkuMappingApi(id)`: call `apiClient.post('/matching/queue/' + id + '/reject')`.

- [ ] **Step 3: Update `crawlerApi.ts`**

Ensure `triggerCrawlApi`, `getStatus`, `getCrawlResultsApi` cleanly propagate backend status and handle HTTP 429 debounce without crashing.

- [ ] **Step 4: Verify frontend build passes**

Run: `npm run build` in `frontend/`
Expected: Zero TypeScript or Vite compilation errors (`tsc -b && vite build` exits 0).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/pricingApi.ts frontend/src/api/crawlerApi.ts
git commit -m "feat(frontend): connect pricing and matching apis to live backend endpoints"
```

---

### Task 5: End-to-End Verification & Sanity Checks

**Files:**
- Create: `backend/scripts/verify_fe_be_integration.py`

**Interfaces:**
- Performs live HTTP requests against running or TestClient FastAPI instance across all core endpoints called by Frontend:
  - `GET /api/v1/pricing/matrix`
  - `POST /api/v1/pricing/matrix/simulate`
  - `GET /api/v1/pricing/recommendations`
  - `POST /api/v1/pricing/recommendations/{id}/approve`
  - `POST /api/v1/pricing/recommendations/{id}/reject`
  - `POST /api/v1/pricing/recommendations/{id}/apply-custom`
  - `GET /api/v1/pricing/history`
  - `GET /api/v1/matching/queue`
  - `POST /api/v1/matching/queue/{id}/approve`
  - `POST /api/v1/matching/queue/{id}/reject`
  - `GET /api/v1/crawl/results`

- [ ] **Step 1: Write integration verification script**

Create `backend/scripts/verify_fe_be_integration.py` testing each endpoint and asserting non-empty status and correct schema structure.

- [ ] **Step 2: Run verification script**

Run: `python backend/scripts/verify_fe_be_integration.py`
Expected: All 11 checks report SUCCESS.

- [ ] **Step 3: Run full pytest suite**

Run: `pytest backend/tests -v`
Expected: All 90+ tests PASS with zero regressions.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/verify_fe_be_integration.py
git commit -m "test: add end-to-end integration verification script"
```
