# Implementation Plan: Database Architecture & Migration

> **Goal:** Thiết kế và triển khai CSDL toàn diện 7 phân hệ theo Obsidian context, PostgreSQL patterns, SQLAlchemy models và Alembic migrations.
> **Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL / SQLite
> **Spec Reference:** `specs/database-design/data-model.md`
> **Domain Context:** `docs/obsidian-notes/Thiết kế Cơ sở Dữ liệu Toàn diện.md`

---

## 1. Technical Context & Constitution Gates

- [x] **I. CodeGraph First & Blast Radius:** Đã khảo sát `backend/app/models/` và các callers trước khi cập nhật.
- [x] **II. Deep Modules & Clean Architecture:** Tách rời các phân hệ: Catalog (`product.py`), Crawler (`crawl_job.py`, `crawl_result.py`), Matching (`sku_mapping.py`), Inventory (`inventory.py`), Demand (`demand.py`), Pricing (`pricing.py`), Chat (`chat.py`).
- [x] **III. TDD & Anti-Regression:** Bộ kiểm thử `tests/test_database_schema.py` đạt 100% pass (27/27 tests).
- [x] **IV. Schema Versioning via Alembic:** Toàn bộ thay đổi CSDL được đóng gói qua migration `dbbe0db0b38f_expand_comprehensive_schema.py`.

---

## 2. Implementation Deliverables

1. **Alembic Migration:**
   - [`backend/alembic/versions/dbbe0db0b38f_expand_comprehensive_schema.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/alembic/versions/dbbe0db0b38f_expand_comprehensive_schema.py)
2. **SQLAlchemy Models:**
   - [`backend/app/models/product.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/product.py)
   - [`backend/app/models/crawl_job.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/crawl_job.py)
   - [`backend/app/models/crawl_result.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/crawl_result.py)
   - [`backend/app/models/sku_mapping.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/sku_mapping.py)
   - [`backend/app/models/inventory.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/inventory.py)
   - [`backend/app/models/demand.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/demand.py)
   - [`backend/app/models/pricing.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/pricing.py)
   - [`backend/app/models/chat.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/chat.py)
   - [`backend/app/models/__init__.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/app/models/__init__.py)
3. **Verification Test Suite:**
   - [`backend/tests/test_database_schema.py`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/backend/tests/test_database_schema.py)
