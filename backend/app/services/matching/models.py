"""Định nghĩa cấu trúc dữ liệu và mô hình cho hệ thống SKU Matching."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Dict


class MatchStatus:
    """Các trạng thái phê duyệt sau so khớp."""
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    UNMATCHED = "UNMATCHED"
    NOT_FOUND = "NOT_FOUND"


class MatchType:
    """Loại thuật toán so khớp được kích hoạt."""
    EXACT_PART_NUMBER = "EXACT_PART_NUMBER"
    NORMALIZED_ATTRIBUTE = "NORMALIZED_ATTRIBUTE"
    UNMATCHED = "UNMATCHED"
    NOT_FOUND = "NOT_FOUND"


@dataclass
class SkuFeatures:
    """Các đặc trưng đã bóc tách của một SKU chuẩn hoặc sản phẩm cào về."""
    sku_id: str
    sku_name: str
    clean_name: str
    brand: Optional[str] = None
    parts: List[str] = field(default_factory=list)
    model_id: Optional[str] = None
    ram: List[str] = field(default_factory=list)
    rom: List[str] = field(default_factory=list)
    color: Optional[str] = None

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchResult:
    """Kết quả chi tiết của một lượt so khớp sản phẩm."""
    fpt_sku_id: str
    fpt_sku_name: str
    match_type: str
    confidence_score: float
    status: str
    fpt_price: Optional[int] = None
    competitor_price: Optional[int] = None
    price_diff_vnd: Optional[int] = None
    price_diff_pct: Optional[float] = None

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def keys(self):
        return self.to_dict().keys()

    def items(self):
        return self.to_dict().items()

    def values(self):
        return self.to_dict().values()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
