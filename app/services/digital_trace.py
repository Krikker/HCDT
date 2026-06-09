from app.models import DigitalTrace, MesTask, Operator, SensorSnapshot, Station


class DigitalTraceService:
    """
    Sense layer.
    Converts operator, task, and IIoT context into a single live trace.
    """

    def build_trace(
        self,
        operator: Operator,
        station: Station,
        mes_task: MesTask,
        sensor_snapshot: SensorSnapshot,
    ) -> DigitalTrace:
        fatigue_index = min(
            1.0,
            operator.fatigue_base
            + operator.current_shift_hours / 14
            + (0.12 if mes_task.shift_type == "night" else 0.0)
            - sensor_snapshot.micro_pause_minutes / 100,
        )

        environment_risk = min(
            1.0,
            (0.35 if not sensor_snapshot.lighting_ok else 0.0)
            + sensor_snapshot.noise_level * 0.55
            + min(sensor_snapshot.cycle_deviation_sec / 90, 0.35),
        )

        attention_risk = min(
            1.0,
            fatigue_index * 0.45
            + operator.training_gap * 0.2
            + min(operator.recent_errors * 0.12, 0.24)
            + environment_risk * 0.25,
        )

        current_step_index = station.process_steps.index(mes_task.current_step)
        predicted_next_step = station.process_steps[
            min(current_step_index + 1, len(station.process_steps) - 1)
        ]

        return DigitalTrace(
            operator_id=operator.id,
            station_id=station.id,
            shift_type=mes_task.shift_type,
            current_step=mes_task.current_step,
            completed_steps=mes_task.completed_steps,
            tool_connected=sensor_snapshot.tool_connected,
            trust_score=operator.trust_score,
            fatigue_index=round(fatigue_index, 3),
            attention_risk=round(attention_risk, 3),
            training_gap=operator.training_gap,
            environment_risk=round(environment_risk, 3),
            cycle_drift=round(min(sensor_snapshot.cycle_deviation_sec / 60, 1.0), 3),
            predicted_next_step=predicted_next_step,
        )
