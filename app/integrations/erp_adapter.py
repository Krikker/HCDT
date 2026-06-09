from app.models import ErpMotivation


class ERPAdapter:
    """
    Demo ERP adapter.
    This block simulates the motivation profile used to calculate
    the bonus coefficient tied to trust and quality compliance.
    """

    def get_motivation_profile(self, operator_id: str) -> ErpMotivation:
        if operator_id == "op-101":
            return ErpMotivation(
                operator_id=operator_id,
                bonus_plan_percent=18,
                discipline_weight=0.45,
                quality_weight=0.55,
            )

        return ErpMotivation(
            operator_id=operator_id,
            bonus_plan_percent=22,
            discipline_weight=0.35,
            quality_weight=0.65,
        )
