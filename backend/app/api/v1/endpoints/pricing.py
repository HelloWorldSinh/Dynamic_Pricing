from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.pricing import PriceRecommendation, PricingAuditLog, PriceHistory
from app.models.product import Product
from app.models.inventory import InventoryMock
from app.models.sku_mapping import SkuMapping
from app.models.crawl_result import CrawlResult
from app.schemas.pricing import (
    GenerateRecommendationsRequest,
    PriceRecommendationResponse,
    PriceRecommendationListResponse,
    ApplyCustomPriceRequest,
    RecommendationActionRequest,
    PricingAuditLogResponse,
    PricingAuditLogListResponse,
    MatrixSimulationRequest,
    MatrixSimulationResponse,
    PriceComparisonItem,
    PriceChangeHistoryItem,
    CompetitorPriceInfo,
)
from app.services.pricing import PricingEngine
from app.services.pricing.schemas import SignalScores

router = APIRouter()
pricing_engine = PricingEngine()


def _normalize_weights(w: Optional[dict]) -> Optional[dict]:
    if not w:
        return None
    d = float(w.get("D", w.get("demand", 0.40)))
    i = float(w.get("I", w.get("inventory", 0.35)))
    c = float(w.get("C", w.get("competitor", 0.25)))
    return {"D": d, "I": i, "C": c}


@router.post(
    "/matrix/simulate",
    response_model=MatrixSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mo phong goi y gia theo ma tran tin hieu",
    description="Mo phong tinh toan de xuat gia theo cac tin hieu D, I, C va rao can an toan ma khong can ghi database.",
)
def simulate_matrix_pricing(
    request: MatrixSimulationRequest,
):
    """Mo phong tinh toan de xuat gia tuc thi phuc vu kiem thu ma tran."""
    norm_weights = _normalize_weights(request.weights)
    scores = SignalScores(
        demand_score=request.demand_score,
        inventory_score=request.inventory_score,
        competitor_score=request.competitor_score,
    )

    scenario_match = pricing_engine.scenario_matrix.evaluate(
        scores=scores,
        weights=norm_weights,
    )
    composite_score = pricing_engine.scenario_matrix.calculate_composite(
        scores=scores,
        weights=norm_weights,
    )

    guardrail_result = pricing_engine.guardrails.apply(
        current_price=request.current_price,
        target_delta_pct=scenario_match.target_delta_pct,
        floor_price=request.floor_price,
        cost_price=request.cost_price,
        competitor_price=request.competitor_price,
        max_rate_cap=request.max_rate_cap,
    )

    return MatrixSimulationResponse(
        demand_score=request.demand_score,
        inventory_score=request.inventory_score,
        competitor_score=request.competitor_score,
        composite_score=round(composite_score, 4),
        scenario_name=scenario_match.scenario_name,
        action_type=scenario_match.action_type,
        target_delta_pct=scenario_match.target_delta_pct,
        current_price=request.current_price,
        recommended_price=guardrail_result.final_price,
        price_delta_amount=guardrail_result.price_delta_amount,
        price_delta_pct=guardrail_result.price_delta_pct,
        is_floor_capped=guardrail_result.is_floor_capped,
        guardrail_notes=guardrail_result.guardrail_notes,
        rationale=scenario_match.rationale,
    )



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


def _enrich_recommendation(rec: PriceRecommendation, db: Session) -> PriceRecommendationResponse:
    prod = rec.product or db.query(Product).filter(Product.id == rec.fpt_product_id).first()
    inv = prod.inventory if prod else None
    if not inv and prod:
        inv = db.query(InventoryMock).filter(InventoryMock.fpt_product_id == prod.id).first()

    cost_price = int(prod.cost_price or (inv.cost_price if inv else 0) or 0) if prod else 0
    floor_price = int(prod.floor_price or (inv.floor_price if inv else 0) or 0) if prod else 0
    doh = inv.doh if inv and inv.doh is not None else 25
    stock_qty = inv.stock_quantity if inv and inv.stock_quantity is not None else 0

    cellphones_price = None
    cellphones_in_stock = True
    hoangha_price = None
    hoangha_in_stock = True
    comp_name = "CellphoneS"

    if prod:
        mappings = db.query(SkuMapping).filter(
            SkuMapping.fpt_product_id == prod.id,
            SkuMapping.status.in_(["APPROVED", "PENDING"])
        ).all()
        for m in mappings:
            c = m.crawl_result
            if c:
                if c.source.upper() == "CELLPHONES":
                    cellphones_price = int(c.current_price) if c.current_price else None
                    cellphones_in_stock = bool(c.is_in_stock)
                elif c.source.upper() == "HOANGHA":
                    hoangha_price = int(c.current_price) if c.current_price else None
                    hoangha_in_stock = bool(c.is_in_stock)

    if rec.competitor_min_price:
        if hoangha_price and hoangha_price == rec.competitor_min_price:
            comp_name = "Hoàng Hà Mobile"
        else:
            comp_name = "CellphoneS"

    margin_impact = round(float(rec.price_delta_pct) * 100, 2)

    return PriceRecommendationResponse(
        id=rec.id,
        fpt_product_id=rec.fpt_product_id,
        current_fpt_price=rec.current_fpt_price,
        competitor_min_price=rec.competitor_min_price,
        recommended_price=rec.recommended_price,
        price_delta_amount=rec.price_delta_amount,
        price_delta_pct=rec.price_delta_pct,
        demand_score=rec.demand_score,
        inventory_score=rec.inventory_score,
        competitor_score=rec.competitor_score,
        composite_score=rec.composite_score,
        scenario_name=rec.scenario_name,
        reasoning_3layers=rec.reasoning_3layers or {},
        is_floor_capped=rec.is_floor_capped,
        status=rec.status,
        reviewed_by=rec.reviewed_by,
        reviewed_at=rec.reviewed_at,
        rejection_reason=rec.rejection_reason,
        created_at=rec.created_at,
        sku=prod.sku if prod else "",
        product_name=prod.name if prod else "",
        category=prod.category if prod else "PHONE",
        brand=prod.brand if prod else "Khác",
        cost_price=cost_price,
        floor_price=floor_price,
        current_price=rec.current_fpt_price,
        suggested_price=rec.recommended_price,
        is_floor_protected=rec.is_floor_capped,
        doh=doh,
        inventory_quantity=stock_qty,
        min_competitor_price=rec.competitor_min_price or rec.current_fpt_price,
        competitor_name=comp_name,
        competitor_in_stock=True,
        cellphones_price=cellphones_price,
        cellphones_in_stock=cellphones_in_stock,
        hoangha_price=hoangha_price,
        hoangha_in_stock=hoangha_in_stock,
        scenario=rec.scenario_name,
        margin_impact_percent=margin_impact,
    )


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

    enriched_items = [_enrich_recommendation(rec, db) for rec in items]
    return PriceRecommendationListResponse(total=total, items=enriched_items)


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
    return _enrich_recommendation(rec, db)


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

    return _enrich_recommendation(rec, db)


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


@router.get(
    "/matrix",
    response_model=List[PriceComparisonItem],
    summary="Ma tran so sanh gia 3 ben",
    description="Truy van danh sach san pham FPT Shop kem gia doi thu CellphoneS va Hoang Ha cung thong tin ton kho.",
)
def get_pricing_matrix(
    category: Optional[str] = Query(None, description="Bo loc nganh hang: PHONE, LAPTOP, hoac ALL"),
    db: Session = Depends(get_db),
):
    """Truy van danh sach ma tran doi soat gia 3 ben."""
    query = db.query(Product).filter(Product.is_active == True)
    if category and category.upper() != "ALL":
        query = query.filter(Product.category == category.upper())
    products = query.all()

    result: List[PriceComparisonItem] = []
    for prod in products:
        inv = db.query(InventoryMock).filter(InventoryMock.fpt_product_id == prod.id).first()
        doh = inv.doh if inv and inv.doh is not None else 25
        stock_qty = inv.stock_quantity if inv and inv.stock_quantity is not None else 0

        mappings = db.query(SkuMapping).filter(
            SkuMapping.fpt_product_id == prod.id,
            SkuMapping.status.in_(["APPROVED", "PENDING"]),
        ).all()

        cellphones_info: Optional[CompetitorPriceInfo] = None
        hoangha_info: Optional[CompetitorPriceInfo] = None
        highest_conf = 0.0
        primary_match_tier = "EXACT_PART_NUMBER"

        comp_prices = []
        for m in mappings:
            c_res = m.crawl_result
            if not c_res:
                continue
            if m.confidence_score > highest_conf:
                highest_conf = m.confidence_score
                primary_match_tier = m.match_type

            c_info = CompetitorPriceInfo(
                source=c_res.source.upper(),
                price=int(c_res.current_price or 0),
                url=c_res.url or "",
                is_in_stock=bool(c_res.is_in_stock),
                product_name=c_res.raw_name,
                matched_at=m.matched_at.isoformat() if m.matched_at else None,
            )
            if c_res.source.upper() == "CELLPHONES":
                cellphones_info = c_info
            elif c_res.source.upper() == "HOANGHA":
                hoangha_info = c_info

            if c_res.current_price and c_res.current_price > 0:
                comp_prices.append(int(c_res.current_price))

        fpt_price = int(prod.base_retail_price or 0)
        min_comp_price = min(comp_prices) if comp_prices else fpt_price
        price_diff = fpt_price - min_comp_price
        diff_pct = round(((price_diff) / min_comp_price) * 100, 1) if min_comp_price > 0 else 0.0

        if min_comp_price == fpt_price and not comp_prices:
            st = "SAFE"
        elif fpt_price == min_comp_price:
            st = "EQUAL"
        elif fpt_price > min_comp_price:
            st = "DANGER"
        elif diff_pct > -5.0:
            st = "WARNING"
        else:
            st = "SAFE"

        item = PriceComparisonItem(
            id=str(prod.id),
            sku=prod.sku,
            name=prod.name,
            category=prod.category,
            brand=prod.brand or "Khac",
            part_number=prod.part_number,
            fpt_price=fpt_price,
            cellphones=cellphones_info,
            hoangha=hoangha_info,
            min_competitor_price=min_comp_price,
            price_diff=price_diff,
            price_diff_percent=diff_pct,
            confidence_score=round(highest_conf * 100, 1) if highest_conf else 100.0,
            match_tier=primary_match_tier,
            doh=doh,
            inventory_quantity=stock_qty,
            cost_price=int(prod.cost_price or 0),
            floor_price=int(prod.floor_price or 0),
            status=st,
        )
        result.append(item)

    return result


@router.get(
    "/history",
    response_model=List[PriceChangeHistoryItem],
    summary="Lich su thay doi gia",
    description="Tra cuu lich su cac lan dieu chinh gia da duoc ap dung hoac dong bo len he thong POS.",
)
def get_pricing_history(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Tra cuu lich su thay doi gia phuc vu Frontend."""
    histories = (
        db.query(PriceHistory)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(limit)
        .all()
    )
    result: List[PriceChangeHistoryItem] = []
    for h in histories:
        p = h.product
        if not p:
            continue
        old_price = int(p.base_retail_price or 0)
        new_price = int(h.price or 0)
        p_change = new_price - old_price
        p_pct = round((p_change / old_price) * 100, 1) if old_price > 0 else 0.0
        cost = int(p.cost_price or 0)
        margin = round(((new_price - cost) / new_price) * 100, 1) if new_price > 0 else 0.0

        item = PriceChangeHistoryItem(
            id=str(h.id),
            sku=p.sku,
            product_name=p.name,
            category=p.category,
            old_price=old_price,
            new_price=new_price,
            price_change=p_change,
            price_change_percent=p_pct,
            cost_price=cost,
            floor_price=int(p.floor_price or 0),
            margin_percent=margin,
            change_type="AI_RECOMMENDED",
            scenario="Dynamic Pricing Matrix Recommendation",
            changed_by="Pricing Engine",
            changed_at=h.recorded_at.isoformat(),
            status="SYNCED_POS",
        )
        result.append(item)
    return result


@router.post(
    "/recommendations/{id}/approve",
    response_model=PriceRecommendationResponse,
    summary="Phe duyet nhanh de xuat gia",
)
def quick_approve_recommendation(
    id: UUID,
    db: Session = Depends(get_db),
):
    """Endpoint tien ich cho phep phe duyet de xuat ma khong can body."""
    action_in = RecommendationActionRequest(
        action="APPROVE",
        reviewed_by="Pricing Analyst",
    )
    return action_recommendation(id=id, action_in=action_in, db=db)


@router.post(
    "/recommendations/{id}/reject",
    response_model=PriceRecommendationResponse,
    summary="Tu choi nhanh de xuat gia",
)
def quick_reject_recommendation(
    id: UUID,
    db: Session = Depends(get_db),
):
    """Endpoint tien ich cho phep tu choi de xuat gia nhanh."""
    action_in = RecommendationActionRequest(
        action="REJECT",
        reviewed_by="Pricing Analyst",
        rejection_reason="Chuyên viên từ chối áp dụng giá đề xuất",
    )
    return action_recommendation(id=id, action_in=action_in, db=db)


@router.post(
    "/recommendations/{id}/apply-custom",
    response_model=PriceRecommendationResponse,
    summary="Ap dung gia tuy bien cho san pham",
)
def apply_custom_price(
    id: UUID,
    custom_in: ApplyCustomPriceRequest,
    db: Session = Depends(get_db),
):
    """Ap dung muc gia do chuyen vien chi dinh, phe duyet de xuat va luu lich su gia."""
    rec = db.query(PriceRecommendation).filter(PriceRecommendation.id == id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price recommendation not found.",
        )

    old_price = rec.recommended_price
    rec.recommended_price = custom_in.custom_price
    rec.price_delta_amount = custom_in.custom_price - rec.current_fpt_price
    rec.price_delta_pct = round((rec.price_delta_amount / rec.current_fpt_price), 4) if rec.current_fpt_price > 0 else 0.0
    rec.status = "APPROVED"
    rec.reviewed_by = custom_in.reviewed_by
    rec.reviewed_at = datetime.now(timezone.utc)

    # Audit log
    audit_log = PricingAuditLog(
        actor=custom_in.reviewed_by,
        action="APPLY_CUSTOM_PRICE",
        entity_type="price_recommendations",
        entity_id=rec.id,
        old_value={"recommended_price": old_price, "status": "PENDING"},
        new_value={"recommended_price": rec.recommended_price, "status": "APPROVED", "change_type": custom_in.change_type},
    )
    db.add(audit_log)

    # Price history
    price_hist = PriceHistory(
        fpt_product_id=rec.fpt_product_id,
        source="FPTSHOP",
        price=custom_in.custom_price,
        is_in_stock=True,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(price_hist)
    db.commit()
    db.refresh(rec)
    return _enrich_recommendation(rec, db)

