from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.pricing import PriceRecommendation, PricingAuditLog
from app.schemas.pricing import (
    GenerateRecommendationsRequest,
    PriceRecommendationResponse,
    PriceRecommendationListResponse,
    RecommendationActionRequest,
    PricingAuditLogResponse,
    PricingAuditLogListResponse,
)
from app.services.pricing import PricingEngine

router = APIRouter()
pricing_engine = PricingEngine()


@router.post(
    "/recommendations/generate",
    response_model=PriceRecommendationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Sinh de xuat gia tu dong",
    description="Kich hoat Dynamic Pricing Engine de tinh toan va sinh de xuat gia cho mot san pham hoac toan bo san pham dang hoat dong.",
)
def generate_recommendations(
    request: GenerateRecommendationsRequest,
    db: Session = Depends(get_db),
):
    """Sinh de xuat gia cho mot san pham cu the hoac toan bo san pham active."""
    if request.fpt_product_id:
        try:
            rec = pricing_engine.generate_for_product(
                db=db,
                product_id=request.fpt_product_id,
                custom_weights=request.custom_weights,
            )
            return PriceRecommendationListResponse(total=1, items=[rec])
        except ValueError as e:
            err_msg = str(e)
            if "not found" in err_msg.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    items = pricing_engine.generate_batch(
        db=db,
        custom_weights=request.custom_weights,
    )
    return PriceRecommendationListResponse(total=len(items), items=items)


@router.get(
    "/recommendations",
    response_model=PriceRecommendationListResponse,
    summary="Danh sach de xuat gia",
    description="Tra cuu danh sach cac de xuat thay doi gia voi bo loc theo trang thai, kich ban, canh bao gia san va ho tro phan trang.",
)
def list_recommendations(
    status_filter: Optional[str] = Query(None, alias="status", description="Bo loc trang thai: PENDING, APPROVED, REJECTED"),
    scenario_name: Optional[str] = Query(None, description="Bo loc theo ten kich ban"),
    is_floor_capped: Optional[bool] = Query(None, description="Bo loc co canh bao cham gia san"),
    skip: int = Query(0, ge=0, description="So ban ghi bo qua"),
    limit: int = Query(50, ge=1, le=500, description="So ban ghi toi da tra ve"),
    db: Session = Depends(get_db),
):
    """Tra cuu danh sach de xuat gia kem bo loc va phan trang."""
    query = db.query(PriceRecommendation)

    if status_filter:
        query = query.filter(PriceRecommendation.status == status_filter.upper())

    if scenario_name:
        query = query.filter(PriceRecommendation.scenario_name == scenario_name)

    if is_floor_capped is not None:
        query = query.filter(PriceRecommendation.is_floor_capped == is_floor_capped)

    total = query.count()
    items = (
        query.order_by(PriceRecommendation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return PriceRecommendationListResponse(total=total, items=items)


@router.get(
    "/recommendations/{id}",
    response_model=PriceRecommendationResponse,
    summary="Chi tiet de xuat gia",
    description="Tra cuu thong tin chi tiet cua mot de xuat gia theo ID.",
)
def get_recommendation(
    id: UUID,
    db: Session = Depends(get_db),
):
    """Lay chi tiet mot de xuat gia theo ID."""
    rec = db.query(PriceRecommendation).filter(PriceRecommendation.id == id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price recommendation not found.",
        )
    return rec


@router.post(
    "/recommendations/{id}/action",
    response_model=PriceRecommendationResponse,
    summary="Phe duyet hoac tu choi de xuat gia",
    description="Thuc hien thao tac phe duyet (APPROVE) hoac tu choi (REJECT) de xuat gia va ghi nhat ky kiem toan.",
)
def action_recommendation(
    id: UUID,
    action_in: RecommendationActionRequest,
    db: Session = Depends(get_db),
):
    """Phe duyet hoac tu choi de xuat gia kem ghi nhat ky kiem toan."""
    rec = db.query(PriceRecommendation).filter(PriceRecommendation.id == id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price recommendation not found.",
        )

    action_norm = action_in.action.strip().upper()
    if action_norm not in ("APPROVE", "REJECT"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be APPROVE or REJECT.",
        )

    if rec.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recommendation has already been processed.",
        )

    old_status = rec.status
    if action_norm == "APPROVE":
        rec.status = "APPROVED"
    else:
        rec.status = "REJECTED"

    rec.reviewed_by = action_in.reviewed_by
    rec.reviewed_at = datetime.now(timezone.utc)
    rec.rejection_reason = action_in.rejection_reason

    audit_log = PricingAuditLog(
        actor=action_in.reviewed_by,
        action=f"{action_norm}_PRICE",
        entity_type="price_recommendations",
        entity_id=rec.id,
        old_value={"status": old_status},
        new_value={
            "status": rec.status,
            "rejection_reason": action_in.rejection_reason,
        },
    )
    db.add(audit_log)
    db.commit()
    db.refresh(rec)

    return rec


@router.get(
    "/audit-logs",
    response_model=PricingAuditLogListResponse,
    summary="Danh sach nhat ky kiem toan gia",
    description="Tra cuu lich su thao tac kiem toan cua chuyen vien gia voi bo loc theo actor, entity_id va phan trang.",
)
def list_audit_logs(
    entity_id: Optional[UUID] = Query(None, description="Bo loc theo ID ban ghi duoc kiem toan"),
    actor: Optional[str] = Query(None, description="Bo loc theo nguoi thao tac"),
    skip: int = Query(0, ge=0, description="So ban ghi bo qua"),
    limit: int = Query(50, ge=1, le=500, description="So ban ghi toi da tra ve"),
    db: Session = Depends(get_db),
):
    """Tra cuu danh sach nhat ky kiem toan gia."""
    query = db.query(PricingAuditLog)

    if entity_id:
        query = query.filter(PricingAuditLog.entity_id == entity_id)

    if actor:
        query = query.filter(PricingAuditLog.actor == actor)

    total = query.count()
    items = (
        query.order_by(PricingAuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return PricingAuditLogListResponse(total=total, items=items)
