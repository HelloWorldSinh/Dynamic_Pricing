"""Database Seeder Service: Ingests ground truth catalogs and operational snapshots into SQLite."""

import os
import logging
import uuid
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Warehouse, InventoryMock, InventorySnapshot
from app.models.demand import DemandEvent
from app.services.matching.feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = BACKEND_DIR / "data"


def safe_parse_price(val: Any) -> Optional[int]:
    """Parse an toàn giá từ ô Excel."""
    if pd.isna(val) or val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            v = int(val)
            return v if v > 0 else None
        s = str(val).replace(",", "").strip()
        v = int(float(s))
        return v if v > 0 else None
    except Exception:
        return None


def safe_int(val: Any, default: int = 0) -> int:
    """Chuyển đổi an toàn giá trị pandas sang int (xử lý float NaN)."""
    if pd.isna(val) or val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: float = 0.0) -> float:
    """Chuyển đổi an toàn giá trị pandas sang float (xử lý float NaN)."""
    if pd.isna(val) or val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def seed_catalog_and_inventory(
    db: Session,
    data_dir: Optional[Path] = None,
    limit: Optional[int] = None,
) -> Dict[str, int]:
    """Nạp danh mục sản phẩm chuẩn FPT, kho hàng, tồn kho và sự kiện nhu cầu vào CSDL."""
    d_dir = data_dir or DEFAULT_DATA_DIR

    dim_product_path = d_dir / "dim_product.xlsx"
    mapping_output_path = d_dir / "crawl_and_sku_mapping_output.xlsx"
    inv_snapshot_path = d_dir / "inventory_snapshot_20260723.xlsx"
    demand_events_path = d_dir / "demand_events_20260723.xlsx"

    counts = {
        "warehouses": 0,
        "products": 0,
        "inventory_snapshots": 0,
        "inventory_mock": 0,
        "demand_events": 0,
    }

    # 1. Khởi tạo Warehouses
    warehouses_data = [
        {"id": "WH-HN-01", "name": "Tổng kho Miền Bắc (Hà Nội)", "region": "NORTH"},
        {"id": "WH-HCM-01", "name": "Tổng kho Miền Nam (TP.HCM)", "region": "SOUTH"},
        {"id": "WH-DN-01", "name": "Tổng kho Miền Trung (Đà Nẵng)", "region": "CENTRAL"},
    ]
    for wh_info in warehouses_data:
        existing_wh = db.query(Warehouse).filter(Warehouse.warehouse_id == wh_info["id"]).first()
        if not existing_wh:
            wh = Warehouse(
                warehouse_id=wh_info["id"],
                warehouse_name=wh_info["name"],
                region=wh_info["region"],
            )
            db.add(wh)
            counts["warehouses"] += 1
    db.flush()

    # 2. Đọc giá tham chiếu FPT
    fpt_prices: Dict[str, int] = {}
    if os.path.exists(mapping_output_path):
        try:
            df_map = pd.read_excel(mapping_output_path)
            for _, r in df_map.iterrows():
                s_id = str(r.get("Mã SKU FPT", "")).strip()
                p_val = r.get("Giá tham chiếu FPT (VND)")
                p = safe_parse_price(p_val)
                if s_id and p:
                    fpt_prices[s_id] = p
        except Exception as e:
            logger.warning(f"Lỗi đọc file crawl_and_sku_mapping_output: {e}")

    # Fallback giá từ demand_events nếu thiếu
    if os.path.exists(demand_events_path) and len(fpt_prices) < 300:
        try:
            df_dem = pd.read_excel(demand_events_path)
            dem_prices = df_dem.groupby("sku_id")["price_at_event"].median().astype(int).to_dict()
            for k, v in dem_prices.items():
                if k not in fpt_prices and v > 0:
                    fpt_prices[k] = v
        except Exception as e:
            logger.warning(f"Lỗi đọc giá từ demand_events: {e}")

    # 3. Nạp danh mục Products (329 SKU)
    if not os.path.exists(dim_product_path):
        raise FileNotFoundError(f"Không tìm thấy file danh mục sản phẩm: {dim_product_path}")

    df_dim = pd.read_excel(dim_product_path)
    if limit:
        df_dim = df_dim.head(limit)

    product_map: Dict[str, Product] = {}
    for _, row in df_dim.iterrows():
        sku_id = str(row["sku_id"]).strip()
        sku_name = str(row["sku_name"]).strip()

        # Bóc tách cấu hình kỹ thuật
        features = FeatureExtractor.extract_features(sku_id=sku_id, sku_name=sku_name)
        name_lower = sku_name.lower()
        brand = features.brand or "Khác"
        category = "LAPTOP" if any(w in name_lower for w in ["laptop", "macbook", "notebook", "vivobook", "aspire", "nitro"]) else "PHONE"
        part_number = features.parts[0] if features.parts else None

        # Giá tham chiếu
        base_price = fpt_prices.get(sku_id, 20_000_000)
        cost_price = int(base_price * 0.85)
        floor_price = int(cost_price * 1.05)

        existing_prod = db.query(Product).filter(Product.sku == sku_id).first()
        if existing_prod:
            existing_prod.name = sku_name
            existing_prod.category = category
            existing_prod.brand = brand
            existing_prod.part_number = part_number
            existing_prod.base_retail_price = base_price
            existing_prod.cost_price = cost_price
            existing_prod.floor_price = floor_price
            existing_prod.specs = features.to_dict()
            product_map[sku_id] = existing_prod
        else:
            new_prod = Product(
                sku=sku_id,
                name=sku_name,
                category=category,
                brand=brand,
                part_number=part_number,
                base_retail_price=base_price,
                cost_price=cost_price,
                floor_price=floor_price,
                min_margin_pct=5.0,
                specs=features.to_dict(),
                is_active=True,
            )
            db.add(new_prod)
            product_map[sku_id] = new_prod
            counts["products"] += 1

    db.flush()

    # 4. Nạp Inventory Snapshots & Inventory Mock
    if os.path.exists(inv_snapshot_path):
        df_inv = pd.read_excel(inv_snapshot_path)
        valid_whs = {"WH-HN-01", "WH-HCM-01", "WH-DN-01"}

        for sku_id, prod in product_map.items():
            sku_inv_rows = df_inv[df_inv["sku_id"] == sku_id]
            if sku_inv_rows.empty:
                # Tạo mock tồn kho cơ bản nếu không có snapshot
                existing_mock = db.query(InventoryMock).filter(InventoryMock.fpt_product_id == prod.id).first()
                if not existing_mock:
                    inv_mock = InventoryMock(
                        fpt_product_id=prod.id,
                        stock_quantity=50,
                        doh=25,
                        cost_price=prod.cost_price,
                        floor_price=prod.floor_price,
                    )
                    db.add(inv_mock)
                    counts["inventory_mock"] += 1
                continue

            # Nạp snapshots
            total_qty = 0
            doh_list = []
            for _, i_row in sku_inv_rows.iterrows():
                wh_id = str(i_row.get("warehouse_id", "WH-HN-01")).strip()
                if wh_id not in valid_whs:
                    wh_id = "WH-HN-01"

                qty_avail = safe_int(i_row.get("qty_available"), 0)
                doh_val = safe_int(i_row.get("stock_cover_days"), 30)
                total_qty += qty_avail
                doh_list.append(doh_val)

                existing_snap = db.query(InventorySnapshot).filter(
                    InventorySnapshot.fpt_product_id == prod.id,
                    InventorySnapshot.warehouse_id == wh_id,
                ).first()
                if not existing_snap:
                    snap = InventorySnapshot(
                        fpt_product_id=prod.id,
                        warehouse_id=wh_id,
                        qty_on_hand=safe_int(i_row.get("qty_on_hand"), qty_avail),
                        qty_reserved=safe_int(i_row.get("qty_reserved"), 0),
                        qty_available=qty_avail,
                        target_stock=safe_int(i_row.get("target_stock"), 50),
                        safety_stock=safe_int(i_row.get("safety_stock"), 10),
                        reorder_level=safe_int(i_row.get("reorder_level"), 15),
                        stock_cover_days=doh_val,
                        is_obsolescence_risk=bool(i_row.get("is_obsolescence_risk", False)),
                        holding_cost_pct_monthly=safe_float(i_row.get("holding_cost_pct_monthly"), 1.5),
                        competitor_oos_count=safe_int(i_row.get("competitor_oos_count"), 0),
                    )
                    db.add(snap)
                    counts["inventory_snapshots"] += 1

            # Nạp hoặc cập nhật InventoryMock tổng hợp
            avg_doh = int(sum(doh_list) / len(doh_list)) if doh_list else 25
            existing_mock = db.query(InventoryMock).filter(InventoryMock.fpt_product_id == prod.id).first()
            if existing_mock:
                existing_mock.stock_quantity = total_qty
                existing_mock.doh = avg_doh
                existing_mock.cost_price = prod.cost_price
                existing_mock.floor_price = prod.floor_price
            else:
                inv_mock = InventoryMock(
                    fpt_product_id=prod.id,
                    stock_quantity=total_qty,
                    doh=avg_doh,
                    cost_price=prod.cost_price,
                    floor_price=prod.floor_price,
                )
                db.add(inv_mock)
                counts["inventory_mock"] += 1

    db.flush()

    # 5. Nạp Demand Events
    if os.path.exists(demand_events_path):
        existing_evt_ids = {r[0] for r in db.query(DemandEvent.event_id).all()}
        df_dem = pd.read_excel(demand_events_path)
        for sku_id, prod in product_map.items():
            sku_dem_rows = df_dem[df_dem["sku_id"] == sku_id]
            if sku_dem_rows.empty:
                continue

            for _, d_row in sku_dem_rows.head(20).iterrows():
                e_id = str(d_row.get("event_id") or uuid.uuid4())
                if e_id in existing_evt_ids:
                    continue

                event_ts_val = d_row.get("event_ts")
                event_ts = datetime.utcnow()
                if pd.notna(event_ts_val):
                    try:
                        event_ts = pd.to_datetime(event_ts_val).to_pydatetime()
                    except Exception:
                        pass

                evt = DemandEvent(
                    event_id=e_id,
                    fpt_product_id=prod.id,
                    session_id=str(d_row.get("session_id") or "sess_default"),
                    user_id=str(d_row.get("user_id") or "usr_default"),
                    event_type=str(d_row.get("event_type") or "view"),
                    is_bounce=bool(d_row.get("is_bounce", False)),
                    is_repeat_view=bool(d_row.get("is_repeat_view", False)),
                    time_on_page_sec=safe_int(d_row.get("time_on_page_sec"), 60),
                    scroll_depth_pct=safe_int(d_row.get("scroll_depth_pct"), 50),
                    cart_action=str(d_row.get("cart_action")) if pd.notna(d_row.get("cart_action")) else None,
                    event_ts=event_ts,
                )
                db.add(evt)
                existing_evt_ids.add(e_id)
                counts["demand_events"] += 1

    db.commit()
    return counts
