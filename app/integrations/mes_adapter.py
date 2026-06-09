from app.models import MesTask


class MESAdapter:
    """
    Demo MES adapter.
    In a real deployment this layer would read task cards, route sheets,
    and event logs from the manufacturing execution system.
    """

    def get_task(self, operator_id: str, station_id: str) -> MesTask:
        if station_id == "st-weld-body":
            return MesTask(
                operator_id=operator_id,
                station_id=station_id,
                vin="BODY-UAZ-2026-0192",
                model_code="PATRIOT-BODY",
                current_step="measure-seam",
                completed_steps=[
                    "identify-body",
                    "load-welding-program",
                    "verify-clamps",
                    "run-weld-cycle",
                ],
                shift_type="night",
            )

        if station_id == "st-engine":
            return MesTask(
                operator_id=operator_id,
                station_id=station_id,
                vin="ENG-UAZ-2026-4411",
                model_code="ZMZ-PRO",
                current_step="tighten-head-bolts",
                completed_steps=["identify-engine", "mount-block"],
                shift_type="day",
            )

        if station_id == "st-paint":
            return MesTask(
                operator_id=operator_id,
                station_id=station_id,
                vin="PAINT-UAZ-2026-8831",
                model_code="PICKUP-PAINT",
                current_step="set-paint-mode",
                completed_steps=["identify-body", "prepare-surface"],
                shift_type="day",
            )

        if station_id == "st-door":
            return MesTask(
                operator_id=operator_id,
                station_id=station_id,
                vin="XTT316300R0001842",
                model_code="PATRIOT-2026",
                current_step="tighten-bolts",
                completed_steps=["identify-vin", "mount-door"],
                shift_type="night",
            )

        if station_id == "st-qc":
            return MesTask(
                operator_id=operator_id,
                station_id=station_id,
                vin="XTT236500R0009471",
                model_code="PICKUP-2026",
                current_step="check-torque-mark",
                completed_steps=["identify-vin", "check-gaps"],
                shift_type="day",
            )

        return MesTask(
            operator_id=operator_id,
            station_id=station_id,
            vin="KIT-UAZ-2026-1024",
            model_code="KIT-LOG-1",
            current_step="pick-parts",
            completed_steps=["read-route-task", "scan-cell"],
            shift_type="day",
        )
