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


def test_feature_extractor_tecno_tcl_and_color():
    """Kiểm tra nhận diện thương hiệu, Model ID và màu sắc cho Tecno, TCL."""
    assert FeatureExtractor.detect_brand("TCL 408 4GB 128GB") == "tcl"
    assert FeatureExtractor.detect_brand("Tecno Spark 50 4GB 128GB") == "tecno"

    assert FeatureExtractor.extract_color("iPhone 15 128GB Đen") == "black"
    assert FeatureExtractor.extract_color("iPhone 15 128GB Titan tự nhiên") == "titanium"
    assert FeatureExtractor.extract_color("Samsung S24 Ultra Tím 256GB") == "purple"
    assert FeatureExtractor.extract_color("Laptop Acer Nitro 5 16GB 512GB") is None

    assert FeatureExtractor.extract_model_identifier("Tecno Spark 50 4GB 128GB") == "tecno_spark_50"
    assert FeatureExtractor.extract_model_identifier("TECNO SPARK 30 5G 6GB 128GB") == "tecno_spark_30"
    assert FeatureExtractor.extract_model_identifier("TECNO SPARK 30C 4GB 128GB") == "tecno_spark_30c"
    assert FeatureExtractor.extract_model_identifier("TCL 408 4GB 128GB") == "tcl_408"


def test_matching_engine_tecno_spark_isolation():
    """Kiểm tra ngăn chặn triệt để hiện tượng Spark 10/20/30 và TCL nhận vơ Spark 50."""
    tecno_50 = SkuFeatures(
        sku_id="SKU_TECNO_50",
        sku_name="Tecno Spark 50 4GB 128GB",
        clean_name="tecno spark 50 4gb 128gb",
        brand="tecno",
        parts=[],
        model_id="tecno_spark_50",
        ram=["4gb"],
        rom=["128gb"],
    )
    index = SkuIndex([tecno_50])
    engine = MatchingEngine(index)

    # 1. Spark 30, Spark 40, TCL phải bị UNMATCHED
    assert engine.match_single_item("TECNO SPARK 30 5G 6GB 128GB").status == MatchStatus.UNMATCHED
    assert engine.match_single_item("TECNO Spark 40 6GB 128GB").status == MatchStatus.UNMATCHED
    assert engine.match_single_item("TECNO SPARK 10 8GB 128GB").status == MatchStatus.UNMATCHED
    assert engine.match_single_item("TCL 408 4GB 128GB").status == MatchStatus.UNMATCHED

    # 2. Đúng Spark 50 cùng cấu hình phải được APPROVED
    res_exact = engine.match_single_item("TECNO Spark 50 4GB 128GB")
    assert res_exact.status == MatchStatus.APPROVED
    assert res_exact.fpt_sku_id == "SKU_TECNO_50"


def test_matching_engine_color_rules():
    """Kiểm tra quy tắc so khớp màu sắc: khác màu -> UNMATCHED, cùng màu hoặc khuyết màu -> APPROVED."""
    iphone_black = SkuFeatures(
        sku_id="SKU_IPHONE_BLACK",
        sku_name="iPhone 15 128GB Đen",
        clean_name="iphone 15 128gb đen",
        brand="apple",
        parts=[],
        model_id="iphone_15_",
        ram=[],
        rom=["128gb"],
        color="black",
    )
    index = SkuIndex([iphone_black])
    engine = MatchingEngine(index)

    # Cùng màu đen -> APPROVED
    res_same = engine.match_single_item("iPhone 15 128GB Đen Chính Hãng")
    assert res_same.status == MatchStatus.APPROVED
    assert res_same.fpt_sku_id == "SKU_IPHONE_BLACK"

    # Khác màu (trắng) -> UNMATCHED
    res_diff = engine.match_single_item("iPhone 15 128GB Trắng Chính Hãng")
    assert res_diff.status == MatchStatus.UNMATCHED

    # Khuyết màu bên đối thủ -> Vẫn cho APPROVED nếu cùng model và ROM
    res_no_color = engine.match_single_item("iPhone 15 128GB Chính Hãng")
    assert res_no_color.status == MatchStatus.APPROVED
    assert res_no_color.fpt_sku_id == "SKU_IPHONE_BLACK"


def test_different_brand_must_not_match():
    """Kiểm tra sản phẩm khác thương hiệu (VD: TCL vs Tecno) tuyệt đối không được ghép cặp."""
    # 1. Kiểm tra nhận diện brand mở rộng
    assert FeatureExtractor.detect_brand("TCL 40 SE (4GB/128GB)") == "tcl"
    assert FeatureExtractor.detect_brand("Infinix Note 40 Pro") == "infinix"
    assert FeatureExtractor.detect_brand("Itel A70 128GB") == "itel"

    skus = [
        SkuFeatures(
            sku_id="SKU_TECNO_SPARK_50",
            sku_name="Tecno Spark 50 4GB 128GB",
            clean_name="tecno spark 50 4gb 128gb",
            brand="tecno",
            parts=[],
            model_id=None,
            ram=["4gb"],
            rom=["128gb"],
        )
    ]
    index = SkuIndex(skus)
    engine = MatchingEngine(index)

    # 2. Khác thương hiệu rõ ràng (TCL vs Tecno)
    res1 = engine.match_single_item(
        scraped_name="TCL 40 SE (4GB/128GB)",
        competitor_price=2490000,
        fpt_prices={"SKU_TECNO_SPARK_50": 2690000}
    )
    assert res1.status == MatchStatus.UNMATCHED
    assert res1.fpt_sku_id == "N/A"
    assert res1.confidence_score < 0.75

    # 3. Thương hiệu đối thủ không có trong từ điển nhưng FPT có brand rõ ràng
    res2 = engine.match_single_item(
        scraped_name="BrandX Phone 40 SE (4GB/128GB)",
        competitor_price=2490000,
        fpt_prices={"SKU_TECNO_SPARK_50": 2690000}
    )
    assert res2.status == MatchStatus.UNMATCHED
    assert res2.fpt_sku_id == "N/A"
    assert res2.confidence_score < 0.75


def test_matching_engine_exact_normalized_string_approved():
    """Kiểm tra: Tiêu chí so sánh chuỗi chuẩn hóa đúng 100% được tự động APPROVED."""
    skus = [
        SkuFeatures(
            sku_id="SKU_HONOR_V5",
            sku_name="Honor Magic V5 5G 16GB 512GB",
            clean_name="honor magic v5 16gb 512gb",
            brand="honor",
            parts=[],
            model_id=None,
            ram=["16gb"],
            rom=["512gb"],
        ),
        SkuFeatures(
            sku_id="SKU_MASSTEL_IZI",
            sku_name="Masstel Izi 15 4G",
            clean_name="masstel izi 15",
            brand="masstel",
            parts=[],
            model_id=None,
            ram=[],
            rom=[],
        ),
    ]
    index = SkuIndex(skus)
    engine = MatchingEngine(index)

    # 1. Khớp chuỗi 100% dù model_id là None -> Vẫn phải APPROVED
    res_honor = engine.match_single_item(
        scraped_name="HONOR Magic V5 16GB 512GB",
        competitor_price=32990000,
        fpt_prices={"SKU_HONOR_V5": 34990000}
    )
    assert res_honor.status == MatchStatus.APPROVED
    assert res_honor.fpt_sku_id == "SKU_HONOR_V5"
    assert res_honor.confidence_score >= 0.85
    assert res_honor.match_type == MatchType.NORMALIZED_ATTRIBUTE

    # 2. Khớp chuỗi 100% sau khi loại bỏ tiền tố/hậu tố marketing -> APPROVED
    res_masstel = engine.match_single_item(
        scraped_name="Điện thoại Masstel Izi 15 4G Chính Hãng",
        competitor_price=450000,
        fpt_prices={"SKU_MASSTEL_IZI": 490000}
    )
    assert res_masstel.status == MatchStatus.APPROVED
    assert res_masstel.fpt_sku_id == "SKU_MASSTEL_IZI"
    assert res_masstel.confidence_score >= 0.85


