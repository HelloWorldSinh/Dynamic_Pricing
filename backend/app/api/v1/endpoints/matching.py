from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.sku_mapping import SkuMapping
from app.models.product import Product
from app.models.crawl_result import CrawlResult
from app.models.pricing import PricingAuditLog
from app.schemas.matching import SkuMappingPairResponse, SkuMatchingStatsResponse
from app.services.matching.feature_extractor import FeatureExtractor

router = APIRouter()


@router.get(
    "/stats",
    response_model=SkuMatchingStatsResponse,
    summary="Thống kê tổng quan tỷ lệ ghép cặp SKU",
    description="Tra cứu tổng số SKU đang kinh doanh, số lượng SKU đã được đối soát duyệt thành công và tỷ lệ ghép cặp.",
)
def get_matching_stats(db: Session = Depends(get_db)):
    """Thống kê tổng quan tỷ lệ ghép cặp SKU FPT với dữ liệu đối thủ."""
    total_skus = db.query(Product).filter(Product.is_active == True).count()

    matched_skus = (
        db.query(SkuMapping.fpt_product_id)
        .join(Product, SkuMapping.fpt_product_id == Product.id)
        .filter(Product.is_active == True, SkuMapping.status == "APPROVED")
        .distinct()
        .count()
    )

    match_rate = round((matched_skus / total_skus * 100), 1) if total_skus > 0 else 0.0

    pending_count = db.query(SkuMapping).filter(SkuMapping.status == "PENDING").count()
    approved_count = db.query(SkuMapping).filter(SkuMapping.status == "APPROVED").count()
    rejected_count = db.query(SkuMapping).filter(SkuMapping.status == "REJECTED").count()

    return SkuMatchingStatsResponse(
        total_skus=total_skus,
        matched_skus=matched_skus,
        match_rate=match_rate,
        pending_queue_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
    )



def _to_pair_response(mapping: SkuMapping) -> SkuMappingPairResponse:
    prod = mapping.product
    crawl = mapping.crawl_result

    fpt_sku = prod.sku if prod else ""
    fpt_name = prod.name if prod else ""
    fpt_part = prod.part_number if prod else None
    fpt_price = int(prod.base_retail_price or 0) if prod else 0

    comp_source = crawl.source.upper() if crawl else "CELLPHONES"
    comp_name = crawl.raw_name if crawl else ""
    comp_url = crawl.url if crawl else ""
    comp_price = int(crawl.current_price or 0) if crawl else 0

    # Extract comparison attributes
    matched_attrs: List[str] = []
    differing_attrs: List[str] = []

    if prod and crawl:
        prod_feat = FeatureExtractor.extract_features(prod.sku, prod.name)
        crawl_feat = FeatureExtractor.extract_features("crawl", crawl.raw_name)

        if prod_feat.brand and crawl_feat.brand and prod_feat.brand.lower() == crawl_feat.brand.lower():
            matched_attrs.append(f"brand: {prod_feat.brand.upper()}")
        elif prod_feat.brand or crawl_feat.brand:
            differing_attrs.append(f"brand: {prod_feat.brand or 'N/A'} vs {crawl_feat.brand or 'N/A'}")

        prod_ram = prod_feat.ram[0] if prod_feat.ram else None
        crawl_ram = crawl_feat.ram[0] if crawl_feat.ram else None
        if prod_ram and crawl_ram and prod_ram.lower() == crawl_ram.lower():
            matched_attrs.append(f"ram: {prod_ram.upper()}")
        elif prod_ram or crawl_ram:
            differing_attrs.append(f"ram: {prod_ram or 'N/A'} vs {crawl_ram or 'N/A'}")

        prod_rom = prod_feat.rom[0] if prod_feat.rom else None
        crawl_rom = crawl_feat.rom[0] if crawl_feat.rom else None
        if prod_rom and crawl_rom and prod_rom.lower() == crawl_rom.lower():
            matched_attrs.append(f"storage: {prod_rom.upper()}")
        elif prod_rom or crawl_rom:
            differing_attrs.append(f"storage: {prod_rom or 'N/A'} vs {crawl_rom or 'N/A'}")

        if not matched_attrs:
            matched_attrs.append(f"match_type: {mapping.match_type}")
        if not differing_attrs and prod.name != crawl.raw_name:
            differing_attrs.append(f"naming: {prod.name[:25]}... vs {crawl.raw_name[:25]}...")

    conf = float(mapping.confidence_score)
    if conf <= 1.0:
        conf = round(conf * 100, 1)
    else:
        conf = round(conf, 1)

    return SkuMappingPairResponse(
        id=str(mapping.id),
        fpt_sku=fpt_sku,
        fpt_name=fpt_name,
        fpt_part_number=fpt_part,
        fpt_price=fpt_price,
        competitor_source=comp_source,
        competitor_name=comp_name,
        competitor_url=comp_url,
        competitor_price=comp_price,
        competitor_part_number=None,
        confidence_score=conf,
        matched_attributes=matched_attrs,
        differing_attributes=differing_attrs,
        status=mapping.status,
    )


@router.get(
    "/queue",
    response_model=List[SkuMappingPairResponse],
    summary="Danh sach hang doi doi soat SKU",
    description="Tra cuu danh sach cac cap doi soat co do tin cay tu 60% den 79% cho chuyen vien duyet.",
)
def get_mapping_queue(
    status_filter: str = Query("PENDING", alias="status", description="Bo loc trang thai: PENDING, APPROVED, REJECTED, ALL"),
    skip: int = Query(0, ge=0, description="So ban ghi bo qua"),
    limit: int = Query(50, ge=1, le=500, description="So ban ghi toi da tra ve"),
    db: Session = Depends(get_db),
):
    """Truy van danh sach cap doi soat SKU theo trang thai."""
    query = db.query(SkuMapping)
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(SkuMapping.status == status_filter.upper())

    mappings = (
        query.order_by(SkuMapping.matched_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [_to_pair_response(m) for m in mappings]


@router.post(
    "/queue/{id}/approve",
    response_model=SkuMappingPairResponse,
    summary="Phe duyet cap doi soat SKU",
)
def approve_mapping_pair(
    id: UUID,
    db: Session = Depends(get_db),
):
    """Phe duyet cap doi soat SKU tu PENDING sang APPROVED."""
    mapping = db.query(SkuMapping).filter(SkuMapping.id == id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU mapping pair not found.",
        )

    old_status = mapping.status
    mapping.status = "APPROVED"

    audit_log = PricingAuditLog(
        actor="Pricing Analyst",
        action="APPROVE_MAPPING",
        entity_type="sku_mappings",
        entity_id=mapping.id,
        old_value={"status": old_status},
        new_value={"status": "APPROVED"},
    )
    db.add(audit_log)
    db.commit()
    db.refresh(mapping)
    return _to_pair_response(mapping)


@router.post(
    "/queue/{id}/reject",
    response_model=SkuMappingPairResponse,
    summary="Tu choi cap doi soat SKU",
)
def reject_mapping_pair(
    id: UUID,
    db: Session = Depends(get_db),
):
    """Tu choi cap doi soat SKU tu PENDING sang REJECTED."""
    mapping = db.query(SkuMapping).filter(SkuMapping.id == id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU mapping pair not found.",
        )

    old_status = mapping.status
    mapping.status = "REJECTED"

    audit_log = PricingAuditLog(
        actor="Pricing Analyst",
        action="REJECT_MAPPING",
        entity_type="sku_mappings",
        entity_id=mapping.id,
        old_value={"status": old_status},
        new_value={"status": "REJECTED"},
    )
    db.add(audit_log)
    db.commit()
    db.refresh(mapping)
    return _to_pair_response(mapping)
