# Dynamic Pricing System - Monorepo

> **Dự án:** LQSMART-OJT — Dynamic Pricing System  
> **Kiến trúc:** Clean Domain Monorepo (Deep Modules & Clean Seams)  
> **Backend:** FastAPI (Python 3.11+) + SQLAlchemy + Alembic + PostgreSQL / SQLite  
> **Frontend:** React + Vite + TypeScript (No-Emoji Minimalist Design System)  
> **Scraping & Matching:** Strategy Pattern (CellphoneS, FPT Shop, Hoàng Hà) + Two-Tiered Matching (Regex + RapidFuzz)

---

## Cấu trúc Thư mục Monorepo

```text
dynamic-pricing/
├── backend/                      # Toàn bộ mã nguồn Python Backend
│   ├── app/                      # FastAPI Clean Architecture (api, core, models, schemas, services)
│   ├── tests/                    # Pytest Test Suite
│   ├── alembic/                  # Database Migrations
│   ├── scripts/                  # Pipeline CLI Scripts (run_full_pipeline.py, verify_setup.py...)
│   ├── data/                     # Dữ liệu mẫu (dim_product.xlsx, sample JSONs)
│   ├── alembic.ini               # Cấu hình Alembic
│   ├── pytest.ini                # Cấu hình Pytest
│   ├── requirements.txt          # Dependencies Python
│   └── .env                      # Biến môi trường Backend
│
├── frontend/                     # Toàn bộ mã nguồn React + Vite + TypeScript Frontend
│   ├── src/
│   │   ├── api/                  # API Client Adapter (crawlerApi.ts, matchingApi.ts)
│   │   ├── components/           # UI Components (MatchingReviewTable, CrawlControlPanel)
│   │   ├── pages/                # DashboardPage
│   │   ├── styles/               # CSS Design Tokens (No-Emoji, Color Coding)
│   │   └── types/                # TypeScript Interfaces
│   ├── package.json              # Dependencies Node.js
│   ├── vite.config.ts            # Cấu hình Vite (Port 5173)
│   └── .env                      # Biến môi trường Frontend (VITE_API_BASE_URL)
│
├── docker-compose.yml            # Chỉ chạy Database PostgreSQL cho môi trường dev local
├── .gitignore                    # Quản lý bỏ qua artifacts Python & Node.js
└── README.md                     # Hướng dẫn tổng thể
```

---

## Hướng dẫn Cài đặt & Vận hành

### 1. Khởi chạy CSDL (Tùy chọn - Docker PostgreSQL)
Nếu muốn sử dụng PostgreSQL thay vì SQLite mặc định:
```bash
docker-compose up -d
```

### 2. Vận hành Backend (FastAPI)
Mở một cửa sổ Terminal:
```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Cài đặt thư viện Python
pip install -r requirements.txt

# 3. Đồng bộ Database Migration
alembic upgrade head

# 4. Khởi động Backend Server
uvicorn app.main:app --reload --port 8000
```
- Swagger UI Tài liệu tương tác: **http://localhost:8000/docs**
- Health Check Endpoint: **http://localhost:8000/health**

### 3. Vận hành Frontend (React + Vite)
Mở cửa sổ Terminal thứ hai:
```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt thư viện Node.js
npm install

# 3. Khởi động Development Server
npm run dev
```
- Truy cập giao diện ứng dụng: **http://localhost:5173**

---

## Chạy Pipeline Đối Soát Đa Nguồn (CLI Scripts)
Tất cả các script đã được tập trung trong `backend/scripts/`:

```bash
# Chạy đầy đủ cào CellphoneS + Hoàng Hà và so khớp với 329 SKU FPT Shop
python backend/scripts/run_full_pipeline.py

# Hoặc dùng cache JSON để so khớp nhanh (skip scrape mạng)
python backend/scripts/run_full_pipeline.py --skip-scrape

# Kiểm thử nhanh thiết lập API & Debounce
python backend/scripts/verify_setup.py
```

---

## Kiểm thử Tự Động (Test Suite)

```bash
# Chạy Pytest từ thư mục backend
cd backend
pytest
```
