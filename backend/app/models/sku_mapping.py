import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID


class SkuMapping(Base):
    """Bảng lưu kết quả đối soát & khớp SKU giữa FPT Shop và đối thủ."""
    __tablename__ = "sku_mappings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    fpt_product_id = Column(GUID(), ForeignKey("products.id"), nullable=False, index=True)
    competitor_crawl_id = Column(GUID(), ForeignKey("crawl_results.id"), nullable=False, index=True)

    # EXACT_PART_NUMBER | NORMALIZED_ATTRIBUTE | MANUAL
    match_type = Column(String(50), nullable=False)

    # Confidence Score: 1.0 (Exact 100%), 0.8 - 0.95 (Normalized), 0.6 - 0.79 (Manual queue)
    confidence_score = Column(Float, nullable=False, default=1.0)

    # PENDING | APPROVED | REJECTED
    status = Column(String(50), default="APPROVED", nullable=False, index=True)
    matched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_by = Column(String(100), nullable=True)                    # Chuyên viên duyệt (nếu là manual review PBI-008)
    reviewed_at = Column(DateTime, nullable=True)                       # Thời điểm duyệt thủ công

    # Relationships
    product = relationship("Product", back_populates="mappings")
    crawl_result = relationship("CrawlResult", back_populates="mappings")
