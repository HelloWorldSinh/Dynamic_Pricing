import os
import pytest
import pandas as pd
from app.services.sku_matcher import SkuMatcher
from app.services.scrapers.hoangha import HoanghaScraper


@pytest.fixture
def mock_matcher():
    """Tạo một SkuMatcher với danh mục FPT giả lập trong RAM để kiểm thử nhanh chóng."""
    matcher = SkuMatcher(dim_product_path="non_existent.xlsx", demand_events_path="non_existent.xlsx")

    # Thiết lập danh mục mẫu
    mock_data = [
        {"sku_id": "SKU_ACER_NITRO", "sku_name": "Laptop Acer Gaming Nitro 5 AN515-58-52SP i5 12500H/16GB/512GB/RTX 3050"},
        {"sku_id": "SKU_ASUS_TUF", "sku_name": "Laptop Asus TUF Gaming FA506NCG-HN329W R5 7535HS/16GB/512GB/RTX 3050"},
        {"sku_id": "SKU_LENOVO_LOQ", "sku_name": "Laptop Lenovo LOQ 15IAX9 83GS001RVN i5 12450HX/16GB/512GB/RTX 3050"},
        {"sku_id": "SKU_IPHONE_14_128", "sku_name": "iPhone 14 128GB"},
        {"sku_id": "SKU_IPHONE_16_128", "sku_name": "iPhone 16 128GB"},
        {"sku_id": "SKU_IPHONE_16_256", "sku_name": "iPhone 16 256GB"},
        {"sku_id": "SKU_SAMSUNG_S24_256", "sku_name": "Samsung Galaxy S24 Ultra 12GB 256GB"},
    ]
    matcher.df_dim = pd.DataFrame(mock_data)
    matcher._precompute_fpt_skus()
    matcher.fpt_prices = {
        "SKU_ACER_NITRO": 21000000,
        "SKU_IPHONE_16_128": 22000000,
        "SKU_SAMSUNG_S24_256": 29000000,
    }
    return matcher


def test_extract_part_numbers():
    """Kiểm tra bóc tách Part-Number các dòng máy phổ biến."""
    # Acer
    parts_acer = SkuMatcher.extract_part_numbers("Laptop Acer Nitro 5 AN515-58-52SP chính hãng")
    assert "AN515-58-52SP" in parts_acer

    # Asus
    parts_asus = SkuMatcher.extract_part_numbers("Laptop Asus Gaming FA506NCG-HN329W")
    assert "FA506NCG-HN329W" in parts_asus

    # Lenovo 8x/83 Series
    parts_lenovo = SkuMatcher.extract_part_numbers("Laptop Lenovo LOQ 15IAX9 83GS001RVN")
    assert "83GS001RVN" in parts_lenovo


def test_exact_part_number_matching(mock_matcher):
    """Kiểm tra Tầng 1: Khớp chính xác 100% bằng Part-Number."""
    scraped = "Laptop Acer Gaming Nitro 5 AN515-58-52SP (i5-12500H/16GB/512GB SSD) giá sốc"
    res = mock_matcher.match_single_item(scraped, competitor_price=19990000)

    assert res["status"] == "APPROVED"
    assert res["match_type"] == "EXACT_PART_NUMBER"
    assert res["confidence_score"] == 1.0
    assert res["fpt_sku_id"] == "SKU_ACER_NITRO"
    assert res["price_diff_vnd"] == 21000000 - 19990000


def test_hard_model_constraint_rejects_wrong_generation(mock_matcher):
    """Kiểm tra Ràng buộc Model: iPhone 18 tuyệt đối KHÔNG ĐƯỢC khớp với iPhone 14/16."""
    scraped = "iPhone 18 Pro Max 128GB Chính hãng"
    res = mock_matcher.match_single_item(scraped, competitor_price=35000000)

    assert res["status"] == "UNMATCHED"
    assert res["fpt_sku_id"] == "N/A"


def test_rom_mismatch_rejection_for_phones(mock_matcher):
    """Kiểm tra Ràng buộc ROM: iPhone 16 128GB không được khớp với bản 256GB."""
    scraped = "Điện thoại Apple iPhone 16 256GB - Chính hãng VN/A"
    res = mock_matcher.match_single_item(scraped, competitor_price=24500000)

    assert res["fpt_sku_id"] == "SKU_IPHONE_16_256"
    assert res["status"] == "APPROVED"

    # Trường hợp đối thủ bán bản 512GB FPT không có
    scraped_512 = "Điện thoại Apple iPhone 16 512GB - Chính hãng VN/A"
    res_512 = mock_matcher.match_single_item(scraped_512, competitor_price=30000000)
    assert res_512["status"] == "UNMATCHED"


def test_hoangha_clean_price():
    """Kiểm tra bóc tách và làm sạch giá Hoàng Hà."""
    scraper = HoanghaScraper()

    # Giá có phần trăm khuyến mãi
    assert scraper._clean_price("- 17% 46,990,000 ₫") == 46990000
    assert scraper._clean_price("24.990.000 ₫ -15%") == 24990000
    assert scraper._clean_price(None) is None
    assert scraper._clean_price("") is None


def test_hoangha_extract_storage_from_name():
    """Kiểm tra trích xuất RAM/ROM từ tên sản phẩm Hoàng Hà."""
    assert HoanghaScraper._extract_storage_from_name("iPhone 16 Pro 256GB") == "256 GB"
    assert HoanghaScraper._extract_storage_from_name("Samsung Galaxy Z Fold6 12GB/512GB") == "12 GB / 512 GB"


def test_match_multi_sources_logic(mock_matcher, tmp_path):
    """Kiểm tra so khớp đa nguồn (CellphoneS + Hoàng Hà) và phân tích định giá trên 3 sheets."""
    cps_items = [
        {
            "Nguồn": "CellphoneS",
            "Tên sản phẩm": "Laptop Acer Gaming Nitro 5 AN515-58-52SP i5 12500H Chính hãng",
            "Giá bán (VND)": 19500000,
            "Giá niêm yết (VND)": 23000000,
            "Còn hàng": "Còn hàng",
            "Thông số kỹ thuật tóm tắt": "i5 12500H | 16GB | 512GB",
            "URL sản phẩm": "https://cellphones.com.vn/acer-nitro-5.html",
            "Thời gian cào": "2026-10-01 12:00:00"
        }
    ]
    hh_items = [
        {
            "Nguồn": "HOANGHA",
            "Tên sản phẩm": "Laptop Acer Gaming Nitro 5 AN515-58-52SP",
            "Giá bán (VND)": 19990000,
            "Giá niêm yết (VND)": 22000000,
            "Còn hàng": "Còn hàng",
            "Thông số kỹ thuật tóm tắt": "i5 12500H | 16GB | 512GB",
            "URL sản phẩm": "https://hoanghamobile.com/acer-nitro-5",
            "Thời gian cào": "2026-10-01 12:00:00"
        }
    ]

    out_file = str(tmp_path / "multi_test.xlsx")
    actual_file = mock_matcher.match_multi_sources(cps_items, hh_items, output_excel_path=out_file)

    assert os.path.exists(actual_file)
    import openpyxl
    wb = openpyxl.load_workbook(actual_file)
    assert wb.sheetnames == ["FPT_Shop_Comparison", "CellphoneS_Data", "HoangHa_Data"]

    df_comp = pd.read_excel(actual_file, sheet_name="FPT_Shop_Comparison")
    df_cps = pd.read_excel(actual_file, sheet_name="CellphoneS_Data")
    df_hh = pd.read_excel(actual_file, sheet_name="HoangHa_Data")

    assert len(df_cps) == 1
    assert len(df_hh) == 1
    assert len(df_comp) == len(mock_matcher.parsed_dim_skus)

    # Kiểm tra dòng SKU_ACER_NITRO
    row_nitro = df_comp[df_comp["Mã SKU FPT"] == "SKU_ACER_NITRO"].iloc[0]
    assert row_nitro["Trạng thái CPS"] == "APPROVED"
    assert row_nitro["Giá CellphoneS (VND)"] == 19500000
    assert row_nitro["Trạng thái HH"] == "APPROVED"
    assert row_nitro["Giá Hoàng Hà (VND)"] == 19990000

    # Xác nhận các cột không cần thiết đã được loại bỏ
    for col in ["STT", "Ngành hàng", "Giá đối thủ thấp nhất (VND)", "Đối thủ rẻ nhất", "Chênh lệch giá (FPT - Min ĐT)", "Tỷ lệ chênh lệch (%)", "Khuyến nghị định giá"]:
        assert col not in df_comp.columns, f"Cột {col} vẫn còn trong FPT_Shop_Comparison!"
