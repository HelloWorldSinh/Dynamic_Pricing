# Architectural Specification: Tách Biệt Codebase Backend và Frontend (Clean Domain Monorepo)

**Ngày lập:** 2026-10-05  
**Trạng thái:** Proposed (Chờ phê duyệt)  
**Tác giả:** AI Assistant & Tech Lead  
**Phương pháp áp dụng:** Superpowers Brainstorming & Codebase Design (Deep Modules, Clean Seams)

---

## 1. Bối cảnh & Mục tiêu (Context & Objectives)

### 1.1. Hiện trạng
Hệ thống **Dynamic Pricing System** hiện tại đang tổ chức dưới dạng một ứng dụng đơn lẻ tập trung hoàn toàn vào Backend Python (FastAPI + SQLAlchemy + Alembic). Toàn bộ mã nguồn, cấu hình, dữ liệu mẫu và các script pipeline đều tập trung tại thư mục gốc repository:
- `app/`: Mã nguồn chính FastAPI.
- `alembic/` & `alembic.ini`: Quản lý migration CSDL.
- `data/`: Dữ liệu mẫu JSON (`fpt_products_329.json`, `cellphones_sample.json`, `hoangha_sample.json`).
- 6 script độc lập ở root: `run_full_pipeline.py`, `run_cellphones_pipeline.py`, `run_hoangha_pipeline.py`, `run_sku_matching_and_export.py`, `collect_sample_data.py`, `verify_setup.py`.

### 1.2. Vấn đề
- Chưa có cấu trúc cho ứng dụng giao diện (Frontend).
- Thư mục gốc bị ô nhiễm bởi các script chạy ngầm và file dữ liệu mẫu, làm mờ nhạt tính bao đóng (locality) của module backend.
- Cần một cấu trúc chuẩn Monorepo để sẵn sàng tích hợp giao diện người dùng (React + Vite + TypeScript) cho phép theo dõi đối thủ và duyệt kết quả so khớp SKU trong Sprint tiếp theo.

### 1.3. Mục tiêu kiến trúc
- Tái cấu trúc codebase thành mô hình **Clean Domain Monorepo** với 2 không gian biệt lập: `backend/` và `frontend/`.
- Thiết lập ranh giới phân tách (Seam) chuẩn mực qua HTTP REST API (OpenAPI 3.0).
- Đảm bảo tính đóng gói sâu (**Deep Modules**), giao diện kiểm thử độc lập (**Test Surfaces**) và bảo toàn 100% lịch sử Git thông qua lệnh di chuyển an toàn (`git mv`).
- Giữ cấu hình Docker Compose tại root ở mức tối giản (chỉ chạy CSDL PostgreSQL), hỗ trợ phát triển theo định hướng **Local-first Dev**.

---

## 2. Các Nguyên tắc Thiết kế (Codebase Design Principles)

Tuân thủ chặt chẽ các thuật ngữ và nguyên lý từ `codebase-design`:

1. **Ranh giới Seam chuẩn mực (HTTP Contract Seam):**
   - Ranh giới giữa Frontend và Backend nằm tại HTTP API (`/api/v1/...`).
   - Mọi thay đổi nội bộ của Backend (thuật toán cào, chuyển đổi CSDL, logic debounce) không làm ảnh hưởng đến Frontend nếu Interface không đổi.
2. **Backend là một Deep Module:**
   - Interface nhỏ (Small Surface Area): Một tập hợp các endpoint RESTful tinh gọn.
   - Implementation sâu (Deep Implementation): Đóng gói toàn bộ logic phức tạp gồm Multi-threading Crawlers, Debounce Task Queue, Two-Tiered SKU Matching Engine, SQLAlchemy Session & Transaction Management.
3. **Frontend API Client Adapter:**
   - Đặt tại Seam phía client để các React Component không gọi trực tiếp `fetch()` hoặc phụ thuộc vào URL cứng.
   - Adapter đóng vai trò chuyển hóa yêu cầu nghiệp vụ thành lời gọi HTTP, bọc lỗi mạng và parse dữ liệu có kiểu (TypeScript types).
4. **Bề mặt kiểm thử độc lập (The Interface is the Test Surface):**
   - Backend được kiểm thử qua Service interfaces (Unit tests) và TestClient (Integration tests).
   - Frontend được kiểm thử độc lập bằng cách thay thế API Adapter bằng Mock Adapter/Fake data, không cần dựng backend server khi chạy unit test giao diện.
5. **The Deletion Test (Kiểm chứng xóa module):**
   - Xóa thư mục `frontend/` không làm ảnh hưởng đến bất kỳ tính năng hay script nào của `backend/`.
   - Thay thế `frontend/` bằng một client khác (Mobile app, CLI) chỉ cần tuân theo OpenAPI schema.

---

## 3. Cấu trúc Cây Thư mục Đích (Target Directory Structure)

```text
dynamic-pricing/
│
├── backend/                             # Không gian Backend (Python 3.11+)
│   ├── app/                             # FastAPI Clean Architecture
│   │   ├── api/                         # REST API Controllers (v1 routers)
│   │   ├── core/                        # Config, Database Engine, Security
│   │   ├── models/                      # SQLAlchemy ORM Models
│   │   ├── schemas/                     # Pydantic Request/Response Models
│   │   ├── services/                    # Crawler Engine, SKU Matching, Inventory
│   │   ├── utils/                       # Helpers & Utilities
│   │   └── main.py                      # FastAPI App Entrypoint
│   ├── tests/                           # Pytest Test Suite
│   ├── alembic/                         # Alembic Migrations
│   ├── alembic.ini                      # Cấu hình Alembic
│   ├── scripts/                         # CLI Scripts & Pipeline Tools
│   │   ├── run_full_pipeline.py
│   │   ├── run_cellphones_pipeline.py
│   │   ├── run_hoangha_pipeline.py
│   │   ├── run_sku_matching_and_export.py
│   │   ├── collect_sample_data.py
│   │   └── verify_setup.py
│   ├── data/                            # Datasets & Mẫu dữ liệu cào
│   │   ├── fpt_products_329.json
│   │   ├── cellphones_sample.json
│   │   └── hoangha_sample.json
│   ├── requirements.txt                 # Thư viện phụ thuộc Python
│   ├── pytest.ini                       # Cấu hình Pytest
│   ├── dynamic_pricing.db               # SQLite local database (dev)
│   ├── .env                             # Biến môi trường Backend
│   └── .env.example
│
├── frontend/                            # Không gian Frontend (React + Vite + TS)
│   ├── src/
│   │   ├── api/                         # API Client Adapter
│   │   │   ├── client.ts                # Axios/Fetch Base instance
│   │   │   ├── crawlerApi.ts            # Quản lý trigger & trạng thái cào
│   │   │   └── matchingApi.ts           # Dữ liệu đối soát SKU & duyệt
│   │   ├── components/                  # UI Components tái sử dụng
│   │   │   ├── layout/                  # Header, Sidebar, Container
│   │   │   ├── MatchingReviewTable.tsx  # Bảng đối soát SKU (No-Emoji, Color-coded)
│   │   │   └── CrawlControlPanel.tsx    # Bảng điều khiển cào tức thời
│   │   ├── pages/                       # Màn hình ứng dụng
│   │   │   ├── DashboardPage.tsx        # Tổng quan & KPI
│   │   │   ├── CrawlManagerPage.tsx     # Quản lý cào đối thủ
│   │   │   └── SkuMatchingPage.tsx      # Quản lý đối soát sản phẩm
│   │   ├── types/                       # TypeScript Data Models
│   │   │   ├── product.ts
│   │   │   ├── crawl.ts
│   │   │   └── mapping.ts
│   │   ├── styles/                      # CSS Modules / Design Tokens
│   │   │   └── tokens.css               # Màu sắc, typography, spacing
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env                             # Biến môi trường Frontend (VITE_API_BASE_URL)
│
├── docker-compose.yml                   # Khởi chạy PostgreSQL CSDL cho môi trường local
├── .gitignore                           # Bỏ qua artifacts cho cả Python và Node.js
├── README.md                            # Hướng dẫn tổng thể monorepo
├── docs/                                # Tài liệu kỹ thuật & Obsidian Notes Bridge
├── .agents/                             # AI Agent Workflows & Skills
├── .specify/                            # Spec Kit Configurations & Constitution
└── .codegraph/                          # CodeGraph Index Data
```

---

## 4. Thiết kế Chi tiết Từng Module & Seams

### 4.1. Seam HTTP API & CORS
- **Base URL:** `http://localhost:8000/api/v1`
- **CORS Configuration (`backend/app/main.py`):**
  Cho phép cổng mặc định của Vite Frontend (`http://localhost:5173`) truy cập:
  ```python
  origins = [
      "http://localhost:5173",
      "http://127.0.0.1:5173",
      *settings.CORS_ORIGINS
  ]
  ```
- **Frontend Environment (`frontend/.env`):**
  ```env
  VITE_API_BASE_URL=http://localhost:8000/api/v1
  ```

### 4.2. Deep Modules trong Backend
1. **`CrawlerService` (`backend/app/services/crawler/`):**
   - Bề mặt công khai (Public Interface):
     - `trigger_crawl(source: str) -> CrawlJobResult`
     - `get_status(source: str) -> DebounceStatus`
   - Đóng gói (Implementation): Thuật toán Debounce 30 giây bảo vệ tài nguyên, Strategy Pattern cào dữ liệu qua `BaseScraper`.
2. **`MatchingEngine` (`backend/app/services/matching/`):**
   - Bề mặt công khai:
     - `match_product(product: Product, candidates: list[CrawlResult]) -> list[MatchCandidate]`
   - Đóng gói: Inverted Index tra cứu $O(1)$, Tier 1 Regex Part-Number, Tier 2 RapidFuzz token matching.
3. **`Scripts & Pipeline` (`backend/scripts/`):**
   - Toàn bộ script độc lập nạp đường dẫn module qua cấu hình động `Path(__file__).resolve().parent.parent` để nhập `app.*` một cách tự nhiên.

### 4.3. Deep Modules trong Frontend
1. **`APIClient` Adapter (`frontend/src/api/`):**
   - Cung cấp giao diện hàm typed trả về dữ liệu thuần túy:
     ```typescript
     export async function getSkuMappings(params?: MappingFilter): Promise<SkuMappingResponse>;
     export async function triggerCrawl(source: string): Promise<CrawlTriggerResponse>;
     ```
   - Xử lý chuyển đổi định dạng và phân tích mã lỗi HTTP tập trung.
2. **`MatchingReviewTable` Component (`frontend/src/components/MatchingReviewTable.tsx`):**
   - Nhận danh sách mapping và callbacks hành động (`onApprove`, `onReject`).
   - Tự động quản lý lọc, phân trang, và hiển thị huy hiệu mức độ tin cậy bằng màu sắc chuẩn mực.
3. **Quy tắc Thiết kế Giao diện (UI Design Guidelines Enforcement):**
   - **Tuyệt đối KHÔNG sử dụng icon hoặc emoji** trang trí trên các nhãn, nút bấm, bảng hoặc thông báo.
   - **Phân cấp trạng thái bằng màu sắc và typography:**
     - Xanh lá (`#16a34a` / `#dcfce7`): Khớp chính xác (Confidence >= 85%).
     - Cam (`#ea580c` / `#ffedd5`): Cần xác nhận thủ công (Confidence 60% - 84%).
     - Đỏ (`#dc2626` / `#fee2e2`): Không khớp (Confidence < 60%).

---

## 5. Kế hoạch Di Dời Tệp & Chuẩn Hóa Đường Dẫn (Safe Migration Plan)

### Bước 1: Di chuyển tệp bằng `git mv` (Bảo toàn Git History)
1. Tạo thư mục `backend/` và di chuyển:
   - `git mv app backend/app`
   - `git mv tests backend/tests`
   - `git mv alembic backend/alembic`
   - `git mv alembic.ini backend/alembic.ini`
   - `git mv requirements.txt backend/requirements.txt`
   - `git mv pytest.ini backend/pytest.ini`
   - `git mv .env backend/.env`
   - `git mv .env.example backend/.env.example`
   - `git mv dynamic_pricing.db backend/dynamic_pricing.db`
2. Tạo thư mục `backend/scripts/` và `backend/data/`:
   - `git mv data backend/data`
   - `git mv run_full_pipeline.py backend/scripts/run_full_pipeline.py`
   - `git mv run_cellphones_pipeline.py backend/scripts/run_cellphones_pipeline.py`
   - `git mv run_hoangha_pipeline.py backend/scripts/run_hoangha_pipeline.py`
   - `git mv run_sku_matching_and_export.py backend/scripts/run_sku_matching_and_export.py`
   - `git mv collect_sample_data.py backend/scripts/collect_sample_data.py`
   - `git mv verify_setup.py backend/scripts/verify_setup.py`

### Bước 2: Cập nhật cấu hình & Đường dẫn tương đối
1. **`backend/alembic.ini`:**
   Giữ nguyên `script_location = alembic`. Khi thực thi lệnh migration, lập trình viên chạy từ thư mục `backend/`:
   ```bash
   cd backend && alembic upgrade head
   ```
2. **`backend/scripts/*.py`:**
   Thêm snippet đường dẫn vào đầu mỗi file script:
   ```python
   import sys
   from pathlib import Path
   BACKEND_DIR = Path(__file__).resolve().parent.parent
   if str(BACKEND_DIR) not in sys.path:
       sys.path.insert(0, str(BACKEND_DIR))
   ```
   Cập nhật đường dẫn nạp file JSON từ `data/...` thành `BACKEND_DIR / "data" / ...`.

### Bước 3: Khởi tạo Cấu trúc `frontend/`
1. Khởi tạo cấu trúc thư mục React + Vite + TypeScript trong `frontend/`.
2. Tạo `package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`.
3. Tạo cấu trúc thư mục `src/api`, `src/components`, `src/pages`, `src/types`, `src/styles`.
4. Tạo `frontend/.env` với `VITE_API_BASE_URL=http://localhost:8000/api/v1`.

### Bước 4: Tinh chỉnh Root và Tài liệu
1. **Root `docker-compose.yml`:** Tối ưu hóa để chỉ duy trì service `postgres` cho CSDL.
2. **Root `.gitignore`:** Thêm quy tắc bỏ qua `frontend/node_modules/`, `frontend/dist/`, `.env.local`.
3. **Root `README.md`:** Cập nhật hướng dẫn chạy Local-first:
   - Backend: `cd backend && uvicorn app.main:app --reload`
   - Frontend: `cd frontend && npm install && npm run dev`
4. **Đồng bộ CodeGraph:** Chạy `codegraph sync` để cập nhật vị trí mới của các biểu tượng mã nguồn.

---

## 6. Tiêu Chuẩn Nghiệm Thu & Kiểm Chứng (Verification Criteria)

1. **Backend Tests:**
   - Đứng tại thư mục `backend/`, thực thi `pytest`: 100% test cases trong `backend/tests/` phải PASS.
2. **Backend API Health:**
   - Khởi động `uvicorn app.main:app --port 8000`: Truy cập `GET http://localhost:8000/health` trả về HTTP 200 `{ "status": "healthy" }`.
3. **Pipeline Execution:**
   - Chạy `python backend/scripts/run_full_pipeline.py --skip-scrape`: Đối soát thành công và xuất dữ liệu đối soát không lỗi đường dẫn.
4. **Frontend Build & Structure:**
   - Khởi tạo thành công khung dự án `frontend/`, chạy `npm run build` hoặc kiểm tra cú pháp TypeScript không có lỗi compile.
5. **Git Integrity:**
   - Lịch sử commit của các file cũ được bảo toàn nguyên vẹn qua `git log --follow`.
