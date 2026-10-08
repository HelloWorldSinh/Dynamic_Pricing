import pytest
from app.core.database import SessionLocal
from app.models import (
    Product,
    InventoryMock,
    SkuMapping,
    PriceRecommendation,
    PriceHistory,
)


def test_real_database_has_sufficient_records():
    """Kiem tra co so du lieu SQLite that da duoc nap du lieu hoat dong day du."""
    db = SessionLocal()
    try:
        product_count = db.query(Product).count()
        inventory_count = db.query(InventoryMock).count()
        mapping_count = db.query(SkuMapping).count()
        rec_count = db.query(PriceRecommendation).count()
        history_count = db.query(PriceHistory).count()

        assert product_count >= 300, f"Expected >= 300 products, got {product_count}"
        assert inventory_count >= 300, f"Expected >= 300 inventory items, got {inventory_count}"
        assert mapping_count >= 50, f"Expected >= 50 SKU mappings, got {mapping_count}"
        assert rec_count >= 200, f"Expected >= 200 price recommendations, got {rec_count}"
        assert history_count >= 5, f"Expected >= 5 price histories, got {history_count}"
    finally:
        db.close()
