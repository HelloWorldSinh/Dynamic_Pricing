"""Service thực hiện ghép cặp sản phẩm cào về với danh mục chuẩn FPT Shop (SKU Matching Engine).

Áp dụng Kiến trúc Phân tầng (Clean Architecture) với Facade Pattern:
- app.services.matching.models: Quản lý cấu trúc dữ liệu SkuFeatures, MatchResult
- app.services.matching.feature_extractor: Bóc tách Brand, Part-Number (kèm Blacklist), RAM/ROM, Model ID
- app.services.matching.sku_index: Inverted Index tra cứu Part-Number O(1) và Brand Bucketing
- app.services.matching.matching_engine: Thuật toán so khớp 2 tầng và tính điểm độ tin cậy
"""

import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

from app.utils.excel_exporter import ExcelExporter
from app.services.matching.models import MatchResult, SkuFeatures, MatchStatus, MatchType
from app.services.matching.feature_extractor import FeatureExtractor
from app.services.matching.sku_index import SkuIndex
from app.services.matching.matching_engine import MatchingEngine

logger = logging.getLogger(__name__)


class SkuMatcher:
    """Facade Service thực hiện ghép cặp sản phẩm cào về với danh mục chuẩn FPT Shop.
    Giữ nguyên 100% giao diện công khai để đảm bảo tương thích ngược cho toàn bộ pipeline.
    """

    # Ánh xạ hằng số từ FeatureExtractor & MatchingEngine
    BRAND_MAP = FeatureExtractor.BRAND_MAP
    LAPTOP_LINES = FeatureExtractor.LAPTOP_LINES

    CONFIDENCE_EXACT = MatchingEngine.CONFIDENCE_EXACT
    CONFIDENCE_APPROVED_THRESHOLD = MatchingEngine.CONFIDENCE_APPROVED_THRESHOLD
    CONFIDENCE_MIN_THRESHOLD = MatchingEngine.CONFIDENCE_MIN_THRESHOLD
    CONFIDENCE_PENDING_CEILING = MatchingEngine.CONFIDENCE_PENDING_CEILING

    # Forwarding các static/class methods sang FeatureExtractor
    detect_brand = FeatureExtractor.detect_brand
    extract_part_numbers = FeatureExtractor.extract_part_numbers
    clean_product_name = FeatureExtractor.clean_product_name
    extract_storage = FeatureExtractor.extract_storage
    extract_ram = FeatureExtractor.extract_ram
    extract_model_identifier = FeatureExtractor.extract_model_identifier
    extract_color = FeatureExtractor.extract_color

    def __init__(
        self,
        dim_product_path: str = "data/dim_product.xlsx",
        demand_events_path: str = "data/demand_events_20260723.xlsx"
    ):
        self.dim_product_path = dim_product_path
        self.demand_events_path = demand_events_path
        self.df_dim = pd.DataFrame()
        self.fpt_prices: Dict[str, int] = {}
        self.parsed_dim_skus: List[SkuFeatures] = []

        self.sku_index = SkuIndex()
        self.engine = MatchingEngine(self.sku_index)

        self._load_data()

    def _load_data(self) -> None:
        """Nạp danh mục sản phẩm chuẩn FPT, giá tham chiếu và tiền xử lý (precompute)."""
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
        """Tiền xử lý và lập Inverted Index tra cứu O(1) cho toàn bộ danh mục FPT Shop."""
        self.parsed_dim_skus = []
        for _, row in self.df_dim.iterrows():
            sku_id = str(row["sku_id"])
            sku_name = str(row["sku_name"])
            features = FeatureExtractor.extract_features(sku_id=sku_id, sku_name=sku_name)
            self.parsed_dim_skus.append(features)

        # Cập nhật Inverted Index và Engine
        self.sku_index.build_index(self.parsed_dim_skus)
        self.engine = MatchingEngine(self.sku_index)

    def match_single_item(
        self,
        scraped_name: str,
        competitor_price: Optional[int] = None
    ) -> MatchResult:
        """Thực hiện ghép cặp 1 sản phẩm cào về thông qua MatchingEngine."""
        return self.engine.match_single_item(
            scraped_name=scraped_name,
            competitor_price=competitor_price,
            fpt_prices=self.fpt_prices
        )

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
                if match_res["status"] in [MatchStatus.APPROVED, MatchStatus.PENDING]:
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
                sku_id = item.sku_id
                sku_name = item.sku_name
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
                        "Loại khớp (Match Type)": MatchType.NOT_FOUND,
                        "Độ tin cậy (Confidence)": 0.0,
                        "Trạng thái (Status)": MatchStatus.NOT_FOUND,
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
        """So khớp dữ liệu từ cả 2 nguồn (CellphoneS & Hoàng Hà Mobile) với danh mục chuẩn FPT Shop."""
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

                if status in [MatchStatus.APPROVED, MatchStatus.PENDING]:
                    fpt_sku = match_res["fpt_sku_id"]
                    conf = match_res["confidence_score"]

                    should_replace = False
                    if fpt_sku not in mapping:
                        should_replace = True
                    else:
                        curr_status = mapping[fpt_sku]["match_res"]["status"]
                        curr_conf = mapping[fpt_sku]["confidence"]
                        if status == MatchStatus.APPROVED and curr_status != MatchStatus.APPROVED:
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
            sku_id = item.sku_id
            sku_name = item.sku_name
            fpt_ref_price = self.fpt_prices.get(sku_id)

            # Dữ liệu CellphoneS
            cps_data = fpt_to_cps.get(sku_id)
            cps_name = cps_data["name"] if cps_data else "N/A"
            cps_price = cps_data["price"] if cps_data else "N/A"
            cps_stock = cps_data["stock"] if cps_data else "N/A"
            cps_conf = cps_data["confidence"] if cps_data else 0.0
            cps_status = cps_data["match_res"]["status"] if cps_data else MatchStatus.NOT_FOUND
            cps_url = cps_data["url"] if cps_data else "N/A"

            # Dữ liệu Hoàng Hà
            hh_data = fpt_to_hh.get(sku_id)
            hh_name = hh_data["name"] if hh_data else "N/A"
            hh_price = hh_data["price"] if hh_data else "N/A"
            hh_stock = hh_data["stock"] if hh_data else "N/A"
            hh_conf = hh_data["confidence"] if hh_data else 0.0
            hh_status = hh_data["match_res"]["status"] if hh_data else MatchStatus.NOT_FOUND
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

        # 5. Xuất file Excel 3 Sheets qua ExcelExporter
        return ExcelExporter.export_multi_source_report(
            df_comparison=df_comparison,
            df_cellphones=df_cellphones,
            df_hoangha=df_hoangha,
            output_excel_path=output_excel_path
        )
