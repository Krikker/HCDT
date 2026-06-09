from app.models import IncidentEvent, LearningState, Operator, PayrollState, Recommendation, RiskDecision, Station
from app.tool_catalog import tool_label


class PayrollEngine:
    def evaluate(
        self,
        operator: Operator,
        station: Station,
        risk: RiskDecision,
        learning: LearningState,
        recommendation: Recommendation,
        event_log: list[IncidentEvent],
    ) -> PayrollState:
        base_earned = operator.hourly_rate_rub * operator.current_shift_hours

        quality_bonus = round(
            operator.hourly_rate_rub
            * operator.current_shift_hours
            * max(0, learning.bonus_coefficient - 1),
            2,
        )

        risk_penalty_map = {"low": 40.0, "medium": 180.0, "high": 420.0, "critical": 760.0}
        risk_penalty = risk_penalty_map[risk.level]
        incident_delta = round(sum(event.payroll_delta_rub for event in event_log), 2)

        mentor_bonus = 220.0 if operator.skill_level == "senior" and learning.trust_score >= 90 else 0.0
        projected_total = max(0.0, base_earned + quality_bonus + mentor_bonus + incident_delta - risk_penalty)

        explanation = (
            f"База за {operator.current_shift_hours} ч на участке '{station.name}' составляет {round(base_earned, 2)} руб. "
            f"Бонус за качество: {quality_bonus} руб, влияние риска: -{risk_penalty} руб, "
            f"события смены: {incident_delta} руб. Рекомендуемый инструмент: {tool_label(recommendation.recommended_tool)}."
        )

        return PayrollState(
            earned_so_far_rub=round(max(0.0, base_earned + quality_bonus + mentor_bonus + incident_delta - risk_penalty / 2), 2),
            projected_shift_total_rub=round(projected_total, 2),
            quality_bonus_rub=quality_bonus,
            risk_penalty_rub=risk_penalty,
            incident_penalty_rub=incident_delta,
            mentor_bonus_rub=mentor_bonus,
            explanation=explanation,
        )
