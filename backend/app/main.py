import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.database import Base, engine
from app import models as _models  # noqa: F401 - registers models with Base.metadata
from app.api.v1.router import api_router

# Thiết lập log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dynamic_pricing")


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Khởi tạo bảng CSDL khi khởi động (đảm bảo chạy ngay không cần gõ lệnh thủ công)
    logger.info(" Đang khởi tạo kết nối CSDL và tự động tạo bảng nếu chưa có...")
    Base.metadata.create_all(bind=engine)
    logger.info(" Hệ thống sẵn sàng phục vụ!")
    yield
    logger.info("Đang tắt hệ thống...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## Hệ thống Hỗ trợ Định giá Bán lẻ Tự động (Dynamic Pricing System)

    ### Tính năng chính Sprint 1:
    * **PBI-001 & PBI-004:** Thu thập dữ liệu đối thủ (CellphoneS, Hoàng Hà, FPT Shop) & Kích hoạt cào tức thời (Debounce 30s).
    * **PBI-006 & PBI-007:** So khớp sản phẩm (Exact Part-Number & Normalized Attribute Match).
    * **PBI-009:** Quản lý tồn kho giả lập FPT Shop (DOH, Giá vốn, Giá sàn).

    Tài liệu API tương tác tự động bởi **Swagger UI**.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Cấu hình CORS cho phép React/Vite Frontend kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn Router v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root():
    """Tự động chuyển hướng từ trang chủ sang Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"])
def health_check():
    """Kiểm tra trạng thái hoạt động của hệ thống."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
