from app.models import ErpMotivation, IncidentEvent, LearningState, RegulationDecision, RiskDecision


class ReputationEngine:
    def update(
        self,
        trust_score: float,
        risk: RiskDecision,
        regulation: RegulationDecision,
        motivation: ErpMotivation,
        event_log: list[IncidentEvent],
    ) -> LearningState:
        delta = 0.0
        if regulation.current_step_allowed and regulation.tool_allowed:
            delta += 1.8
        if risk.level == "low":
            delta += 1.2
        elif risk.level == "medium":
            delta += 0.3
        elif risk.level == "high":
            delta -= 1.5
        else:
            delta -= 3.0

        incident_delta = round(sum(event.trust_delta for event in event_log), 2)
        updated_trust = max(0.0, min(100.0, trust_score + delta + incident_delta))

        normalized_trust = updated_trust / 100
        bonus_coefficient = (
            1
            + motivation.bonus_plan_percent / 100
            * (
                normalized_trust * motivation.quality_weight
                + (1 if regulation.current_step_allowed else 0) * motivation.discipline_weight
            )
        )

        if updated_trust >= 90:
            growth_hint = "Можно назначать на роль наставника и сложные станции."
            micro_lesson = "Закрепить статус эксперта: короткий разбор кейсов и помощь младшим операторам."
            skill_progress_percent = 96
        elif updated_trust >= 75:
            growth_hint = "Подходит для расширения профиля и cross-skill обучения."
            micro_lesson = "Повторить критические точки регламента и пройти мини-тренажер по нестандартным ситуациям."
            skill_progress_percent = 82
        elif updated_trust >= 60:
            growth_hint = "Нужны точечные тренировки по критическим операциям."
            micro_lesson = "Пройти обучающий сценарий по последовательности шагов и выбору инструмента."
            skill_progress_percent = 64
        else:
            growth_hint = "Требуется усиленное сопровождение мастером и повторное обучение."
            micro_lesson = "Перейти в режим наставничества на 2-3 цикла и подтвердить понимание регламента."
            skill_progress_percent = 41

        return LearningState(
            trust_score=round(updated_trust, 2),
            bonus_coefficient=round(bonus_coefficient, 3),
            growth_hint=growth_hint,
            micro_lesson=micro_lesson,
            skill_progress_percent=skill_progress_percent,
            shift_trust_delta=round(delta + incident_delta, 2),
        )
