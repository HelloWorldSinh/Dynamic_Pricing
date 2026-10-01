import re
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import pandas as pd

from app.utils.excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)


class SkuMatcher:
    """Service thực hiện ghép cặp sản phẩm cào về với danh mục chuẩn FPT Shop (SKU Matching Engine).

    Tuân thủ chiến lược 2 tầng:
    - Tầng 1: Exact Match bằng mã Part-Number Regex (Độ tin cậy 100%)
    - Tầng 2: Normalized Attribute Matching (RapidFuzz / Levenshtein + so sánh RAM/ROM + Hard Model Constraints)
    """

    BRAND_MAP = {
        "apple": "apple", "iphone": "apple", "macbook": "apple", "ipad": "apple",
        "samsung": "samsung", "galaxy": "samsung",
        "xiaomi": "xiaomi", "redmi": "xiaomi", "poco": "xiaomi",
        "oppo": "oppo", "vivo": "vivo", "realme": "realme", "tecno": "tecno",
        "acer": "acer", "asus": "asus", "lenovo": "lenovo", "dell": "dell",
        "hp": "hp", "msi": "msi", "honor": "honor"
    }

    LAPTOP_LINES = (
        "macbook air", "macbook pro", "macbook",
        "aspire 7", "aspire go", "aspire lite", "nitro v", "nitro lite", "nitro", "predator", "swift",
        "vivobook go", "vivobook s14", "vivobook 14", "vivobook", "tuf gaming", "rog strix", "zenbook",
        "ideapad slim", "ideapad gaming", "loq", "legion", "thinkbook",
        "inspiron", "vostro", "latitude", "pavilion", "victus", "omen", "katana"
    )

    CONFIDENCE_EXACT = 1.0
    CONFIDENCE_APPROVED_THRESHOLD = 0.85
    CONFIDENCE_MIN_THRESHOLD = 0.75
    CONFIDENCE_PENDING_CEILING = 0.79

    def __init__(
        self,
        dim_product_path: str = "data/dim_product.xlsx",
        demand_events_path: str = "data/demand_events_20260723.xlsx"
    ):
        self.dim_product_path = dim_product_path
        self.demand_events_path = demand_events_path
        self.df_dim = pd.DataFrame()
        self.fpt_prices: Dict[str, int] = {}
        self.parsed_dim_skus: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self) -> None:
        """Nạp danh mục sản phẩm chuẩn FPT, giá tham chiếu và tiền xử lý (precompute)
        toàn bộ đặc trưng regex của SKU FPT để tối ưu hiệu năng O(1) khi so khớp.
        """
        if os.path.exists(self.dim_product_path):
            self.df_dim = pd.read_excel(self.dim_product_path)
            self._precompute_fpt_skus()
            logger.info(f"Đã nạp và tiền xử lý {len(self.parsed_dim_skus)} SKU chuẩn từ {self.dim_product_path}")
        else:
            logger.warning(f"Không tìm thấy file danh mục chuẩn: {self.dim_product_path}")

        if os.path.exists(self.demand_events_path):
            try:
                df_dem = pd.read_excel(self.demand_events_path)
                self.fpt_prices = df_dem.groupby("sku_id")["price_at_event"].median().astype(int).to_dict()
                logger.info(f"Đã nạp giá tham chiếu FPT cho {len(self.fpt_prices)} SKU")
            except Exception as e:
                logger.warning(f"Không thể đọc giá từ {self.demand_events_path}: {e}")

    def _precompute_fpt_skus(self) -> None:
        """Tiền xử lý trước Part Number, Brand, Model ID, RAM, ROM cho toàn bộ danh mục FPT.
        Tránh tính toán lại hàng triệu phép Regex khi duyệt qua từng sản phẩm cào về.
        """
        self.parsed_dim_skus = []
        for _, row in self.df_dim.iterrows():
            sku_id = str(row["sku_id"])
            sku_name = str(row["sku_name"])
            clean_name = self.clean_product_name(sku_name)
            self.parsed_dim_skus.append({
                "sku_id": sku_id,
                "sku_name": sku_name,
                "clean_name": clean_name,
                "brand": self.detect_brand(sku_name),
                "parts": self.extract_part_numbers(sku_name),
                "model_id": self.extract_model_identifier(sku_name),
                "ram": self.extract_ram(clean_name),
                "rom": self.extract_storage(clean_name),
            })

    @classmethod
    def detect_brand(cls, text: str) -> Optional[str]:
        """Chuẩn hóa và nhận diện thương hiệu chuẩn (Brand Normalization)."""
        if not text:
            return None
        t = text.lower()
        for kw, canonical in cls.BRAND_MAP.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", t):
                return canonical
        return None

    @staticmethod
    def extract_part_numbers(text: str) -> List[str]:
        """Trích xuất danh sách Part-Number từ tên sản phẩm.
        Hỗ trợ các định dạng:
        - Acer: A715-59G-57TU, AN515-58-52SP, ANV15-52-50VA, NL16-71G-71UJ
        - Asus: X1404VA-EB355W, FA506NCG-HN329W, UX3407QA-QD299WS
        - Lenovo: 83UQ003NVN, 83RQ002PVN, 83GS001RVN
        - MSI / HP / Dell: B13VEK-2440VN, v.v.
        """
        if not text:
            return []
        p1 = re.findall(r"\b[A-Za-z0-9]{2,}-[A-Za-z0-9]{2,}(?:-[A-Za-z0-9]{2,})*\b", text)
        p2 = re.findall(r"\b8[0-9][A-Za-z0-9]{6,8}\b", text)
        parts = set(p1 + p2)
        return [p.upper() for p in parts if len(p) >= 6 and any(c.isdigit() for c in p)]

    @staticmethod
    def clean_product_name(text: str) -> str:
        """Làm sạch các từ ngữ marketing gây nhiễu."""
        if not text:
            return ""
        t = text.lower()
        t = re.sub(r"\|\s*chính hãng\s*(?:vn/a)?", "", t)
        t = re.sub(r"\b(điện thoại|laptop|máy tính xách tay|máy tính bảng|chính hãng|vn/a|đã kích hoạt|cũ đẹp|đổi trả|5g|4g|lte|mới 100%|new)\b", "", t)
        t = re.sub(r"[-–|/]", " ", t)
        return re.sub(r"\s+", " ", t).strip()

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
        found = [f"{m.group(1)}gb".lower() for m in re.finditer(r"\b(4|6|8|12|16|24|32)\s*gb\b", text, re.I)]
        return list(set(found))

    @classmethod
    def extract_model_identifier(cls, text: str) -> Optional[str]:
        """Trích xuất định danh model cốt lõi (Hard Model Constraint).
        Ngăn chặn việc ghép sai thế hệ hoặc sai dòng máy (VD: iPhone 18 vs iPhone 14, Z Fold8 vs S25).
        """
        if not text:
            return None
        t = text.lower()

        # 1. iPhone
        ip = re.search(r"\biphone\s*(\d+|se|x|xs|xr)\s*(pro\s*max|pro|plus|mini|e)?\b", t)
        if ip:
            gen = ip.group(1)
            sub = (ip.group(2) or "").replace(" ", "")
            return f"iphone_{gen}_{sub}"

        # 2. Samsung
        ss = re.search(r"\bgalaxy\s*(z\s*fold|z\s*flip|s|a|m)\s*(\d+)\s*(ultra|plus|fe|edge)?\b", t)
        if ss:
            series = ss.group(1).replace(" ", "")
            num = ss.group(2)
            sub = ss.group(3) or ""
            return f"samsung_{series}{num}_{sub}"

        # 3. Xiaomi / Redmi / Poco
        redmi = re.search(r"\b(?:xiaomi\s+)?(redmi\s*note\s*\d+[a-z]?|redmi\s*\d+[a-z]?|poco\s*[a-z0-9]+|xiaomi\s*\d+[a-z]?)\b", t)
        if redmi:
            return re.sub(r"\s+", "_", redmi.group(1).strip())

        # 4. Oppo
        oppo = re.search(r"\boppo\s*(find\s*[a-z0-9]+|reno\s*[a-z0-9]+|a\s*\d+[a-z]?)\s*(ultra|pro|plus|fe|s)?\b", t)
        if oppo:
            main = oppo.group(1).replace(" ", "_")
            sub = oppo.group(2) or ""
            return f"oppo_{main}_{sub}".rstrip("_")

        # 5. Laptop Series
        for line in cls.LAPTOP_LINES:
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
        scraped_parts_set = set(scraped_parts)

        best_sku_id = None
        best_sku_name = None
        best_confidence = 0.0
        match_type = "UNMATCHED"

        # --- TẦNG 1: EXACT MATCH QUA PART-NUMBER ---
        if scraped_parts:
            for item in self.parsed_dim_skus:
                dim_sku_id = item["sku_id"]
                dim_name = item["sku_name"]
                dim_parts_set = set(item["parts"])

                # 1. So sánh giao của hai tập part number
                if scraped_parts_set.intersection(dim_parts_set):
                    best_sku_id = dim_sku_id
                    best_sku_name = dim_name
                    best_confidence = self.CONFIDENCE_EXACT
                    match_type = "EXACT_PART_NUMBER"
                    break

                # 2. Kiểm tra part number cào được có nằm trong tên chuẩn FPT không
                dim_name_upper = dim_name.upper()
                if any(p in dim_name_upper for p in scraped_parts):
                    best_sku_id = dim_sku_id
                    best_sku_name = dim_name
                    best_confidence = self.CONFIDENCE_EXACT
                    match_type = "EXACT_PART_NUMBER"
                    break

        # --- TẦNG 2: NORMALIZED ATTRIBUTE VỚI RÀNG BUỘC MODEL CỨNG ---
        if not best_sku_id:
            c_clean = self.clean_product_name(scraped_name)
            scraped_brand = self.detect_brand(scraped_name)
            scraped_model_id = self.extract_model_identifier(scraped_name)

            s_ram = self.extract_ram(c_clean)
            s_rom = self.extract_storage(c_clean)
            s_ram_set = set(s_ram)
            s_rom_set = set(s_rom)
            is_series_generic = "series" in c_clean.lower()

            for item in self.parsed_dim_skus:
                dim_sku_id = item["sku_id"]
                dim_name = item["sku_name"]
                dim_clean = item["clean_name"]
                dim_brand = item["brand"]
                dim_model_id = item["model_id"]

                # Ràng buộc 1: Khác thương hiệu thì bỏ qua ngay
                if scraped_brand and dim_brand and scraped_brand != dim_brand:
                    continue

                # Ràng buộc 2: Bắt buộc cùng Model Identifier nếu cả 2 bên nhận diện được model
                if scraped_model_id and dim_model_id and scraped_model_id != dim_model_id:
                    continue

                if scraped_brand in ["apple", "samsung", "oppo", "xiaomi"]:
                    if (scraped_model_id and not dim_model_id) or (not scraped_model_id and dim_model_id):
                        continue
                elif scraped_model_id and not dim_model_id:
                    continue

                dim_ram = item["ram"]
                dim_rom = item["rom"]

                # Ràng buộc 3: Bắt buộc cùng ROM cho điện thoại nếu cả 2 bên đều có thông số ROM
                if scraped_brand in ["apple", "samsung", "oppo", "xiaomi"]:
                    if s_rom and dim_rom and s_rom_set != set(dim_rom):
                        continue

                # Tính độ tương đồng chuỗi cơ sở
                ratio = SequenceMatcher(None, c_clean, dim_clean).ratio()

                bonus = 0.0
                if s_ram and dim_ram and s_ram_set == set(dim_ram):
                    bonus += 0.1
                if s_rom and dim_rom and s_rom_set == set(dim_rom):
                    bonus += 0.1
                if scraped_model_id and scraped_model_id == dim_model_id:
                    bonus += 0.15

                score = min(0.95, ratio + bonus)

                # Nếu cả 2 bên đều có Part-Number nhưng khác nhau -> Không được Approved
                dim_parts_set = set(item["parts"])
                if scraped_parts_set and dim_parts_set and not scraped_parts_set.intersection(dim_parts_set):
                    score = min(self.CONFIDENCE_PENDING_CEILING, score)

                if is_series_generic:
                    score = min(self.CONFIDENCE_PENDING_CEILING, score)

                if score > best_confidence and score >= self.CONFIDENCE_MIN_THRESHOLD:
                    best_confidence = score
                    best_sku_id = dim_sku_id
                    best_sku_name = dim_name
                    match_type = "NORMALIZED_ATTRIBUTE"

        # Phân loại trạng thái duyệt
        status = "UNMATCHED"
        if best_sku_id:
            status = "APPROVED" if best_confidence >= self.CONFIDENCE_APPROVED_THRESHOLD else "PENDING"

        fpt_price = self.fpt_prices.get(best_sku_id, None) if best_sku_id else None

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
        """Ghép cặp sản phẩm cào về và xuất báo cáo Excel 2 sheet (ủy quyền qua ExcelExporter)."""
        logger.info(f"Bắt đầu so khớp {len(scraped_items)} sản phẩm và xuất file Excel (master_by_fpt={master_by_fpt})...")

        # 1. Tạo Data Sheet 1: Scraped_All_Data
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

        # 2. Tạo Data Sheet 2: SKU_Mapping
        sheet2_rows = []
        if master_by_fpt and not self.df_dim.empty:
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

            for idx, item in enumerate(self.parsed_dim_skus, 1):
                sku_id = item["sku_id"]
                sku_name = item["sku_name"]
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

        # 3. Xuất qua ExcelExporter chuyên trách
        return ExcelExporter.export_sku_mapping_report(
            df_sheet1=df_sheet1,
            df_sheet2=df_sheet2,
            output_excel_path=output_excel_path
        )

    def match_multi_sources(
        self,
        cellphones_items: List[Dict[str, Any]],
        hoangha_items: List[Dict[str, Any]],
        output_excel_path: str = "data/crawl_and_sku_mapping_output.xlsx"
    ) -> str:
        """So khớp dữ liệu từ cả 2 nguồn (CellphoneS & Hoàng Hà Mobile) với danh mục chuẩn FPT Shop (329 SKUs)
        và xuất ra 1 file Excel duy nhất gồm 3 sheet:
        - Sheet 1: FPT_Shop_Comparison (Bảng Master đối sánh 329 SKU FPT với 2 đối thủ song song)
        - Sheet 2: CellphoneS_Data (Dữ liệu cào thực tế từ CellphoneS)
        - Sheet 3: HoangHa_Data (Dữ liệu cào thực tế từ Hoàng Hà Mobile)
        """
        logger.info(
            f"Bắt đầu so khớp đa nguồn: CellphoneS ({len(cellphones_items)} SP) + "
            f"Hoàng Hà ({len(hoangha_items)} SP) với {len(self.parsed_dim_skus)} SKU FPT..."
        )

        # 1. Chuẩn hóa Data Sheet 2: CellphoneS_Data
        cps_rows = []
        for idx, item in enumerate(cellphones_items, 1):
            cps_rows.append({
                "STT": idx,
                "Nguồn": item.get("Nguồn", "CellphoneS"),
                "Tên sản phẩm cào được": item.get("Tên sản phẩm", item.get("Tên sản phẩm cào được", "")),
                "Giá bán đối thủ (VND)": item.get("Giá bán (VND)", item.get("Giá bán đối thủ (VND)")),
                "Giá niêm yết (VND)": item.get("Giá niêm yết (VND)"),
                "Tình trạng kho": item.get("Còn hàng", item.get("Tình trạng kho", "Còn hàng")),
                "Thông số kỹ thuật tóm tắt": item.get("Thông số kỹ thuật tóm tắt", "N/A"),
                "URL sản phẩm": item.get("URL sản phẩm", item.get("URL", "")),
                "Thời gian cào": item.get("Thời gian cào", "")
            })
        df_cellphones = pd.DataFrame(cps_rows)

        # 2. Chuẩn hóa Data Sheet 3: HoangHa_Data
        hh_rows = []
        for idx, item in enumerate(hoangha_items, 1):
            hh_rows.append({
                "STT": idx,
                "Nguồn": item.get("Nguồn", "HOANGHA"),
                "Tên sản phẩm cào được": item.get("Tên sản phẩm", item.get("Tên sản phẩm cào được", "")),
                "Giá bán đối thủ (VND)": item.get("Giá bán (VND)", item.get("Giá bán đối thủ (VND)")),
                "Giá niêm yết (VND)": item.get("Giá niêm yết (VND)"),
                "Tình trạng kho": item.get("Còn hàng", item.get("Tình trạng kho", "Còn hàng")),
                "Thông số kỹ thuật tóm tắt": item.get("Thông số kỹ thuật tóm tắt", "N/A"),
                "URL sản phẩm": item.get("URL sản phẩm", item.get("URL", "")),
                "Thời gian cào": item.get("Thời gian cào", "")
            })
        df_hoangha = pd.DataFrame(hh_rows)

        # 3. Thuật toán Mapping Best Match cho từng đối thủ
        def _build_best_mapping(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
            mapping: Dict[str, Dict[str, Any]] = {}
            for it in items:
                name = it.get("Tên sản phẩm", it.get("Tên sản phẩm cào được", it.get("Tên sản phẩm đối thủ", "")))
                price = it.get("Giá bán (VND)", it.get("Giá bán đối thủ (VND)"))
                match_res = self.match_single_item(name, price)
                status = match_res["status"]

                if status in ["APPROVED", "PENDING"]:
                    fpt_sku = match_res["fpt_sku_id"]
                    conf = match_res["confidence_score"]

                    should_replace = False
                    if fpt_sku not in mapping:
                        should_replace = True
                    else:
                        curr_status = mapping[fpt_sku]["match_res"]["status"]
                        curr_conf = mapping[fpt_sku]["confidence"]
                        if status == "APPROVED" and curr_status != "APPROVED":
                            should_replace = True
                        elif status == curr_status and conf > curr_conf:
                            should_replace = True

                    if should_replace:
                        mapping[fpt_sku] = {
                            "item": it,
                            "match_res": match_res,
                            "confidence": conf,
                            "name": name,
                            "price": price,
                            "stock": it.get("Còn hàng", it.get("Tình trạng kho", "Còn hàng")),
                            "url": it.get("URL sản phẩm", it.get("URL", ""))
                        }
            return mapping

        fpt_to_cps = _build_best_mapping(cellphones_items)
        fpt_to_hh = _build_best_mapping(hoangha_items)

        # 4. Chuẩn hóa Data Sheet 1: FPT_Shop_Comparison (Master 329 SKU)
        comparison_rows = []
        for idx, item in enumerate(self.parsed_dim_skus, 1):
            sku_id = item["sku_id"]
            sku_name = item["sku_name"]
            fpt_ref_price = self.fpt_prices.get(sku_id)

            # Dữ liệu CellphoneS
            cps_data = fpt_to_cps.get(sku_id)
            cps_name = cps_data["name"] if cps_data else "N/A"
            cps_price = cps_data["price"] if cps_data else "N/A"
            cps_stock = cps_data["stock"] if cps_data else "N/A"
            cps_conf = cps_data["confidence"] if cps_data else 0.0
            cps_status = cps_data["match_res"]["status"] if cps_data else "NOT_FOUND"
            cps_url = cps_data["url"] if cps_data else "N/A"

            # Dữ liệu Hoàng Hà
            hh_data = fpt_to_hh.get(sku_id)
            hh_name = hh_data["name"] if hh_data else "N/A"
            hh_price = hh_data["price"] if hh_data else "N/A"
            hh_stock = hh_data["stock"] if hh_data else "N/A"
            hh_conf = hh_data["confidence"] if hh_data else 0.0
            hh_status = hh_data["match_res"]["status"] if hh_data else "NOT_FOUND"
            hh_url = hh_data["url"] if hh_data else "N/A"

            comparison_rows.append({
                "Mã SKU FPT": sku_id,
                "Tên sản phẩm chuẩn (FPT Shop)": sku_name,
                "Giá tham chiếu FPT (VND)": fpt_ref_price if fpt_ref_price else "Chưa có giá",
                # Cột CellphoneS
                "Tên SP CellphoneS": cps_name,
                "Giá CellphoneS (VND)": cps_price,
                "Kho CellphoneS": cps_stock,
                "Độ tin cậy CPS": cps_conf if cps_data else "N/A",
                "Trạng thái CPS": cps_status,
                "URL CellphoneS": cps_url,
                # Cột Hoàng Hà
                "Tên SP Hoàng Hà": hh_name,
                "Giá Hoàng Hà (VND)": hh_price,
                "Kho Hoàng Hà": hh_stock,
                "Độ tin cậy HH": hh_conf if hh_data else "N/A",
                "Trạng thái HH": hh_status,
                "URL Hoàng Hà": hh_url,
            })

        df_comparison = pd.DataFrame(comparison_rows)

        # 6. Xuất file Excel 3 Sheets qua ExcelExporter
        return ExcelExporter.export_multi_source_report(
            df_comparison=df_comparison,
            df_cellphones=df_cellphones,
            df_hoangha=df_hoangha,
            output_excel_path=output_excel_path
        )
