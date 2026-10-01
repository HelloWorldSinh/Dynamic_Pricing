"""Package matching - Hệ thống lõi so khớp SKU chuẩn hóa theo Clean Architecture."""

from app.services.matching.models import MatchResult, SkuFeatures
from app.services.matching.feature_extractor import FeatureExtractor
from app.services.matching.sku_index import SkuIndex
from app.services.matching.matching_engine import MatchingEngine

__all__ = [
    "MatchResult",
    "SkuFeatures",
    "FeatureExtractor",
    "SkuIndex",
    "MatchingEngine",
]
