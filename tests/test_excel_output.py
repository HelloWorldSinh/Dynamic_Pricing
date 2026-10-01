import os
import sys
import pandas as pd
import openpyxl
from app.utils.excel_exporter import ExcelExporter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_excel_deliverable():
    file_path = os.path.join(BASE_DIR, "data", "crawl_and_sku_mapping_output.xlsx")
    if not os.path.exists(file_path):
        return  # Bỏ qua nếu chưa chạy pipeline tạo file

    assert os.path.getsize(file_path) > 10000, "File quá nhỏ hoặc bị rỗng!"

    wb = openpyxl.load_workbook(file_path)

    # Hỗ trợ cả 3 sheets (pipeline mới) hoặc 2 sheets (legacy)
    if "FPT_Shop_Comparison" in wb.sheetnames:
        assert "CellphoneS_Data" in wb.sheetnames, "Thiếu Sheet 'CellphoneS_Data'!"
        assert "HoangHa_Data" in wb.sheetnames, "Thiếu Sheet 'HoangHa_Data'!"
        df_comp = pd.read_excel(file_path, sheet_name="FPT_Shop_Comparison")
        df_cps = pd.read_excel(file_path, sheet_name="CellphoneS_Data")
        df_hh = pd.read_excel(file_path, sheet_name="HoangHa_Data")

        assert len(df_comp) == 329, f"Bảng FPT_Shop_Comparison phải có đúng 329 SKU FPT (hiện có {len(df_comp)})!"
        assert len(df_cps) > 0, "Sheet CellphoneS_Data bị rỗng!"
        assert len(df_hh) > 0, "Sheet HoangHa_Data bị rỗng!"
    else:
        assert "Scraped_All_Data" in wb.sheetnames, "Thiếu Sheet 'Scraped_All_Data'!"
        assert "SKU_Mapping" in wb.sheetnames, "Thiếu Sheet 'SKU_Mapping'!"


def test_multi_source_excel_export_structure(tmp_path):
    """Kiểm tra cấu trúc và định dạng styling của file Excel 3 sheets."""
    df_comparison = pd.DataFrame([
        {
            "Mã SKU FPT": "SKU_001",
            "Tên sản phẩm chuẩn (FPT Shop)": "Laptop Test FPT 16GB",
            "Giá tham chiếu FPT (VND)": 20000000,
            "Tên SP CellphoneS": "Laptop Test CPS",
            "Giá CellphoneS (VND)": 19000000,
            "Kho CellphoneS": "Còn hàng",
            "Độ tin cậy CPS": 1.0,
            "Trạng thái CPS": "APPROVED",
            "URL CellphoneS": "https://cellphones.com.vn/test",
            "Tên SP Hoàng Hà": "Laptop Test HH",
            "Giá Hoàng Hà (VND)": 19500000,
            "Kho Hoàng Hà": "Còn hàng",
            "Độ tin cậy HH": 0.85,
            "Trạng thái HH": "APPROVED",
            "URL Hoàng Hà": "https://hoanghamobile.com/test",
        }
    ])
    df_cellphones = pd.DataFrame([
        {
            "STT": 1,
            "Nguồn": "CellphoneS",
            "Tên sản phẩm cào được": "Laptop Test CPS",
            "Giá bán đối thủ (VND)": 19000000,
            "Giá niêm yết (VND)": 22000000,
            "Tình trạng kho": "Còn hàng",
            "Thông số kỹ thuật tóm tắt": "16GB RAM",
            "URL sản phẩm": "https://cellphones.com.vn/test",
            "Thời gian cào": "2026-10-01 12:00:00"
        }
    ])
    df_hoangha = pd.DataFrame([
        {
            "STT": 1,
            "Nguồn": "HOANGHA",
            "Tên sản phẩm cào được": "Laptop Test HH",
            "Giá bán đối thủ (VND)": 19500000,
            "Giá niêm yết (VND)": 21000000,
            "Tình trạng kho": "Còn hàng",
            "Thông số kỹ thuật tóm tắt": "16GB RAM",
            "URL sản phẩm": "https://hoanghamobile.com/test",
            "Thời gian cào": "2026-10-01 12:00:00"
        }
    ])

    test_out = str(tmp_path / "test_3sheets.xlsx")
    res_path = ExcelExporter.export_multi_source_report(
        df_comparison=df_comparison,
        df_cellphones=df_cellphones,
        df_hoangha=df_hoangha,
        output_excel_path=test_out
    )

    assert os.path.exists(res_path)
    wb = openpyxl.load_workbook(res_path)
    assert wb.sheetnames == ["FPT_Shop_Comparison", "CellphoneS_Data", "HoangHa_Data"]

    # Verify styling
    ws = wb["FPT_Shop_Comparison"]
    # Check header fill (Navy Blue: 1F4E79)
    color_val = str(ws.cell(row=1, column=1).fill.start_color.value or "")
    assert "1F4E79" in color_val.upper()

