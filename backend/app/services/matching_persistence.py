"""Service for running Two-Tiered SKU Matching and persisting results into sku_mappings."""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.services.matching.feature_extractor import FeatureExtractor
from app.services.matching.sku_index import SkuIndex
from app.services.matching.matching_engine import MatchingEngine
from app.services.matching.models import MatchStatus, SkuFeatures, MatchResult

logger = logging.getLogger(__name__)


def run_sku_matching_and_persist(
    db: Session,
    batch_size: Optional[int] = None,
    overwrite_existing: bool = False,
) -> int:
    """So khớp danh mục FPT (Master List) với các sản phẩm cào đối thủ trong crawl_results.
    
    Quy trình FPT Master Loop:
    1. Duyệt qua từng sản phẩm chuẩn FPT (Product).
    2. Đối soát với tập crawl_results của đối thủ theo thuật toán 2 tầng.
    3. Chọn sản phẩm đối thủ tốt nhất (Best Match) cho từng nguồn đối thủ (CELLPHONES, HOANGHA).
    4. Lưu vào bảng sku_mappings.
    
    Args:
        db: SQLAlchemy session
        batch_size: Giới hạn số lượng crawl_results cần xử lý (None = tất cả)
        overwrite_existing: Nếu True, xóa các mapping cũ trước khi chạy lại
        
    Returns:
        Số lượng sku_mappings mới được tạo và lưu thành công
    """
    # 1. Nạp danh mục products từ DB và lập SkuIndex
    products = db.query(Product).all()
    if not products:
        logger.warning("Không có sản phẩm nào trong bảng products để thực hiện đối soát.")
        return 0

    sku_to_prod_id: Dict[str, Any] = {}
    fpt_prices: Dict[str, int] = {}
    parsed_skus: List[SkuFeatures] = []

    for prod in products:
        sku_to_prod_id[prod.sku] = prod.id
        fpt_prices[prod.sku] = prod.base_retail_price or 0
        features = FeatureExtractor.extract_features(sku_id=prod.sku, sku_name=prod.name)
        parsed_skus.append(features)

    sku_index = SkuIndex()
    sku_index.build_index(parsed_skus)
    engine = MatchingEngine(sku_index)

    # 2. Xử lý ghi đè nếu yêu cầu
    if overwrite_existing:
        db.query(SkuMapping).delete()
        db.flush()

    # 3. Lấy danh sách crawl_results cần so khớp
    existing_mapped_crawl_ids = set()
    if not overwrite_existing:
        existing_rows = db.query(SkuMapping.competitor_crawl_id).all()
        existing_mapped_crawl_ids = {r[0] for r in existing_rows}

    crawl_query = db.query(CrawlResult)
    if existing_mapped_crawl_ids:
        crawl_query = crawl_query.filter(~CrawlResult.id.in_(existing_mapped_crawl_ids))

    if batch_size:
        crawl_query = crawl_query.limit(batch_size)

    crawl_items = crawl_query.all()
    if not crawl_items:
        logger.info("Không có crawl_results mới nào cần so khớp.")
        return 0

    # 4. Gom nhóm crawl_items theo Brand để tối ưu tốc độ tìm kiếm
    brand_to_crawls = defaultdict(list)
    for crawl_item in crawl_items:
        if not crawl_item.raw_name:
            continue
        c_brand = FeatureExtractor.detect_brand(crawl_item.raw_name)
        brand_to_crawls[c_brand].append(crawl_item)

    # 5. FPT Master Loop: Duyệt qua từng sản phẩm FPT
    created_count = 0
    assigned_crawl_ids = set()

    for prod_feat in parsed_skus:
        prod_id = sku_to_prod_id.get(prod_feat.sku_id)
        if not prod_id:
            continue

        # Lấy các crawl_items cùng Brand (hoặc fallback nếu không xác định brand)
        relevant_crawls = brand_to_crawls.get(prod_feat.brand, [])
        if not relevant_crawls and not prod_feat.brand:
            relevant_crawls = crawl_items

        # Tìm best match cho từng nguồn đối thủ (CELLPHONES, HOANGHA...)
        best_by_source: Dict[str, Tuple[CrawlResult, MatchResult]] = {}

        for crawl_item in relevant_crawls:
            if crawl_item.id in assigned_crawl_ids:
                continue

            match_res = engine.match_single_item(
                scraped_name=crawl_item.raw_name,
                competitor_price=crawl_item.current_price,
                fpt_prices=fpt_prices,
            )

            # Chỉ chấp nhận nếu khớp đúng mã SKU của sản phẩm FPT này
            if (
                match_res.status in [MatchStatus.APPROVED, MatchStatus.PENDING]
                and match_res.fpt_sku_id == prod_feat.sku_id
            ):
                source = crawl_item.source or "COMPETITOR"
                conf = float(match_res.confidence_score)
                status = match_res.status

                should_replace = False
                if source not in best_by_source:
                    should_replace = True
                else:
                    _, curr_res = best_by_source[source]
                    curr_status = curr_res.status
                    curr_conf = float(curr_res.confidence_score)

                    if status == MatchStatus.APPROVED and curr_status != MatchStatus.APPROVED:
                        should_replace = True
                    elif status == curr_status and conf > curr_conf:
                        should_replace = True

                if should_replace:
                    best_by_source[source] = (crawl_item, match_res)

        # Lưu các best matches vào Database
        for source, (crawl_item, match_res) in best_by_source.items():
            mapping = SkuMapping(
                id=uuid.uuid4(),
                fpt_product_id=prod_id,
                competitor_crawl_id=crawl_item.id,
                match_type=match_res.match_type,
                confidence_score=round(float(match_res.confidence_score), 4),
                status=match_res.status,
                matched_at=datetime.utcnow(),
            )
            db.add(mapping)
            assigned_crawl_ids.add(crawl_item.id)
            created_count += 1

    db.commit()
    logger.info(f"Đã so khớp FPT Master và lưu thành công {created_count} cặp SKU vào sku_mappings.")
    return created_count
