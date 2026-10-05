from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SourceEnum(str, Enum):
    ALL = "all"
    FPTSHOP = "fptshop"
    CELLPHONES = "cellphones"
    HOANGHA = "hoangha"


class CategoryEnum(str, Enum):
    PHONE = "phone"
    LAPTOP = "laptop"


class CrawlTriggerRequest(BaseModel):
    source: SourceEnum = Field(default=SourceEnum.CELLPHONES, description="Nguồn cần cào: fptshop | cellphones | hoangha | all")
    category: CategoryEnum = Field(default=CategoryEnum.PHONE, description="Ngành hàng: phone | laptop")
    target_url: Optional[str] = Field(default=None, description="URL cụ thể cần cào test (tuỳ chọn)")
    limit: Optional[int] = Field(default=None, description="Số lượng tối đa cần cào (None = không giới hạn, cào hết các trang)")


class CrawlJobResponse(BaseModel):
    task_id: str
    status: str = Field(description="PENDING | PROCESSING | COMPLETED | FAILED")
    message: str
    started_at: datetime = Field(default_factory=datetime.utcnow)


class CrawlProgressResponse(BaseModel):
    task_id: str
    source: str
    category: str
    status: str = Field(description="PENDING | RUNNING | COMPLETED | FAILED")
    current_page: int = 0
    total_pages: Optional[int] = 1
    scraped_count: int = 0
    progress_percent: int = 0
    message: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ScrapedProductItem(BaseModel):
    source: str
    url: str
    product_name: str
    current_price: Optional[int] = None
    original_price: Optional[int] = None
    is_in_stock: bool = True
    specifications: Dict[str, Any] = Field(default_factory=dict)
