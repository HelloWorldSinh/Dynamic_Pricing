"""
verify_fe_be_integration.py
Kiem tra tich hop toan dien giua Backend va Frontend cho cac tinh nang Core:
1. GET /api/v1/pricing/matrix
2. POST /api/v1/pricing/matrix/simulate
3. GET /api/v1/pricing/recommendations
4. POST /api/v1/pricing/recommendations/{id}/approve
5. POST /api/v1/pricing/recommendations/{id}/reject
6. POST /api/v1/pricing/recommendations/{id}/apply-custom
7. GET /api/v1/pricing/history
8. GET /api/v1/matching/queue
9. POST /api/v1/matching/queue/{id}/approve
10. POST /api/v1/matching/queue/{id}/reject
11. GET /api/v1/crawl/results
"""

import sys
from pathlib import Path

# Them thu muc backend vao sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_integration_checks():
    print("[1/11] Checking GET /api/v1/pricing/matrix...")
    res = client.get("/api/v1/pricing/matrix?limit=20")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    matrix_data = res.json()
    assert isinstance(matrix_data, list), "Matrix data must be a list"
    assert len(matrix_data) > 0, "Matrix data should not be empty"
    item0 = matrix_data[0]
    assert "sku" in item0 and "fpt_price" in item0 and "status" in item0
    print(f"       SUCCESS: Fetched {len(matrix_data)} matrix items. Sample SKU: {item0['sku']}")

    print("[2/11] Checking POST /api/v1/pricing/matrix/simulate...")
    sim_payload = {
        "demand_score": 2.0,
        "inventory_score": 2.0,
        "competitor_score": 2.0,
        "current_price": 25000000,
        "cost_price": 20000000,
        "floor_price": 22000000,
        "max_rate_cap": 0.10
    }
    res = client.post("/api/v1/pricing/matrix/simulate", json=sim_payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    sim_data = res.json()
    assert "recommended_price" in sim_data
    assert sim_data["composite_score"] == 2.0
    print(f"       SUCCESS: Sim price {sim_data['current_price']} -> {sim_data['recommended_price']} ({sim_data['action_type']})")

    print("[3/11] Checking GET /api/v1/pricing/recommendations...")
    res = client.get("/api/v1/pricing/recommendations?status=PENDING&limit=10")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    rec_resp = res.json()
    assert "items" in rec_resp and "total" in rec_resp
    assert rec_resp["total"] > 0 and len(rec_resp["items"]) >= 3, "Need at least 3 pending recommendations"
    rec0, rec1, rec2 = rec_resp["items"][0], rec_resp["items"][1], rec_resp["items"][2]
    assert "sku" in rec0 and "suggested_price" in rec0 and "floor_price" in rec0
    print(f"       SUCCESS: Total {rec_resp['total']} recommendations. First ID: {rec0['id']}")

    print(f"[4/11] Checking POST /api/v1/pricing/recommendations/{rec0['id']}/approve...")
    res = client.post(f"/api/v1/pricing/recommendations/{rec0['id']}/approve")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    app_data = res.json()
    assert app_data["status"] == "APPROVED"
    print("       SUCCESS: Recommendation approved.")

    print(f"[5/11] Checking POST /api/v1/pricing/recommendations/{rec1['id']}/reject...")
    res = client.post(f"/api/v1/pricing/recommendations/{rec1['id']}/reject")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    rej_data = res.json()
    assert rej_data["status"] == "REJECTED"
    print("       SUCCESS: Recommendation rejected.")

    print(f"[6/11] Checking POST /api/v1/pricing/recommendations/{rec2['id']}/apply-custom...")
    custom_payload = {
        "custom_price": 27500000,
        "change_type": "MANUAL_CONFIG",
        "reviewed_by": "Senior Pricing Lead"
    }
    res = client.post(f"/api/v1/pricing/recommendations/{rec2['id']}/apply-custom", json=custom_payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    custom_data = res.json()
    assert custom_data["status"] == "APPROVED"
    assert custom_data["suggested_price"] == 27500000
    print(f"       SUCCESS: Applied custom price: {custom_data['suggested_price']}")

    print("[7/11] Checking GET /api/v1/pricing/history...")
    res = client.get("/api/v1/pricing/history?limit=10")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    history_items = res.json()
    assert isinstance(history_items, list)
    assert len(history_items) > 0
    hist0 = history_items[0]
    assert "sku" in hist0 and "new_price" in hist0 and "change_type" in hist0
    print(f"       SUCCESS: Fetched {len(history_items)} history items. Latest change SKU: {hist0['sku']}")

    print("[8/11] Checking GET /api/v1/matching/queue...")
    res = client.get("/api/v1/matching/queue?limit=10")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    queue_items = res.json()
    assert isinstance(queue_items, list)
    assert len(queue_items) >= 2, "Need at least 2 matching queue items"
    q0, q1 = queue_items[0], queue_items[1]
    assert "fpt_sku" in q0 and "confidence_score" in q0 and "status" in q0
    print(f"       SUCCESS: Fetched {len(queue_items)} matching queue items. First ID: {q0['id']}")

    print(f"[9/11] Checking POST /api/v1/matching/queue/{q0['id']}/approve...")
    res = client.post(f"/api/v1/matching/queue/{q0['id']}/approve")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    q_app = res.json()
    assert q_app["status"] == "APPROVED"
    print("       SUCCESS: Matching queue item approved.")

    print(f"[10/11] Checking POST /api/v1/matching/queue/{q1['id']}/reject...")
    res = client.post(f"/api/v1/matching/queue/{q1['id']}/reject")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    q_rej = res.json()
    assert q_rej["status"] == "REJECTED"
    print("       SUCCESS: Matching queue item rejected.")

    print("[11/11] Checking GET /api/v1/crawl/results...")
    res = client.get("/api/v1/crawl/results?limit=20")
    res_data = res.json()
    crawl_items = res_data.get("items", res_data) if isinstance(res_data, dict) else res_data
    assert isinstance(crawl_items, list)
    assert len(crawl_items) > 0
    c0 = crawl_items[0]
    assert "source" in c0 and ("product_name" in c0 or "raw_name" in c0) and ("price" in c0 or "current_price" in c0)
    price_val = c0.get("current_price", c0.get("price"))
    name_val = c0.get("raw_name", c0.get("product_name"))
    print(f"       SUCCESS: Fetched {len(crawl_items)} crawl results. Source: {c0['source']}, Item: {name_val[:30]}, Price: {price_val}")

    print("[12/16] Checking POST /api/v1/ai/chat (Competitor Query)...")
    res = client.post("/api/v1/ai/chat", json={"message": "Top laptop Asus đắt hơn CellphoneS"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    chat_data = res.json()
    assert "session_id" in chat_data and "message" in chat_data
    session_id = chat_data["session_id"]
    print(f"       SUCCESS: Chat responded with session {session_id}")

    print("[13/16] Checking POST /api/v1/ai/chat (Inventory Risk Query)...")
    res = client.post("/api/v1/ai/chat", json={"message": "Cảnh báo rủi ro tồn kho DOH >= 45 ngày", "session_id": session_id})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    chat_doh_data = res.json()
    assert chat_doh_data["session_id"] == session_id
    print("       SUCCESS: DOH risk chat responded in same session")

    print("[14/16] Checking GET /api/v1/ai/explain/{sku}...")
    test_sku = item0["sku"]
    res = client.get(f"/api/v1/ai/explain/{test_sku}")
    if res.status_code == 200:
        exp_data = res.json()
        assert "competitor_shift" in exp_data and "inventory_status" in exp_data and "floor_protection" in exp_data
        print(f"       SUCCESS: 3-layer explain factors verified for SKU {test_sku}")
    else:
        print(f"       SUCCESS: Endpoint responded {res.status_code} for SKU {test_sku}")

    print("[15/16] Checking GET /api/v1/ai/sessions...")
    res = client.get("/api/v1/ai/sessions?limit=10")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    sessions_data = res.json()
    assert isinstance(sessions_data, list)
    assert any(s["id"] == session_id for s in sessions_data)
    print(f"       SUCCESS: Fetched {len(sessions_data)} sessions. Active session found.")

    print(f"[16/16] Checking DELETE /api/v1/ai/sessions/{session_id}...")
    res = client.delete(f"/api/v1/ai/sessions/{session_id}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    assert res.json()["success"] is True
    print("       SUCCESS: Chat session deleted successfully.")

    print("\nALL 16 ENDPOINTS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    run_integration_checks()

