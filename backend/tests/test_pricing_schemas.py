from app.services.pricing.schemas import SignalScores, ScenarioMatch, GuardrailResult, PricingRecommendationDTO


def test_signal_scores_validation_and_composite():
    scores = SignalScores(demand_score=1.5, inventory_score=-1.0, competitor_score=0.5)
    assert scores.demand_score == 1.5
    assert scores.inventory_score == -1.0
    assert scores.competitor_score == 0.5

    # Default weights: D=0.4, I=0.35, C=0.25 -> 1.5*0.4 + (-1.0)*0.35 + 0.5*0.25 = 0.6 - 0.35 + 0.125 = 0.375 -> round 0.38
    comp = scores.composite()
    assert comp == 0.38

    # Custom weights
    custom_comp = scores.composite(weights={"D": 0.5, "I": 0.3, "C": 0.2})
    # 1.5*0.5 + (-1.0)*0.3 + 0.5*0.2 = 0.75 - 0.3 + 0.1 = 0.55
    assert custom_comp == 0.55


def test_scenario_match_dataclass():
    match = ScenarioMatch(
        scenario_name="Kịch bản 1: Festival / Sự kiện lớn",
        target_delta_pct=0.12,
        action_type="Strong raise",
        rationale="Cả 3 tín hiệu tăng mạnh",
    )
    assert match.scenario_name.startswith("Kịch bản 1")
    assert match.target_delta_pct == 0.12
    assert match.action_type == "Strong raise"


def test_guardrail_result_dataclass():
    res = GuardrailResult(
        final_price=25000000,
        price_delta_amount=-1000000,
        price_delta_pct=-0.038,
        is_floor_capped=True,
        guardrail_notes=["Cắt về giá sàn floor_price"],
    )
    assert res.final_price == 25000000
    assert res.is_floor_capped is True
