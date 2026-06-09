from app.models import Recommendation, RegulationDecision, RiskDecision, Station


class RecommendationEngine:
    def build(
        self,
        station: Station,
        regulation: RegulationDecision,
        risk: RiskDecision,
    ) -> Recommendation:
        actions: list[str] = []
        teaching_points: list[str] = []
        recommended_tool = station.allowed_tools[0]

        if not regulation.tool_allowed:
            actions.append("Выберите допустимый инструмент для текущего шага и подтвердите его перед продолжением.")
            actions.append("Сверьте название инструмента на терминале с тем, что используется на рабочем месте.")
            teaching_points.append("Сначала выбирайте нужный инструмент, затем переходите к выполнению шага.")
            teaching_points.append("Если инструмент не совпадает с маршрутом, не подтверждайте шаг до замены.")

        if not regulation.current_step_allowed:
            actions.append("Вернитесь к предыдущему обязательному шагу и закройте его перед переходом дальше.")
            actions.append("Сверьте маршрут операции с текущим номером шага на терминале.")
            teaching_points.append("Не пропускайте контрольные шаги: они фиксируют правильность выполнения операции.")
            teaching_points.append("Переходите дальше только после подтверждения текущего действия в системе.")

        if risk.level in {"high", "critical"}:
            actions.append("Сделайте короткую паузу и повторно проверьте текущий шаг, инструмент и последовательность операции.")
            actions.append("Выполняйте действия по одному, подтверждая каждый шаг только после фактической проверки результата.")
            actions.append("Если есть сомнение в результате, позовите мастера до подтверждения шага.")
            teaching_points.append("При высоком риске не ускоряйте темп: важнее точность, чем скорость завершения шага.")
            teaching_points.append("После каждого действия сверяйте результат с маршрутом и визуальным состоянием узла.")
        elif risk.level == "medium":
            actions.append("Повторно сверьте инструмент и текущий шаг перед подтверждением операции.")
            actions.append("Проверьте, не осталось ли незакрытых действий по маршруту.")
            teaching_points.append("При среднем риске достаточно короткой самопроверки перед переходом к следующему шагу.")

        if not actions:
            actions.append("Продолжайте работу по текущему маршруту и подтверждайте шаги сразу после их выполнения.")
            actions.append("Перед переходом дальше убедитесь, что инструмент и состояние узла соответствуют операции.")
            teaching_points.append("Поддерживайте текущий ритм и не пропускайте подтверждение завершенных действий.")

        if station.segment == "welding":
            recommended_tool = "seam-gauge"
            teaching_points.append("После сварки сначала проверьте геометрию и состояние шва, затем переходите к следующему шагу.")
            teaching_points.append("Если есть отклонение по шву, не запускайте следующий цикл до повторной проверки.")
        elif station.segment == "assembly":
            recommended_tool = "torque-wrench"
            teaching_points.append("На операциях затяжки фиксируйте момент и угол, чтобы исключить скрытый дефект крепежа.")
            teaching_points.append("После затяжки убедитесь, что крепеж закрыт полностью и без перекоса.")
        elif station.segment == "paint":
            recommended_tool = "thickness-meter"
            teaching_points.append("Перед нанесением материала проверьте режим камеры и состояние поверхности.")
            teaching_points.append("После прохода сверяйте толщину покрытия, а не переходите сразу к следующей детали.")
        elif station.segment == "quality":
            recommended_tool = "gap-gauge"
            teaching_points.append("В ОТК сначала измеряйте зазоры и контрольные признаки, затем оформляйте выпуск.")
            teaching_points.append("Если параметр вызывает сомнение, зафиксируйте отклонение до закрытия операции.")
        elif station.segment == "logistics":
            recommended_tool = "pick-to-light"
            teaching_points.append("При комплектации сначала сканируйте ячейку, затем деталь и только потом закрывайте набор.")
            teaching_points.append("Не подтверждайте комплект, пока не проверена каждая позиция по маршруту.")

        if risk.level == "critical":
            summary = "Высокая вероятность дефекта до завершения операции."
        elif risk.level == "high":
            summary = "Есть существенный риск ошибки, нужен более внимательный проход по шагам."
        elif risk.level == "medium":
            summary = "Нужна дополнительная самопроверка перед следующим действием."
        else:
            summary = "Ситуация стабильна, можно продолжать работу по маршруту."

        explanation_parts = [
            f"Станция '{station.name}' относится к зоне риска '{station.risk_zone}'.",
            f"Уровень когнитивного риска: {risk.level}.",
            f"Потенциальная цена дефекта: около {station.quality_cost_rub} руб.",
        ]
        if regulation.violation_reason:
            explanation_parts.append(regulation.violation_reason)
        explanation_parts.extend(risk.top_factors[:2])

        return Recommendation(
            summary=summary,
            explanation=" ".join(explanation_parts),
            actions=actions[:4],
            teaching_points=teaching_points[:4],
            recommended_tool=recommended_tool,
            next_check_in_minutes=5 if risk.level in {"high", "critical"} else 12,
        )
