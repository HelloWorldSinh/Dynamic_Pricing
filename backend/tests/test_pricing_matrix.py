import pytest
from app.services.pricing.schemas import SignalScores, ScenarioMatch
from app.services.pricing.matrix import ScenarioMatrix


def test_scenario_matrix_evaluates_9_scenarios():
    matrix = ScenarioMatrix()

    # Scenario 1: Festival D=+2, I=+2, C=+2 -> Strong raise (+12%)
    match_s1 = matrix.evaluate(SignalScores(2.0, 2.0, 2.0))
    assert match_s1.scenario_name == "Kịch bản 1: Festival / Sự kiện lớn"
    assert match_s1.target_delta_pct == 0.12
    assert match_s1.action_type == "Strong raise"
    assert "Nhu cầu bùng nổ" in match_s1.rationale

    # Scenario 2: Viral D=+2, I=0, C=0 -> Moderate raise (+6%)
    match_s2 = matrix.evaluate(SignalScores(2.0, 0.0, 0.0))
    assert match_s2.scenario_name == "Kịch bản 2: Sản phẩm Viral"
    assert match_s2.target_delta_pct == 0.06
    assert match_s2.action_type == "Moderate raise"

    # Scenario 3: Baseline D=0, I=0, C=0 -> Hold (0%)
    match_s3 = matrix.evaluate(SignalScores(0.0, 0.0, 0.0))
    assert match_s3.scenario_name == "Kịch bản 3: Bình thường (Baseline)"
    assert match_s3.target_delta_pct == 0.0
    assert match_s3.action_type == "Hold"

    # Scenario 4: Cầu cao nhưng Hàng ứ D=+2, I=-2, C=0 -> Hold + Review (0%)
    match_s4 = matrix.evaluate(SignalScores(2.0, -2.0, 0.0))
    assert match_s4.scenario_name == "Kịch bản 4: Cầu cao nhưng Hàng ứ"
    assert match_s4.target_delta_pct == 0.0
    assert match_s4.action_type == "Hold + Review"

    # Scenario 5: Hàng khan, Đối thủ hết nhưng Cầu yếu D=-1, I=+2, C=+2 -> Mild raise (+2%)
    match_s5 = matrix.evaluate(SignalScores(-1.0, 2.0, 2.0))
    assert match_s5.scenario_name == "Kịch bản 5: Hàng khan, Đối thủ hết nhưng Cầu yếu"
    assert match_s5.target_delta_pct == 0.02
    assert match_s5.action_type == "Mild raise"

    # Scenario 6: Khủng hoảng Nhu cầu D=-2, I=-2, C=-2 -> Strong lower (-15%)
    match_s6 = matrix.evaluate(SignalScores(-2.0, -2.0, -2.0))
    assert match_s6.scenario_name == "Kịch bản 6: Khủng hoảng Nhu cầu"
    assert match_s6.target_delta_pct == -0.15
    assert match_s6.action_type == "Strong lower"

    # Scenario 7: Khách quay lưng, Đối thủ rẻ D=-2, I=0, C=-2 -> Moderate lower (-10%)
    match_s7 = matrix.evaluate(SignalScores(-2.0, 0.0, -2.0))
    assert match_s7.scenario_name == "Kịch bản 7: Khách quay lưng, Đối thủ rẻ"
    assert match_s7.target_delta_pct == -0.10
    assert match_s7.action_type == "Moderate lower"

    # Scenario 8: Cầu cao, Hàng khan nhưng Đối thủ rẻ D=+2, I=+2, C=-2 -> Moderate raise (+6%)
    match_s8 = matrix.evaluate(SignalScores(2.0, 2.0, -2.0))
    assert match_s8.scenario_name == "Kịch bản 8: Cầu cao, Hàng khan nhưng Đối thủ rẻ"
    assert match_s8.target_delta_pct == 0.06
    assert match_s8.action_type == "Moderate raise"

    # Scenario 9: Tín hiệu Hỗn độn D=+1, I=-1, C=+1 -> Hold + A/B Test (0%)
    match_s9 = matrix.evaluate(SignalScores(1.0, -1.0, 1.0))
    assert match_s9.scenario_name == "Kịch bản 9: Tín hiệu Hỗn độn"
    assert match_s9.target_delta_pct == 0.0
    assert match_s9.action_type == "Hold + A/B Test"

    # Scenario Clearance / S10: Cuối vòng đời D=-2, I=-2, C=0 -> Strong lower (-15%)
    match_s10 = matrix.evaluate(SignalScores(-2.0, -2.0, 0.0))
    assert "Cuối vòng đời" in match_s10.scenario_name
    assert match_s10.target_delta_pct == -0.15
    assert match_s10.action_type == "Strong lower"


def test_composite_score_calculation():
    matrix = ScenarioMatrix()

    # D*0.4 + I*0.35 + C*0.25
    scores = SignalScores(demand_score=1.5, inventory_score=-1.0, competitor_score=0.5)
    # 1.5*0.4 + (-1.0)*0.35 + 0.5*0.25 = 0.60 - 0.35 + 0.125 = 0.375 -> round to 0.38
    comp = matrix.calculate_composite(scores)
    assert comp == 0.38

    # Static / Class method call
    comp_static = ScenarioMatrix.calculate_composite(scores)
    assert comp_static == 0.38

    # Custom weights
    custom_w = {"D": 0.50, "I": 0.30, "C": 0.20}
    # 1.5*0.5 + (-1.0)*0.3 + 0.5*0.2 = 0.75 - 0.30 + 0.10 = 0.55
    comp_custom = matrix.calculate_composite(scores, weights=custom_w)
    assert comp_custom == 0.55

    # Instance with custom default weights
    custom_matrix = ScenarioMatrix(default_weights=custom_w)
    assert custom_matrix.calculate_composite(scores) == 0.55


def test_7_band_fallbacks():
    matrix = ScenarioMatrix()

    # Band 1: Composite >= 1.50 -> Strong raise (+12%)
    s_band1 = SignalScores(1.8, 1.6, 1.5)  # 1.8*0.4 + 1.6*0.35 + 1.5*0.25 = 0.72 + 0.56 + 0.375 = 1.655 -> 1.66
    match_b1 = matrix.evaluate(s_band1)
    assert match_b1.action_type == "Strong raise"
    assert match_b1.target_delta_pct == 0.12

    # Band 2: 0.75 <= Composite < 1.50 -> Moderate raise (+6%)
    s_band2 = SignalScores(1.0, 1.0, 1.0)  # 1.0*0.4 + 1.0*0.35 + 1.0*0.25 = 1.0
    match_b2 = matrix.evaluate(s_band2)
    assert match_b2.action_type == "Moderate raise"
    assert match_b2.target_delta_pct == 0.06

    # Band 3: 0.25 <= Composite < 0.75 -> Mild raise (+2%)
    s_band3 = SignalScores(0.5, 0.5, 0.5)  # 0.50
    match_b3 = matrix.evaluate(s_band3)
    assert match_b3.action_type == "Mild raise"
    assert match_b3.target_delta_pct == 0.02

    # Band 4: -0.24 <= Composite < 0.25 -> Hold (0%)
    s_band4 = SignalScores(0.1, 0.1, 0.0)  # 0.1*0.4 + 0.1*0.35 + 0.0 = 0.075 -> 0.08
    match_b4 = matrix.evaluate(s_band4)
    assert match_b4.action_type == "Hold"
    assert match_b4.target_delta_pct == 0.0

    # Band 5: -0.74 <= Composite < -0.24 -> Mild lower (-2%)
    s_band5 = SignalScores(-0.5, -0.5, -0.5)  # -0.50
    match_b5 = matrix.evaluate(s_band5)
    assert match_b5.action_type == "Mild lower"
    assert match_b5.target_delta_pct == -0.02

    # Band 6: -1.49 <= Composite < -0.74 -> Moderate lower (-6%)
    s_band6 = SignalScores(-1.0, -1.0, -1.0)  # -1.00
    match_b6 = matrix.evaluate(s_band6)
    assert match_b6.action_type == "Moderate lower"
    assert match_b6.target_delta_pct == -0.06

    # Band 7: Composite < -1.49 -> Strong lower (-12%)
    s_band7 = SignalScores(-1.8, -1.6, -1.5)  # -1.66
    match_b7 = matrix.evaluate(s_band7)
    assert match_b7.action_type == "Strong lower"
    assert match_b7.target_delta_pct == -0.12


def test_fallback_boundary_thresholds():
    matrix = ScenarioMatrix()

    # Exact threshold 1.50
    # D=1.5, I=1.5, C=1.5 -> 1.50
    match_150 = matrix.evaluate(SignalScores(1.5, 1.5, 1.5))
    assert match_150.action_type == "Strong raise"
    assert match_150.target_delta_pct == 0.12

    # Exact threshold 0.75
    # D=0.75, I=0.75, C=0.75 -> 0.75
    match_075 = matrix.evaluate(SignalScores(0.75, 0.75, 0.75))
    assert match_075.action_type == "Moderate raise"
    assert match_075.target_delta_pct == 0.06

    # Exact threshold 0.25
    # D=0.25, I=0.25, C=0.25 -> 0.25
    match_025 = matrix.evaluate(SignalScores(0.25, 0.25, 0.25))
    assert match_025.action_type == "Mild raise"
    assert match_025.target_delta_pct == 0.02

    # Exact threshold -0.24
    # D=-0.24, I=-0.24, C=-0.24 -> -0.24
    match_neg024 = matrix.evaluate(SignalScores(-0.24, -0.24, -0.24))
    assert match_neg024.action_type == "Hold"
    assert match_neg024.target_delta_pct == 0.0

    # Value just below -0.24: -0.25
    match_neg025 = matrix.evaluate(SignalScores(-0.25, -0.25, -0.25))
    assert match_neg025.action_type == "Mild lower"
    assert match_neg025.target_delta_pct == -0.02

    # Exact threshold -0.74
    match_neg074 = matrix.evaluate(SignalScores(-0.74, -0.74, -0.74))
    assert match_neg074.action_type == "Mild lower"
    assert match_neg074.target_delta_pct == -0.02

    # Value just below -0.74: -0.75
    match_neg075 = matrix.evaluate(SignalScores(-0.75, -0.75, -0.75))
    assert match_neg075.action_type == "Moderate lower"
    assert match_neg075.target_delta_pct == -0.06

    # Exact threshold -1.49
    match_neg149 = matrix.evaluate(SignalScores(-1.49, -1.49, -1.49))
    assert match_neg149.action_type == "Moderate lower"
    assert match_neg149.target_delta_pct == -0.06

    # Value below -1.49: -1.50
    match_neg150 = matrix.evaluate(SignalScores(-1.5, -1.5, -1.5))
    assert match_neg150.action_type == "Strong lower"
    assert match_neg150.target_delta_pct == -0.12


def test_no_emojis_or_icons_in_results():
    matrix = ScenarioMatrix()
    test_cases = [
        SignalScores(2.0, 2.0, 2.0),
        SignalScores(0.0, 0.0, 0.0),
        SignalScores(-2.0, -2.0, -2.0),
        SignalScores(1.8, 1.6, 1.5),
        SignalScores(-1.8, -1.6, -1.5),
    ]
    disallowed_symbols = ["↑", "↓", "⚠️", "⚡", "🎯", "✨", "🔥"]

    for scores in test_cases:
        res = matrix.evaluate(scores)
        for sym in disallowed_symbols:
            assert sym not in res.scenario_name
            assert sym not in res.action_type
            assert sym not in res.rationale
