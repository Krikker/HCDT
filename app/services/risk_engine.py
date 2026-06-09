from app.models import DigitalTrace, Operator, RegulationDecision, RiskDecision, SensorSnapshot, Station


class RiskEngine:
    """
    Reason layer part 2.
    Calculates the cognitive risk index and exposes a readable breakdown.
    """

    def evaluate(
        self,
        operator: Operator,
        station: Station,
        trace: DigitalTrace,
        regulation: RegulationDecision,
        sensor_snapshot: SensorSnapshot,
    ) -> RiskDecision:
        breakdown = [
            {
                "label": "Усталость смены",
                "value": round(trace.fatigue_index * 0.25, 3),
                "explanation": "Чем ближе конец смены и меньше пауз, тем выше риск ошибки.",
            },
            {
                "label": "Риск потери внимания",
                "value": round(trace.attention_risk * 0.2, 3),
                "explanation": "Учитывает накопленные ошибки, нагрузку и отвлекающий контекст.",
            },
            {
                "label": "Нехватка обучения",
                "value": round(trace.training_gap * 0.15, 3),
                "explanation": "Если профиль обучения закрыт не полностью, система усиливает поддержку.",
            },
            {
                "label": "Контекст рабочего места",
                "value": round(trace.environment_risk * 0.1, 3),
                "explanation": "Шум, освещенность и отклонение цикла влияют на надежность выполнения.",
            },
            {
                "label": "Отклонение темпа",
                "value": round(trace.cycle_drift * 0.1, 3),
                "explanation": "Резкое изменение темпа часто связано с пропуском контрольного действия.",
            },
            {
                "label": "Критичность участка",
                "value": 0.12 if station.risk_zone == "high" else 0.05,
                "explanation": "На критичных участках даже небольшой промах дороже для качества.",
            },
            {
                "label": "Trust Score",
                "value": round(((100 - operator.trust_score) / 100) * 0.08, 3),
                "explanation": "Низкий рейтинг доверия повышает частоту повторных проверок.",
            },
            {
                "label": "Инструмент не соответствует",
                "value": 0.18 if not regulation.tool_allowed else 0.0,
                "explanation": "Если инструмент не подходит шагу, риск дефекта растет резко.",
            },
            {
                "label": "Нарушение маршрута",
                "value": 0.15 if not regulation.current_step_allowed else 0.0,
                "explanation": "Пропуск шага регламента мешает системе подтвердить безопасный переход дальше.",
            },
            {
                "label": "Параметр операции вне допуска",
                "value": 0.08 if not sensor_snapshot.torque_ok else 0.0,
                "explanation": "Например, момент затяжки или аналогичный параметр вышел из диапазона.",
            },
        ]

        risk = max(0.0, min(1.0, sum(item["value"] for item in breakdown)))

        if risk >= 0.8:
            level = "critical"
        elif risk >= 0.6:
            level = "high"
        elif risk >= 0.35:
            level = "medium"
        else:
            level = "low"

        top_factors: list[str] = []
        if trace.fatigue_index >= 0.55:
            top_factors.append("Накопленная усталость смены")
        if trace.environment_risk >= 0.45:
            top_factors.append("Неблагоприятный контекст рабочего места")
        if not regulation.tool_allowed:
            top_factors.append("Несоответствие инструмента текущей операции")
        if not regulation.current_step_allowed:
            top_factors.append("Риск пропуска шага регламента")
        if not sensor_snapshot.torque_ok:
            top_factors.append("Параметр операции вышел за допустимый диапазон")
        if operator.training_gap >= 0.2:
            top_factors.append("Незавершенный обучающий профиль")

        if not top_factors:
            top_factors.append("Отклонения незначительны, процесс стабилен")

        return RiskDecision(
            cognitive_risk_index=round(risk, 3),
            level=level,
            top_factors=top_factors,
            breakdown=breakdown,
        )
