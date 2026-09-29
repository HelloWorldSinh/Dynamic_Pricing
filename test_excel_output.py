import os
import sys
import pandas as pd
import openpyxl

def test_excel_deliverable():
    file_path = "data/crawl_and_sku_mapping_output.xlsx"
    assert os.path.exists(file_path), f"File {file_path} không tồn tại!"
    assert os.path.getsize(file_path) > 10000, "File quá nhỏ hoặc bị rỗng!"

    wb = openpyxl.load_workbook(file_path)
    assert "Scraped_All_Data" in wb.sheetnames, "Thiếu Sheet 'Scraped_All_Data'!"
    assert "SKU_Mapping" in wb.sheetnames, "Thiếu Sheet 'SKU_Mapping'!"

    df_all = pd.read_excel(file_path, sheet_name="Scraped_All_Data")
    df_map = pd.read_excel(file_path, sheet_name="SKU_Mapping")

    assert len(df_all) >= 60, f"Sheet 1 có ít hơn 60 dòng ({len(df_all)})!"
    assert len(df_map) == len(df_all), "Số dòng 2 sheet không đồng nhất!"

    matched = df_map[df_map["Trạng thái (Status)"].isin(["APPROVED", "PENDING"])]
    print(f"[TEST PASS] Đã xác thực thành công file {file_path}")
    print(f" - Sheet 1 (Scraped_All_Data): {len(df_all)} dòng, {len(df_all.columns)} cột.")
    print(f" - Sheet 2 (SKU_Mapping): {len(df_map)} dòng, {len(df_map.columns)} cột.")
    print(f" - Số lượng sản phẩm ghép cặp thành công: {len(matched)} / {len(df_map)} ({len(matched)/len(df_map)*100:.1f}%)")

if __name__ == "__main__":
    test_excel_deliverable()
