# Dynamic Pricing System - Backend API

> **Dự án:** LQSMART-OJT — Dynamic Pricing System  
> **Backend:** FastAPI (Python 3.11+) + SQLAlchemy + Alembic + PostgreSQL / SQLite  
> **Scraping:** Strategy Pattern (CellphoneS, FPT Shop, Hoàng Hà) + RapidFuzz

---

## 🚀 Tính năng đã triển khai (Sprint 1 Foundation)

1. **Cơ sở dữ liệu (PostgreSQL / SQLite):**
   - `products`: Danh mục sản phẩm chuẩn FPT Shop.
   - `crawl_results`: Dữ liệu cào từ các trang đối thủ (chứa thông số kỹ thuật JSONB).
   - `sku_mappings`: Bảng đối soát khớp sản phẩm (Confidence Score).
   - `inventory_mock`: Tồn kho giả lập, số ngày lưu kho (DOH), giá sàn và giá vốn (PBI-009).
2. **Quản lý Database Migration:**
   - Sử dụng **Alembic** để tự động quản lý phiên bản và đồng bộ bảng CSDL.
3. **Deep Modules & Crawler Engine:**
   - **Strategy Pattern:** `BaseScraper` -> `CellphonesScraper`, `HoanghaScraper`.
   - **CrawlerService:** Quản lý BackgroundTasks và cơ chế **Debounce 30 giây** bảo vệ hệ thống.
   - **SKU Matching Engine:** So khớp 2 tầng chuẩn Clean Architecture, tra cứu $O(1)$ qua Inverted Index (`app/services/matching/`).
4. **FastAPI & Swagger UI:**
   - Tự động sinh tài liệu API trực quan tại `/docs`.
   - Cấu hình sẵn CORS cho Frontend (React/Vite) kết nối.
   - Endpoint: `POST /api/v1/crawl/trigger` kích hoạt cào tức thời (PBI-004).

---

## 🛠️ Hướng dẫn cài đặt & Chạy dự án

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
File `.env` mặc định sử dụng SQLite để chạy test ngay lập tức mà không cần cài đặt thêm:
```env
DATABASE_URL=sqlite:///./dynamic_pricing.db
DEBOUNCE_SECONDS=30
```
*(Nếu muốn dùng PostgreSQL với Docker, xem file `docker-compose.yml` và đổi sang `postgresql+psycopg2://postgres:postgres@localhost:5432/dynamic_pricing`)*

### 3. Đồng bộ CSDL (Migration)
```bash
alembic upgrade head
```

### 4. Khởi động Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

Truy cập Swagger UI trên trình duyệt:  
👉 **http://localhost:8000/docs**

---

## 🧪 Chạy Pipeline Đối Soát Đa Nguồn (Full Pipeline)
```bash
# Chạy đầy đủ cào CellphoneS + Hoàng Hà và đối soát với 329 SKU FPT Shop
python run_full_pipeline.py

# Hoặc dùng cache JSON để đối soát nhanh không cần cào lại mạng
python run_full_pipeline.py --skip-scrape
```

---

## 🧪 Kiểm thử (Test Suite)
```bash
pytest
```
