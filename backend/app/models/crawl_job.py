import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import GUID
from app.utils.datetime_utils import get_vietnam_now


class CrawlJob(Base):
    """Bảng quản lý các đợt cào dữ liệu đối thủ (PBI-004 & PBI-005)."""
    __tablename__ = "crawl_jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    trigger_type = Column(String(30), nullable=False, default="SCHEDULED")  # SCHEDULED | ON_DEMAND
    source = Column(String(50), nullable=False, default="ALL")              # CELLPHONES | HOANGHA | FPTSHOP | ALL
    category = Column(String(50), nullable=False, default="ALL")            # PHONE | LAPTOP | ALL
    status = Column(String(30), nullable=False, default="PENDING", index=True)  # PENDING | RUNNING | COMPLETED | FAILED
    total_items = Column(Integer, default=0, nullable=False)
    success_items = Column(Integer, default=0, nullable=False)
    error_items = Column(Integer, default=0, nullable=False)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, default=get_vietnam_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    # Relationships
    crawl_results = relationship("CrawlResult", back_populates="job", cascade="all, delete-orphan")
