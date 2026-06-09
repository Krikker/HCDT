from app.models import MesTask, RegulationDecision, SensorSnapshot, Station
from app.tool_catalog import tool_label


class RegulationEngine:
    def evaluate(
        self,
        station: Station,
        mes_task: MesTask,
        sensor_snapshot: SensorSnapshot,
    ) -> RegulationDecision:
        expected_index = len(mes_task.completed_steps)
        expected_step = station.process_steps[expected_index]
        current_step_allowed = mes_task.current_step == expected_step
        tool_allowed = sensor_snapshot.tool_connected in station.allowed_tools

        violation_reason = None
        if not current_step_allowed:
            violation_reason = (
                f"Нарушена последовательность: ожидается шаг '{expected_step}', "
                f"а получен '{mes_task.current_step}'."
            )
        elif not tool_allowed:
            violation_reason = f"Подключен недопустимый инструмент '{tool_label(sensor_snapshot.tool_connected)}'."
        elif mes_task.current_step == "tighten-bolts" and sensor_snapshot.tool_connected != "torque-wrench":
            tool_allowed = False
            violation_reason = "Для затяжки крепежа нужен динамометрический ключ, иначе возрастает риск скрытого дефекта."

        next_allowed_steps = []
        if current_step_allowed and expected_index + 1 < len(station.process_steps):
            next_allowed_steps.append(station.process_steps[expected_index + 1])

        return RegulationDecision(
            current_step_allowed=current_step_allowed,
            tool_allowed=tool_allowed,
            next_allowed_steps=next_allowed_steps,
            violation_reason=violation_reason,
        )
