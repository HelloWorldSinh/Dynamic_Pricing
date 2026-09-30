import re
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class SkuMatcher:
    """Service thực hiện ghép cặp sản phẩm cào về với danh mục chuẩn (SKU Matching Engine).
    Tuân thủ chiến lược 2 tầng theo skill regex-vs-llm-structured-text:
    - Tầng 1: Exact Match bằng mã Part-Number Regex (Độ tin cậy 100%)
    - Tầng 2: Normalized Attribute Matching (RapidFuzz / Levenshtein + so sánh RAM/ROM)
    """

    def __init__(self, dim_product_path: str = "data/dim_product.xlsx", demand_events_path: str = "data/demand_events_20260723.xlsx"):
        self.dim_product_path = dim_product_path
        self.demand_events_path = demand_events_path
        self.df_dim = pd.DataFrame()
        self.fpt_prices: Dict[str, int] = {}
        self._load_data()

    def _load_data(self):
        """Nạp danh mục sản phẩm chuẩn FPT và giá tham chiếu."""
        if os.path.exists(self.dim_product_path):
            self.df_dim = pd.read_excel(self.dim_product_path)
            logger.info(f"Đã nạp {len(self.df_dim)} SKU chuẩn từ {self.dim_product_path}")
        else:
            logger.warning(f"Không tìm thấy file danh mục chuẩn: {self.dim_product_path}")

        if os.path.exists(self.demand_events_path):
            try:
                df_dem = pd.read_excel(self.demand_events_path)
                # Lấy giá median làm giá niêm yết tham chiếu của FPT
                self.fpt_prices = df_dem.groupby("sku_id")["price_at_event"].median().astype(int).to_dict()
                logger.info(f"Đã nạp giá tham chiếu FPT cho {len(self.fpt_prices)} SKU")
            except Exception as e:
                logger.warning(f"Không thể đọc giá từ {self.demand_events_path}: {e}")

    @staticmethod
    def extract_part_numbers(text: str) -> List[str]:
        """Trích xuất danh sách Part-Number từ tên sản phẩm.
        Hỗ trợ các định dạng:
        - Acer: A715-59G-57TU, ANV15-52-50VA, NL16-71G-71UJ
        - Asus: X1404VA-EB355W, FA506NCG-HN329W, UX3407QA-QD299WS
        - Lenovo: 83UQ003NVN, 83RQ002PVN
        - MSI / HP / Dell: B13VEK-2440VN, v.v.
        """
        if not text:
            return []
        # Pattern 1: Dạng có dấu gạch ngang (ABC-123 hoặc ABC-123-XYZ)
        p1 = re.findall(r"\b[A-Za-z0-9]{3,}-[A-Za-z0-9]{3,}(?:-[A-Za-z0-9]{2,})?\b", text)
        # Pattern 2: Mã Lenovo 8x/83 series
        p2 = re.findall(r"\b8[0-9][A-Za-z0-9]{6,8}\b", text)
        
        parts = set(p1 + p2)
        # Lọc các chuỗi ngắn hoặc không có số
        valid_parts = [p.upper() for p in parts if len(p) >= 6 and any(c.isdigit() for c in p)]
        return valid_parts

    @staticmethod
    def clean_product_name(text: str) -> str:
        """Làm sạch các từ ngữ marketing gây nhiễu."""
        if not text:
            return ""
        t = text.lower()
        t = re.sub(r"\|\s*chính hãng\s*(?:vn/a)?", "", t)
        t = re.sub(r"\b(chính hãng|vn/a|đã kích hoạt|cũ đẹp|đổi trả|5g|4g|lte|mới 100%|new)\b", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    @staticmethod
    def extract_storage(text: str) -> List[str]:
        """Trích xuất danh sách dung lượng bộ nhớ trong ROM/SSD (VD: 128gb, 256gb, 512gb, 1tb, 2tb)."""
        if not text:
            return []
        found = []
        for m in re.finditer(r"\b(64|128|256|512)\s*gb\b", text, re.I):
            found.append(f"{m.group(1)}gb".lower())
        for m in re.finditer(r"\b(1|2)\s*tb\b", text, re.I):
            found.append(f"{m.group(1)}tb".lower())
        return list(set(found))

    @staticmethod
    def extract_ram(text: str) -> List[str]:
        """Trích xuất dung lượng RAM (VD: 4gb, 6gb, 8gb, 12gb, 16gb, 24gb, 32gb)."""
        if not text:
            return []
        found = []
        for m in re.finditer(r"\b(4|6|8|12|16|24|32)\s*gb\b", text, re.I):
            found.append(f"{m.group(1)}gb".lower())
        return list(set(found))

    @staticmethod
    def extract_model_identifier(text: str) -> Optional[str]:
        """Trích xuất định danh model cốt lõi (Hard Model Constraint).
        Ngăn chặn triệt để việc nhầm lẫn:
        - iPhone 18 với iPhone 14 / iPhone 17
        - Galaxy Z Fold với Galaxy S25 / S26
        - Laptop Aspire với Nitro / TUF Gaming
        """
        if not text:
            return None
        t = text.lower()
        
        # 1. iPhone: bắt buộc đúng thế hệ (14, 15, 16, 17, 18, SE) + phân khúc (pro max, pro, plus, e, mini)
        ip = re.search(r"\biphone\s*(\d+|se|x|xs|xr)\s*(pro\s*max|pro|plus|mini|e)?\b", t)
        if ip:
            gen = ip.group(1)
            sub = (ip.group(2) or "").replace(" ", "")
            return f"iphone_{gen}_{sub}"
            
        # 2. Samsung: bắt buộc đúng dòng (z fold, z flip, s, a, m) + thế hệ số
        ss = re.search(r"\bgalaxy\s*(z\s*fold|z\s*flip|s|a|m)\s*(\d+)\s*(ultra|plus|fe|edge)?\b", t)
        if ss:
            series = ss.group(1).replace(" ", "")
            num = ss.group(2)
            sub = (ss.group(3) or "")
            return f"samsung_{series}{num}_{sub}"

        # 3. Xiaomi / Redmi / Poco
        redmi = re.search(r"\b(?:xiaomi\s+)?(redmi\s*note\s*\d+[a-z]?|redmi\s*\d+[a-z]?|poco\s*[a-z0-9]+|xiaomi\s*\d+[a-z]?)\b", t)
        if redmi:
            return re.sub(r"\s+", "_", redmi.group(1).strip())

        # 4. Oppo: bắt buộc phân biệt rõ ultra, pro, plus, s
        oppo = re.search(r"\boppo\s*(find\s*[a-z0-9]+|reno\s*[a-z0-9]+|a\s*\d+[a-z]?)\s*(ultra|pro|plus|fe|s)?\b", t)
        if oppo:
            main = oppo.group(1).replace(" ", "_")
            sub = oppo.group(2) or ""
            return f"oppo_{main}_{sub}".rstrip("_")

        # 5. Laptop Series: Phải đúng dòng
        laptop_lines = [
            "macbook air", "macbook pro", "macbook",
            "aspire 7", "aspire go", "aspire lite", "nitro v", "nitro lite", "nitro", "predator", "swift",
            "vivobook go", "vivobook s14", "vivobook 14", "vivobook", "tuf gaming", "rog strix", "zenbook",
            "ideapad slim", "ideapad gaming", "loq", "legion", "thinkbook",
            "inspiron", "vostro", "latitude", "pavilion", "victus", "omen", "katana"
        ]
        for line in laptop_lines:
            if line in t:
                return line.replace(" ", "_")

        return None

    def match_single_item(self, scraped_name: str, competitor_price: Optional[int] = None) -> Dict[str, Any]:
        """Thực hiện ghép cặp 1 sản phẩm cào với danh mục chuẩn.
        Tuân thủ:
        1. Exact Part-Number (100% tin cậy)
        2. Hard Model Identifier (Bắt buộc phải cùng thế hệ và dòng máy)
        3. Thuộc tính RAM / ROM (Chỉ approved khi cấu hình trùng khớp)
        """
        scraped_parts = self.extract_part_numbers(scraped_name)
        
        best_sku_id = None
        best_sku_name = None
        best_confidence = 0.0
        match_type = "UNMATCHED"
        
        # --- TẦNG 1: EXACT MATCH QUA PART-NUMBER ---
        if scraped_parts:
            for _, row in self.df_dim.iterrows():
                dim_sku_id = str(row["sku_id"])
                dim_name = str(row["sku_name"])
                dim_parts = self.extract_part_numbers(dim_name)
                
                # 1. So sánh giao của hai tập part number
                common = set(scraped_parts).intersection(set(dim_parts))
                if common:
                    best_sku_id = dim_sku_id
                    best_sku_name = dim_name
                    best_confidence = 1.0
                    match_type = "EXACT_PART_NUMBER"
                    break
                
                # 2. Kiểm tra part number cào được có nằm trong tên chuẩn FPT không
                for p in scraped_parts:
                    if p in dim_name.upper():
                        best_sku_id = dim_sku_id
                        best_sku_name = dim_name
                        best_confidence = 1.0
                        match_type = "EXACT_PART_NUMBER"
                        break
                if best_sku_id:
                    break

        # --- TẦNG 2: NORMALIZED ATTRIBUTE VỚI RÀNG BUỘC MODEL CỨNG ---
        if not best_sku_id:
            c_clean = self.clean_product_name(scraped_name)
            scraped_model_id = self.extract_model_identifier(scraped_name)
            
            # Trích xuất thương hiệu chính
            brands = ["apple", "iphone", "samsung", "xiaomi", "oppo", "vivo", "realme", "tecno", "acer", "asus", "lenovo", "dell", "hp", "msi", "poco", "honor"]
            detected_brand = next((b for b in brands if b in c_clean), None)
            
            # Trích xuất cấu hình RAM & Ổ cứng bằng helper chuẩn
            s_ram = self.extract_ram(c_clean)
            s_rom = self.extract_storage(c_clean)
            is_series_generic = "series" in c_clean.lower()
            
            for _, row in self.df_dim.iterrows():
                dim_sku_id = str(row["sku_id"])
                dim_name = str(row["sku_name"])
                dim_clean = self.clean_product_name(dim_name)
                dim_model_id = self.extract_model_identifier(dim_name)
                
                # RÀNG BUỘC 1: Nếu khác thương hiệu thì bỏ qua ngay
                if detected_brand and detected_brand not in dim_clean:
                    continue
                
                # RÀNG BUỘC 2: NẾU ĐÃ BẮT ĐƯỢC MODEL IDENTIFIER THÌ BẮT BUỘC PHẢI TRÙNG NHAU
                # Tránh tuyệt đối: iPhone 18 ghép iPhone 14, Z Fold8 ghép S25
                if scraped_model_id and dim_model_id and scraped_model_id != dim_model_id:
                    continue
                
                # Nếu một bên có model_id cụ thể (ví dụ iPhone 18) mà bên kia không có -> không ghép đối với điện thoại
                if detected_brand in ["apple", "iphone", "samsung", "oppo", "xiaomi"]:
                    if (scraped_model_id and not dim_model_id) or (not scraped_model_id and dim_model_id):
                        continue
                elif scraped_model_id and not dim_model_id:
                    continue
                
                # Trích xuất RAM & ROM của FPT
                dim_ram = self.extract_ram(dim_clean)
                dim_rom = self.extract_storage(dim_clean)

                # RÀNG BUỘC 3: Nếu là điện thoại, bắt buộc cùng ROM nếu cả 2 bên đều có thông số ROM
                if detected_brand in ["apple", "iphone", "samsung", "oppo", "xiaomi"]:
                    if s_rom and dim_rom and set(s_rom) != set(dim_rom):
                        continue # Khác dung lượng bộ nhớ thì không được ghép
                
                # Tính độ tương đồng chuỗi cơ sở
                ratio = SequenceMatcher(None, c_clean, dim_clean).ratio()
                
                bonus = 0.0
                if s_ram and dim_ram and set(s_ram) == set(dim_ram):
                    bonus += 0.1
                if s_rom and dim_rom and set(s_rom) == set(dim_rom):
                    bonus += 0.1
                if scraped_model_id and scraped_model_id == dim_model_id:
                    bonus += 0.15 # Thưởng lớn nếu trùng chính xác model định danh
                    
                score = min(0.95, ratio + bonus)
                
                # Nếu cả 2 bên đều có Part-Number nhưng khác nhau -> Không được Approved, tối đa PENDING
                dim_parts = self.extract_part_numbers(dim_name)
                if scraped_parts and dim_parts and not set(scraped_parts).intersection(set(dim_parts)):
                    score = min(0.79, score)

                # Nếu là tên nhóm chung chung như "Series" thì không được cho điểm quá cao để tránh tự động Approved
                if is_series_generic:
                    score = min(0.79, score)
                
                # Chỉ chấp nhận khi độ tương đồng đủ cao và đúng model
                if score > best_confidence and score >= 0.75:
                    best_confidence = score
                    best_sku_id = dim_sku_id
                    best_sku_name = dim_name
                    match_type = "NORMALIZED_ATTRIBUTE"

        # Phân loại trạng thái duyệt
        status = "UNMATCHED"
        if best_sku_id:
            status = "APPROVED" if best_confidence >= 0.85 else "PENDING"
            
        fpt_price = self.fpt_prices.get(best_sku_id, None) if best_sku_id else None
        
        # Tính chênh lệch giá (FPT vs Đối thủ)
        price_diff_vnd = None
        price_diff_pct = None
        if fpt_price and competitor_price:
            price_diff_vnd = fpt_price - competitor_price
            price_diff_pct = (price_diff_vnd / fpt_price) * 100

        return {
            "fpt_sku_id": best_sku_id if best_sku_id else "N/A",
            "fpt_sku_name": best_sku_name if best_sku_name else "Không tìm thấy SKU tương ứng",
            "match_type": match_type,
            "confidence_score": round(best_confidence, 3),
            "status": status,
            "fpt_price": fpt_price,
            "competitor_price": competitor_price,
            "price_diff_vnd": price_diff_vnd,
            "price_diff_pct": round(price_diff_pct, 1) if price_diff_pct is not None else None
        }

    def process_and_export_excel(
        self,
        scraped_items: List[Dict[str, Any]],
        output_excel_path: str = "data/crawl_and_sku_mapping_output.xlsx",
        master_by_fpt: bool = False
    ) -> str:
        """Quy trình toàn diện Bước 2 & Bước 3:
        1. So khớp toàn bộ sản phẩm cào về.
        2. Tạo file Excel chuẩn 2 Sheet (Scraped_All_Data và SKU_Mapping).
           - Nếu master_by_fpt=True: Sheet 2 lấy toàn bộ 329 SKU của FPT làm chuẩn Master Table,
             sản phẩm nào đối thủ không có sẽ hiển thị 'N/A' (NOT_FOUND).
           - Nếu master_by_fpt=False: Giữ nguyên theo danh sách sản phẩm cào được.
        3. Định dạng styling chuyên nghiệp.
        """
        logger.info(f"Bắt đầu so khớp {len(scraped_items)} sản phẩm và xuất file Excel (master_by_fpt={master_by_fpt})...")
        
        # --- 1. Tạo Data Sheet 1: Scraped_All_Data ---
        sheet1_rows = []
        for idx, item in enumerate(scraped_items, 1):
            sheet1_rows.append({
                "STT": idx,
                "Nguồn": item.get("Nguồn", "ĐỐI THỦ"),
                "Tên sản phẩm cào được": item.get("Tên sản phẩm", item.get("Tên sản phẩm đối thủ", "")),
                "Giá bán đối thủ (VND)": item.get("Giá bán (VND)"),
                "Giá niêm yết (VND)": item.get("Giá niêm yết (VND)"),
                "Tình trạng kho": item.get("Còn hàng", "Còn hàng"),
                "Thông số kỹ thuật tóm tắt": item.get("Thông số kỹ thuật tóm tắt", "N/A"),
                "URL sản phẩm": item.get("URL sản phẩm", ""),
                "Thời gian cào": item.get("Thời gian cào", "")
            })
        df_sheet1 = pd.DataFrame(sheet1_rows)

        # --- 2. Tạo Data Sheet 2: SKU_Mapping ---
        sheet2_rows = []

        if master_by_fpt and not self.df_dim.empty:
            # Chế độ Master FPT: Lấy toàn bộ 329 SKU của FPT làm trục chuẩn
            source_name = scraped_items[0].get("Nguồn", "ĐỐI THỦ") if scraped_items else "ĐỐI THỦ"

            # Tìm best match từ danh sách sản phẩm cào về cho từng SKU FPT
            fpt_to_competitor: Dict[str, Dict[str, Any]] = {}
            for item in scraped_items:
                scraped_name = item.get("Tên sản phẩm", item.get("Tên sản phẩm đối thủ", ""))
                c_price = item.get("Giá bán (VND)")
                match_res = self.match_single_item(scraped_name, c_price)
                if match_res["status"] in ["APPROVED", "PENDING"]:
                    fpt_sku = match_res["fpt_sku_id"]
                    conf = match_res["confidence_score"]
                    if fpt_sku not in fpt_to_competitor or conf > fpt_to_competitor[fpt_sku]["confidence"]:
                        fpt_to_competitor[fpt_sku] = {
                            "item": item,
                            "match_res": match_res,
                            "confidence": conf,
                            "competitor_name": scraped_name
                        }

            for idx, (_, row) in enumerate(self.df_dim.iterrows(), 1):
                sku_id = str(row["sku_id"])
                sku_name = str(row["sku_name"])
                fpt_ref_price = self.fpt_prices.get(sku_id)

                if sku_id in fpt_to_competitor:
                    c_data = fpt_to_competitor[sku_id]
                    m = c_data["match_res"]
                    c_price = m["competitor_price"]
                    diff_vnd = m["price_diff_vnd"]
                    diff_pct = m["price_diff_pct"]

                    sheet2_rows.append({
                        "STT": idx,
                        "Mã SKU FPT": sku_id,
                        "Tên sản phẩm chuẩn (FPT Shop)": sku_name,
                        "Nguồn đối thủ": source_name,
                        "Tên sản phẩm đối thủ cào về": c_data["competitor_name"],
                        "Giá đối thủ (VND)": c_price,
                        "Giá tham chiếu FPT (VND)": fpt_ref_price if fpt_ref_price else "Chưa có giá",
                        "Chênh lệch giá (FPT - ĐT)": diff_vnd if diff_vnd is not None else "N/A",
                        "Chênh lệch (%)": f"{diff_pct}%" if diff_pct is not None else "N/A",
                        "Loại khớp (Match Type)": m["match_type"],
                        "Độ tin cậy (Confidence)": m["confidence_score"],
                        "Trạng thái (Status)": m["status"],
                    })
                else:
                    sheet2_rows.append({
                        "STT": idx,
                        "Mã SKU FPT": sku_id,
                        "Tên sản phẩm chuẩn (FPT Shop)": sku_name,
                        "Nguồn đối thủ": source_name,
                        "Tên sản phẩm đối thủ cào về": "N/A",
                        "Giá đối thủ (VND)": "N/A",
                        "Giá tham chiếu FPT (VND)": fpt_ref_price if fpt_ref_price else "Chưa có giá",
                        "Chênh lệch giá (FPT - ĐT)": "N/A",
                        "Chênh lệch (%)": "N/A",
                        "Loại khớp (Match Type)": "NOT_FOUND",
                        "Độ tin cậy (Confidence)": 0.0,
                        "Trạng thái (Status)": "NOT_FOUND",
                    })
        else:
            for idx, item in enumerate(scraped_items, 1):
                scraped_name = item.get("Tên sản phẩm", item.get("Tên sản phẩm đối thủ", ""))
                c_price = item.get("Giá bán (VND)")
                source = item.get("Nguồn", "ĐỐI THỦ")
                
                match_res = self.match_single_item(scraped_name, c_price)
                
                sheet2_rows.append({
                    "STT": idx,
                    "Mã SKU FPT": match_res["fpt_sku_id"],
                    "Tên sản phẩm chuẩn (FPT Shop)": match_res["fpt_sku_name"],
                    "Nguồn đối thủ": source,
                    "Tên sản phẩm đối thủ cào về": scraped_name,
                    "Giá đối thủ (VND)": match_res["competitor_price"],
                    "Giá tham chiếu FPT (VND)": match_res["fpt_price"] if match_res["fpt_price"] else "Chưa có giá",
                    "Chênh lệch giá (FPT - ĐT)": match_res["price_diff_vnd"] if match_res["price_diff_vnd"] is not None else "N/A",
                    "Chênh lệch (%)": f"{match_res['price_diff_pct']}%" if match_res['price_diff_pct'] is not None else "N/A",
                    "Loại khớp (Match Type)": match_res["match_type"],
                    "Độ tin cậy (Confidence)": match_res["confidence_score"],
                    "Trạng thái (Status)": match_res["status"],
                })
        df_sheet2 = pd.DataFrame(sheet2_rows)

        # --- 3. Xuất ra Excel với định dạng chuyên nghiệp ---
        actual_path = output_excel_path
        try:
            with pd.ExcelWriter(actual_path, engine="openpyxl") as writer:
                df_sheet1.to_excel(writer, sheet_name="Scraped_All_Data", index=False)
                df_sheet2.to_excel(writer, sheet_name="SKU_Mapping", index=False)
        except PermissionError:
            from datetime import datetime
            actual_path = os.path.join(os.path.dirname(output_excel_path), f"crawl_and_sku_mapping_output_{datetime.now().strftime('%H%M%S')}.xlsx")
            logger.warning(f"File {output_excel_path} đang mở trong ứng dụng khác. Lưu sang: {actual_path}")
            with pd.ExcelWriter(actual_path, engine="openpyxl") as writer:
                df_sheet1.to_excel(writer, sheet_name="Scraped_All_Data", index=False)
                df_sheet2.to_excel(writer, sheet_name="SKU_Mapping", index=False)

        # Áp dụng styling OpenPyXL
        self._apply_excel_styling(actual_path)
        logger.info(f"Đã xuất và định dạng thành công file Excel 2 sheet tại: {actual_path}")
        return actual_path

    @staticmethod
    def _apply_excel_styling(file_path: str):
        """Định dạng phông chữ, màu sắc, tiền tệ và độ rộng cột."""
        wb = openpyxl.load_workbook(file_path)

        # Style definition
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid") # Navy Blue
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        
        green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid") # Khớp APPROVED
        yellow_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid") # Cần duyệt PENDING
        red_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid") # Unmatched
        
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        for sheetname in wb.sheetnames:
            ws = wb[sheetname]
            
            # Format header
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws.row_dimensions[1].height = 28

            # Format data rows
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

            # Tô màu trạng thái cho Sheet SKU_Mapping
            if sheetname == "SKU_Mapping":
                for row in range(2, ws.max_row + 1):
                    status_cell = ws.cell(row=row, column=12) # Cột Status
                    conf_cell = ws.cell(row=row, column=11)   # Cột Confidence
                    
                    if isinstance(conf_cell.value, (int, float)):
                        conf_cell.number_format = '0.0%'
                        conf_cell.alignment = Alignment(horizontal="center", vertical="center")
                        
                    if status_cell.value == "APPROVED":
                        status_cell.fill = green_fill
                    elif status_cell.value == "PENDING":
                        status_cell.fill = yellow_fill
                    elif status_cell.value in ["UNMATCHED", "NOT_FOUND"]:
                        status_cell.fill = red_fill

            # Auto-fit độ rộng cột
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    val_str = str(cell.value or "")
                    if cell.row == 1:
                        max_len = max(max_len, len(val_str) + 4)
                    else:
                        max_len = max(max_len, min(len(val_str), 55)) # Giới hạn tối đa 55 ký tự để không quá bè
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(file_path)
