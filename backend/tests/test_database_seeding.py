"""Tests for Database Ingestion and Seeding Engine (Task 1)."""

import pytest
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.inventory import Warehouse, InventoryMock, InventorySnapshot
from app.models.demand import DemandEvent
from app.services.seeder import seed_catalog_and_inventory


def test_seed_catalog_and_inventory(db_session: Session):
    """Kiểm thử hàm seed nạp đầy đủ danh mục FPT, kho hàng và tồn kho."""
    # Chạy hàm seed với sample limit để test nhanh
    counts = seed_catalog_and_inventory(db_session, limit=10)

    # 1. Kiểm tra bảng products
    assert counts["products"] == 10
    prods = db_session.query(Product).all()
    assert len(prods) == 10
    sample_prod = prods[0]
    assert sample_prod.sku.startswith("SKU")
    assert sample_prod.name != ""
    assert sample_prod.category in ["PHONE", "LAPTOP"]
    assert sample_prod.base_retail_price > 0
    assert sample_prod.cost_price > 0
    assert sample_prod.floor_price >= sample_prod.cost_price

    # 2. Kiểm tra bảng warehouses
    whs = db_session.query(Warehouse).all()
    assert len(whs) >= 3

    # 3. Kiểm tra bảng inventory_mock
    invs = db_session.query(InventoryMock).all()
    assert len(invs) > 0

    # 4. Kiểm tra bảng demand_events
    events = db_session.query(DemandEvent).all()
    assert len(events) > 0
