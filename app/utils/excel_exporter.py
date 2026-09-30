import os
import logging
from datetime import datetime
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Tiện ích xuất dữ liệu ra file Excel với định dạng chuyên nghiệp theo chuẩn báo cáo."""

    @staticmethod
    def export_sku_mapping_report(
        df_sheet1: pd.DataFrame,
        df_sheet2: pd.DataFrame,
        output_excel_path: str = "data/crawl_and_sku_mapping_output.xlsx",
    ) -> str:
        """Xuất 2 sheet (Scraped_All_Data và SKU_Mapping) và áp dụng styling chuyên nghiệp.
        Tự động xử lý trường hợp file đích đang bị khóa (PermissionError).
        """
        os.makedirs(os.path.dirname(output_excel_path) or ".", exist_ok=True)
        actual_path = output_excel_path

        try:
            with pd.ExcelWriter(actual_path, engine="openpyxl") as writer:
                df_sheet1.to_excel(writer, sheet_name="Scraped_All_Data", index=False)
                df_sheet2.to_excel(writer, sheet_name="SKU_Mapping", index=False)
        except PermissionError:
            timestamp = datetime.now().strftime("%H%M%S")
            base, ext = os.path.splitext(output_excel_path)
            actual_path = f"{base}_{timestamp}{ext}"
            logger.warning(f"File {output_excel_path} đang mở trong ứng dụng khác. Lưu sang: {actual_path}")
            with pd.ExcelWriter(actual_path, engine="openpyxl") as writer:
                df_sheet1.to_excel(writer, sheet_name="Scraped_All_Data", index=False)
                df_sheet2.to_excel(writer, sheet_name="SKU_Mapping", index=False)

        ExcelExporter.apply_excel_styling(actual_path)
        logger.info(f"Đã xuất và định dạng thành công file Excel tại: {actual_path}")
        return actual_path

    @staticmethod
    def apply_excel_styling(file_path: str) -> None:
        """Định dạng phông chữ, màu sắc header/status, tiền tệ VND và độ rộng cột."""
        wb = openpyxl.load_workbook(file_path)

        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")  # Navy Blue
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")   # APPROVED
        yellow_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # PENDING
        red_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")     # UNMATCHED / NOT_FOUND

        thin_border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        )

        for sheetname in wb.sheetnames:
            ws = wb[sheetname]

            # 1. Format Header
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws.row_dimensions[1].height = 28

            # 2. Format Data Rows
            for row in range(2, ws.max_row + 1):
                ws.row_dimensions[row].height = 20
                for col in range(1, ws.max_column + 1):
                    cell = ws.cell(row=row, column=col)
                    cell.border = thin_border
                    cell.font = Font(name="Calibri", size=10)

                    # Căn lề STT
                    if col == 1:
                        cell.alignment = Alignment(horizontal="center", vertical="center")

                    # Format số tiền VND (nếu là số nguyên > 1000)
                    if isinstance(cell.value, (int, float)) and cell.value > 1000:
                        cell.number_format = '#,##0 "₫"'
                        cell.alignment = Alignment(horizontal="right", vertical="center")

            # 3. Tô màu trạng thái và định dạng % confidence cho Sheet SKU_Mapping
            if sheetname == "SKU_Mapping":
                for row in range(2, ws.max_row + 1):
                    # Tìm đúng cột theo header name để tránh hardcode index lệch khi schema đổi
                    for col in range(1, ws.max_column + 1):
                        col_name = str(ws.cell(row=1, column=col).value or "")
                        cell = ws.cell(row=row, column=col)

                        if "Confidence" in col_name or "Độ tin cậy" in col_name:
                            if isinstance(cell.value, (int, float)):
                                cell.number_format = "0.0%"
                                cell.alignment = Alignment(horizontal="center", vertical="center")

                        if "Status" in col_name or "Trạng thái" in col_name:
                            if cell.value == "APPROVED":
                                cell.fill = green_fill
                            elif cell.value == "PENDING":
                                cell.fill = yellow_fill
                            elif cell.value in ["UNMATCHED", "NOT_FOUND"]:
                                cell.fill = red_fill

            # 4. Auto-fit độ rộng cột
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    val_str = str(cell.value or "")
                    if cell.row == 1:
                        max_len = max(max_len, len(val_str) + 4)
                    else:
                        max_len = max(max_len, min(len(val_str), 55))
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(file_path)
