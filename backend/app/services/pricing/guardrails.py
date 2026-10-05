"""Safety Guardrails for Dynamic Pricing Recommendation Engine.

Implements circuit-breaker protections:
1. Rate-of-Change Cap: Clamps maximum price jump/drop percentage (default +/-10%).
2. Margin Floor Protection: Ensures recommended price never drops below floor_price.
3. Predatory Pricing Check: Detects and logs warnings if competitor price is below 80% of cost price.
"""

from typing import List, Optional
from app.services.pricing.schemas import GuardrailResult


class SafetyGuardrails:
    """Rào cản an toàn và kiểm soát biên độ định giá tự động."""

    def apply(
        self,
        current_price: int,
        target_delta_pct: float,
        floor_price: int,
        cost_price: int,
        competitor_price: Optional[int] = None,
        max_rate_cap: float = 0.10,
    ) -> GuardrailResult:
        """Áp dụng các rào chắn bảo vệ an toàn cho giá đề xuất.

        Args:
            current_price: Giá hiện tại của sản phẩm (VND).
            target_delta_pct: Tỷ lệ thay đổi giá mục tiêu từ ScenarioMatrix (vd: +0.06, -0.15).
            floor_price: Mức giá sàn tối thiểu được phép bán (cost_price * (1 + min_margin)).
            cost_price: Giá vốn nhập kho của sản phẩm.
            competitor_price: Giá thấp nhất của đối thủ cạnh tranh (nếu có).
            max_rate_cap: Biên độ điều chỉnh tối đa cho phép trong 1 lần (mặc định 0.10 tức +/-10%).

        Returns:
            GuardrailResult: Chứa giá cuối cùng, chênh lệch VND/%, cờ chặn giá sàn và danh sách ghi chú.
        """
        if current_price <= 0:
            raise ValueError("current_price must be greater than 0")
        if floor_price < 0:
            raise ValueError("floor_price must be non-negative")
        if cost_price < 0:
            raise ValueError("cost_price must be non-negative")
        if max_rate_cap <= 0:
            raise ValueError("max_rate_cap must be positive")

        guardrail_notes: List[str] = []

        # 1. Rate-of-Change Cap
        if target_delta_pct > max_rate_cap:
            clamped_pct = max_rate_cap
            guardrail_notes.append(
                f"Rate-of-change cap activated: Adjustment clamped from {target_delta_pct:+.1%} to {clamped_pct:+.1%}"
            )
        elif target_delta_pct < -max_rate_cap:
            clamped_pct = -max_rate_cap
            guardrail_notes.append(
                f"Rate-of-change cap activated: Adjustment clamped from {target_delta_pct:+.1%} to {clamped_pct:+.1%}"
            )
        else:
            clamped_pct = target_delta_pct

        raw_candidate_price = int(round(current_price * (1.0 + clamped_pct)))
        unclamped_target_price = int(round(current_price * (1.0 + target_delta_pct)))

        # 2. Margin Floor Check
        if raw_candidate_price < floor_price or (
            unclamped_target_price < floor_price and raw_candidate_price <= floor_price
        ):
            final_price = floor_price
            is_floor_capped = True
            guardrail_notes.append("Margin floor protection activated: Price capped at floor_price")
        else:
            final_price = raw_candidate_price
            is_floor_capped = False

        # 3. Recalculate deltas
        price_delta_amount = final_price - current_price
        price_delta_pct = round((final_price - current_price) / current_price, 4)

        # 4. Predatory Pricing Check
        if competitor_price is not None and competitor_price < int(cost_price * 0.8):
            guardrail_notes.append(
                "Predatory pricing warning: Competitor price is below 80% of cost price"
            )

        return GuardrailResult(
            final_price=final_price,
            price_delta_amount=price_delta_amount,
            price_delta_pct=price_delta_pct,
            is_floor_capped=is_floor_capped,
            guardrail_notes=guardrail_notes,
        )
