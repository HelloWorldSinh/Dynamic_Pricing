"""Module quản lý chỉ mục tra cứu nhanh (Inverted Index) cho danh mục sản phẩm chuẩn."""

from typing import List, Dict, Optional, Iterable
from app.services.matching.models import SkuFeatures


class SkuIndex:
    """Lập chỉ mục bộ nhớ trong (In-Memory Inverted Index) cho danh mục SKU FPT Shop.
    Tối ưu hóa các thao tác tra cứu:
    - Tra cứu Part-Number: O(1) qua Hash Map
    - Phân nhóm theo thương hiệu (Brand Bucketing) để thu hẹp không gian tìm kiếm
    """

    def __init__(self, skus: Optional[List[SkuFeatures]] = None):
        self.all_skus: List[SkuFeatures] = []
        self.sku_by_id: Dict[str, SkuFeatures] = {}
        self.part_to_sku: Dict[str, SkuFeatures] = {}
        self.brand_buckets: Dict[str, List[SkuFeatures]] = {}

        if skus:
            self.build_index(skus)

    def build_index(self, skus: List[SkuFeatures]) -> None:
        """Xây dựng lại toàn bộ các bảng chỉ mục từ danh sách SkuFeatures."""
        self.all_skus = list(skus)
        self.sku_by_id = {s.sku_id: s for s in skus}
        self.part_to_sku = {}
        self.brand_buckets = {}

        for s in skus:
            # 1. Inverted Index cho Part-Number
            for part in s.parts:
                p_norm = part.upper()
                if p_norm not in self.part_to_sku:
                    self.part_to_sku[p_norm] = s

            # 2. Phân nhóm Brand
            brand_key = s.brand or "unknown"
            self.brand_buckets.setdefault(brand_key, []).append(s)

    def lookup_by_part(self, part_number: str) -> Optional[SkuFeatures]:
        """Tra cứu nhanh SKU theo Part-Number đơn lẻ trong O(1)."""
        if not part_number:
            return None
        return self.part_to_sku.get(part_number.upper())

    def lookup_any_part(self, parts: Iterable[str]) -> Optional[SkuFeatures]:
        """Tra cứu nhanh SKU qua danh sách part-number cào được (O(K), K là số part của đối thủ)."""
        for p in parts:
            match = self.lookup_by_part(p)
            if match:
                return match
        return None

    def lookup_part_in_name(self, parts: Iterable[str]) -> Optional[SkuFeatures]:
        """Phương án dự phòng: Kiểm tra xem part number của đối thủ có nằm trong chuỗi tên chuẩn FPT hay không."""
        for s in self.all_skus:
            sku_name_upper = s.sku_name.upper()
            if any(p.upper() in sku_name_upper for p in parts):
                return s
        return None

    def get_candidates(self, brand: Optional[str]) -> List[SkuFeatures]:
        """Lấy danh sách ứng viên đã lọc theo thương hiệu.
        Nếu có thương hiệu xác định, chỉ duyệt danh sách của thương hiệu đó.
        Nếu không có, fallback duyệt toàn bộ danh mục.
        """
        if brand and brand in self.brand_buckets:
            return self.brand_buckets[brand]
        return self.all_skus

    def get_by_id(self, sku_id: str) -> Optional[SkuFeatures]:
        """Lấy thông tin SKU theo mã ID."""
        return self.sku_by_id.get(sku_id)

    def __len__(self) -> int:
        return len(self.all_skus)

    def __iter__(self):
        return iter(self.all_skus)
