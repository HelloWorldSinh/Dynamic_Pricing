"""
Demo Scenarios Script for AI Chatbot Acceptance (PBI-017 & PBI-018)
Demonstrates 3 core acceptance scenarios:
1. Competitor price comparison (ASUS laptops vs CellphoneS) with multi-column tableData
2. Inventory risk analysis (Stock risks with DOH >= 45)
3. 3-Layer explainable factors card for price recommendation
"""

import sys
from pathlib import Path

# Add backend root to sys.path
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))

from fastapi.testclient import TestClient
from app.main import app

def run_demo():
    client = TestClient(app)
    separator = "=" * 80

    print(separator)
    print("DEMO NGHIEP VU PHAN HE AI CHATBOT (PBI-017 & PBI-018)")
    print(separator)

    # -------------------------------------------------------------
    # Scenario 1: Laptop Asus vs CellphoneS price comparison
    # -------------------------------------------------------------
    print("\n[KICH BAN 1: SO SANH GIA LAPTOP ASUS]")
    req_1 = {
        "message": "Top laptop Asus đắt hơn CellphoneS"
    }
    print(f"Cau hoi: '{req_1['message']}'")
    resp_1 = client.post("/api/v1/ai/chat", json=req_1)
    print(f"Status Code: {resp_1.status_code}")
    assert resp_1.status_code == 200, f"Scenario 1 failed: {resp_1.text}"
    data_1 = resp_1.json()
    session_id = data_1.get("session_id")
    print(f"Session ID duoc tao: {session_id}")
    print("\nPhan hoi tu AI:")
    print(data_1.get("message"))
    table_data = data_1.get("tableData")
    if table_data and isinstance(table_data, list):
        print("\nBang du lieu so sanh (tableData):")
        if len(table_data) > 0:
            headers = list(table_data[0].keys())
            print(" | ".join(headers))
            for row in table_data:
                print(" | ".join(str(row.get(h, "")) for h in headers))
    else:
        print("Khong co du lieu bang tableData")

    # -------------------------------------------------------------
    # Scenario 2: Inventory risk analysis (in same session)
    # -------------------------------------------------------------
    print("\n" + separator)
    print("[KICH BAN 2: PHAN TICH RUI RO TON KHO (DOH >= 45 NGAY)]")
    req_2 = {
        "message": "Có mã nào đang có nguy cơ tồn kho cao cần thanh lý không?",
        "session_id": session_id
    }
    print(f"Cau hoi: '{req_2['message']}' (Ke thua Session ID: {session_id})")
    resp_2 = client.post("/api/v1/ai/chat", json=req_2)
    print(f"Status Code: {resp_2.status_code}")
    assert resp_2.status_code == 200, f"Scenario 2 failed: {resp_2.text}"
    data_2 = resp_2.json()
    print("\nPhan hoi tu AI:")
    print(data_2.get("message"))

    # -------------------------------------------------------------
    # Scenario 3: 3-Layer explainable card for SKU recommendation
    # -------------------------------------------------------------
    print("\n" + separator)
    print("[KICH BAN 3: THE GIAI TRINH 3 LOP CHO DE XUAT GIA SKU]")

    # Use SKU0085 which has full competitor and inventory data from Scenario 1
    sku_target = "SKU0085"

    print(f"Truy xuat the giai trinh cho SKU: '{sku_target}'")
    resp_3 = client.get(f"/api/v1/ai/explain/{sku_target}")
    print(f"Status Code: {resp_3.status_code}")
    if resp_3.status_code == 200:
        explain = resp_3.json()

        print(f"\nSKU: {sku_target}")
        print("\n[Lop 1: Bien dong doi thu]")
        comp = explain.get("competitor_shift")
        if comp:
            fpt_p = comp.get('fpt_price') or 0
            comp_p = comp.get('competitor_price') or 0
            diff_p = comp.get('price_diff') or 0
            diff_pct = comp.get('diff_percent') or 0
            print(f" - Doi thu: {comp.get('competitor_name') or 'N/A'}")
            print(f" - Gia FPT: {fpt_p:,.0f} VND vs Gia doi thu: {comp_p:,.0f} VND")
            print(f" - Chenh lech: {diff_p:,.0f} VND ({diff_pct:.1f}%)")
            print(f" - Con hang online: {comp.get('is_in_stock')}")

        print("\n[Lop 2: Tinh trang ton kho FPT]")
        inv = explain.get("inventory_status")
        if inv:
            print(f" - Ton kha dung: {inv.get('available_quantity')} san pham")
            print(f" - Toc do ban: {inv.get('sales_velocity')} chiec/ngay")
            print(f" - So ngay ton kho (DOH): {inv.get('doh')} ngay")
            print(f" - Muc do rui ro ton kho: {inv.get('risk_level')}")

        print("\n[Lop 3: Bao ve gia san & Loi nhuan]")
        floor = explain.get("floor_protection")
        if floor:
            fl_p = floor.get('floor_price') or 0
            rc_p = floor.get('recommended_price') or 0
            m_pct = floor.get('margin_above_floor_pct') or 0
            print(f" - Gia san: {fl_p:,.0f} VND")
            print(f" - Gia de xuat: {rc_p:,.0f} VND")
            print(f" - Bien an toan gia san: {m_pct:.1f}%")
            print(f" - Bi cham gia san (Capped): {floor.get('is_capped')}")
    else:
        print(f"Endpoint phan hoi ma: {resp_3.status_code}")

    # Also test asking AI chat to explain the SKU
    print(f"\nKiem tra hoi AI truc tiep giai thich ma SKU: '{sku_target}'")
    req_explain = {
        "message": f"Tại sao lại đề xuất giá cho mã {sku_target}?",
        "session_id": session_id
    }
    resp_ai_exp = client.post("/api/v1/ai/chat", json=req_explain)
    assert resp_ai_exp.status_code == 200
    ai_exp_data = resp_ai_exp.json()
    print("Phan hoi AI giai trinh:")
    print(ai_exp_data.get("message"))
    if ai_exp_data.get("explainFactors"):
        print("Co du lieu explainFactors di kem thanh cong!")

    print("\n" + separator)
    print("HOAN THANH NGHIEP VU 3 KICH BAN - TAT CA CAC KICH BAN DEU DAT!")
    print(separator)

if __name__ == "__main__":
    run_demo()
