# Tách Biệt Backend và Frontend (Monorepo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tái cấu trúc repository thành mô hình Clean Domain Monorepo với 2 không gian biệt lập: `backend/` (FastAPI, Alembic, Scrapers, Matching Engine, Scripts, Datasets) và `frontend/` (React, Vite, TypeScript), chuẩn hóa Seam HTTP REST API và bảo toàn 100% lịch sử Git.

**Architecture:** Áp dụng các nguyên tắc từ `codebase-design`: phân tách Seam tại HTTP API (`/api/v1`), xem Backend như một Deep Module và Frontend sử dụng API Client Adapter chuyên trách; gom toàn bộ logic, scripts, dữ liệu mẫu vào `backend/` để bảo đảm tính Locality; tạo khung skeleton Frontend sẵn sàng kết nối.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pytest, React 18/19, Vite, TypeScript, Vanilla CSS (Design Tokens, Không Emoji/Icon), Git, PostgreSQL / SQLite.

**Spec:** [`docs/superpowers/specs/2026-10-05-monorepo-backend-frontend-design.md`](file:///c:/Users/nguye/OneDrive/Desktop/Du_an/dynamic-priciing/docs/superpowers/specs/2026-10-05-monorepo-backend-frontend-design.md)

## Global Constraints

- **Git Preservation:** Bắt buộc dùng `git mv` cho tất cả các file mã nguồn hiện có để bảo toàn lịch sử commit git.
- **Zero Emoji/Icon:** Tuyệt đối không dùng emoji hoặc icon trang trí trong bất kỳ UI component hay style nào của Frontend; dùng typography và bảng mã màu (color-coding) để phân cấp trạng thái.
- **Deep Modules:** Giữ cho interface của service và API adapter luôn nhỏ gọn, đóng gói toàn bộ logic phức tạp bên trong.
- **Test Integrity:** Toàn bộ test suite `pytest` phải chạy thành công 100% khi đứng từ thư mục `backend/`.
- **Local-first Dev:** Backend chạy qua `uvicorn app.main:app` trong `backend/`, frontend chạy qua `npm run dev` trong `frontend/`, root `docker-compose.yml` chỉ khởi chạy Database PostgreSQL.

## Review Focus

1. **Broken imports trong `backend/scripts/*.py`:** Khi script được chuyển vào `backend/scripts/`, các lệnh `from app.core...` có thể gặp `ModuleNotFoundError` nếu không nạp `backend` vào `sys.path`. Pin test: chạy thử script với flag `--help` hoặc mock execution.
2. **File data không tìm thấy khi chạy script:** Các script tham chiếu tới `data/fpt_products_329.json` theo đường dẫn tương đối sẽ lỗi nếu đường dẫn bị hardcode. Pin test: kiểm tra đường dẫn qua `Path(__file__).resolve().parent.parent / "data"`.
3. **Alembic migration path mismatch:** File `alembic.ini` cần trỏ đúng thư mục `alembic` khi lệnh được gọi từ `backend/`. Pin test: chạy `alembic check` hoặc `alembic heads` từ `backend/`.
4. **CORS policy blocking Frontend:** Vite dev server chạy cổng 5173 cần được cho phép truy cập backend cổng 8000. Pin test: kiểm tra `CORSMiddleware` cấu hình trong `backend/app/main.py`.
5. **Git merge conflict / lost files:** Kiểm tra kỹ `git status` trước và sau mỗi bước di chuyển để không bỏ sót file nào ở root.

---

### Task 1: Di chuyển Mã nguồn Backend và Cấu hình vào `backend/`

**Files:**
- Create: `backend/`
- Modify (Move via `git mv`):
  - `app/` ➔ `backend/app/`
  - `tests/` ➔ `backend/tests/`
  - `alembic/` ➔ `backend/alembic/`
  - `alembic.ini` ➔ `backend/alembic.ini`
  - `requirements.txt` ➔ `backend/requirements.txt`
  - `pytest.ini` ➔ `backend/pytest.ini`
  - `.env` ➔ `backend/.env`
  - `.env.example` ➔ `backend/.env.example`
  - `dynamic_pricing.db` ➔ `backend/dynamic_pricing.db`

**Interfaces:**
- Consumes: Cấu trúc backend hiện tại ở root.
- Produces: Thư mục `backend/` chứa toàn bộ mã nguồn core và cấu hình chạy FastAPI.

- [ ] **Step 1: Tạo thư mục `backend/` và thực thi di chuyển tệp bằng `git mv`**
  ```powershell
  mkdir backend
  git mv app backend/app
  git mv tests backend/tests
  git mv alembic backend/alembic
  git mv alembic.ini backend/alembic.ini
  git mv requirements.txt backend/requirements.txt
  git mv pytest.ini backend/pytest.ini
  git mv .env backend/.env
  git mv .env.example backend/.env.example
  git mv dynamic_pricing.db backend/dynamic_pricing.db
  ```

- [ ] **Step 2: Kiểm tra trạng thái git**
  Chạy: `git status -s`  
  Kỳ vọng: Các tệp hiển thị dạng rename `R  app/... -> backend/app/...` chứng tỏ lịch sử git được giữ nguyên.

- [ ] **Step 3: Commit thay đổi cấu trúc backend**
  ```powershell
  git commit -m "refactor(backend): move app, tests, and configs to backend directory"
  ```

---

### Task 2: Di chuyển Scripts & Datasets vào `backend/scripts/` và `backend/data/` kèm Chuẩn hóa Path

**Files:**
- Modify (Move via `git mv`):
  - `data/` ➔ `backend/data/`
  - `run_full_pipeline.py` ➔ `backend/scripts/run_full_pipeline.py`
  - `run_cellphones_pipeline.py` ➔ `backend/scripts/run_cellphones_pipeline.py`
  - `run_hoangha_pipeline.py` ➔ `backend/scripts/run_hoangha_pipeline.py`
  - `run_sku_matching_and_export.py` ➔ `backend/scripts/run_sku_matching_and_export.py`
  - `collect_sample_data.py` ➔ `backend/scripts/collect_sample_data.py`
  - `verify_setup.py` ➔ `backend/scripts/verify_setup.py`
- Modify: `backend/scripts/*.py` (Bổ sung `sys.path` injection và cập nhật đường dẫn `data/`)

**Interfaces:**
- Consumes: Datasets và scripts từ root.
- Produces: `backend/scripts/` với khả năng chạy độc lập từ bất kỳ thư mục nào bằng cách tự nạp `backend/` vào `sys.path`.

- [ ] **Step 1: Di chuyển thư mục `data/` và các scripts bằng `git mv`**
  ```powershell
  git mv data backend/data
  mkdir backend/scripts
  git mv run_full_pipeline.py backend/scripts/run_full_pipeline.py
  git mv run_cellphones_pipeline.py backend/scripts/run_cellphones_pipeline.py
  git mv run_hoangha_pipeline.py backend/scripts/run_hoangha_pipeline.py
  git mv run_sku_matching_and_export.py backend/scripts/run_sku_matching_and_export.py
  git mv collect_sample_data.py backend/scripts/collect_sample_data.py
  git mv verify_setup.py backend/scripts/verify_setup.py
  ```

- [ ] **Step 2: Cập nhật `sys.path` và đường dẫn dữ liệu trong các file `backend/scripts/*.py`**
  Thêm đoạn mã chuẩn hóa vào đầu mỗi script:
  ```python
  import sys
  from pathlib import Path
  BACKEND_DIR = Path(__file__).resolve().parent.parent
  if str(BACKEND_DIR) not in sys.path:
      sys.path.insert(0, str(BACKEND_DIR))
  DATA_DIR = BACKEND_DIR / "data"
  ```
  Thay thế các chuỗi `"data/..."` hoặc `Path("data/...")` thành `DATA_DIR / "..."`.

- [ ] **Step 3: Chạy thử kiểm chứng pipeline script**
  Chạy: `python backend/scripts/run_full_pipeline.py --help`  
  Kỳ vọng: Hiển thị hướng dẫn command line, không có lỗi `ModuleNotFoundError`.

- [ ] **Step 4: Commit thay đổi scripts và data**
  ```powershell
  git commit -m "refactor(backend): relocate scripts and datasets to backend with normalized paths"
  ```

---

### Task 3: Xác minh Hoạt động Backend (Alembic, Pytest Suite & FastAPI Health)

**Files:**
- Modify: `backend/alembic.ini` (nếu cần điều chỉnh đường dẫn tương đối)
- Modify: `backend/app/main.py` (đảm bảo CORS cho phép `http://localhost:5173`)
- Test: `backend/tests/`

**Interfaces:**
- Consumes: Mã nguồn và test suite đã chuyển vào `backend/`.
- Produces: Backend vận hành ổn định, 100% tests PASS, Alembic nhận diện migration.

- [ ] **Step 1: Chạy kiểm tra Alembic từ thư mục `backend/`**
  Chạy lệnh trong PowerShell:
  ```powershell
  cd backend; alembic heads; cd ..
  ```
  Kỳ vọng: Hiển thị revision head hiện tại (ví dụ: `001_initial_schema (head)`).

- [ ] **Step 2: Chạy toàn bộ Pytest Test Suite từ thư mục `backend/`**
  Chạy lệnh trong PowerShell:
  ```powershell
  cd backend; pytest; cd ..
  ```
  Kỳ vọng: Toàn bộ tests trong `backend/tests/` PASS 100%.

- [ ] **Step 3: Kiểm tra cấu hình CORS trong `backend/app/main.py`**
  Đảm bảo danh sách `allow_origins` chứa cả `http://localhost:5173` và `http://127.0.0.1:5173`.

- [ ] **Step 4: Commit xác minh backend**
  ```powershell
  git add backend/app/main.py backend/alembic.ini
  git commit -m "fix(backend): verify alembic and cors configuration for frontend port 5173"
  ```

---

### Task 4: Khởi tạo Khung Ứng Dụng `frontend/` (React + Vite + TypeScript)

**Files:**
- Create:
  - `frontend/package.json`
  - `frontend/tsconfig.json`
  - `frontend/tsconfig.node.json`
  - `frontend/vite.config.ts`
  - `frontend/index.html`
  - `frontend/.env`
  - `frontend/.env.example`
  - `frontend/src/main.tsx`
  - `frontend/src/App.tsx`
  - `frontend/src/styles/tokens.css`
  - `frontend/src/types/index.ts`
  - `frontend/src/api/client.ts`
  - `frontend/src/api/crawlerApi.ts`
  - `frontend/src/api/matchingApi.ts`
  - `frontend/src/components/MatchingReviewTable.tsx`
  - `frontend/src/components/CrawlControlPanel.tsx`
  - `frontend/src/pages/DashboardPage.tsx`

**Interfaces:**
- Consumes: OpenAPI Contract từ Backend (`/api/v1/crawl`, `/api/v1/mappings`, `/api/v1/products`).
- Produces: Ứng dụng Frontend độc lập có API Client Adapter, UI Modules không icon/emoji, sẵn sàng chạy với `npm run dev`.

- [ ] **Step 1: Khởi tạo cấu trúc file cấu hình `frontend/`**
  Tạo `frontend/package.json` với các dependency: `react`, `react-dom`, `@types/react`, `@types/react-dom`, `vite`, `typescript`.  
  Tạo `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/index.html`.  
  Tạo `frontend/.env` với:
  ```env
  VITE_API_BASE_URL=http://localhost:8000/api/v1
  ```

- [ ] **Step 2: Xây dựng Design Tokens (`frontend/src/styles/tokens.css`)**
  Thiết lập biến màu sắc chuẩn:
  - Màu nền, chữ, viền tối giản và thanh lịch.
  - Mã màu trạng thái: Green (`#16a34a`), Orange (`#ea580c`), Red (`#dc2626`).
  - Font typography chuẩn (Inter / system-ui).
  - Tuân thủ quy định: KHÔNG emoji, KHÔNG icon trang trí.

- [ ] **Step 3: Xây dựng API Client Adapter (`frontend/src/api/client.ts`, `crawlerApi.ts`, `matchingApi.ts`)**
  Xây dựng Deep Module bọc `fetch()` với base URL từ env, type definitions rõ ràng cho `Product`, `CrawlResult`, `SkuMapping`.

- [ ] **Step 4: Xây dựng các UI Components và Trang Dashboard**
  Tạo `MatchingReviewTable.tsx`, `CrawlControlPanel.tsx`, `DashboardPage.tsx` với giao diện chuyên nghiệp, phân cấp thông tin rõ ràng.

- [ ] **Step 5: Kiểm tra tính hợp lệ của TypeScript & Build**
  Kiểm tra cú pháp code frontend (không có lỗi type hay import gãy).

- [ ] **Step 6: Commit khung ứng dụng frontend**
  ```powershell
  git add frontend/
  git commit -m "feat(frontend): scaffold react vite typescript application with deep api adapter"
  ```

---

### Task 5: Tối ưu Cấu hình Root và Đồng bộ Hệ thống (`docker-compose`, `.gitignore`, `README`)

**Files:**
- Modify: `docker-compose.yml` (chỉ giữ lại service PostgreSQL cho local development)
- Modify: `.gitignore` (bổ sung rules cho Node.js `node_modules`, `dist`, `.env.local` và Python `backend/`)
- Modify: `README.md` (hướng dẫn vận hành Monorepo)

**Interfaces:**
- Consumes: Cấu trúc monorepo hoàn chỉnh.
- Produces: Thư mục root tinh gọn, tài liệu hướng dẫn rõ ràng cho cả Backend và Frontend.

- [ ] **Step 1: Cập nhật `docker-compose.yml` tại root**
  Giữ lại service PostgreSQL trên cổng 5432, loại bỏ cấu hình cũ không cần thiết nếu có.

- [ ] **Step 2: Cập nhật `.gitignore` tại root**
  Đảm bảo ignore:
  ```gitignore
  # Backend Python
  backend/__pycache__/
  backend/*.db
  backend/.pytest_cache/
  backend/.env

  # Frontend Node.js
  frontend/node_modules/
  frontend/dist/
  frontend/.env.local
  ```

- [ ] **Step 3: Cập nhật `README.md`**
  Cập nhật tài liệu:
  - Kiến trúc Monorepo (`backend/` & `frontend/`).
  - Lệnh chạy Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
  - Lệnh chạy Frontend: `cd frontend && npm install && npm run dev`
  - Lệnh chạy Database: `docker-compose up -d`
  - Lệnh chạy pipeline: `python backend/scripts/run_full_pipeline.py`

- [ ] **Step 4: Đồng bộ chỉ mục CodeGraph**
  Chạy lệnh: `codegraph sync` (hoặc `codegraph index` nếu cấu trúc thay đổi lớn) để cập nhật vị trí mới của các symbols vào `.codegraph/`.

- [ ] **Step 5: Commit cấu hình root**
  ```powershell
  git add docker-compose.yml .gitignore README.md
  git commit -m "chore: update root docker-compose, gitignore, and monorepo documentation"
  ```

---

### Task 6: Kiểm thử Tích hợp & Nghiệm thu Toàn diện (End-to-End Verification)

**Files:**
- Test: Toàn bộ hệ thống Backend và Frontend.

- [ ] **Step 1: Chạy Pytest từ `backend/`**
  ```powershell
  cd backend; pytest; cd ..
  ```
  Kỳ vọng: 100% tests PASS.

- [ ] **Step 2: Chạy kiểm tra Full Pipeline (Skip Scrape)**
  ```powershell
  python backend/scripts/run_full_pipeline.py --skip-scrape
  ```
  Kỳ vọng: Pipeline nạp dữ liệu từ `backend/data/` thành công, thực hiện so khớp và không có lỗi đường dẫn.

- [ ] **Step 3: Kiểm tra tính sạch sẽ của Git Workspace**
  ```powershell
  git status
  ```
  Kỳ vọng: `working tree clean`, không còn file rác nào ở root.
