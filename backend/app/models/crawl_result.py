import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID


class CrawlResult(Base):
    """Bảng lưu dữ liệu cào thô từ 3 nguồn: CellphoneS, Hoàng Hà, FPT Shop."""
    __tablename__ = "crawl_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("crawl_jobs.id"), nullable=True, index=True)
    source = Column(String(50), nullable=False, index=True)   # CELLPHONES | HOANGHA | FPTSHOP
    url = Column(String(1000), nullable=False)
    raw_name = Column(String(255), nullable=False, index=True)
    current_price = Column(BigInteger, nullable=True)         # Giá bán thực tế (VND)
    original_price = Column(BigInteger, nullable=True)        # Giá niêm yết (VND)
    is_in_stock = Column(Boolean, default=True, nullable=False)  # Còn hàng hay ngừng kinh doanh
    stock_status_text = Column(String(100), nullable=True)    # Nhãn trạng thái gốc: "Còn hàng", "Tạm hết"...
    raw_specs = Column(JSON, nullable=True)                   # Bảng thông số kỹ thuật thô bóc tách
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    job = relationship("CrawlJob", back_populates="crawl_results")
    mappings = relationship("SkuMapping", back_populates="crawl_result", cascade="all, delete-orphan")

