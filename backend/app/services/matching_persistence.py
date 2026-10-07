"""Service for running Two-Tiered SKU Matching and persisting results into sku_mappings."""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.sku_mapping import SkuMapping
from app.services.matching.feature_extractor import FeatureExtractor
from app.services.matching.sku_index import SkuIndex
from app.services.matching.matching_engine import MatchingEngine
from app.services.matching.models import MatchStatus, SkuFeatures

logger = logging.getLogger(__name__)


def run_sku_matching_and_persist(
    db: Session,
    batch_size: Optional[int] = None,
    overwrite_existing: bool = False,
) -> int:
    """So khớp các sản phẩm cào đối thủ trong crawl_results với products và lưu vào sku_mappings.
    
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

    created_count = 0
    for crawl_item in crawl_items:
        if not crawl_item.raw_name:
            continue

        match_res = engine.match_single_item(
            scraped_name=crawl_item.raw_name,
            competitor_price=crawl_item.current_price,
            fpt_prices=fpt_prices,
        )

        if match_res.status in [MatchStatus.APPROVED, MatchStatus.PENDING] and match_res.fpt_sku_id:
            prod_id = sku_to_prod_id.get(match_res.fpt_sku_id)
            if prod_id:
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
                created_count += 1

    db.commit()
    logger.info(f"Đã so khớp và lưu thành công {created_count} cặp SKU vào sku_mappings.")
    return created_count
