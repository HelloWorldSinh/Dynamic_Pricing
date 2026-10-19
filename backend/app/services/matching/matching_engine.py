"""Module động cơ so khớp SKU (Matching Engine)."""

from difflib import SequenceMatcher
from typing import Optional, Dict
from app.services.matching.models import MatchResult, MatchStatus, MatchType
from app.services.matching.feature_extractor import FeatureExtractor
from app.services.matching.sku_index import SkuIndex


class MatchingEngine:
    """Động cơ so khớp SKU 2 tầng theo chuẩn nghiệp vụ:
    - Tầng 1: Exact Match bằng Part-Number qua SkuIndex (Tốc độ O(1), độ tin cậy 1.0)
    - Tầng 2: Normalized Attribute Matching (Ràng buộc Brand, Model ID, RAM/ROM + Similarity Ratio)
    """

    CONFIDENCE_EXACT = 1.0
    CONFIDENCE_APPROVED_THRESHOLD = 0.85
    CONFIDENCE_MIN_THRESHOLD = 0.75
    CONFIDENCE_PENDING_CEILING = 0.84

    def __init__(self, sku_index: SkuIndex):
        self.sku_index = sku_index

    def match_single_item(
        self,
        scraped_name: str,
        competitor_price: Optional[int] = None,
        fpt_prices: Optional[Dict[str, int]] = None
    ) -> MatchResult:
        """Thực hiện ghép cặp 1 sản phẩm cào về với danh mục chuẩn FPT Shop."""
        if fpt_prices is None:
            fpt_prices = {}

        scraped_parts = FeatureExtractor.extract_part_numbers(scraped_name)
        scraped_parts_set = set(scraped_parts)

        best_sku_id: Optional[str] = None
        best_sku_name: Optional[str] = None
        best_confidence: float = 0.0
        match_type: str = MatchType.UNMATCHED

        # --- TẦNG 1: EXACT MATCH QUA PART-NUMBER (O(1)) ---
        if scraped_parts:
            # 1. Tra cứu trực tiếp trong Inverted Index O(1)
            matched_sku = self.sku_index.lookup_any_part(scraped_parts)
            if matched_sku:
                best_sku_id = matched_sku.sku_id
                best_sku_name = matched_sku.sku_name
                best_confidence = self.CONFIDENCE_EXACT
                match_type = MatchType.EXACT_PART_NUMBER
            else:
                # 2. Kiểm tra part number cào được có nằm trong tên chuẩn FPT không (fallback)
                matched_sku_fallback = self.sku_index.lookup_part_in_name(scraped_parts)
                if matched_sku_fallback:
                    best_sku_id = matched_sku_fallback.sku_id
                    best_sku_name = matched_sku_fallback.sku_name
                    best_confidence = self.CONFIDENCE_EXACT
                    match_type = MatchType.EXACT_PART_NUMBER

        # --- TẦNG 2: NORMALIZED ATTRIBUTE VỚI TIÊU CHÍ SO SÁNH CHUỖI 100% VÀ RÀNG BUỘC MODEL CỨNG ---
        if not best_sku_id:
            c_clean = FeatureExtractor.clean_product_name(scraped_name)
            scraped_brand = FeatureExtractor.detect_brand(scraped_name)
            scraped_model_id = FeatureExtractor.extract_model_identifier(scraped_name)
            scraped_color = FeatureExtractor.extract_color(scraped_name)

            # 2.1. Tiêu chí so sánh chuỗi đúng 100% (Exact Normalized String Match -> Tự động APPROVED)
            exact_clean_match = self.sku_index.lookup_exact_normalized(
                clean_name=c_clean,
                scraped_name=scraped_name,
                scraped_parts=scraped_parts,
                scraped_brand=scraped_brand,
            )
            if exact_clean_match:
                best_sku_id = exact_clean_match.sku_id
                best_sku_name = exact_clean_match.sku_name
                best_confidence = 0.95  # >= CONFIDENCE_APPROVED_THRESHOLD (0.85) -> APPROVED
                match_type = MatchType.NORMALIZED_ATTRIBUTE
            elif scraped_brand and scraped_model_id:
                # 2.2. So khớp thuộc tính mờ với ràng buộc Brand & Model ID
                s_ram = FeatureExtractor.extract_ram(c_clean)
                s_rom = FeatureExtractor.extract_storage(c_clean)
                s_ram_set = set(s_ram)
                s_rom_set = set(s_rom)
                is_series_generic = "series" in c_clean.lower()

                # Lấy danh sách ứng viên đã rút gọn theo Brand qua Brand Bucketing
                candidates = self.sku_index.get_candidates(scraped_brand)

                for item in candidates:
                    dim_sku_id = item.sku_id
                    dim_name = item.sku_name
                    dim_clean = item.clean_name
                    dim_brand = item.brand
                    dim_model_id = item.model_id
                    dim_color = item.color

                    # Ràng buộc 1: Bắt buộc cùng thương hiệu
                    if not dim_brand or scraped_brand != dim_brand:
                        continue

                    # Ràng buộc 2: Bắt buộc cùng Model Identifier
                    if not dim_model_id or scraped_model_id != dim_model_id:
                        continue

                    dim_ram = item.ram
                    dim_rom = item.rom

                    # Ràng buộc 3: Bắt buộc cùng ROM nếu cả 2 bên đều có thông số ROM
                    if s_rom and dim_rom and s_rom_set != set(dim_rom):
                        continue

                    # Ràng buộc 4: Bắt buộc cùng RAM nếu cả 2 bên đều có thông số RAM
                    if s_ram and dim_ram and s_ram_set != set(dim_ram):
                        continue

                    # Ràng buộc 5: Kiểm tra màu sắc (Nếu cả 2 bên đều có màu mà khác màu -> UNMATCHED)
                    if scraped_color and dim_color and scraped_color != dim_color:
                        continue

                    # Tính độ tương đồng chuỗi cơ sở
                    ratio = SequenceMatcher(None, c_clean, dim_clean).ratio()

                    # Tiêu chí chuỗi đúng 100% -> Đảm bảo mức điểm APPROVED
                    if ratio == 1.0:
                        score = 0.95
                    else:
                        bonus = 0.0
                        if s_ram and dim_ram and s_ram_set == set(dim_ram):
                            bonus += 0.1
                        if s_rom and dim_rom and s_rom_set == set(dim_rom):
                            bonus += 0.1
                        if scraped_model_id and scraped_model_id == dim_model_id:
                            bonus += 0.15
                        if scraped_color and dim_color and scraped_color == dim_color:
                            bonus += 0.05

                        score = min(0.95, ratio + bonus)

                    # Nếu cả 2 bên đều có Part-Number nhưng khác nhau -> Không được Approved
                    dim_parts_set = set(item.parts)
                    if scraped_parts_set and dim_parts_set and not scraped_parts_set.intersection(dim_parts_set):
                        score = min(self.CONFIDENCE_PENDING_CEILING, score)

                    if is_series_generic:
                        score = min(self.CONFIDENCE_PENDING_CEILING, score)

                    if score > best_confidence and score >= self.CONFIDENCE_MIN_THRESHOLD:
                        best_confidence = score
                        best_sku_id = dim_sku_id
                        best_sku_name = dim_name
                        match_type = MatchType.NORMALIZED_ATTRIBUTE

        # Phân loại trạng thái duyệt
        status = MatchStatus.UNMATCHED
        if best_sku_id:
            status = MatchStatus.APPROVED if best_confidence >= self.CONFIDENCE_APPROVED_THRESHOLD else MatchStatus.PENDING

        fpt_price = fpt_prices.get(best_sku_id, None) if best_sku_id else None

        price_diff_vnd = None
        price_diff_pct = None
        if fpt_price and competitor_price:
            price_diff_vnd = fpt_price - competitor_price
            price_diff_pct = (price_diff_vnd / fpt_price) * 100

        return MatchResult(
            fpt_sku_id=best_sku_id if best_sku_id else "N/A",
            fpt_sku_name=best_sku_name if best_sku_name else "Không tìm thấy SKU tương ứng",
            match_type=match_type,
            confidence_score=round(best_confidence, 3),
            status=status,
            fpt_price=fpt_price,
            competitor_price=competitor_price,
            price_diff_vnd=price_diff_vnd,
            price_diff_pct=round(price_diff_pct, 1) if price_diff_pct is not None else None
        )
