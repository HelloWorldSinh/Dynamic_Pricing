"""Scenario Matrix & Composite Score calculation for Dynamic Pricing Recommendation Engine.

Maps market signal scores (D, I, C) to 9 business scenarios,
or falls back to 7 Composite Score action bands.
"""

from typing import Dict, Optional, Tuple, Union
from app.services.pricing.schemas import SignalScores, ScenarioMatch


class ScenarioMatrix:
    """Ma trận định giá và tính toán điểm tổng hợp Composite Score."""

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "D": 0.40,
        "I": 0.35,
        "C": 0.25,
    }

    # 9 kịch bản nghiệp vụ chuẩn và kịch bản xả kho cuối vòng đời (Clearance)
    EXACT_SCENARIOS: Dict[Tuple[float, float, float], ScenarioMatch] = {
        (2.0, 2.0, 2.0): ScenarioMatch(
            scenario_name="Kịch bản 1: Festival / Sự kiện lớn",
            target_delta_pct=0.12,
            action_type="Strong raise",
            rationale="Cả 3 yếu tố cùng tăng mạnh: Nhu cầu bùng nổ, hàng khan hiếm trong kho, đối thủ đang bán giá cao hơn.",
        ),
        (2.0, 0.0, 0.0): ScenarioMatch(
            scenario_name="Kịch bản 2: Sản phẩm Viral",
            target_delta_pct=0.06,
            action_type="Moderate raise",
            rationale="Lượt tìm kiếm và quan tâm tăng vọt, trong khi lượng tồn kho vẫn đảm bảo và đối thủ chưa kịp điều chỉnh giá.",
        ),
        (0.0, 0.0, 0.0): ScenarioMatch(
            scenario_name="Kịch bản 3: Bình thường (Baseline)",
            target_delta_pct=0.0,
            action_type="Hold",
            rationale="Thị trường ổn định, cung cầu cân bằng, giá đối thủ ngang bằng trong biên độ an toàn.",
        ),
        (2.0, -2.0, 0.0): ScenarioMatch(
            scenario_name="Kịch bản 4: Cầu cao nhưng Hàng ứ",
            target_delta_pct=0.0,
            action_type="Hold + Review",
            rationale="Nhu cầu mua lớn nhưng lượng tồn kho thực tế quá cao làm triệt tiêu áp lực tăng giá. Ưu tiên giải phóng tồn kho.",
        ),
        (-1.0, 2.0, 2.0): ScenarioMatch(
            scenario_name="Kịch bản 5: Hàng khan, Đối thủ hết nhưng Cầu yếu",
            target_delta_pct=0.02,
            action_type="Mild raise",
            rationale="Kho sắp hết hàng và đối thủ đã Out-Of-Stock, nhưng nhu cầu khách chưa cao. Tăng nhẹ do hạn chế nguồn cung.",
        ),
        (-2.0, -2.0, -2.0): ScenarioMatch(
            scenario_name="Kịch bản 6: Khủng hoảng Nhu cầu",
            target_delta_pct=-0.15,
            action_type="Strong lower",
            rationale="Cả 3 yếu tố đều chạm đáy: Cầu sụt giảm nghiêm trọng, kho ứ đọng nặng, đối thủ đang xả hàng. Cần giảm giá sâu.",
        ),
        (-2.0, 0.0, -2.0): ScenarioMatch(
            scenario_name="Kịch bản 7: Khách quay lưng, Đối thủ rẻ",
            target_delta_pct=-0.10,
            action_type="Moderate lower",
            rationale="Lượt xem và giỏ hàng giảm mạnh do đối thủ đang bán rẻ hơn. Cần giảm giá tương ứng để chặn đà mất khách.",
        ),
        (2.0, 2.0, -2.0): ScenarioMatch(
            scenario_name="Kịch bản 8: Cầu cao, Hàng khan nhưng Đối thủ rẻ",
            target_delta_pct=0.06,
            action_type="Moderate raise",
            rationale="Nhu cầu lớn và kho khan hàng tạo động lực tăng giá mạnh, lấn át yếu tố đối thủ rẻ.",
        ),
        (1.0, -1.0, 1.0): ScenarioMatch(
            scenario_name="Kịch bản 9: Tín hiệu Hỗn độn",
            target_delta_pct=0.0,
            action_type="Hold + A/B Test",
            rationale="Các tín hiệu giằng co kéo theo các hướng ngược nhau, điểm tổng hợp gần 0. Đề xuất giữ giá và chạy A/B Test.",
        ),
        (-2.0, -2.0, 0.0): ScenarioMatch(
            scenario_name="Kịch bản 10: Cuối vòng đời (Clearance)",
            target_delta_pct=-0.15,
            action_type="Strong lower",
            rationale="Sản phẩm cuối vòng đời, cần xả kho thu hồi vốn dứt điểm.",
        ),
    }

    def __init__(self, default_weights: Optional[Dict[str, float]] = None) -> None:
        """Khởi tạo ma trận với trọng số mặc định tùy chọn."""
        self.default_weights: Dict[str, float] = (
            default_weights.copy() if default_weights else self.DEFAULT_WEIGHTS.copy()
        )

    @classmethod
    def _compute_composite(
        cls,
        scores: SignalScores,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """Tính điểm tổng hợp làm tròn 2 chữ số thập phân."""
        w = weights or cls.DEFAULT_WEIGHTS
        w_d = w.get("D", 0.40)
        w_i = w.get("I", 0.35)
        w_c = w.get("C", 0.25)
        raw_score = (scores.demand_score * w_d) + (scores.inventory_score * w_i) + (scores.competitor_score * w_c)
        return round(raw_score, 2)

    def calculate_composite(
        self_or_scores: Union["ScenarioMatrix", SignalScores],
        scores_or_weights: Optional[Union[SignalScores, Dict[str, float]]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """Tính điểm tổng hợp Composite Score (hỗ trợ cả instance call và static/class call)."""
        if isinstance(self_or_scores, SignalScores):
            scores = self_or_scores
            eff_weights = weights or (scores_or_weights if isinstance(scores_or_weights, dict) else None)
        else:
            scores = scores_or_weights  # type: ignore
            eff_weights = weights or getattr(self_or_scores, "default_weights", ScenarioMatrix.DEFAULT_WEIGHTS)

        return ScenarioMatrix._compute_composite(scores, eff_weights)

    def evaluate(
        self_or_scores: Union["ScenarioMatrix", SignalScores],
        scores_or_weights: Optional[Union[SignalScores, Dict[str, float]]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> ScenarioMatch:
        """Đánh giá tín hiệu thị trường: ưu tiên 9 kịch bản chuẩn, fallback theo 7 dải Composite Score."""
        if isinstance(self_or_scores, SignalScores):
            scores = self_or_scores
            eff_weights = weights or (scores_or_weights if isinstance(scores_or_weights, dict) else None)
        else:
            scores = scores_or_weights  # type: ignore
            eff_weights = weights or getattr(self_or_scores, "default_weights", ScenarioMatrix.DEFAULT_WEIGHTS)

        # 1. Kiểm tra 9 kịch bản đặc thù (+ clearance)
        key = (
            round(float(scores.demand_score), 2),
            round(float(scores.inventory_score), 2),
            round(float(scores.competitor_score), 2),
        )
        if key in ScenarioMatrix.EXACT_SCENARIOS:
            return ScenarioMatrix.EXACT_SCENARIOS[key]

        # 2. Fallback theo 7 dải Composite Score
        comp = ScenarioMatrix._compute_composite(scores, eff_weights)

        if comp >= 1.50:
            return ScenarioMatch(
                scenario_name="Dải Composite: Strong raise",
                target_delta_pct=0.12,
                action_type="Strong raise",
                rationale=f"Điểm tổng hợp cao (Composite = {comp:.2f} >= 1.50), khuyến nghị tăng giá mạnh.",
            )
        elif comp >= 0.75:
            return ScenarioMatch(
                scenario_name="Dải Composite: Moderate raise",
                target_delta_pct=0.06,
                action_type="Moderate raise",
                rationale=f"Điểm tổng hợp tích cực (Composite = {comp:.2f} >= 0.75), khuyến nghị tăng giá vừa phải.",
            )
        elif comp >= 0.25:
            return ScenarioMatch(
                scenario_name="Dải Composite: Mild raise",
                target_delta_pct=0.02,
                action_type="Mild raise",
                rationale=f"Điểm tổng hợp tăng nhẹ (Composite = {comp:.2f} >= 0.25), khuyến nghị tăng giá nhẹ.",
            )
        elif comp >= -0.24:
            return ScenarioMatch(
                scenario_name="Dải Composite: Hold",
                target_delta_pct=0.0,
                action_type="Hold",
                rationale=f"Điểm tổng hợp cân bằng (Composite = {comp:.2f} nằm trong [-0.24, 0.25)), khuyến nghị giữ nguyên giá.",
            )
        elif comp >= -0.74:
            return ScenarioMatch(
                scenario_name="Dải Composite: Mild lower",
                target_delta_pct=-0.02,
                action_type="Mild lower",
                rationale=f"Điểm tổng hợp giảm nhẹ (Composite = {comp:.2f} nằm trong [-0.74, -0.24)), khuyến nghị giảm giá nhẹ.",
            )
        elif comp >= -1.49:
            return ScenarioMatch(
                scenario_name="Dải Composite: Moderate lower",
                target_delta_pct=-0.06,
                action_type="Moderate lower",
                rationale=f"Điểm tổng hợp tiêu cực (Composite = {comp:.2f} nằm trong [-1.49, -0.74)), khuyến nghị giảm giá vừa phải.",
            )
        else:
            return ScenarioMatch(
                scenario_name="Dải Composite: Strong lower",
                target_delta_pct=-0.12,
                action_type="Strong lower",
                rationale=f"Điểm tổng hợp rất thấp (Composite = {comp:.2f} < -1.49), khuyến nghị giảm giá mạnh.",
            )
