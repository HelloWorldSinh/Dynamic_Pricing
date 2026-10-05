"""Unit tests for Dynamic Pricing Safety Guardrails (guardrails.py).

Verifies Margin Floor protection, Rate-of-Change Cap, Predatory Pricing detection,
and ensures strict absence of emojis or decorative icons in guardrail notes.
"""

import pytest
import re
from app.services.pricing.guardrails import SafetyGuardrails
from app.services.pricing.schemas import GuardrailResult


def test_margin_floor_protection_caps_price():
    """Verify margin floor clamps candidate price when dropping below floor."""
    guard = SafetyGuardrails()
    # current = 10,000,000, delta = -20% -> raw = 8,000,000; floor = 9,000,000
    res = guard.apply(
        current_price=10_000_000,
        target_delta_pct=-0.20,
        floor_price=9_000_000,
        cost_price=8_500_000,
    )
    assert isinstance(res, GuardrailResult)
    assert res.final_price == 9_000_000
    assert res.is_floor_capped is True
    assert res.price_delta_pct == -0.10
    assert res.price_delta_amount == -1_000_000
    assert "Margin floor protection activated: Price capped at floor_price" in res.guardrail_notes


def test_margin_floor_protection_with_moderate_drop():
    """Verify floor protection activates when candidate price is strictly below floor."""
    guard = SafetyGuardrails()
    # current = 10,000,000, delta = -8% -> candidate = 9,200,000; floor = 9,500,000
    res = guard.apply(
        current_price=10_000_000,
        target_delta_pct=-0.08,
        floor_price=9_500_000,
        cost_price=9_000_000,
    )
    assert res.final_price == 9_500_000
    assert res.is_floor_capped is True
    assert res.price_delta_amount == -500_000
    assert res.price_delta_pct == -0.05
    assert "Margin floor protection activated: Price capped at floor_price" in res.guardrail_notes


def test_rate_of_change_cap_upward():
    """Verify upward price jump exceeding default cap (+10%) is clamped."""
    guard = SafetyGuardrails()
    # delta = +15% clamped to +10%
    res = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.15,
        floor_price=8_000_000,
        cost_price=7_000_000,
    )
    assert res.final_price == 11_000_000
    assert res.price_delta_amount == 1_000_000
    assert res.price_delta_pct == 0.10
    assert res.is_floor_capped is False
    assert any("Rate-of-change cap activated" in note for note in res.guardrail_notes)


def test_rate_of_change_cap_downward():
    """Verify downward price drop exceeding default cap (-10%) is clamped when above floor."""
    guard = SafetyGuardrails()
    # delta = -20% clamped to -10%, candidate = 9,000,000 > floor 7,000,000
    res = guard.apply(
        current_price=10_000_000,
        target_delta_pct=-0.20,
        floor_price=7_000_000,
        cost_price=6_000_000,
    )
    assert res.final_price == 9_000_000
    assert res.price_delta_amount == -1_000_000
    assert res.price_delta_pct == -0.10
    assert res.is_floor_capped is False
    assert any("Rate-of-change cap activated" in note for note in res.guardrail_notes)


def test_configurable_max_rate_cap():
    """Verify configurable max_rate_cap (e.g. 0.15 for strong raise/lower scenarios)."""
    guard = SafetyGuardrails()
    # delta = +15% with max_rate_cap = 0.15 -> not clamped
    res_up = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.15,
        floor_price=8_000_000,
        cost_price=7_000_000,
        max_rate_cap=0.15,
    )
    assert res_up.final_price == 11_500_000
    assert res_up.price_delta_pct == 0.15
    assert res_up.is_floor_capped is False
    assert not any("Rate-of-change cap activated" in note for note in res_up.guardrail_notes)

    # delta = +20% with max_rate_cap = 0.15 -> clamped to +15%
    res_up_clamp = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.20,
        floor_price=8_000_000,
        cost_price=7_000_000,
        max_rate_cap=0.15,
    )
    assert res_up_clamp.final_price == 11_500_000
    assert res_up_clamp.price_delta_pct == 0.15
    assert any("Rate-of-change cap activated" in note for note in res_up_clamp.guardrail_notes)


def test_predatory_pricing_detection():
    """Verify predatory pricing warning when competitor price is below 80% of cost price."""
    guard = SafetyGuardrails()
    cost = 10_000_000  # 80% = 8_000_000

    # Competitor price = 7,900,000 (< 8,000,000) -> predatory detected
    res_pred = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.0,
        floor_price=9_000_000,
        cost_price=cost,
        competitor_price=7_900_000,
    )
    assert "Predatory pricing warning: Competitor price is below 80% of cost price" in res_pred.guardrail_notes

    # Competitor price = 8,000,000 (== 80%) -> safe, no warning
    res_safe = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.0,
        floor_price=9_000_000,
        cost_price=cost,
        competitor_price=8_000_000,
    )
    assert not any("Predatory pricing warning" in note for note in res_safe.guardrail_notes)

    # Competitor price is None -> safe, no warning
    res_none = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.0,
        floor_price=9_000_000,
        cost_price=cost,
        competitor_price=None,
    )
    assert not any("Predatory pricing warning" in note for note in res_none.guardrail_notes)


def test_normal_price_adjustment_within_safe_bounds():
    """Verify normal price adjustment when no guardrails are violated."""
    guard = SafetyGuardrails()
    res = guard.apply(
        current_price=10_000_000,
        target_delta_pct=0.05,
        floor_price=9_000_000,
        cost_price=8_500_000,
        competitor_price=9_500_000,
    )
    assert res.final_price == 10_500_000
    assert res.price_delta_amount == 500_000
    assert res.price_delta_pct == 0.05
    assert res.is_floor_capped is False
    assert res.guardrail_notes == []


def test_no_emojis_or_icons_in_guardrail_notes():
    """Verify strictly zero emoji or icon characters appear in guardrail notes."""
    guard = SafetyGuardrails()
    disallowed_symbols = ["↑", "↓", "⚠️", "⚡", "🎯", "✨", "🔥", "🛑", "🚨"]

    # Trigger multiple notes: rate cap + predatory + floor cap
    res = guard.apply(
        current_price=10_000_000,
        target_delta_pct=-0.25,
        floor_price=9_500_000,
        cost_price=8_000_000,
        competitor_price=6_000_000,
    )
    assert len(res.guardrail_notes) > 0
    for note in res.guardrail_notes:
        for sym in disallowed_symbols:
            assert sym not in note
        # Check standard emoji unicode range
        assert not re.search(r"[\U00010000-\U0010ffff]", note)


def test_invalid_inputs_raise_value_error():
    """Verify validation errors on non-positive or negative parameters."""
    guard = SafetyGuardrails()

    with pytest.raises(ValueError, match="current_price must be greater than 0"):
        guard.apply(current_price=0, target_delta_pct=0.05, floor_price=100, cost_price=100)

    with pytest.raises(ValueError, match="floor_price must be non-negative"):
        guard.apply(current_price=1000, target_delta_pct=0.05, floor_price=-1, cost_price=100)

    with pytest.raises(ValueError, match="cost_price must be non-negative"):
        guard.apply(current_price=1000, target_delta_pct=0.05, floor_price=100, cost_price=-1)

    with pytest.raises(ValueError, match="max_rate_cap must be positive"):
        guard.apply(current_price=1000, target_delta_pct=0.05, floor_price=100, cost_price=100, max_rate_cap=0.0)
