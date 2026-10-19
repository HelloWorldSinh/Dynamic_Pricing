"""Module quản lý chỉ mục tra cứu nhanh (Inverted Index) cho danh mục sản phẩm chuẩn."""

import re
from typing import List, Dict, Optional, Iterable
from app.services.matching.models import SkuFeatures


class SkuIndex:
    """Lập chỉ mục bộ nhớ trong (In-Memory Inverted Index) cho danh mục SKU FPT Shop.
    Tối ưu hóa các thao tác tra cứu:
    - Tra cứu Part-Number: O(1) qua Hash Map
    - Phân nhóm theo thương hiệu (Brand Bucketing) để thu hẹp không gian tìm kiếm
    - Chỉ mục chuỗi chuẩn hóa (Exact Normalized Match): O(1) qua Hash Map
    """

    def __init__(self, skus: Optional[List[SkuFeatures]] = None):
        self.all_skus: List[SkuFeatures] = []
        self.sku_by_id: Dict[str, SkuFeatures] = {}
        self.part_to_sku: Dict[str, SkuFeatures] = {}
        self.brand_buckets: Dict[str, List[SkuFeatures]] = {}
        self.clean_name_buckets: Dict[str, List[SkuFeatures]] = {}
        self.clean_tokens_buckets: Dict[str, List[SkuFeatures]] = {}

        if skus:
            self.build_index(skus)

    def build_index(self, skus: List[SkuFeatures]) -> None:
        """Xây dựng lại toàn bộ các bảng chỉ mục từ danh sách SkuFeatures."""
        self.all_skus = list(skus)
        self.sku_by_id = {s.sku_id: s for s in skus}
        self.part_to_sku = {}
        self.brand_buckets = {}
        self.clean_name_buckets = {}
        self.clean_tokens_buckets = {}

        for s in skus:
            # 1. Inverted Index cho Part-Number
            for part in s.parts:
                p_norm = part.upper()
                if p_norm not in self.part_to_sku:
                    self.part_to_sku[p_norm] = s

            # 2. Phân nhóm Brand
            brand_key = s.brand or "unknown"
            self.brand_buckets.setdefault(brand_key, []).append(s)

            # 3. Chỉ mục chuỗi chuẩn hóa (Exact & Token Set) cho Tầng 2
            if s.clean_name:
                self.clean_name_buckets.setdefault(s.clean_name, []).append(s)
                tok_key = " ".join(sorted(s.clean_name.split()))
                self.clean_tokens_buckets.setdefault(tok_key, []).append(s)

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

    def lookup_exact_normalized(
        self,
        clean_name: str,
        scraped_name: str = "",
        scraped_parts: Optional[Iterable[str]] = None,
        scraped_brand: Optional[str] = None
    ) -> Optional[SkuFeatures]:
        """Tra cứu nhanh SKU khi chuỗi chuẩn hóa khớp 100% (Exact Normalized String Match).
        Đảm bảo không xung đột Part-Number và phân định rõ biến thể 5G / 4G nếu có.
        """
        if not clean_name:
            return None

        # 1. Tra cứu theo chuỗi chuẩn hóa chính xác hoặc tập token chuẩn hóa
        candidates = self.clean_name_buckets.get(clean_name, [])
        if not candidates:
            tok_key = " ".join(sorted(clean_name.split()))
            candidates = self.clean_tokens_buckets.get(tok_key, [])

        if not candidates:
            return None

        scraped_parts_set = set(p.upper() for p in scraped_parts) if scraped_parts else set()
        is_scraped_5g = bool(re.search(r"\b5g\b", scraped_name, re.I)) if scraped_name else False

        filtered: List[SkuFeatures] = []
        for s in candidates:
            # Ràng buộc Part-number: Nếu cả 2 bên đều có mã part thì không được xung đột
            dim_parts_set = set(p.upper() for p in s.parts)
            if scraped_parts_set and dim_parts_set and not scraped_parts_set.intersection(dim_parts_set):
                continue

            # Ràng buộc Brand: Không được xung đột thương hiệu
            if scraped_brand and s.brand and scraped_brand != s.brand:
                continue

            filtered.append(s)

        if not filtered:
            return None

        if len(filtered) == 1:
            return filtered[0]

        # Nếu có nhiều hơn 1 ứng viên (ví dụ bản 4G và bản 5G trùng tên sau khi clean):
        # Ưu tiên khớp chính xác chỉ số 5G
        for s in filtered:
            is_dim_5g = bool(re.search(r"\b5g\b", s.sku_name, re.I))
            if is_scraped_5g == is_dim_5g:
                return s

        return filtered[0]

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
