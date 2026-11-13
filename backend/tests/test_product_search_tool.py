import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.product import Product
from app.models.inventory import InventoryMock
from app.services.ai.gemini_client import GeminiClient, TOOL_DECLARATIONS
from app.services.ai.tools import search_products


def test_search_products_declaration_exists():
    """Kiểm tra tool search_products đã được khai báo chính xác trong TOOL_DECLARATIONS."""
    tool_names = [t.get("name") for t in TOOL_DECLARATIONS]
    assert "search_products" in tool_names

    search_tool = next(t for t in TOOL_DECLARATIONS if t.get("name") == "search_products")
    props = search_tool["parameters"]["properties"]
    assert "query" in props
    assert "category" in props
    assert "brand" in props
    assert "limit" in props
    assert "query" in search_tool["parameters"]["required"]


def test_search_products_by_name_and_sku(db_session: Session):
    """Kiểm tra tìm kiếm sản phẩm theo tên và mã SKU trong CSDL."""
    # 1. Tạo sản phẩm mẫu trong db_session
    prod = Product(
        sku="FPT-ASUS-ZEN14-TEST",
        name="Laptop ASUS Zenbook 14 OLED UX3405",
        category="LAPTOP",
        brand="ASUS",
        part_number="UX3405MA",
        base_retail_price=27990000,
        cost_price=24000000,
        floor_price=25000000,
    )
    db_session.add(prod)
    db_session.flush()

    inv = InventoryMock(
        fpt_product_id=prod.id,
        stock_quantity=15,
        doh=28,
        cost_price=24000000,
        floor_price=25000000,
    )
    db_session.add(inv)
    db_session.commit()

    # 2. Tìm kiếm theo tên sản phẩm
    results_by_name = search_products(db=db_session, query="Zenbook")
    assert len(results_by_name) >= 1
    found_item = next(item for item in results_by_name if item["SKU"] == "FPT-ASUS-ZEN14-TEST")
    assert "Zenbook 14" in found_item["Tên sản phẩm"]
    assert "27.990.000đ" in found_item["Giá FPT"]
    assert "28 ngày" in found_item["DOH"]

    # 3. Tìm kiếm theo mã SKU
    results_by_sku = search_products(db=db_session, query="FPT-ASUS-ZEN14-TEST")
    assert len(results_by_sku) == 1
    assert results_by_sku[0]["SKU"] == "FPT-ASUS-ZEN14-TEST"

    # 4. Tìm kiếm không khớp
    no_results = search_products(db=db_session, query="NonExistentProduct123XYZ")
    assert len(no_results) == 0


def test_execute_tool_search_products(db_session: Session):
    """Kiểm tra hàm _execute_tool xử lý đúng khi Gemini gọi search_products."""
    # Tạo sản phẩm mẫu
    prod = Product(
        sku="FPT-IPHONE-15-128-TEST",
        name="iPhone 15 128GB Chính Hãng VN/A",
        category="PHONE",
        brand="Apple",
        base_retail_price=19990000,
        cost_price=17500000,
        floor_price=18000000,
    )
    db_session.add(prod)
    db_session.commit()

    client = GeminiClient()
    tool_result, table_data, explain_factors, intent = client._execute_tool(
        db=db_session,
        func_name="search_products",
        args={"query": "iPhone 15", "limit": 5}
    )

    assert intent == "PRODUCT_SEARCH"
    assert table_data is not None
    assert len(table_data) >= 1
    assert any(p["SKU"] == "FPT-IPHONE-15-128-TEST" for p in table_data)
    assert explain_factors is None


def test_api_chat_endpoint_product_search(db_session: Session):
    """Kiểm tra API endpoint /api/v1/ai/chat trả về phản hồi hợp lệ cho intent PRODUCT_SEARCH."""
    client = TestClient(app)
    sample_table = [
        {
            "SKU": "FPT-IPHONE-15-128",
            "Tên sản phẩm": "iPhone 15 128GB",
            "Ngành hàng": "PHONE",
            "Giá FPT": "19.990.000đ",
            "Giá sàn": "18.000.000đ",
            "Tồn kho": "45 máy",
            "DOH": "32 ngày",
            "Đối thủ": "19.490.000đ",
        }
    ]

    with patch("app.api.v1.endpoints.ai.chat_service.gemini_client") as mock_gemini:
        mock_gemini.generate_chat_response.return_value = (
            "Tôi tìm thấy 1 sản phẩm iPhone 15 128GB.",
            sample_table,
            None,
            "PRODUCT_SEARCH"
        )

        payload = {"message": "Tìm thông tin sản phẩm iPhone 15"}
        response = client.post("/api/v1/ai/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["tableData"] is not None
        assert len(data["tableData"]) == 1
        assert data["tableData"][0]["SKU"] == "FPT-IPHONE-15-128"
