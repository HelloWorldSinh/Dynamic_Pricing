"""Tests for Pricing Matrix Simulation API Endpoint (TDD Phase: RED)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """TestClient fixture for calling FastAPI endpoints."""
    with TestClient(app) as test_client:
        yield test_client


def test_simulate_scenario_festival(client):
    """Kịch bản 1: Festival (D=2, I=2, C=2) -> Strong raise."""
    payload = {
        "demand_score": 2.0,
        "inventory_score": 2.0,
        "competitor_score": 2.0,
        "current_price": 30_000_000,
        "cost_price": 25_000_000,
        "floor_price": 26_000_000,
        "competitor_price": 32_000_000,
        "max_rate_cap": 0.10,
    }
    response = client.post("/api/v1/pricing/matrix/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Festival" in data["scenario_name"]
    assert data["action_type"] == "Strong raise"
    assert data["target_delta_pct"] == 0.12
    assert data["composite_score"] == 2.0
    # Clamped by 10% rate cap: 30M * 1.1 = 33M
    assert data["recommended_price"] == 33_000_000
    assert data["price_delta_amount"] == 3_000_000
    assert data["price_delta_pct"] == 0.10
    assert data["is_floor_capped"] is False
    assert len(data["guardrail_notes"]) > 0


def test_simulate_baseline_scenario(client):
    """Kịch bản 3: Baseline (D=0, I=0, C=0) -> Hold."""
    payload = {
        "demand_score": 0.0,
        "inventory_score": 0.0,
        "competitor_score": 0.0,
        "current_price": 20_000_000,
        "cost_price": 16_000_000,
        "floor_price": 17_000_000,
    }
    response = client.post("/api/v1/pricing/matrix/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Baseline" in data["scenario_name"]
    assert data["action_type"] == "Hold"
    assert data["target_delta_pct"] == 0.0
    assert data["composite_score"] == 0.0
    assert data["recommended_price"] == 20_000_000
    assert data["price_delta_amount"] == 0


def test_simulate_floor_price_protection(client):
    """Kiểm thử bảo vệ giá sàn khi kịch bản yêu cầu giảm giá mạnh."""
    payload = {
        "demand_score": -2.0,
        "inventory_score": -2.0,
        "competitor_score": -2.0,
        "current_price": 10_000_000,
        "cost_price": 8_500_000,
        "floor_price": 9_500_000,
        "max_rate_cap": 0.15,
    }
    response = client.post("/api/v1/pricing/matrix/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_floor_capped"] is True
    assert data["recommended_price"] == 9_500_000
    assert any("floor" in note.lower() for note in data["guardrail_notes"])


def test_simulate_predatory_pricing_warning(client):
    """Cảnh báo khi đối thủ bán dưới 80% giá vốn."""
    payload = {
        "demand_score": 0.0,
        "inventory_score": 0.0,
        "competitor_score": -1.0,
        "current_price": 10_000_000,
        "cost_price": 8_000_000,
        "floor_price": 8_500_000,
        "competitor_price": 6_000_000,  # 6M < 80% của 8M (6.4M)
    }
    response = client.post("/api/v1/pricing/matrix/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("predatory" in note.lower() for note in data["guardrail_notes"])


def test_simulate_custom_weights(client):
    """Kiểm thử tùy biến trọng số ngành hàng."""
    payload = {
        "demand_score": 1.0,
        "inventory_score": 0.0,
        "competitor_score": -1.0,
        "weights": {"demand": 0.5, "inventory": 0.3, "competitor": 0.2},
        "current_price": 15_000_000,
        "cost_price": 12_000_000,
        "floor_price": 13_000_000,
    }
    response = client.post("/api/v1/pricing/matrix/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    # composite = 1.0*0.5 + 0.0*0.3 + (-1.0)*0.2 = 0.5 - 0.2 = 0.3
    assert abs(data["composite_score"] - 0.3) < 1e-4


def test_simulate_validation_errors(client):
    """Kiểm thử bắt lỗi đầu vào không hợp lệ."""
    # Current price âm
    response = client.post(
        "/api/v1/pricing/matrix/simulate",
        json={
            "demand_score": 0.0,
            "inventory_score": 0.0,
            "competitor_score": 0.0,
            "current_price": -100,
            "cost_price": 100,
            "floor_price": 100,
        },
    )
    assert response.status_code == 422

    # Demand score vượt quá 2.0
    response = client.post(
        "/api/v1/pricing/matrix/simulate",
        json={
            "demand_score": 3.0,
            "inventory_score": 0.0,
            "competitor_score": 0.0,
            "current_price": 1000,
            "cost_price": 100,
            "floor_price": 100,
        },
    )
    assert response.status_code == 422
