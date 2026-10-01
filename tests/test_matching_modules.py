"""Kiểm thử chuyên sâu cho các module con trong package app.services.matching:
- FeatureExtractor (Brand, Model, RAM, ROM, Part-Number Blacklist)
- SkuIndex (Tra cứu O(1), Brand Bucketing)
- MatchingEngine & Models
"""

import pytest
from app.services.matching.models import SkuFeatures, MatchStatus, MatchType
from app.services.matching.feature_extractor import FeatureExtractor
from app.services.matching.sku_index import SkuIndex
from app.services.matching.matching_engine import MatchingEngine


def test_feature_extractor_part_number_and_blacklist():
    """Kiểm tra trích xuất Part-Number và bộ lọc Blacklist loại trừ CPU/GPU/Screen-size."""
    text = (
        "Laptop Acer Gaming Nitro 5 AN515-58-52SP i5-12500H 16GB 512GB RTX-3050 15-6-inch Win-11"
    )
    parts = FeatureExtractor.extract_part_numbers(text)

    # AN515-58-52SP là part number chuẩn -> Phải có
    assert "AN515-58-52SP" in parts

    # CPU/GPU/Screen/Win là linh kiện thông số -> Bắt buộc bị Blacklist lọc bỏ
    assert "I5-12500H" not in parts
    assert "RTX-3050" not in parts
    assert "15-6-INCH" not in parts
    assert "WIN-11" not in parts


def test_feature_extractor_ram_and_storage():
    """Kiểm tra bóc tách RAM và ROM chính xác."""
    text = "Laptop Lenovo Legion 5 16GB RAM SSD 1TB + 512GB"
    clean = FeatureExtractor.clean_product_name(text)

    ram = FeatureExtractor.extract_ram(clean)
    storage = FeatureExtractor.extract_storage(clean)

    assert "16gb" in ram
    assert "1tb" in storage
    assert "512gb" in storage


def test_feature_extractor_brand_and_model():
    """Kiểm tra nhận diện thương hiệu và Model Identifier."""
    assert FeatureExtractor.detect_brand("iPhone 16 Pro Max 256GB") == "apple"
    assert FeatureExtractor.detect_brand("Samsung Galaxy S24 Ultra") == "samsung"
    assert FeatureExtractor.detect_brand("Redmi Note 13 Pro") == "xiaomi"

    assert FeatureExtractor.extract_model_identifier("iPhone 16 Pro Max 256GB") == "iphone_16_promax"
    assert FeatureExtractor.extract_model_identifier("Samsung Galaxy S24 Ultra") == "samsung_s24_ultra"


def test_sku_index_o1_lookup():
    """Kiểm tra SkuIndex tra cứu O(1) qua Part-Number và Brand Bucketing."""
    skus = [
        SkuFeatures(
            sku_id="SKU_ACER_1",
            sku_name="Laptop Acer Nitro 5 AN515-58-52SP",
            clean_name="laptop acer nitro 5 an515 58 52sp",
            brand="acer",
            parts=["AN515-58-52SP"],
            model_id="nitro",
            ram=["16gb"],
            rom=["512gb"],
        ),
        SkuFeatures(
            sku_id="SKU_IPHONE_16",
            sku_name="iPhone 16 128GB",
            clean_name="iphone 16 128gb",
            brand="apple",
            parts=[],
            model_id="iphone_16_",
            ram=[],
            rom=["128gb"],
        ),
    ]

    index = SkuIndex(skus)

    # 1. Tra cứu Part-Number O(1)
    found = index.lookup_by_part("an515-58-52sp")
    assert found is not None
    assert found.sku_id == "SKU_ACER_1"

    assert index.lookup_by_part("NON_EXISTENT") is None

    # 2. Tra cứu Any Part
    found_any = index.lookup_any_part(["DUMMY", "AN515-58-52SP"])
    assert found_any is not None
    assert found_any.sku_id == "SKU_ACER_1"

    # 3. Brand Bucketing
    apple_skus = index.get_candidates("apple")
    assert len(apple_skus) == 1
    assert apple_skus[0].sku_id == "SKU_IPHONE_16"

    acer_skus = index.get_candidates("acer")
    assert len(acer_skus) == 1
    assert acer_skus[0].sku_id == "SKU_ACER_1"


def test_matching_engine_standalone():
    """Kiểm tra MatchingEngine hoạt động độc lập hoàn toàn không cần đọc file."""
    skus = [
        SkuFeatures(
            sku_id="SKU_DELL_1",
            sku_name="Laptop Dell Inspiron 3520 i5 8GB 512GB",
            clean_name="laptop dell inspiron 3520 i5 8gb 512gb",
            brand="dell",
            parts=["INSPIRON-3520"],
            model_id="inspiron",
            ram=["8gb"],
            rom=["512gb"],
        )
    ]
    index = SkuIndex(skus)
    engine = MatchingEngine(index)

    # Exact part match
    res = engine.match_single_item(
        scraped_name="Dell Inspiron 3520 (INSPIRON-3520)",
        competitor_price=14000000,
        fpt_prices={"SKU_DELL_1": 15000000}
    )

    assert res.status == MatchStatus.APPROVED
    assert res.match_type == MatchType.EXACT_PART_NUMBER
    assert res.fpt_sku_id == "SKU_DELL_1"
    assert res.price_diff_vnd == 1000000

    # Kiểm tra dict-like compatibility
    assert res["status"] == "APPROVED"
    assert res["price_diff_vnd"] == 1000000
